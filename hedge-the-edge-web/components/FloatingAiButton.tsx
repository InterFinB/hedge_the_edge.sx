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
        title="Ask Hedge the Edge"
        className="group relative flex h-[72px] w-[72px] items-center justify-center rounded-full border border-slate-200 bg-white/90 shadow-[0_18px_45px_rgba(15,23,42,0.18)] backdrop-blur transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_22px_55px_rgba(15,23,42,0.22)] active:translate-y-0"
      >
        <span className="pointer-events-none absolute right-[5.25rem] whitespace-nowrap rounded-full bg-slate-900 px-3 py-1.5 text-xs font-medium text-white opacity-0 shadow-lg transition duration-200 group-hover:opacity-100">
          Ask AI
        </span>

        <div className="flex h-14 w-14 items-center justify-center overflow-hidden rounded-full bg-white ring-1 ring-slate-200 transition duration-200 group-hover:scale-[1.03]">
          <Image
            src="/hedge-icon.png"
            alt="Hedge the Edge"
            width={54}
            height={54}
            className="h-11 w-11 object-contain"
            priority
          />
        </div>
      </button>
    </div>
  );
}