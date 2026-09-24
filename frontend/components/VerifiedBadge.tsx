export function VerifiedBadge({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 20 20"
      aria-label="Verified founder"
      role="img"
      className={`inline-block h-4 w-4 shrink-0 text-verified ${className}`}
    >
      <title>Verified founder</title>
      <path
        fill="currentColor"
        d="M10 1.5l2.2 1.6 2.7-.1.9 2.6 2.2 1.6-.8 2.6.8 2.6-2.2 1.6-.9 2.6-2.7-.1L10 18.5l-2.2-1.6-2.7.1-.9-2.6L2 12.8l.8-2.6L2 7.6l2.2-1.6.9-2.6 2.7.1L10 1.5z"
      />
      <path fill="none" stroke="var(--surface)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" d="M6.5 10.2l2.3 2.3 4.7-4.9" />
    </svg>
  );
}
