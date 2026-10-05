const steps = [
  ["Explore your options", "Understand suitable courses and study destinations. Begin with your interests, your background, and what you want to do next."],
  ["Prepare your application", "Get guidance on requirements and application preparation, so you can approach each step with a clearer sense of what comes next."],
  ["Plan your next step", "Bring your questions to an adviser and receive personalised guidance for the journey ahead."],
];
export default function Services() {
  return (
    <section id="services" className="services page-container section-space" aria-labelledby="services-title">
      <div className="services-heading"><p className="eyebrow">HOW WE HELP</p><h2 id="services-title">Big decisions.<br /><em>Considered steps.</em></h2><p>You don’t need to have every answer.<br />Just a place to start.</p></div>
      <ol className="journey-steps">{steps.map(([title, description], index) => <li key={title}><span className="step-number">0{index + 1}</span><div><h3>{title}</h3><p>{description}</p></div></li>)}</ol>
    </section>
  );
}
