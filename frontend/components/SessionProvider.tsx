"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/client-api";
import type { Me } from "@/lib/types";

/** undefined = still loading, null = logged out. */
const SessionContext = createContext<Me | null | undefined>(undefined);

/** Fetches /auth/me once per page load and shares it (header, auth prompt, …). */
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<Me | null | undefined>(undefined);
  useEffect(() => {
    api<Me | null>("/auth/me").then(setMe).catch(() => setMe(null));
  }, []);
  return <SessionContext.Provider value={me}>{children}</SessionContext.Provider>;
}

export function useMe() {
  return useContext(SessionContext);
}
