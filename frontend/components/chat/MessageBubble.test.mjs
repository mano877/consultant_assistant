import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import swc from "next/dist/build/swc/index.js";

const source = await readFile(new URL("./MessageBubble.jsx", import.meta.url), "utf8");
const transformed = swc.transformSync(source, {
  filename: "MessageBubble.jsx",
  jsc: { parser: { syntax: "ecmascript", jsx: true }, transform: { react: { runtime: "automatic" } } },
  module: { type: "es6" },
}).code.replace(/from (["'])([^"']+)\1/g, (_match, _quote, specifier) => {
  const url = specifier === "@/config/brandConfig"
    ? new URL("../../config/brandConfig.js", import.meta.url).href
    : import.meta.resolve(specifier);
  return `from ${JSON.stringify(url)}`;
});
const { default: MessageBubble } = await import(`data:text/javascript;base64,${Buffer.from(transformed).toString("base64")}`);
const render = (text, role = "assistant") => renderToStaticMarkup(React.createElement(MessageBubble, { role, text }));

test("assistant Markdown renders useful formatting and tables", () => {
  const html = render("**Bold**\n\n- First\n- Second\n\n[Safe](https://example.com)\n\n| A | B |\n| - | - |\n| C | D |");
  for (const tag of ["strong", "ul", "li", "table", "th", "td"]) assert.match(html, new RegExp(`<${tag}[ >]`));
  assert.match(html, /href="https:\/\/example.com"/);
  assert.match(html, /rel="noopener noreferrer"/);
});

test("raw HTML, images, and unsafe URLs cannot create executable elements", () => {
  const html = render('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n[Bad](javascript:alert%281%29)\n\n[Data](data:text/html,test)\n\n![Remote](https://example.com/track.png)');
  assert.doesNotMatch(html, /<script|<img|onerror=|href="javascript:|href="data:/);
});

test("user content remains escaped plain text with anywhere wrapping", () => {
  const html = render('<img src=x onerror=alert(1)> **not bold**', "user");
  assert.doesNotMatch(html, /<img|<strong/);
  assert.match(html, /&lt;img/);
  assert.match(html, /overflow-wrap:anywhere/);
});
