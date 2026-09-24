/**
 * The Wall of Founders mark: a tiny masonry wall. Three columns of rounded tiles in
 * staggered heights (the layout of the site itself), with one tile in the accent colour:
 * the story pinned to the wall. Flat and geometric; readable down to 16px.
 */
export function LogoMark({ className = "h-8 w-8", title = "Wall of Founders" }: { className?: string; title?: string }) {
  return (
    <svg viewBox="0 0 32 32" role="img" aria-label={title} className={className}>
      <title>{title}</title>
      <g fill="currentColor">
        <rect x="1.5" y="1.5" width="8.6" height="16" rx="2.6" />
        <rect x="1.5" y="20" width="8.6" height="10.5" rx="2.6" />
        <rect x="11.7" y="11.2" width="8.6" height="19.3" rx="2.6" />
        <rect x="21.9" y="1.5" width="8.6" height="10" rx="2.6" />
        <rect x="21.9" y="14" width="8.6" height="16.5" rx="2.6" />
      </g>
      <rect x="11.7" y="1.5" width="8.6" height="7.2" rx="2.6" fill="var(--accent)" />
    </svg>
  );
}

export function Logo({ withWordmark = true }: { withWordmark?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark className="h-7 w-7 shrink-0" />
      {withWordmark && (
        <span className="font-serif text-[1.45rem] leading-none tracking-tight">
          Wall <span className="italic text-muted">of</span> Founders
        </span>
      )}
    </span>
  );
}
