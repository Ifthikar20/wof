/** Initial-based avatar (no third-party avatar services, no tracking). */
export function Avatar({ name, size = 40, className = "" }: { name: string; size?: number; className?: string }) {
  return (
    <span
      aria-hidden
      className={`grid shrink-0 place-items-center rounded-full bg-ink font-semibold text-bg ${className}`}
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {name.slice(0, 1).toUpperCase()}
    </span>
  );
}
