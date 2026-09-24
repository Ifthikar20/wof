import { SettingsNav } from "@/components/SettingsNav";

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto grid max-w-5xl gap-10 py-6 md:grid-cols-[200px_1fr]">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[.16em] text-muted">Settings</p>
        <SettingsNav />
      </div>
      <div className="min-w-0">{children}</div>
    </div>
  );
}
