// The single source of node markup. See elk-task/elk-plan.md 6.
//
// measure.ts renders these offscreen to obtain sizes, graph-renderer.ts renders
// them for real. Both must call renderNode, never build markup of their own, or
// measured sizes stop matching what is drawn.
import type { NodeModel, RowModel } from "../graph-model";

export const NODE_CLASS = "elk-node";
export const HEADER_CLASS = "elk-node-header";
export const ROWS_CLASS = "elk-node-rows";
export const ROW_CLASS = "elk-row";

function div(className: string, text?: string): HTMLDivElement {
  const element = document.createElement("div");
  element.className = className;
  if (text !== undefined) {
    // textContent, not innerHTML: trace values are program data.
    element.textContent = text;
  }
  return element;
}

function renderRow(row: RowModel): HTMLElement {
  const element = div(ROW_CLASS);
  const key = div("elk-row-key" + (row.isReturn ? " return-value" : ""), row.key);
  const value = div("elk-row-value", row.value);
  if (row.ref !== undefined) {
    element.classList.add("elk-row-ref");
  }
  if (row.keyRef !== undefined) {
    key.classList.add("elk-key-ref");
  }
  element.append(key, value);
  return element;
}

export function renderNode(model: NodeModel): HTMLElement {
  const node = div(`${NODE_CLASS} elk-${model.kind}`);
  node.dataset.nodeId = model.id;

  const header = div(HEADER_CLASS);
  const collapsible = model.address !== undefined;
  if (collapsible) {
    // Discoverable and keyboard-operable (plan 6.3).
    header.classList.add("elk-collapsible");
    header.setAttribute("role", "button");
    header.setAttribute("tabindex", "0");
    header.setAttribute("aria-expanded", String(!model.collapsed));
    header.append(div("elk-caret", model.collapsed ? "\u25B8" : "\u25BE"));
  }
  header.append(div("elk-node-title", model.header));
  node.append(header);

  // Collapsed is a single line: the header and nothing under it. A summary row said
  // "3 fields", which the caret beside it already implies and expanding shows properly,
  // so it spent a second line -- and the width of its text -- on nothing new.
  if (model.collapsed) {
    node.classList.add("elk-collapsed");
    return node;
  }

  const rows = div(ROWS_CLASS);
  model.rows.forEach((row, index) => {
    const element = renderRow(row);
    // The index is what ties a row back to its ports, and so to the edges leaving it
    // (graph-renderer.ts). Written here rather than in the renderer so that the markup
    // measure.ts sizes and the markup the reader points at stay the same markup.
    element.dataset.rowIndex = String(index);
    rows.append(element);
  });
  node.append(rows);

  return node;
}

/** Row elements of a rendered node, in model order. */
export function rowElements(node: HTMLElement): HTMLElement[] {
  const rows = node.querySelector(`.${ROWS_CLASS}`);
  return rows ? (Array.from(rows.children) as HTMLElement[]) : [];
}

export function headerElement(node: HTMLElement): HTMLElement | null {
  return node.querySelector(`.${HEADER_CLASS}`);
}
