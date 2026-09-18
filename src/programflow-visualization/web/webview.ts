// Render and control the program-flow visualization UI inside the webview
import type { Address, BackendTraceElem } from "../types";
import { clearLayoutCache, prewarm, renderStep } from "./elk-view";
import { attachPanZoom, type PanZoom } from "./pan-zoom";

type ResetMsg = {
  command: "reset";
  trace: BackendTraceElem[];
  complete: boolean;
};

type AppendMsg = {
  command: "append";
  elem: BackendTraceElem;
  complete: boolean;
};

// Optional example trace format (designer mode)
type StaticTrace = { complete: boolean; trace: BackendTraceElem[] };

let trace: BackendTraceElem[] = [];
let traceComplete = false;
let traceIndex = 0;

/** Heap objects the user has folded away. Kept across steps on purpose. */
const collapsed = new Set<Address>();

let panZoom: PanZoom | undefined;
/** Bounds of the last render, so the Fit button has something to fit to. */
let lastBounds = { width: 0, height: 0 };

type NavType = "first" | "prev" | "next" | "last";

//DOM helpers
function $(sel: string): HTMLElement {
  const el = document.querySelector(sel);
  if (!el) {throw new Error(`Missing element: ${sel}`);}
  return el as HTMLElement;
}

function setDisabled(id: string, disabled: boolean) {
  (document.querySelector(id) as HTMLButtonElement).disabled = disabled;
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

//Rendering
function updateControls() {
  const max = Math.max(0, trace.length - 1);
  traceIndex = clamp(traceIndex, 0, max);

  // Update slider + counters
  const slider = $("#traceSlider") as HTMLInputElement;
  slider.max = String(max);
  slider.value = String(traceIndex);

  $("#traceMax").innerHTML = "/" + (traceComplete ? String(max) : "?");
  $("#indexCounter").innerHTML = String(traceIndex);

  // Update button enable/disable
  setDisabled("#firstButton", traceIndex <= 0);
  setDisabled("#prevButton", traceIndex <= 0);
  setDisabled("#nextButton", traceIndex >= max);
  setDisabled("#lastButton", traceIndex >= max);
}

function renderCurrent() {
  updateControls();

  // Nothing to show yet
  if (trace.length === 0) {
    $("#stdout-log").textContent = "";
    $("#elk-canvas").textContent = "";
    return;
  }

  const backendElem = trace[traceIndex];
  updateStdout(backendElem);
  void renderElk(backendElem);
}

function updateStdout(elem: BackendTraceElem) {
  const stdoutLog = $("#stdout-log");
  stdoutLog.textContent = elem.stdout;
  if (elem.traceback !== undefined) {
    const traceback = document.createElement("span");
    traceback.className = "traceback-text";
    traceback.textContent = elem.traceback;
    stdoutLog.append(traceback);
  }
  stdoutLog.scrollTo(0, stdoutLog.scrollHeight);
}

function renderElk(elem: BackendTraceElem): Promise<void> {
  // A collapsed object can end up off-screen, so offer a way back without hunting for it.
  $("#expandAllButton").hidden = collapsed.size === 0;
  return renderStep($("#elk-canvas"), elem, collapsed, {
    step: String(traceIndex),
    onToggle: (address) => {
      if (collapsed.has(address)) {
        collapsed.delete(address);
      } else {
        collapsed.add(address);
      }
      void renderElk(trace[traceIndex]);
    },
    onBounds: (width, height) => {
      lastBounds = { width, height };
      panZoom?.autoFit(width, height);
    },
  }).catch((err) => {
    console.error("ELK layout failed:", err);
  });
}

function postCurrentHighlight() {
  if (trace.length === 0) {
    return;
  }
  window.dispatchEvent(new CustomEvent("programflow:highlight", {
    detail: {
      filePath: trace[traceIndex].filePath,
      line: trace[traceIndex].line,
    },
  }));
}

function navigate(type: NavType) {
  const max = Math.max(0, trace.length - 1);

  switch (type) {
    case "first":
      traceIndex = 0;
      break;

    case "prev":
      traceIndex = Math.max(0, traceIndex - 1);
      break;

    case "next":
      traceIndex = Math.min(max, traceIndex + 1);
      break;

    case "last":
      traceIndex = max;
      break;
  }

  renderCurrent();
  postCurrentHighlight();
}

function slideTo(rawValue: string) {
  traceIndex = Number(rawValue) || 0;
  renderCurrent();
  postCurrentHighlight();
}

/**
 * While the slider is being dragged only the cheap parts follow along. Layout is far too
 * expensive to run per `input` event (plan 6.5), so it waits for `change`.
 */
function scrubTo(rawValue: string) {
  traceIndex = Number(rawValue) || 0;
  updateControls();
  if (trace.length > 0) {
    updateStdout(trace[traceIndex]);
  }
  postCurrentHighlight();
}

//Incoming events (from vscode-host-adapter.ts)
window.addEventListener("programflow:reset", (e: Event) => {
  const msg = (e as CustomEvent<ResetMsg>).detail;
  trace = msg.trace ?? [];
  traceComplete = !!msg.complete;
  // A reset means a different trace, so every cached layout is keyed on stale indices.
  clearLayoutCache();
  renderCurrent();
  postCurrentHighlight();
});

window.addEventListener("programflow:append", (e: Event) => {
  const msg = (e as CustomEvent<AppendMsg>).detail;
  trace.push(msg.elem);
  traceComplete = !!msg.complete;
  renderCurrent();
});


function setupUi() {
  panZoom = attachPanZoom($("#elk-viewport"), $("#elk-canvas"));
  watchThemeChanges();
  // Warm elkjs up while the user is still reading the first step.
  void prewarm().then(renderCurrent);

  // Disable until first reset arrives
  setDisabled("#nextButton", true);
  setDisabled("#lastButton", true);
  setDisabled("#prevButton", true);
  setDisabled("#firstButton", true);

  // Button clicks -> local navigation
  $("#firstButton").addEventListener("click", () => {
    navigate("first");
  });
  $("#prevButton").addEventListener("click", () => {
    navigate("prev");
  });
  $("#nextButton").addEventListener("click", () => {
    navigate("next");
  });
  $("#lastButton").addEventListener("click", () => {
    navigate("last");
  });
  $("#expandAllButton").addEventListener("click", () => {
    collapsed.clear();
    renderCurrent();
  });
  $("#fitButton").addEventListener("click", () => {
    panZoom?.fit(lastBounds.width, lastBounds.height);
  });
  $("#zoomInButton").addEventListener("click", () => {
    panZoom?.zoomIn();
  });
  $("#zoomOutButton").addEventListener("click", () => {
    panZoom?.zoomOut();
  });

  // Slider input -> local navigation
  const slider = $("#traceSlider") as HTMLInputElement;
  slider.addEventListener("input", (e: Event) => {
    scrubTo((e.target as HTMLInputElement).value);
  });
  slider.addEventListener("change", (e: Event) => {
    slideTo((e.target as HTMLInputElement).value);
  });

  // Optional: example trace mode
  const anyWin = window as any;
  const staticTrace: StaticTrace | undefined = anyWin.__PROGRAMFLOW_TRACE__;

  if (staticTrace?.trace) {
    trace = staticTrace.trace;
    traceComplete = !!staticTrace.complete;
    traceIndex = 0;
    renderCurrent();
  }
}

document.addEventListener("DOMContentLoaded", setupUi);

/**
 * VS Code signals a theme change by swapping the class on `<body>`. That changes the
 * colours *and* potentially the font, so the cached layouts have to go (plan 6.5).
 */
function watchThemeChanges() {
  const observer = new MutationObserver(() => {
    clearLayoutCache();
    renderCurrent();
  });
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ["class", "style"],
  });
}
