// Draws a laid-out graph. See elk-task/elk-plan.md 6.3.
//
// Builds the node elements from the same `renderNode` measure.ts used, then places them at
// the coordinates ELK computed. Edges go into one SVG overlay behind the nodes.
import type { ElkExtendedEdge, ElkNode } from "elkjs/lib/elk-api";
import type { NodeModel } from "../graph-model";
import { keyPortId, rowPortId } from "../graph-model";
import { headerElement, NODE_CLASS, renderNode, ROW_CLASS } from "./node-view";

const SVG_NS = "http://www.w3.org/2000/svg";

/**
 * Slack above and below the nodes, in graph pixels.
 *
 * Edges do leave the nodes' vertical span -- measured over the 49 steps of the showcase
 * they reach 33px above the topmost node and 10px below the lowest -- and the SVG
 * overlay clips to the canvas box, so this has to cover them. The band above the nodes
 * adds BAND_HEIGHT on top of it.
 */
const MARGIN_Y = 24;

/**
 * The same to the left and right, and much smaller because nothing overflows sideways:
 * over those 49 steps the leftmost edge point stays 220px *inside* the leftmost node
 * and the rightmost stays 120px inside the rightmost. Sideways margin is therefore
 * decoration, and it was conspicuous -- a graph scaled to fit sat 44px from the left of
 * the panel while sitting 8px from the bottom.
 */
const MARGIN_X = 8;

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

function band(
  label: string,
  modifier: string,
  left: number,
  width: number
): HTMLElement {
  const element = document.createElement("div");
  element.className = `elk-band ${modifier}`;
  element.textContent = label;
  element.style.left = `${left}px`;
  element.style.top = `${MARGIN_Y}px`;
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

  // ELK leaves its own padding around the content -- 12px by default -- and the
  // coordinates it reports include it, so drawing them as-is put ELK's padding and ours
  // end to end, and only on the left. Measuring from the content's own left edge instead
  // makes MARGIN_X the whole of the margin, and keeps the canvas box tight, which in
  // turn lets the fit pick its scale from the graph rather than from the padding.
  const contentLeft = children.length
    ? Math.min(...children.map((child) => child.x ?? 0))
    : 0;
  const width =
    Math.max(...children.map((child) => (child.x ?? 0) + (child.width ?? 0)), 0) -
    contentLeft;
  const height = Math.max(
    ...children.map((child) => (child.y ?? 0) + (child.height ?? 0)),
    0
  );
  const canvasWidth = width + 2 * MARGIN_X;
  const canvasHeight = height + BAND_HEIGHT + 2 * MARGIN_Y;
  container.style.width = `${canvasWidth}px`;
  container.style.height = `${canvasHeight}px`;

  const offsetX = MARGIN_X - contentLeft;
  const offsetY = MARGIN_Y + BAND_HEIGHT;

  // Edges first: the SVG sits behind the nodes.
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "elk-edges");
  svg.setAttribute("width", `${canvasWidth}`);
  svg.setAttribute("height", `${canvasHeight}`);
  const defs = document.createElementNS(SVG_NS, "defs");
  defs.append(arrowMarker());
  svg.append(defs);

  // Two indexes over the same paths: by node, for pointing at a whole box, and by the
  // port an edge leaves from, for pointing at the single row it belongs to.
  const edgesByNode = new Map<string, SVGPathElement[]>();
  const edgesBySourcePort = new Map<string, SVGPathElement[]>();
  const track = (
    index: Map<string, SVGPathElement[]>,
    key: string | undefined,
    path: SVGPathElement
  ) => {
    if (!key) {
      return;
    }
    const list = index.get(key);
    if (list) {
      list.push(path);
    } else {
      index.set(key, [path]);
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
        .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x + offsetX} ${point.y + offsetY}`)
        .join(" ")
    );
    path.setAttribute("class", "elk-edge");
    path.setAttribute("marker-end", "url(#elk-arrowhead)");
    svg.append(path);
    track(edgesByNode, portToNode.get(edge.sources[0]), path);
    track(edgesByNode, portToNode.get(edge.targets[0]), path);
    track(edgesBySourcePort, edge.sources[0], path);
  }
  container.append(svg);

  // Hovering highlights what the pointer is on, and fades everything else (plan 6.4).
  // One shared "what is active" state, so that a re-render can restore it without a
  // gesture.
  let active: HTMLElement | undefined;
  let activeEdges: SVGPathElement[] = [];

  /**
   * The edges leaving one row. Two of them when the row is a dict entry whose key is a
   * reference: that row owns a second port, and both arrows leave the row being pointed
   * at, so both belong to it.
   */
  const edgesLeavingRow = (row: HTMLElement): SVGPathElement[] => {
    const nodeId = row.closest<HTMLElement>(`.${NODE_CLASS}`)?.dataset.nodeId;
    const index = Number(row.dataset.rowIndex);
    if (nodeId === undefined || !Number.isInteger(index)) {
      return [];
    }
    return [
      ...(edgesBySourcePort.get(rowPortId(nodeId, index)) ?? []),
      ...(edgesBySourcePort.get(keyPortId(nodeId, index)) ?? []),
    ];
  };

  /**
   * What the pointer at `target` picks out: the row, when an edge leaves it, and
   * otherwise the box that row is in. Falling back to the box is what lets a row with no
   * edge, a header and the gap between rows all keep the behaviour they had before rows
   * were pickable at all, without a case of their own.
   */
  const hoverTarget = (target: Element | null | undefined): HTMLElement | undefined => {
    const row = target?.closest<HTMLElement>(`.${ROW_CLASS}`) ?? undefined;
    if (row && container.contains(row) && edgesLeavingRow(row).length > 0) {
      return row;
    }
    const node = target?.closest<HTMLElement>(`.${NODE_CLASS}`) ?? undefined;
    return node && container.contains(node) ? node : undefined;
  };

  const paint = (on: boolean) => {
    if (active) {
      if (active.classList.contains(ROW_CLASS)) {
        active.classList.toggle("elk-row-active", on);
        // The box holding a lit row must not be dimmed: opacity applies to the whole
        // subtree, so dimming the box would take its highlighted row down with it.
        active
          .closest<HTMLElement>(`.${NODE_CLASS}`)
          ?.classList.toggle("elk-row-host", on);
      } else {
        active.classList.toggle("elk-node-active", on);
      }
    }
    for (const path of activeEdges) {
      path.classList.toggle("elk-edge-active", on);
    }
  };

  const setActive = (element: HTMLElement | undefined) => {
    if (active === element) {
      return;
    }
    paint(false);
    active = element;
    activeEdges = !element
      ? []
      : element.classList.contains(ROW_CLASS)
        ? edgesLeavingRow(element)
        : edgesByNode.get(element.dataset.nodeId ?? "") ?? [];
    paint(true);
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
    element.style.left = `${(child.x ?? 0) + offsetX}px`;
    element.style.top = `${(child.y ?? 0) + offsetY}px`;
    element.style.width = `${child.width ?? 0}px`;

    if (model.address === undefined) {
      framesRight = Math.max(
        framesRight,
        (child.x ?? 0) - contentLeft + (child.width ?? 0)
      );
    } else {
      objectsLeft = Math.min(objectsLeft, (child.x ?? 0) - contentLeft);
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

    // mouseover/mouseout rather than mouseenter/mouseleave: these bubble, so the rows
    // inside the box are reachable from one pair of listeners on the box itself. Still
    // per box, not delegated to the container, because the container outlives a render
    // and its listeners would pile up; these go away with the elements they are on.
    element.addEventListener("mouseover", (event) => {
      setActive(hoverTarget(event.target as Element | null));
    });
    element.addEventListener("mouseout", (event) => {
      const to = event.relatedTarget as Element | null;
      // Crossing from one row to the next fires mouseout before the matching mouseover,
      // so only a pointer that has really left the box clears the highlight. Without
      // this the row being moved onto would be cleared again by the row left behind.
      if (!to || !element.contains(to)) {
        setActive(undefined);
      }
    });

    container.append(element);
  }

  // Column captions, derived from where the nodes actually ended up: there are no
  // container nodes to hang them off (plan 4).
  if (framesRight > Number.NEGATIVE_INFINITY) {
    container.append(band("Frames", "elk-band-frames", MARGIN_X, framesRight));
  }
  if (objectsLeft < Number.POSITIVE_INFINITY) {
    container.append(
      band("Objects", "elk-band-objects", objectsLeft + MARGIN_X, width - objectsLeft)
    );
  }

  // Whatever the cursor is sitting on now is hovered, even though it never moved.
  // elementFromPoint flushes layout, so the positions set above are already in effect.
  if (pointer) {
    setActive(hoverTarget(document.elementFromPoint(pointer.x, pointer.y)));
  }
}
