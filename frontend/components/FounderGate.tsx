import Link from "next/link";
import type { Me } from "@/lib/types";

/** Explains why a founder-only screen isn't available yet, with the one next step. */
export function FounderGate({ me }: { me: Me }) {
  const needs2fa = me.is_verified_founder && !me.totp_enabled;
  return (
    <div className="mx-auto max-w-lg py-20 text-center">
      <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-chip text-3xl" aria-hidden>{needs2fa ? "🔐" : "✍️"}</span>
      <h1 className="mt-6 font-serif text-5xl leading-none">{needs2fa ? "One more step: turn on 2FA" : "Only verified founders can publish"}</h1>
      <p className="mt-4 text-muted">
        {needs2fa
          ? "Founder accounts need two-factor authentication so nobody can publish in your name."
          : "It keeps the Wall trustworthy. Submitting takes a couple of minutes: a work email and a LinkedIn or Crunchbase link."}
      </p>
      <Link href={needs2fa ? "/settings/security" : "/verify"} className="btn btn-primary mt-8 h-12 px-6">
        {needs2fa ? "Set up two-factor authentication" : "Verify that you're a founder"}
      </Link>
    </div>
  );
}
