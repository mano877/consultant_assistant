import { brand } from "@/config/brandConfig";
import MessageBubble from "@/components/chat/MessageBubble";
import QuickActions from "@/components/chat/QuickActions";
import TypingIndicator from "@/components/chat/TypingIndicator";
import { RefreshIcon } from "@/components/icons";
export default function ChatMessages({ messages, loading, error, onRetry, onQuickAction, onOpenLeadForm, messagesEndRef }) {
  return <div className="chat-scroll chat-messages" role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions">
    {messages.length === 0 && <><div className="chat-welcome"><h2>{brand.chat.welcomeGreeting}</h2><p>{brand.chat.welcomeBody}</p></div><div><p className="starter-label">{brand.chat.welcomePrompt}</p><QuickActions onSelect={onQuickAction} /></div></>}
    {messages.map(m => m.type === "lead-prompt" ? <LeadPromptCard key={m.id} onOpen={onOpenLeadForm} /> : <MessageBubble key={m.id} role={m.role} text={m.text} />)}
    {loading && <TypingIndicator />}
    {error && <div className="chat-error" role="alert"><p>Something went wrong while connecting to the assistant. Please try again.</p><button onClick={onRetry} className="retry-button"><RefreshIcon />Retry</button></div>}
    <div ref={messagesEndRef} />
  </div>;
}
function LeadPromptCard({ onOpen }) {
  return <div className="lead-prompt"><h3>Ready for personalised guidance?</h3><p>Try the next step in this education consultancy demonstration.</p><button onClick={onOpen} className="button button-primary">Request a consultation <span aria-hidden="true">→</span></button></div>;
}
