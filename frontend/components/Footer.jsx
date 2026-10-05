import { brand } from "@/config/brandConfig";
export default function Footer() {
  return <footer className="site-footer page-container"><div className="footer-main"><a className="wordmark" href="#home" aria-label="GlobalPath Consulting home"><span className="brand-emblem" aria-hidden="true">G<span>↗</span></span><span>GlobalPath<small>CONSULTING</small></span></a><p>{brand.footer.description}</p><nav aria-label="Footer navigation">{brand.nav.map(item => <a key={item.label} href={item.href}>{item.label}</a>)}</nav></div><div className="footer-bottom"><span>© {new Date().getFullYear()} {brand.legalLine}</span><span>Interactive demonstration for education consultancies.</span><a href="#home">Back to top ↑</a></div></footer>;
}
