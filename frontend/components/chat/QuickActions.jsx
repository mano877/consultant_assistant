import { brand } from "@/config/brandConfig";
export default function QuickActions({ onSelect }) {
  return <div className="quick-actions">{brand.chat.quickActions.map(action => <button key={action.label} onClick={() => onSelect(action)}>{action.label}<span aria-hidden="true">↗</span></button>)}</div>;
}
