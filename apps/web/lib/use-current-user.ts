"use client";

import { useEffect, useState } from "react";

import { fetchCurrentUser } from "@/lib/browser-api";
import type { AuthenticatedResponse } from "@/lib/api/types";

type CurrentUserState = {
  user: AuthenticatedResponse["user"] | null;
  loading: boolean;
};

export function useCurrentUser() {
  const [state, setState] = useState<CurrentUserState>({ user: null, loading: true });

  useEffect(() => {
    let active = true;

    void fetchCurrentUser()
      .then((user) => {
        if (!active) {
          return;
        }
        setState({ user, loading: false });
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setState({ user: null, loading: false });
      });

    return () => {
      active = false;
    };
  }, []);

  return state;
}
