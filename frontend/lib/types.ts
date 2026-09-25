export type Author = {
  handle: string;
  display_name: string;
  is_verified_founder: boolean;
  company: string | null;
  title: string | null;
};

export type Cover = {
  url: string;
  thumb_url: string;
  width: number;
  height: number;
  dominant_color: string;
};

export type StoryCard = {
  slug: string;
  title: string;
  dek: string;
  cover: Cover | null;
  author: Author;
  tags: string[];
  reading_minutes: number;
  like_count: number;
  save_count: number;
  comment_count: number;
  published_at: string | null;
};

export type StoryDetail = StoryCard & {
  id: string;
  body_html: string;
  status: "draft" | "published" | "hidden" | "removed";
  revision_number: number;
  content_hash: string;
  updated_at: string;
  viewer: { liked: boolean; is_author: boolean } | null;
};

export type Page<T> = { next: string | null; previous: string | null; results: T[] };

export type Me = {
  handle: string;
  display_name: string;
  bio: string;
  email: string;
  role: "reader" | "moderator" | "admin";
  is_verified_founder: boolean;
  email_verified: boolean;
  totp_enabled: boolean;
  founder_status: string;
  /** Server-side: verified founder, and 2FA is on if the server requires it. */
  can_publish: boolean;
  /** The server requires 2FA before this founder can publish. */
  needs_2fa: boolean;
};

export type Founder = {
  handle: string;
  display_name: string;
  bio: string;
  avatar_url: string | null;
  is_verified_founder: boolean;
  follower_count: number;
  founder?: { company: string; domain: string; title: string; verified_at: string };
};

export type Tag = { name: string; slug: string };

export type Comment = {
  id: string;
  author: { handle: string; display_name: string; is_verified_founder: boolean };
  body: string;
  status: string;
  created_at: string;
};

export type ApiError = { error: { code: string; message: string; fields?: Record<string, string[]> } };
