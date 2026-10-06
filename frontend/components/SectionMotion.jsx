"use client";

import { useEffect } from "react";

export default function SectionMotion() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;

    const elements = document.querySelectorAll(".introduction, .section-heading, .destination, .services-heading, .journey-steps li, .final-cta .page-container");
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(({ target, isIntersecting }) => {
        if (!isIntersecting) return;
        if (!target.contains(document.activeElement)) target.classList.add("section-enter");
        observer.unobserve(target);
      });
    }, { threshold: 0.12 });

    elements.forEach((element) => observer.observe(element));
    return () => {
      observer.disconnect();
      elements.forEach((element) => element.classList.remove("section-enter"));
    };
  }, []);

  return null;
}
