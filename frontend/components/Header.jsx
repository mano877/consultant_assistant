"use client";
import { useState } from "react";
import { brand } from "@/config/brandConfig";
import { useChatWidget } from "@/context/ChatWidgetContext";

export default function Header() {
  const { openLeadForm } = useChatWidget();
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <header className="site-header">
      <div className="page-container header-inner">
        <a className="wordmark" href="#home" aria-label="Consultancy AI Assistant home">
          <span className="brand-emblem" aria-hidden="true">C<span>↗</span></span>
          <span>Consultancy<small>AI ASSISTANT</small></span>
        </a>
        <nav className="desktop-nav" aria-label="Main navigation">
          {brand.nav.map(item => <a key={item.label} href={item.href}>{item.label}</a>)}
        </nav>
        <button className="button button-outline header-cta" onClick={openLeadForm}>Talk to an Adviser <span aria-hidden="true">↗</span></button>
        <button className="menu-toggle" aria-label={mobileOpen ? "Close menu" : "Open menu"} aria-expanded={mobileOpen} aria-controls="mobile-navigation" onClick={() => setMobileOpen(v => !v)}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d={mobileOpen ? "M6 6l12 12M18 6 6 18" : "M4 8h16M4 16h16"} /></svg>
        </button>
      </div>
      {mobileOpen && <nav id="mobile-navigation" className="mobile-nav page-container" aria-label="Mobile navigation">
        {brand.nav.map(item => <a key={item.label} href={item.href} onClick={() => setMobileOpen(false)}>{item.label}<span aria-hidden="true">↗</span></a>)}
        <button className="button button-primary" onClick={() => { setMobileOpen(false); openLeadForm(); }}>Talk to an Adviser <span aria-hidden="true">↗</span></button>
      </nav>}
    </header>
  );
}
