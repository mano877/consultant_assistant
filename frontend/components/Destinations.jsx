"use client";
import EditorialImagePlaceholder from "@/components/EditorialImagePlaceholder";
import { useChatWidget } from "@/context/ChatWidgetContext";
const destinations = [
  { name: "Sydney", caption: "Find your direction.", image: "/images/sydney.jpg", alt: "Students on the lawn outside the UNSW library in Sydney", position: "30% 50%", variant: "sydney" },
  { name: "Melbourne", caption: "Imagine your next chapter.", image: "/images/melbourne.png", alt: "Students walking toward a sandstone campus entrance with University of Melbourne signage", position: "65% 50%", variant: "melbourne" },
  { name: "Brisbane", caption: "Explore a different perspective.", image: "/images/brisbane.jpg", alt: "Sandstone facade and entrance of the University of Queensland Steele Building", position: "50% 50%", variant: "brisbane" },
  { name: "Adelaide", caption: "Make room for possibility.", image: "/images/adelaide.jpg", alt: "Adelaide University campus courtyard with brick arcades and Adelaide lettering", position: "50% 75%", variant: "adelaide" },
];
export default function Destinations() {
  const { openChat } = useChatWidget();
  return (
    <section id="destinations" className="destinations section-space" aria-labelledby="destinations-title">
      <div className="page-container">
        <div className="section-heading"><div><p className="eyebrow">FIND YOUR PLACE</p><h2 id="destinations-title">A new chapter.<br /><em>An Australian setting.</em></h2></div><p>Start with a place that speaks to you.<br />Then explore the study options that fit.</p></div>
        <div className="destination-grid">{destinations.map((city, index) => (
          <article className="destination" key={city.name}>
            <button className="destination-button" onClick={() => openChat(`I'd like to explore IT study options in ${city.name}. What information do you need from me?`)} aria-label={`Explore study options in ${city.name}`}>
              <EditorialImagePlaceholder src={city.image} alt={city.alt} position={city.position} variant={city.variant} sizes="(max-width: 600px) calc((100vw - 56px) / 2), (max-width: 850px) calc((100vw - 96px) / 2), (max-width: 1360px) 22vw, 294px" />
              <span className="destination-title"><span><small>0{index + 1} / AUSTRALIA</small><span className="destination-name">{city.name}</span></span><span className="destination-arrow" aria-hidden="true">↗</span></span>
            </button>
            <p>{city.caption}</p>
          </article>
        ))}</div>
      </div>
    </section>
  );
}
