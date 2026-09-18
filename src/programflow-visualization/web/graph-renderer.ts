// Draws a laid-out graph. See elk-task/elk-plan.md 6.3.
//
// Builds the node elements from the same `renderNode` measure.ts used, then places them at
// the coordinates ELK computed. Edges go into one SVG overlay behind the nodes.
import type { ElkExtendedEdge, ElkNode } from "elkjs/lib/elk-api";
import type { NodeModel } from "../graph-model";
import { headerElement, NODE_CLASS, renderNode } from "./node-view";

const SVG_NS = "http://www.w3.org/2000/svg";
const MARGIN = 24;
/** Room above the nodes for the "Frames" / "Objects" captions. */
const BAND_HEIGHT = 28;

/**
 * Last seen pointer position, in client coordinates. Collapsing a node re-lays out the
 * graph under a stationary cursor, and a stationary cursor fires no mouseenter on the
 * freshly built elements, so each render has to re-derive the hover itself.
 */
let pointer: { x: number; y: number } | undefined;
let pointerTracked = false;

function trackPointer(): void {
  if (pointerTracked) {
    return;
  }
  pointerTracked = true;
  window.addEventListener(
    "pointermove",
    (event: PointerEvent) => {
      pointer = { x: event.clientX, y: event.clientY };
    },
    { passive: true, capture: true }
  );
  // A pointer that has left the window is not over anything. pointerleave does not
  // bubble, so this has to sit on the element it is targeted at, not on window.
  document.documentElement.addEventListener("pointerleave", () => {
    pointer = undefined;
  });
}

export type RenderOptions = {
  /** Called when a collapsible node header is activated. */
  onToggle?: (address: number) => void;
};

function pointsOf(edge: ElkExtendedEdge): Array<{ x: number; y: number }> {
  const section = edge.sections?.[0];
  if (!section) {
    return [];
  }
  return [section.startPoint, ...(section.bendPoints ?? []), section.endPoint];
}

function arrowMarker(): SVGMarkerElement {
  const marker = document.createElementNS(SVG_NS, "marker");
  marker.setAttribute("id", "elk-arrowhead");
  marker.setAttribute("viewBox", "0 0 8 8");
  marker.setAttribute("refX", "7");
  marker.setAttribute("refY", "4");
  marker.setAttribute("markerWidth", "7");
  marker.setAttribute("markerHeight", "7");
  marker.setAttribute("orient", "auto-start-reverse");
  const path = document.createElementNS(SVG_NS, "path");
  path.setAttribute("d", "M 0 0 L 8 4 L 0 8 z");
  path.setAttribute("class", "elk-arrowhead");
  marker.append(path);
  return marker;
}

function band(label: string, left: number, width: number): HTMLElement {
  const element = document.createElement("div");
  element.className = "elk-band";
  element.textContent = label;
  element.style.left = `${left}px`;
  element.style.top = `${MARGIN}px`;
  element.style.height = `${BAND_HEIGHT}px`;
  element.style.width = `${Math.max(width, 0)}px`;
  return element;
}

export function renderGraph(
  container: HTMLElement,
  laidOut: ElkNode,
  models: Map<string, NodeModel>,
  options: RenderOptions = {}
): void {
  trackPointer();
  container.textContent = "";
  container.classList.add("elk-canvas");
  // Wiping the children destroys the hovered node without ever firing its mouseleave,
  // so the dim-everything-else class would otherwise survive with nothing highlighted.
  container.classList.remove("elk-dimming");

  const children = laidOut.children ?? [];
  const portToNode = new Map<string, string>();
  for (const child of children) {
    for (const port of child.ports ?? []) {
      portToNode.set(port.id, child.id);
    }
  }

  const width = Math.max(
    ...children.map((child) => (child.x ?? 0) + (child.width ?? 0)),
    0
  );
  const height = Math.max(
    ...children.map((child) => (child.y ?? 0) + (child.height ?? 0)),
    0
  );
  container.style.width = `${width + 2 * MARGIN}px`;
  container.style.height = `${height + BAND_HEIGHT + 2 * MARGIN}px`;

  const offsetY = MARGIN + BAND_HEIGHT;

  // Edges first: the SVG sits behind the nodes.
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "elk-edges");
  svg.setAttribute("width", `${width + 2 * MARGIN}`);
  svg.setAttribute("height", `${height + BAND_HEIGHT + 2 * MARGIN}`);
  const defs = document.createElementNS(SVG_NS, "defs");
  defs.append(arrowMarker());
  svg.append(defs);

  const edgesByNode = new Map<string, SVGPathElement[]>();
  const track = (nodeId: string | undefined, path: SVGPathElement) => {
    if (!nodeId) {
      return;
    }
    const list = edgesByNode.get(nodeId);
    if (list) {
      list.push(path);
    } else {
      edgesByNode.set(nodeId, [path]);
    }
  };

  for (const edge of (laidOut.edges ?? []) as ElkExtendedEdge[]) {
    const points = pointsOf(edge);
    if (points.length < 2) {
      continue;
    }
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute(
      "d",
      points
        .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x + MARGIN} ${point.y + offsetY}`)
        .join(" ")
    );
    path.setAttribute("class", "elk-edge");
    path.setAttribute("marker-end", "url(#elk-arrowhead)");
    svg.append(path);
    track(portToNode.get(edge.sources[0]), path);
    track(portToNode.get(edge.targets[0]), path);
  }
  container.append(svg);

  // Hovering a node highlights everything it is connected to (plan 6.4). One shared
  // "which node is active" state, so that a re-render can restore it without a gesture.
  let active: HTMLElement | undefined;

  const paintActive = (element: HTMLElement, on: boolean) => {
    element.classList.toggle("elk-node-active", on);
    for (const path of edgesByNode.get(element.dataset.nodeId ?? "") ?? []) {
      path.classList.toggle("elk-edge-active", on);
    }
  };

  const setActive = (element: HTMLElement | undefined) => {
    if (active === element) {
      return;
    }
    if (active) {
      paintActive(active, false);
    }
    active = element;
    if (active) {
      paintActive(active, true);
    }
    container.classList.toggle("elk-dimming", active !== undefined);
  };

  // Nodes.
  let framesRight = Number.NEGATIVE_INFINITY;
  let objectsLeft = Number.POSITIVE_INFINITY;

  for (const child of children) {
    const model = models.get(child.id);
    if (!model) {
      continue;
    }
    const element = renderNode(model);
    element.dataset.nodeId = child.id;
    element.style.left = `${(child.x ?? 0) + MARGIN}px`;
    element.style.top = `${(child.y ?? 0) + offsetY}px`;
    element.style.width = `${child.width ?? 0}px`;

    if (model.address === undefined) {
      framesRight = Math.max(framesRight, (child.x ?? 0) + (child.width ?? 0));
    } else {
      objectsLeft = Math.min(objectsLeft, child.x ?? 0);
      const header = headerElement(element);
      const address = model.address;
      const toggle = () => options.onToggle?.(address);
      header?.addEventListener("click", toggle);
      header?.addEventListener("keydown", (event) => {
        const key = (event as KeyboardEvent).key;
        if (key === "Enter" || key === " ") {
          event.preventDefault();
          toggle();
        }
      });
    }

    // Hovering a node highlights everything it is connected to (plan 6.4).
    element.addEventListener("mouseenter", () => {
      setActive(element);
    });
    element.addEventListener("mouseleave", () => {
      setActive(undefined);
    });

    container.append(element);
  }

  // Column captions, derived from where the nodes actually ended up: there are no
  // container nodes to hang them off (plan 4).
  if (framesRight > Number.NEGATIVE_INFINITY) {
    container.append(band("Frames", MARGIN, framesRight));
  }
  if (objectsLeft < Number.POSITIVE_INFINITY) {
    container.append(band("Objects", objectsLeft + MARGIN, width - objectsLeft));
  }

  // Whatever the cursor is sitting on now is hovered, even though it never moved.
  // elementFromPoint flushes layout, so the positions set above are already in effect.
  if (pointer) {
    const hit = document.elementFromPoint(pointer.x, pointer.y);
    const node = hit?.closest<HTMLElement>(`.${NODE_CLASS}`) ?? undefined;
    setActive(node && container.contains(node) ? node : undefined);
  }
}
