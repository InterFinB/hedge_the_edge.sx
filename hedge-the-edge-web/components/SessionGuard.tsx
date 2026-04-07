"use client";

import { useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

const IDLE_TIMEOUT_MS = 15 * 60 * 1000;

export default function SessionGuard() {
  const supabase = useMemo(() => createClient(), []);
  const router = useRouter();
  const timeoutRef = useRef<number | null>(null);
  const lastEmailRef = useRef("");

  async function getCurrentUserEmail() {
    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      const email = user?.email?.trim().toLowerCase() ?? "";
      lastEmailRef.current = email;

      if (email) {
        localStorage.setItem("hte_last_approved_email", email);
      }

      return email;
    } catch {
      return "";
    }
  }

  async function signOutToAccessApproved() {
    const email =
      lastEmailRef.current ||
      localStorage.getItem("hte_last_approved_email") ||
      (await getCurrentUserEmail());

    try {
      await supabase.auth.signOut();
    } catch {
      // best effort
    }

    const destination = email
      ? `/access-approved?email=${encodeURIComponent(email)}`
      : "/access-approved";

    router.push(destination);
    router.refresh();
  }

  function clearIdleTimer() {
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }

  function startIdleTimer() {
    clearIdleTimer();
    timeoutRef.current = window.setTimeout(() => {
      void signOutToAccessApproved();
    }, IDLE_TIMEOUT_MS);
  }

  useEffect(() => {
    void getCurrentUserEmail();
    startIdleTimer();

    const activityEvents: Array<keyof WindowEventMap> = [
      "mousemove",
      "mousedown",
      "keydown",
      "scroll",
      "touchstart",
      "click",
    ];

    const resetTimer = () => {
      startIdleTimer();
    };

    activityEvents.forEach((eventName) => {
      window.addEventListener(eventName, resetTimer, { passive: true });
    });

    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        const email = lastEmailRef.current || localStorage.getItem("hte_last_approved_email") || "";
        if (email) {
          localStorage.setItem("hte_last_approved_email", email);
        }
        void supabase.auth.signOut();
      }
    };

    const handlePageHide = () => {
      const email = lastEmailRef.current || localStorage.getItem("hte_last_approved_email") || "";
      if (email) {
        localStorage.setItem("hte_last_approved_email", email);
      }
      void supabase.auth.signOut();
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("pagehide", handlePageHide);

    return () => {
      clearIdleTimer();

      activityEvents.forEach((eventName) => {
        window.removeEventListener(eventName, resetTimer);
      });

      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("pagehide", handlePageHide);
    };
  }, [router, supabase]);

  return null;
}