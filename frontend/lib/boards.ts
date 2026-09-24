"use client";

import { api } from "./client-api";

export type Board = { id: string; name: string };

/** Save a story to the user's first board, creating "Saved stories" if they have none.
 *  Throws ApiException (403 when logged out) so callers can redirect to login. */
export async function saveStory(slug: string): Promise<Board> {
  const boards = await api<Board[]>("/boards");
  const board = boards[0] ?? (await api<Board>("/boards", { method: "POST", body: { name: "Saved stories" } }));
  await api(`/boards/${board.id}/saves`, { method: "POST", body: { story: slug } });
  return board;
}
