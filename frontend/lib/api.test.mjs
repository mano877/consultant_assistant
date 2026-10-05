import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

// Load the actual browser API module without changing the package module type.
const source = await readFile(new URL("./api.js", import.meta.url), "utf8");
const { sendChatMessage, submitLead } = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);

test("chat and lead retain the supplied session ID", async (t) => {
  const bodies = [];
  t.mock.method(globalThis, "fetch", async (_url, options) => {
    bodies.push(JSON.parse(options.body));
    return { ok: true, json: async () => ({ reply: "Hello" }) };
  });
  await sendChatMessage("visitor-1", "Hello");
  await sendChatMessage("visitor-1", "Next question");
  await submitLead({ session_id: "visitor-1", name: "Test" });
  assert.deepEqual(bodies.map((b) => b.session_id), ["visitor-1", "visitor-1", "visitor-1"]);
});

test("non-2xx responses reject into the existing error/Retry path", async (t) => {
  t.mock.method(globalThis, "fetch", async () => ({ ok: false, status: 503 }));
  await assert.rejects(sendChatMessage("visitor-1", "Hello"), /Please try again/);
  await assert.rejects(submitLead({ session_id: "visitor-1" }), /Please try again/);
});

test("60 second timeout aborts a hanging request and allows retry", async (t) => {
  let expire;
  let cleared = 0;
  t.mock.method(globalThis, "setTimeout", (fn, delay) => {
    assert.equal(delay, 60000);
    expire = fn;
    return 1;
  });
  t.mock.method(globalThis, "clearTimeout", () => cleared++);
  t.mock.method(globalThis, "fetch", (_url, { signal }) => new Promise((_, reject) => {
    signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
  }));
  const pending = sendChatMessage("visitor-1", "Hello");
  expire();
  await assert.rejects(pending, { name: "AbortError" });
  assert.equal(cleared, 1);
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ reply: "Recovered" }) });
  assert.deepEqual(await sendChatMessage("visitor-1", "Hello"), { reply: "Recovered" });
  assert.equal(cleared, 2);
});
