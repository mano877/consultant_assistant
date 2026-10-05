import { brand } from "@/config/brandConfig";
import { XIcon } from "@/components/icons";
export default function ChatHeader({ onClose }) {
  return <div className="chat-header"><div className="chat-header-brand"><span className="chat-monogram" aria-hidden="true">G</span><div><p className="chat-title">{brand.chat.name}</p><p className="chat-subtitle">{brand.chat.tagline}</p></div></div><button aria-label="Close chat" onClick={onClose} className="chat-close"><XIcon /></button></div>;
}
