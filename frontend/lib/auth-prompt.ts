/**
 * Timing rules for the sign-up prompt shown to logged-out visitors.
 *
 * This is a conversion nudge, NOT an access control: every story is in the server-rendered
 * HTML (for search engines) and the API serves it anonymously. Real protection against
 * harvesting lives server-side (rate limits, no bulk endpoints, edge bot management).
 */

export const SOFT_DELAY_MS = Number(process.env.NEXT_PUBLIC_AUTH_PROMPT_DELAY_MS ?? 45_000) || 45_000;
export const FIRM_DELAY_MS = SOFT_DELAY_MS * 2;

export type PromptState = { startedAt: number; softDismissedAt?: number };
export type PromptDecision = { mode: "soft" | "firm"; dueAt: number };

const KEY = "wof.authPrompt";
let memoryState: PromptState | null = null; // fallback when sessionStorage is blocked

/** Pages where the prompt would get in the way of completing sign-up or a token flow. */
const EXEMPT_PATHS = [/^\/login/, /^\/signup/, /^\/verify/, /^\/settings/, /^\/digest\/confirm/, /^\/digest\/unsubscribe/];

/** Search-engine crawlers and link-preview bots always see the plain page. */
const BOT_UA = /bot|crawl|spider|slurp|facebookexternalhit|linkedin|slack|discord|whatsapp|telegram|embedly|preview/i;

export function isExemptPath(path: string) {
  return EXEMPT_PATHS.some((re) => re.test(path));
}

export function isBot(userAgent: string) {
  return BOT_UA.test(userAgent);
}

/** Soft prompt after SOFT_DELAY from the start of the visit; once dismissed, a firm
 *  (non-dismissible) prompt after FIRM_DELAY more. The visit clock survives navigation. */
export function nextPrompt(state: PromptState): PromptDecision {
  if (state.softDismissedAt === undefined) {
    return { mode: "soft", dueAt: state.startedAt + SOFT_DELAY_MS };
  }
  return { mode: "firm", dueAt: state.softDismissedAt + FIRM_DELAY_MS };
}

export function loadState(now: number): PromptState {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as PromptState;
      if (typeof parsed.startedAt === "number") return parsed;
    }
  } catch {
    /* storage blocked or corrupt: fall through */
  }
  if (!memoryState) memoryState = { startedAt: now };
  saveState(memoryState);
  return memoryState;
}

export function saveState(state: PromptState) {
  memoryState = state;
  try {
    sessionStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* ignore */
  }
}
