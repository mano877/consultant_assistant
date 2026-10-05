"use client";
import { createContext, useCallback, useContext, useMemo, useState } from "react";

const ChatWidgetContext = createContext(null);

export function ChatWidgetProvider({ children }) {
  const [isOpen, setIsOpen] = useState(false);
  const [pendingMessage, setPendingMessage] = useState(null);
  const [leadFormOpen, setLeadFormOpen] = useState(false);

  const openChat = useCallback((message) => {
    setIsOpen(true);
    if (message) setPendingMessage(message);
  }, []);

  const openLeadForm = useCallback(() => {
    setIsOpen(true);
    setLeadFormOpen(true);
  }, []);

  const closeLeadForm = useCallback(() => setLeadFormOpen(false), []);
  const closeChat = useCallback(() => setIsOpen(false), []);
  const toggleChat = useCallback(() => setIsOpen((prev) => !prev), []);

  const consumePendingMessage = useCallback(() => {
    setPendingMessage(null);
  }, []);

  const value = useMemo(
    () => ({
      isOpen,
      openChat,
      closeChat,
      toggleChat,
      openLeadForm,
      closeLeadForm,
      leadFormOpen,
      pendingMessage,
      consumePendingMessage,
    }),
    [isOpen, openChat, closeChat, toggleChat, openLeadForm, closeLeadForm, leadFormOpen, pendingMessage, consumePendingMessage]
  );

  return <ChatWidgetContext.Provider value={value}>{children}</ChatWidgetContext.Provider>;
}

export function useChatWidget() {
  const ctx = useContext(ChatWidgetContext);
  if (!ctx) throw new Error("useChatWidget must be used within a ChatWidgetProvider");
  return ctx;
}
