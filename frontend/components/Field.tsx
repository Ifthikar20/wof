export function Field(props: { label: string; error?: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm font-semibold">{props.label}</span>
      {props.children}
      {props.hint && !props.error && <span className="text-xs text-muted">{props.hint}</span>}
      {props.error && <span className="text-xs text-red-600" role="alert">{props.error}</span>}
    </label>
  );
}

export function Card({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto mt-6 max-w-md rounded-3xl border border-line bg-surface p-8 shadow-sm">
      <h1 className="font-serif text-2xl font-bold">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      <div className="mt-6">{children}</div>
    </div>
  );
}
