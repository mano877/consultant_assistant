import { brand } from "@/config/brandConfig";

export default function Footer() {
  return (
    <footer className="site-footer page-container">
      <div className="footer-main">
        <div className="footer-brand">
          <a className="wordmark" href="#home" aria-label="Consultancy AI Assistant home">
            <span className="brand-emblem" aria-hidden="true">C<span>↗</span></span>
            <span>Consultancy<small>AI ASSISTANT</small></span>
          </a>
          <span className="footer-copyright">© {new Date().getFullYear()} {brand.legalLine}</span>
        </div>
        <p className="footer-disclaimer">Interactive demonstration for education consultancies.</p>
        <a className="footer-back-top" href="#home">Back to top ↑</a>
      </div>
    </footer>
  );
}
