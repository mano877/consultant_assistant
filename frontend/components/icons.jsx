function base(children, props) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

export function SendIcon(props) {
  return base(<path d="M22 2 11 13M22 2 15 22l-4-9-9-4 20-7Z" />, props);
}

export function XIcon(props) {
  return base(<path d="M18 6 6 18M6 6l12 12" />, props);
}

export function RefreshIcon(props) {
  return base(
    <>
      <path d="M21 12a9 9 0 1 1-3-6.7" />
      <path d="M21 3v6h-6" />
    </>,
    props
  );
}
