export function Field(props: { label: string; error?: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[13px] font-semibold">{props.label}</span>
      {props.children}
      {props.hint && !props.error && <span className="text-xs text-muted">{props.hint}</span>}
      {props.error && <span className="text-xs text-red-600" role="alert">{props.error}</span>}
    </label>
  );
}

export function Card({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto mt-10 max-w-md rounded-[28px] border border-line/70 bg-surface/90 p-9 shadow-[0_30px_80px_-40px_rgba(21,19,15,.35)] backdrop-blur">
      <h1 className="font-serif text-4xl leading-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      <div className="mt-6">{children}</div>
    </div>
  );
}
