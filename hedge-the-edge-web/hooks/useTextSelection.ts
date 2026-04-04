"use client";

import { useEffect, useState } from "react";
import type { SelectionContext } from "@/types/portfolio";

export type TextSelectionPayload = {
  text: string;
  x: number;
  y: number;
  selectionContext: SelectionContext;
};

function isIgnoredTarget(element: HTMLElement | null) {
  if (!element) return false;

  return Boolean(
    element.closest(
      'input, textarea, button, a, [contenteditable="true"], [data-no-selection-ask="true"]'
    )
  );
}

function getSelectionSection(
  element: HTMLElement | null
): SelectionContext["section"] {
  const explicitSection = element?.closest("[data-ask-section]");
  const sectionValue = explicitSection?.getAttribute("data-ask-section");

  switch (sectionValue) {
    case "explanation":
    case "chat_response":
    case "simulation":
    case "risk":
    case "weights":
    case "allocation":
      return sectionValue;
    default:
      return "unknown";
  }
}

function getSelectionLabel(element: HTMLElement | null): string | null {
  const explicitLabel = element?.closest("[data-ask-label]");
  return explicitLabel?.getAttribute("data-ask-label") ?? null;
}

export function useTextSelection() {
  const [selection, setSelection] = useState<TextSelectionPayload | null>(null);

  useEffect(() => {
    const updateSelection = () => {
      const sel = window.getSelection();

      if (!sel || sel.isCollapsed || sel.rangeCount === 0) {
        setSelection(null);
        return;
      }

      const text = sel.toString().trim();

      if (!text || text.length < 8) {
        setSelection(null);
        return;
      }

      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();

      if (!rect || (!rect.width && !rect.height)) {
        setSelection(null);
        return;
      }

      const rawNode = range.commonAncestorContainer;
      const element =
        rawNode.nodeType === Node.ELEMENT_NODE
          ? (rawNode as HTMLElement)
          : rawNode.parentElement;

      if (isIgnoredTarget(element)) {
        setSelection(null);
        return;
      }

      setSelection({
        text,
        x: rect.left + rect.width / 2,
        y: rect.top + window.scrollY - 10,
        selectionContext: {
          source_type: "text_selection",
          section: getSelectionSection(element),
          selected_text: text,
          surrounding_label: getSelectionLabel(element),
        },
      });
    };

    const clearSelection = () => {
      setSelection(null);
    };

    const deferredUpdate = () => {
      window.setTimeout(updateSelection, 0);
    };

    document.addEventListener("mouseup", deferredUpdate);
    document.addEventListener("keyup", deferredUpdate);
    document.addEventListener("scroll", clearSelection, true);

    return () => {
      document.removeEventListener("mouseup", deferredUpdate);
      document.removeEventListener("keyup", deferredUpdate);
      document.removeEventListener("scroll", clearSelection, true);
    };
  }, []);

  return selection;
}