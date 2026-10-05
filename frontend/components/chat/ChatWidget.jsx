"use client";
import { useEffect, useRef, useState } from "react";
import { brand } from "@/config/brandConfig";
import { sendChatMessage } from "@/lib/api";
import { useChatWidget } from "@/context/ChatWidgetContext";
import ChatHeader from "@/components/chat/ChatHeader";
import ChatMessages from "@/components/chat/ChatMessages";
import ChatInput from "@/components/chat/ChatInput";
import LeadCaptureForm from "@/components/chat/LeadCaptureForm";

let messageId = 0;
const nextId = () => `m${Date.now()}-${messageId++}`;

export default function ChatWidget() {
  const {
    isOpen,
    toggleChat,
    closeChat,
    pendingMessage,
    consumePendingMessage,
    leadFormOpen,
    openLeadForm,
    closeLeadForm,
  } = useChatWidget();

  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [lastFailedMessage, setLastFailedMessage] = useState(null);
  const [collectedFields, setCollectedFields] = useState({});
  const [leadStatus, setLeadStatus] = useState(null);
  const [leadPromptShown, setLeadPromptShown] = useState(false);

  const sessionId = useRef(null);
  if (sessionId.current === null && typeof window !== "undefined") {
    sessionId.current = crypto.randomUUID();
  }
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, error, leadFormOpen]);

  // External triggers (header/hero/CTA buttons) can send a message or open the lead form.
  useEffect(() => {
    if (pendingMessage) {
      sendMessage(pendingMessage);
      consumePendingMessage();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingMessage]);

  async function sendMessage(text, { isRetry = false } = {}) {
    if (!text.trim()) return;
    setError(false);
    if (!isRetry) {
      setMessages((prev) => [...prev, { id: nextId(), role: "user", text }]);
    }
    setLoading(true);

    try {
      const data = await sendChatMessage(sessionId.current, text);
      setMessages((prev) => [...prev, { id: nextId(), role: "assistant", text: data.reply }]);
      setCollectedFields(data.collected_fields || {});
      if (data.lead_status) setLeadStatus(data.lead_status);

      if (data.lead_ready && !leadPromptShown) {
        setLeadPromptShown(true);
        setMessages((prev) => [...prev, { id: nextId(), type: "lead-prompt" }]);
      }
    } catch {
      setError(true);
      setLastFailedMessage(text);
    } finally {
      setLoading(false);
    }
  }

  function handleRetry() {
    if (!lastFailedMessage) return;
    const text = lastFailedMessage;
    setLastFailedMessage(null);
    sendMessage(text, { isRetry: true });
  }

  function handleQuickAction(action) {
    if (action.type === "lead") {
      openLeadForm();
      return;
    }
    sendMessage(action.message);
  }

  function handleLeadSubmitted(success) {
    closeLeadForm();
    setMessages((prev) => [
      ...prev,
      {
        id: nextId(),
        role: "assistant",
        text: success
          ? "✓ Request received. A GlobalPath advisor will get in touch with you shortly."
          : "Something went wrong submitting your details. Please try again.",
      },
    ]);
  }

  return (
    <>
      {!isOpen && (
        <button onClick={toggleChat} className="adviser-launcher" aria-label="Open GlobalPath Student Adviser">
          <span className="launcher-mark" aria-hidden="true">G</span>
          <span className="launcher-copy"><small>Need help choosing your next step?</small><strong>{brand.chat.bubbleLabel}</strong></span>
          <span className="launcher-arrow" aria-hidden="true">↗</span>
        </button>
      )}
      {isOpen && (
        <section className="chat-widget" aria-label="GlobalPath Student Adviser">
          <ChatHeader onClose={closeChat} />
          <div className="chat-body">
            <ChatMessages messages={messages} loading={loading} error={error} onRetry={handleRetry} onQuickAction={handleQuickAction} onOpenLeadForm={openLeadForm} messagesEndRef={messagesEndRef} />
            {leadFormOpen && <LeadCaptureForm sessionId={sessionId.current} collectedFields={collectedFields} leadStatus={leadStatus} onClose={closeLeadForm} onSubmitted={handleLeadSubmitted} />}
          </div>
          <p className="chat-note">{brand.chat.knowledgeNote}</p>
          <ChatInput onSend={sendMessage} disabled={loading} />
        </section>
      )}
    </>
  );
}
