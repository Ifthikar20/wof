import Link from "next/link";
import { Logo } from "./Logo";

/** Split-screen auth layout: full-frame artwork on the left, the form on the right. */
export function AuthShell(props: { art: string; quote: string; children: React.ReactNode }) {
  return (
    <div className="-mt-4 grid min-h-[calc(100vh-61px)] gap-6 py-4 lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden rounded-[32px] lg:block">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={props.art} alt="" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />
        <Link href="/" className="absolute left-8 top-8 text-white" aria-label="Wall of Founders home">
          <Logo />
        </Link>
        <p className="absolute bottom-10 left-10 right-10 font-serif text-[clamp(2rem,3.2vw,3.25rem)] leading-[1.05] text-white">
          {props.quote}
        </p>
      </aside>
      <div className="flex items-center justify-center px-2 py-8">
        <div className="w-full max-w-[400px]">{props.children}</div>
      </div>
    </div>
  );
}
