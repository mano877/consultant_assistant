"use client";
import { brand } from "@/config/brandConfig";
import { useChatWidget } from "@/context/ChatWidgetContext";
import EditorialImagePlaceholder from "@/components/EditorialImagePlaceholder";

export default function Hero() {
  const { openChat, openLeadForm } = useChatWidget();
  return (
    <section id="home" className="hero page-container" aria-labelledby="hero-title">
      <div className="hero-copy">
        <p className="eyebrow"><span className="eyebrow-line" />{brand.hero.eyebrow}</p>
        <h1 id="hero-title">Study abroad<br />with <em>clarity</em><br />and confidence.</h1>
        <p className="hero-description">{brand.hero.sub}</p>
        <div className="hero-actions">
          <a className="button button-primary" href="#destinations">{brand.hero.primaryCta}<span aria-hidden="true">↗</span></a>
          <button className="text-link" onClick={openLeadForm}>{brand.hero.secondaryCta}<span aria-hidden="true">↗</span></button>
        </div>
        <div className="hero-adviser"><span>Considering your options?</span><button onClick={() => openChat()}>Ask our digital student adviser <span aria-hidden="true">→</span></button></div>
      </div>
      <figure className="hero-image">
        <EditorialImagePlaceholder src="/images/hero.png" alt="Three graduates in caps and gowns walking together outside a sandstone university building" position="52% 50%" sizes="(max-width: 600px) calc(100vw - 40px), (max-width: 1100px) 45vw, 575px" preload />
        <figcaption><span>A WORLD OF POSSIBILITY</span><span>Your next chapter, thoughtfully planned.</span></figcaption>
      </figure>
    </section>
  );
}
