/** Original artwork used when a story has no cover photo. Chosen deterministically per slug. */
const ART = ["/art/dusk.webp", "/art/night.webp", "/art/dusk-portrait.webp"];

export function artFor(seed: string): string {
  let h = 0;
  for (const ch of seed) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return ART[h % ART.length];
}
