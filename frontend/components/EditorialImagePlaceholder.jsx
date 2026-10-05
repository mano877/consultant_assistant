import Image from "next/image";

export default function EditorialImagePlaceholder({ subject, variant = "hero", src, alt, sizes, position = "50% 50%", preload = false }) {
  if (src) {
    return (
      <div className={`editorial-placeholder placeholder-${variant}`}>
        <Image src={src} alt={alt} fill sizes={sizes} preload={preload} style={{ objectFit: "cover", objectPosition: position }} />
      </div>
    );
  }
  return (
    <div className={`editorial-placeholder placeholder-${variant}`} role="img" aria-label={`Temporary photography placeholder: ${subject}. To be replaced with licensed photography before deployment.`}>
      <div className="placeholder-frame" aria-hidden="true"><span>+</span><span>+</span><span>+</span><span>+</span></div>
      <div className="placeholder-caption"><span>PHOTOGRAPHY TO COME</span><p>{subject}</p><small>Temporary image placeholder</small></div>
    </div>
  );
}
