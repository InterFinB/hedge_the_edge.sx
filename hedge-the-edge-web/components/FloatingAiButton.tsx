"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

type FloatingAiButtonProps = {
  targetId: string;
};

export default function FloatingAiButton({
  targetId,
}: FloatingAiButtonProps) {
  const [isNearTarget, setIsNearTarget] = useState(false);

  useEffect(() => {
    const target = document.getElementById(targetId);
    if (!target) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsNearTarget(entry.isIntersecting);
      },
      {
        threshold: 0.15,
        rootMargin: "0px 0px -120px 0px",
      }
    );

    observer.observe(target);

    return () => observer.disconnect();
  }, [targetId]);

  const handleClick = () => {
    const target = document.getElementById(targetId);
    if (!target) return;

    target.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  return (
    <div
      className={[
        "fixed bottom-24 right-5 z-50 transition-all duration-300 sm:bottom-6",
        isNearTarget
          ? "pointer-events-none translate-y-3 opacity-0"
          : "translate-y-0 opacity-100",
      ].join(" ")}
    >
      <button
        type="button"
        onClick={handleClick}
        aria-label="Jump to AI assistant"
        title="Ask Hedge the Edge AI"
        className="group relative flex h-[76px] w-[76px] items-center justify-center rounded-full border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.96)_0%,rgba(248,250,252,0.94)_100%)] shadow-[0_20px_50px_rgba(15,23,42,0.18)] backdrop-blur transition duration-300 hover:-translate-y-1 hover:shadow-[0_26px_60px_rgba(15,23,42,0.24)] active:translate-y-0 focus:outline-none focus:ring-4 focus:ring-slate-900/10"
      >
        <span className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.65),transparent_60%)] opacity-80" />

        <span className="absolute right-[5.75rem] whitespace-nowrap rounded-full border border-slate-200 bg-slate-950 px-3.5 py-1.5 text-xs font-medium text-white opacity-0 shadow-[0_10px_24px_rgba(15,23,42,0.22)] transition duration-300 group-hover:opacity-100">
          Ask Hedge the Edge AI
        </span>

        <span className="absolute right-2 top-2 flex h-3 w-3">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/60" />
          <span className="relative inline-flex h-3 w-3 rounded-full border border-white bg-emerald-500 shadow-sm" />
        </span>

        <div className="relative flex h-[58px] w-[58px] items-center justify-center overflow-hidden rounded-full bg-white ring-1 ring-slate-200 shadow-inner transition duration-300 group-hover:scale-[1.05]">
          <Image
            src="/hedge-icon.png"
            alt="Hedge the Edge"
            width={46}
            height={46}
            className="h-[46px] w-[46px] object-cover transition duration-300 group-hover:scale-[1.75]"
            priority
          />
        </div>
      </button>
    </div>
  );
}