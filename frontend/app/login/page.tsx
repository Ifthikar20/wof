"use client";

import Link from "next/link";
import { AuthShell } from "@/components/AuthShell";
import { LoginForm } from "@/components/LoginForm";
import { safeNext } from "@/lib/safe-redirect";

export default function LoginPage() {
  return (
    <AuthShell art="/art/dusk-portrait.webp" quote="Every story here was lived by the person who wrote it.">
      <h1 className="font-serif text-5xl leading-none">Welcome back</h1>
      <p className="mb-8 mt-3 text-muted">Log in to save stories and follow founders.</p>
      <LoginForm
        autoFocus
        onSuccess={() => {
          window.location.href = safeNext(new URLSearchParams(window.location.search).get("next"));
        }}
      />
      <p className="mt-8 text-center text-sm text-muted">
        New here? <Link className="font-semibold text-ink underline underline-offset-4" href="/signup">Create an account</Link>
      </p>
    </AuthShell>
  );
}
