import { HTMLGenerator } from "./html-generator";
import LinkerLine from "linkerline";
import type { BackendTraceElem } from "../types";

const isVscode = typeof (window as any).acquireVsCodeApi === "function";

type ResetMsg = {
  command: "reset";
  trace: BackendTraceElem[];
  complete: boolean;
  index: number;
};

type AppendMsg = {
  command: "append";
  elem: BackendTraceElem;
  complete: boolean;
  index: number;
  len: number;
};

// Optional example trace format (designer mode)
type StaticTrace = { complete: boolean; trace: BackendTraceElem[] };

let refLines: any[] = [];
let trace: BackendTraceElem[] = [];
let traceComplete = false;
let traceIndex = 0;

const gen = new HTMLGenerator();

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
function renderCurrent() {
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

  // Nothing to show yet
  if (trace.length === 0) {
    $("#stdout-log").innerHTML = "";
    clearArrows();
    return;
  }

  const backendElem = trace[traceIndex];
  const frontendElem = gen.generateHTML(backendElem);

  updateVisualization(frontendElem);
  updateIndent(frontendElem);
  updateRefArrows(frontendElem);
}

function updateVisualization(traceElem: any /* FrontendTraceElem */) {
  clearArrows();
  const data = `
    <div class="row">
      <div class="column floating-left">
        <div class="row title">Frames</div>
        <div class="divider"></div>
      </div>
      <div class="column floating-right">
        <div class="row title">Objects</div>
        <div class="divider"></div>
      </div>
    </div>
    <div class="row">
      <div class="column floating-left floating-left-content" id="frames">
        ${traceElem.stackHTML}
      </div>
      <div class="column floating-right floating-right-content" id="objects">
        ${traceElem.heapHTML}
      </div>
    </div>
  `;

  const viz = document.getElementById("viz")!;
  viz.innerHTML = data;

  const stdoutLog = document.getElementById("stdout-log")!;
  stdoutLog.innerHTML = traceElem.outputState;
  stdoutLog.scrollTo(0, stdoutLog.scrollHeight);
}

function updateIndent(traceElem: any /* FrontendTraceElem */) {
  const heapTags = traceElem.heapHTML.match(/(?<=startPointer)[0-9]+/g);
  if (heapTags) {
    heapTags.forEach((tag: string) => {
      const element = document.getElementById("objectItem" + tag);
      if (element) {element.classList.add("object-intendation");}
    });
  }
}

//Arrows
function clearArrows() {
  refLines.forEach((l) => {
    try {
      l.remove();
    } catch {}
  });
  refLines = [];
}

function updateRefArrows(traceElem: any /* FrontendTraceElem */) {
  const tags = getCurrentTags(traceElem);
  if (!tags) { return; }

  requestAnimationFrame(() => {
    const parent = document.getElementById("viz");
    if (!parent) { return; }

    const usable = tags.filter((t: any) => {
      const a = t.elem1 as HTMLElement | null | undefined;
      const b = t.elem2 as HTMLElement | null | undefined;
      return !!a && !!b && a.isConnected && b.isConnected;
    });

    const lines: any[] = [];
    for (const t of usable) {
      try {
        lines.push(
          new (LinkerLine as any)({
            parent,
            start: t.elem1,
            end: t.elem2,
            size: 2,
            path: "magnet",
            startSocket: "right",
            endSocket: "left",
            startPlug: "square",
            startSocketGravity: [50, -10],
            endSocketGravity: [-5, -5],
            endPlug: "arrow1",
            color: getColor(t),
          })
        );
      } catch (err) {
        // Keep going if one arrow fails (prevents breaking the whole render)
        console.warn("LinkerLine failed for one tag:", t, err);
      }
    }

    refLines = lines;
  });
}

function getCurrentTags(traceElem: any /* FrontendTraceElem */) {
  const stackTags = traceElem.stackHTML.match(/(?<=id=")(.+)Pointer[0-9]+/g);
  const heapTags = traceElem.heapHTML.match(/(?<=startPointer)[0-9]+/g);
  const uniqueId = traceElem.heapHTML.match(/\d+(?=startPointer)/g);

  if (!stackTags) {return;}

  const stackRefs = stackTags.map((tag: string) => {
    const id = tag.match(/(?<=.*Pointer)[\d]+/g);
    return {
      tag: id,
      elem1: document.getElementById(tag),
      elem2: document.getElementById("heapEndPointer" + id),
    };
  });

  let heapRefs: any[] = [];
  if (heapTags && uniqueId) {
    heapRefs = heapTags.map((reference: string, index: number) => {
      return {
        tag: reference,
        elem1: document.getElementById(uniqueId[index] + "startPointer" + reference),
        elem2: document.getElementById("heapEndPointer" + reference),
      };
    });
  }

  return [...heapRefs, ...stackRefs];
}

function getColor(tag: any) {
  const hue = ((0.618033988749895 + Number(tag.tag) / 10) % 1) * 100;
  return `hsl(${hue}, 60%, 45%)`;
}

//Incoming events (from vscode-host-adapter.ts)
window.addEventListener("programflow:reset", (e: Event) => {
  const msg = (e as CustomEvent<ResetMsg>).detail;
  trace = msg.trace ?? [];
  traceComplete = !!msg.complete;
  traceIndex = Number(msg.index ?? 0);
  renderCurrent();
});

window.addEventListener("programflow:append", (e: Event) => {
  const msg = (e as CustomEvent<AppendMsg>).detail;
  trace.push(msg.elem);
  traceComplete = !!msg.complete;
  traceIndex = Number(msg.index ?? traceIndex);
  renderCurrent();
});

window.addEventListener("programflow:updateButtons", (e: Event) => {
  const msg = (e as CustomEvent<any>).detail;
  setDisabled("#nextButton", !msg.next);
  setDisabled("#prevButton", !msg.prev);
  setDisabled("#firstButton", !msg.first);
  setDisabled("#lastButton", !msg.last);
});

window.addEventListener("programflow:updateContent", (e: Event) => {
  const msg = (e as CustomEvent<any>).detail;

  const max = Math.max(0, (msg.traceLen ?? 0) - 1);
  const slider = $("#traceSlider") as HTMLInputElement;
  slider.max = String(max);
  slider.value = String(msg.traceIndex ?? 0);

  $("#traceMax").innerHTML = "/" + (msg.traceComplete ? String(max) : "?");
  $("#indexCounter").innerHTML = String(msg.traceIndex ?? 0);

  updateVisualization(msg.traceElem);
  updateIndent(msg.traceElem);
  updateRefArrows(msg.traceElem);
});

// Browser-only navigation handling
if (!isVscode) {

  window.addEventListener("programflow:onClick", (e: Event) => {
    const ce = e as CustomEvent<{ type: "first" | "prev" | "next" | "last" }>;
    const max = Math.max(0, trace.length - 1);

    switch (ce.detail.type) {
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
  });

  window.addEventListener("programflow:onSlide", (e: Event) => {
    const ce = e as CustomEvent<{ value: string }>;
    traceIndex = Number(ce.detail.value) || 0;
    renderCurrent();
  });

}


function setupUi() {
  // Disable until first reset arrives
  setDisabled("#nextButton", true);
  setDisabled("#lastButton", true);
  setDisabled("#prevButton", true);
  setDisabled("#firstButton", true);

  // Button clicks -> dispatch events (adapter forwards to VS Code)
  $("#firstButton").addEventListener("click", () => {
    window.dispatchEvent(new CustomEvent("programflow:onClick", { detail: { type: "first" } }));
  });
  $("#prevButton").addEventListener("click", () => {
    window.dispatchEvent(new CustomEvent("programflow:onClick", { detail: { type: "prev" } }));
  });
  $("#nextButton").addEventListener("click", () => {
    window.dispatchEvent(new CustomEvent("programflow:onClick", { detail: { type: "next" } }));
  });
  $("#lastButton").addEventListener("click", () => {
    window.dispatchEvent(new CustomEvent("programflow:onClick", { detail: { type: "last" } }));
  });

  // Slider input -> dispatch event
  ($("#traceSlider") as HTMLInputElement).addEventListener("input", (e: Event) => {
    const value = (e.target as HTMLInputElement).value;
    window.dispatchEvent(new CustomEvent("programflow:onSlide", { detail: { value } }));
  });

  // Optional: example trace mode
  const anyWin = window as any;
  const staticTrace: StaticTrace | undefined = anyWin.__PROGRAMFLOW_TRACE__;

  console.log("static trace mode:", !!staticTrace?.trace, staticTrace?.trace?.length);
  
  if (staticTrace?.trace) {
    trace = staticTrace.trace;
    traceComplete = !!staticTrace.complete;
    traceIndex = 0;
    renderCurrent();
  }
}

document.addEventListener("DOMContentLoaded", setupUi);