// Ties the pipeline together: model -> measure -> ELK -> DOM.
// See elk-task/elk-plan.md 6.
import ELK from "elkjs/lib/elk.bundled.js";
import type { ElkNode } from "elkjs/lib/elk-api";
import type { Address, BackendTraceElem } from "../types";
import { buildGraph, type NodeModel } from "../graph-model";
import { ensureFontsReady, measureGraph } from "./measure";
import { renderGraph, type RenderOptions } from "./graph-renderer";

// No workerUrl: elkjs then uses its in-process fake worker. A real Web Worker
// would be blocked anyway, the webview CSP has no worker-src (plan 2).
let elk: InstanceType<typeof ELK> | null = null;

function elkInstance(): InstanceType<typeof ELK> {
  if (!elk) {
    elk = new ELK();
  }
  return elk;
}

// Layout is async, and steps can be requested faster than they finish. Only the
// most recent request is allowed to touch the DOM.
let renderToken = 0;

type CacheEntry = { laidOut: ElkNode; models: Map<string, NodeModel> };

/**
 * Stepping back and forth re-visits the same graphs constantly, and layout is the
 * expensive part (plan 6.5). Bounded, or a long trace keeps every step ever visited.
 */
const MAX_CACHED_LAYOUTS = 40;
const layoutCache = new Map<string, CacheEntry>();

/**
 * Text metrics are baked into every cached layout, so anything that changes them -- a
 * theme switch, an editor font-size change -- invalidates all of it.
 */
export function clearLayoutCache(): void {
  layoutCache.clear();
}

function cacheKey(step: string, collapsed: ReadonlySet<Address>): string {
  return `${step}|${[...collapsed].sort((a, b) => a - b).join(",")}`;
}

function remember(key: string, entry: CacheEntry): void {
  layoutCache.set(key, entry);
  while (layoutCache.size > MAX_CACHED_LAYOUTS) {
    const oldest = layoutCache.keys().next();
    if (oldest.done) {
      break;
    }
    layoutCache.delete(oldest.value);
  }
}

/**
 * The first layout pays ~330 ms of JIT warm-up (spike, plan 6.5). Doing it on a
 * throwaway graph at start-up keeps that cost out of the first real step.
 */
export async function prewarm(): Promise<void> {
  await ensureFontsReady();
  try {
    await elkInstance().layout({
      id: "prewarm",
      children: [
        { id: "a", width: 10, height: 10 },
        { id: "b", width: 10, height: 10 },
      ],
      edges: [{ id: "e", sources: ["a"], targets: ["b"] }],
    });
  } catch {
    // Warm-up only; a failure here says nothing about real layouts.
  }
}

export type StepRenderOptions = RenderOptions & {
  /** Identifies the step; together with the collapsed set it keys the layout cache. */
  step: string;
  /** Bounds of the drawn graph, reported after every render so the caller can fit. */
  onBounds?: (width: number, height: number) => void;
};

export async function renderStep(
  container: HTMLElement,
  elem: BackendTraceElem,
  collapsed: ReadonlySet<Address>,
  options: StepRenderOptions
): Promise<void> {
  const token = ++renderToken;
  const key = cacheKey(options.step, collapsed);

  const cached = layoutCache.get(key);
  if (cached) {
    // Re-insert so this becomes the most recently used entry.
    layoutCache.delete(key);
    layoutCache.set(key, cached);
    paint(container, cached, options);
    return;
  }

  const viz = buildGraph(elem, collapsed);
  measureGraph(viz);
  const laidOut = await elkInstance().layout(viz.graph);
  if (token !== renderToken) {
    return;
  }
  const entry: CacheEntry = { laidOut, models: viz.nodes };
  remember(key, entry);
  paint(container, entry, options);
}

function paint(
  container: HTMLElement,
  entry: CacheEntry,
  options: StepRenderOptions
): void {
  renderGraph(container, entry.laidOut, entry.models, options);
  options.onBounds?.(
    parseFloat(container.style.width) || 0,
    parseFloat(container.style.height) || 0
  );
}
