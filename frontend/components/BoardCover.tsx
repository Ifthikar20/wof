import { artFor } from "@/lib/art";

type Preview = { slug: string; thumb_url: string | null };

/** Pinterest-style board cover: one large tile and two small ones. */
export function BoardCover({ preview, seed }: { preview: Preview[]; seed: string }) {
  const src = (i: number) => (preview[i] ? preview[i].thumb_url ?? artFor(preview[i].slug) : null);
  const tile = (i: number, cls: string) => {
    const s = src(i);
    return s ? (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={s} alt="" className={`h-full w-full object-cover ${cls}`} style={{ objectPosition: `${(i * 37) % 100}% 60%` }} />
    ) : (
      <div className={`h-full w-full bg-chip ${cls}`} />
    );
  };
  return (
    <div className="grid aspect-[4/3] grid-cols-[2fr_1fr] grid-rows-2 gap-0.5 overflow-hidden rounded-[20px]" data-seed={seed}>
      <div className="row-span-2">{tile(0, "")}</div>
      <div>{tile(1, "")}</div>
      <div>{tile(2, "")}</div>
    </div>
  );
}
