"use client";
import { useState } from "react";
import { SendIcon } from "@/components/icons";

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState("");

  function handleSend() {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
  }

  return (
    <div className="chat-input-area">
      <div className="chat-input-wrap">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          aria-label="Your message"
          placeholder="Type your question..."
          disabled={disabled}
          className="chat-input"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className="chat-send"
        >
          <SendIcon className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
