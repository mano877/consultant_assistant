"use client";
import { useState } from "react";
import { brand } from "@/config/brandConfig";
import { submitLead } from "@/lib/api";
import { XIcon } from "@/components/icons";

const VISIBLE_FIELDS = [
  { key: "name", label: "Full Name", type: "text", autoComplete: "name" },
  { key: "email", label: "Email", type: "email", autoComplete: "email" },
  { key: "phone_whatsapp", label: "Phone / WhatsApp", type: "tel", autoComplete: "tel" },
  { key: "course_interest", label: "Interested In", type: "text", autoComplete: "off" },
  { key: "preferred_location", label: "Preferred Destination", type: "text", autoComplete: "off" },
];

const CARRIED_FIELD_DEFAULTS = {
  current_education: "Not specified",
  english_test_status: "Not specified",
  budget_intake: "Not specified",
  current_country_status: "Not specified",
};

export default function LeadCaptureForm({ sessionId, collectedFields, leadStatus, onClose, onSubmitted }) {
  const [form, setForm] = useState(() => {
    const base = {};
    for (const field of VISIBLE_FIELDS) {
      base[field.key] = collectedFields?.[field.key] || "";
    }
    return base;
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError(false);

    const payload = {
      session_id: sessionId,
      ...form,
    };
    for (const [key, fallback] of Object.entries(CARRIED_FIELD_DEFAULTS)) {
      payload[key] = collectedFields?.[key] || fallback;
    }
    for (const key of ["budget", "intake"]) {
      if (collectedFields?.[key]) payload[key] = collectedFields[key];
    }
    if (leadStatus) payload.lead_status = leadStatus;

    try {
      await submitLead(payload);
      setSuccess(true);
      setTimeout(() => onSubmitted(true), 1400);
    } catch {
      setSubmitError(true);
      setSubmitting(false);
    }
  }

  return (
    <div className="lead-form-panel" role="region" aria-label="Request a consultation">
      {success ? (
        <div className="lead-success" role="status"><span aria-hidden="true">✓</span><h2>Request received.</h2><p>Your details have been saved for demonstration.</p></div>
      ) : (
        <>
          <div className="lead-form-heading"><div><h2>Ready for personalised guidance?</h2><p>Share a few details to try the education consultancy demonstration.</p></div><button aria-label="Close form" onClick={onClose} className="chat-close form-close"><XIcon /></button></div>
          <form onSubmit={handleSubmit} className="consultation-form chat-scroll">
            {VISIBLE_FIELDS.map((field) => (
              <label key={field.key}>{field.label}<input required type={field.type} autoComplete={field.autoComplete} value={form[field.key]} onChange={(e) => setForm((prev) => ({ ...prev, [field.key]: e.target.value }))} /></label>
            ))}
            {submitError && <p className="form-error" role="alert">Something went wrong submitting your details. Please try again.</p>}
            <button type="submit" disabled={submitting} className="button button-primary">{submitting ? "Submitting..." : "Request a consultation"}<span aria-hidden="true">→</span></button>
          </form>
        </>
      )}
    </div>
  );
}
