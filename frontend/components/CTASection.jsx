"use client";
import { brand } from "@/config/brandConfig";
import { useChatWidget } from "@/context/ChatWidgetContext";
export default function CTASection() {
  const { openLeadForm } = useChatWidget();
  return <section id="contact" className="final-cta" aria-labelledby="cta-title"><div className="page-container"><p className="eyebrow">LET’S BEGIN</p><h2 id="cta-title">Your study journey starts<br />with the <em>right conversation.</em></h2><p>{brand.ctaSection.sub}</p><button className="button button-light" onClick={openLeadForm}>{brand.ctaSection.primaryCta}<span aria-hidden="true">↗</span></button></div></section>;
}
