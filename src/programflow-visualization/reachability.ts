// Reachability filter for the visualization: decides which heap objects are visible
// for a trace step, given the set of collapsed objects. See elk-task/elk-plan.md 6.3.
//
// Pure and free of DOM/ELK dependencies so it can be unit tested directly.
import type { Address, BackendTraceElem, HeapValue, NamedValue, Value } from "./types";

type RefValue = { type: 'ref'; value: Address };

/**
 * `heap`, `dict.keys`, `dict.value` and `instance.value` are declared as `Map`s in
 * types.ts, but after the IPC/JSON round trip they are plain objects. Everything here
 * goes through this helper instead of `Map` methods.
 */
export function asRecord<T>(mapLike: unknown): Record<string, T> {
  return (mapLike ?? {}) as Record<string, T>;
}

function isRef<T extends Value>(value: T): value is T & RefValue {
  return value.type === 'ref';
}

export function heapEntries(heap: BackendTraceElem['heap']): Array<[Address, HeapValue]> {
  return Object.entries(asRecord<HeapValue>(heap)).map(
    ([address, value]) => [Number(address), value]
  );
}

/** Addresses referenced by a heap object: elements, dict keys and values, instance fields. */
export function outgoingRefs(heapValue: HeapValue): Address[] {
  switch (heapValue.type) {
    case 'dict': {
      const keys = Object.values(asRecord<Value>(heapValue.keys));
      const values = Object.values(asRecord<Value>(heapValue.value));
      return [...keys, ...values].filter(isRef).map((value) => value.value);
    }
    case 'instance': {
      const fields = Object.values(asRecord<Value>(heapValue.value));
      return fields.filter(isRef).map((value) => value.value);
    }
    default:
      return heapValue.value.filter(isRef).map((value) => value.value);
  }
}

/** Addresses referenced directly by a stack frame, i.e. the roots of the traversal. */
export function rootRefs(elem: BackendTraceElem): Address[] {
  return elem.stack.flatMap((frame) =>
    (frame.locals as Array<NamedValue>).filter(isRef).map((local) => local.value)
  );
}

/**
 * Every heap address that should be rendered for this step.
 *
 * Traversal starts at the stack frames and does not follow edges *out of* a collapsed
 * object - the collapsed object itself stays visible. An object therefore disappears
 * only when it is exclusively downstream of a collapsed one; anything still reachable
 * by another path stays.
 */
export function visibleAddresses(
  elem: BackendTraceElem,
  collapsed: ReadonlySet<Address> = new Set()
): Set<Address> {
  const heap = new Map(heapEntries(elem.heap));
  const visible = new Set<Address>();
  const pending = rootRefs(elem).filter((address) => heap.has(address));

  while (pending.length > 0) {
    const address = pending.pop()!;
    if (visible.has(address)) {
      continue;
    }
    visible.add(address);

    // Collapsed: render the box, but nothing behind it.
    if (collapsed.has(address)) {
      continue;
    }

    for (const next of outgoingRefs(heap.get(address)!)) {
      if (!visible.has(next) && heap.has(next)) {
        pending.push(next);
      }
    }
  }

  return visible;
}
