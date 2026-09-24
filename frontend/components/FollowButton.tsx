"use client";

import { useState } from "react";
import { api, ApiException } from "@/lib/client-api";

export function FollowButton({ handle }: { handle: string }) {
  const [following, setFollowing] = useState(false);
  return (
    <button
      className={`btn ${following ? "btn-ghost" : "btn-primary"} min-w-28`}
      onClick={async () => {
        try {
          const res = await api<{ following: boolean }>(`/founders/${handle}/follow`, { method: following ? "DELETE" : "POST" });
          setFollowing(res.following);
        } catch (err) {
          if (err instanceof ApiException && err.status === 403) window.location.href = `/login?next=/f/${handle}`;
        }
      }}
    >
      {following ? "Following" : "Follow"}
    </button>
  );
}
