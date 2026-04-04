"use client";

import type { TextSelectionPayload } from "@/hooks/useTextSelection";

export default function SelectionAskBubble({
  selection,
  onAsk,
}: {
  selection: TextSelectionPayload | null;
  onAsk: (selection: TextSelectionPayload) => void;
}) {
  if (!selection) return null;

  return (
    <button
      type="button"
      onClick={() => onAsk(selection)}
      style={{
        position: "absolute",
        top: selection.y,
        left: selection.x,
        transform: "translate(-50%, -100%)",
      }}
      className="z-50 rounded-full bg-slate-950 px-4 py-2 text-xs font-medium text-white shadow-[0_10px_25px_rgba(15,23,42,0.18)] transition hover:bg-slate-800"
    >
      Ask Hedge The Edge
    </button>
  );
}