// Draws a laid-out graph. See elk-task/elk-plan.md 6.3.
//
// Builds the node elements from the same `renderNode` measure.ts used, then places them at
// the coordinates ELK computed. Edges go into one SVG overlay behind the nodes.
import type { ElkExtendedEdge, ElkNode } from "elkjs/lib/elk-api";
import type { NodeModel } from "../graph-model";
import { keyPortId, parsePortId, rowPortId } from "../graph-model";
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
 * How far along an edge its K/V badge sits, from the point where the edge leaves the
 * node. One offset per glyph, because vertical room is what this graph has least of:
 * ports are a third of a row height apart within a row and two thirds across the row
 * boundary, which at any zoom is less than the glyphs are tall. Staggering the two
 * sideways means a K and a V can never collide whatever the spacing; two badges of the
 * same letter are a whole row apart and never do.
 */
const BADGE_DX_KEY = 4;
const BADGE_DX_VALUE = 13;

/** And how far above the line, so the stroke does not run through the glyph. */
const BADGE_DY = 2;

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

/** The `K`/`V` glyph sitting on an edge, just outside the dict row it leaves. */
function edgeBadge(text: "K" | "V", x: number, y: number): SVGTextElement {
  const label = document.createElementNS(SVG_NS, "text");
  label.setAttribute("class", "elk-edge-badge");
  label.setAttribute("x", `${x + (text === "K" ? BADGE_DX_KEY : BADGE_DX_VALUE)}`);
  label.setAttribute("y", `${y - BADGE_DY}`);
  label.textContent = text;
  return label;
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

  // Three indexes over the same edge elements. Into/out of a node are kept apart rather
  // than merged, because pointing at a row inside a box wants the incoming ones only (see
  // `hoverTarget`). By source port is the finest: the single row an arrow leaves from.
  //
  // An edge is a path plus, on dict rows, its K/V badge. Both go into every index, so
  // the badge lights up and dims with the line it belongs to.
  const edgesIntoNode = new Map<string, SVGElement[]>();
  const edgesOutOfNode = new Map<string, SVGElement[]>();
  const edgesBySourcePort = new Map<string, SVGElement[]>();
  const track = (
    index: Map<string, SVGElement[]>,
    key: string | undefined,
    parts: SVGElement[]
  ) => {
    if (!key) {
      return;
    }
    const list = index.get(key);
    if (list) {
      list.push(...parts);
    } else {
      index.set(key, [...parts]);
    }
  };

  /**
   * `K` or `V` for an edge leaving a dict row, undefined everywhere else.
   *
   * Only dicts pair two things per row, so only dicts leave a reader asking which half
   * an arrow came from; labelling every edge in the graph would be noise.
   */
  const badgeTextFor = (sourcePortId: string): "K" | "V" | undefined => {
    const port = parsePortId(sourcePortId);
    if (!port || models.get(port.nodeId)?.kind !== "dict") {
      return undefined;
    }
    return port.isKey ? "K" : "V";
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

    const parts: SVGElement[] = [path];
    const text = badgeTextFor(edge.sources[0]);
    if (text) {
      const badge = edgeBadge(text, points[0].x + offsetX, points[0].y + offsetY);
      svg.append(badge);
      parts.push(badge);
    }

    track(edgesOutOfNode, portToNode.get(edge.sources[0]), parts);
    track(edgesIntoNode, portToNode.get(edge.targets[0]), parts);
    track(edgesBySourcePort, edge.sources[0], parts);
  }
  container.append(svg);

  // Hovering highlights what the pointer is on, and fades everything else (plan 6.4).
  // One shared "what is active" state, so that a re-render can restore it without a
  // gesture.

  /** What a hover picks out: one element to mark, and the edges that belong to it. */
  type Hover = {
    element: HTMLElement;
    /** `row` washes the row itself; both `box` kinds outline the whole box. */
    kind: "row" | "box-incoming" | "box-all";
    edges: SVGElement[];
  };

  let active: Hover | undefined;

  /**
   * The edges leaving one row. Two of them when the row is a dict entry whose key is a
   * reference: that row owns a second port, and both arrows leave the row being pointed
   * at, so both belong to it.
   */
  const edgesLeavingRow = (row: HTMLElement): SVGElement[] => {
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
   * What the pointer at `target` picks out. Three cases, narrowest first:
   *
   * - a row with an arrow leaving it: the row, and that arrow;
   * - any other row: the box it sits in, but only the edges coming *into* the box. Its
   *   outgoing edges belong to other rows, and lighting them up while the reader points
   *   at a row that references nothing says the opposite of the truth;
   * - anything else — a header, the gap between rows: the box and everything touching
   *   it, which is what hovering has always done.
   */
  const hoverTarget = (target: Element | null | undefined): Hover | undefined => {
    const node = target?.closest<HTMLElement>(`.${NODE_CLASS}`) ?? undefined;
    if (!node || !container.contains(node)) {
      return undefined;
    }
    const nodeId = node.dataset.nodeId ?? "";
    const incoming = edgesIntoNode.get(nodeId) ?? [];
    const row = target?.closest<HTMLElement>(`.${ROW_CLASS}`) ?? undefined;
    if (row) {
      const leaving = edgesLeavingRow(row);
      return leaving.length > 0
        ? { element: row, kind: "row", edges: leaving }
        : { element: node, kind: "box-incoming", edges: incoming };
    }
    return {
      element: node,
      kind: "box-all",
      edges: [...incoming, ...(edgesOutOfNode.get(nodeId) ?? [])],
    };
  };

  const paint = (on: boolean) => {
    if (!active) {
      return;
    }
    if (active.kind === "row") {
      active.element.classList.toggle("elk-row-active", on);
      // The box holding a lit row must not be dimmed: opacity applies to the whole
      // subtree, so dimming the box would take its highlighted row down with it.
      active.element
        .closest<HTMLElement>(`.${NODE_CLASS}`)
        ?.classList.toggle("elk-row-host", on);
    } else {
      active.element.classList.toggle("elk-node-active", on);
    }
    for (const path of active.edges) {
      path.classList.toggle("elk-edge-active", on);
    }
  };

  const setActive = (next: Hover | undefined) => {
    // Both halves matter: a header and an edgeless row resolve to the same box and
    // differ only in which of its edges they light.
    if (active?.element === next?.element && active?.kind === next?.kind) {
      return;
    }
    paint(false);
    active = next;
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
