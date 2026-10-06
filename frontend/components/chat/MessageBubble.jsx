import { brand } from "@/config/brandConfig";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const allowedElements = ["p", "br", "strong", "em", "del", "ul", "ol", "li", "a", "blockquote", "code", "pre", "table", "thead", "tbody", "tr", "th", "td", "hr"];

function safeUrl(url) {
  return /^(https?:\/\/|mailto:)/i.test(url) ? url : "";
}

export default function MessageBubble({ role, text }) {
  const isUser = role === "user";

  return (
    <div className={`message-row ${isUser ? "message-user" : "message-assistant"}`}>
      {!isUser && <span className="chat-monogram message-avatar" aria-hidden="true">C</span>}
      <div
        className="message-bubble [overflow-wrap:anywhere]"
        style={isUser ? { backgroundColor: brand.color } : undefined}
      >
        {isUser ? <span className="whitespace-pre-wrap">{text}</span> : (
          <div className="message-markdown">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              skipHtml
              allowedElements={allowedElements}
              unwrapDisallowed
              urlTransform={safeUrl}
              components={{
                a: ({ href, children }) => href ? <a href={href} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span>,
                table: ({ children }) => <table className="w-full table-fixed border-collapse text-left">{children}</table>,
              }}
            >{text}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
