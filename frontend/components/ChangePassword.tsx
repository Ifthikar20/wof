"use client";

import { useState } from "react";
import { Field } from "./Field";
import { api, fieldErrors } from "@/lib/client-api";

export function ChangePassword() {
  const [form, setForm] = useState({ current_password: "", new_password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);

  return (
    <section className="rounded-[24px] border border-line bg-surface/80 p-6">
      <h2 className="text-lg font-semibold">Password</h2>
      <p className="mt-1 text-sm text-muted">Changing it signs you out on every other device.</p>
      <form
        className="mt-5 grid gap-4 sm:grid-cols-2"
        onSubmit={async (e) => {
          e.preventDefault();
          setErrors({});
          setDone(false);
          try {
            await api("/auth/password", { method: "POST", body: form });
            setForm({ current_password: "", new_password: "" });
            setDone(true);
          } catch (err) {
            setErrors(fieldErrors(err));
          }
        }}
      >
        <Field label="Current password" error={errors.current_password}>
          <input id="current-password" className="input" type="password" autoComplete="current-password" required
                 value={form.current_password} onChange={(e) => setForm({ ...form, current_password: e.target.value })} />
        </Field>
        <Field label="New password" error={errors.new_password} hint="12+ characters, not found in data breaches.">
          <input id="new-password" className="input" type="password" autoComplete="new-password" minLength={12} required
                 value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} />
        </Field>
        <div className="flex items-center gap-3 sm:col-span-2">
          <button className="btn btn-primary">Update password</button>
          {done && <span className="text-sm text-emerald-700" role="status">Password updated. Other devices were signed out.</span>}
        </div>
      </form>
    </section>
  );
}
