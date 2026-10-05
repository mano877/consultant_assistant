import Header from "@/components/Header";
import Hero from "@/components/Hero";
import Introduction from "@/components/Introduction";
import Destinations from "@/components/Destinations";
import Services from "@/components/Services";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";
import ChatWidget from "@/components/chat/ChatWidget";
export default function Home() {
  return <><a className="skip-link" href="#main-content">Skip to content</a><Header /><main id="main-content"><Hero /><Introduction /><Destinations /><Services /><CTASection /></main><Footer /><ChatWidget /></>;
}
