"use client";

import { useEffect, useState } from "react";

export default function FloatingAiButton({ targetId }: { targetId: string }) {
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    const el = document.getElementById(targetId);
    if (!el) return;

    const obs = new IntersectionObserver(
      ([e]) => setHidden(e.isIntersecting),
      { threshold: 0.2 }
    );

    obs.observe(el);
    return () => obs.disconnect();
  }, [targetId]);

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 transition ${
        hidden ? "opacity-0 translate-y-4" : "opacity-100"
      }`}
    >
      <button
        onClick={() =>
          document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth" })
        }
        className="relative flex h-16 w-16 items-center justify-center rounded-full bg-slate-900 text-white shadow-xl hover:scale-105 transition"
      >
        <span className="absolute h-3 w-3 bg-emerald-400 rounded-full top-2 right-2 animate-pulse" />
        ✨
      </button>
    </div>
  );
}