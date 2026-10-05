const REQUEST_TIMEOUT_MS = 60000;

async function postJson(path, payload) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error("Request failed. Please try again.");
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

export function sendChatMessage(sessionId, message) {
  return postJson("/chat", { session_id: sessionId, message });
}

export function submitLead(lead) {
  return postJson("/lead", lead);
}
