/* eslint-disable @typescript-eslint/naming-convention */
// Structure tests for buildGraph. No DOM and no ELK run - this is the pure half of the
// pipeline, the half that the browser harness is bad at checking (elk-task/elk-plan.md 7.8).
import * as assert from 'assert';

import {
  buildGraph,
  formatValue,
  frameNodeId,
  inputPortId,
  keyPortId,
  objectNodeId,
  rowPortId,
  rowsOfHeapValue,
} from '../../programflow-visualization/graph-model';
import type { NodeModel, VizGraph } from '../../programflow-visualization/graph-model';
import { outgoingRefs } from '../../programflow-visualization/reachability';
import type { Address, BackendTraceElem, HeapValue } from '../../programflow-visualization/types';
import { dict, frame, instance, int, list, local, none, ref, set, step, str, tuple } from './fixtures';

// Helpers ---------------------------------------------------------------------

function build(elem: BackendTraceElem, collapsed: Array<Address> = []): VizGraph {
  return buildGraph(elem, new Set(collapsed));
}

function nodeIds(viz: VizGraph): Array<string> {
  return (viz.graph.children ?? []).map((child) => child.id);
}

function node(viz: VizGraph, id: string) {
  const found = (viz.graph.children ?? []).find((child) => child.id === id);
  assert.ok(found, `no node ${id}`);
  return found;
}

function portIds(viz: VizGraph, id: string): Array<string> {
  return (node(viz, id).ports ?? []).map((port) => port.id);
}

function model(viz: VizGraph, id: string): NodeModel {
  const found = viz.nodes.get(id);
  assert.ok(found, `no model ${id}`);
  return found;
}

/** Every edge as `sourcePort -> targetPort`, sorted, for order-free comparison. */
function edges(viz: VizGraph): Array<string> {
  return (viz.graph.edges ?? [])
    .map((edge) => `${edge.sources[0]} -> ${edge.targets[0]}`)
    .sort();
}

/** How many references the step contains among the visible objects. */
function refCount(elem: BackendTraceElem, heap: Record<number, HeapValue>): number {
  const fromStack = elem.stack.reduce(
    (total, stackElem) => total + stackElem.locals.filter((value) => value.type === 'ref').length,
    0
  );
  const fromHeap = Object.values(heap).reduce(
    (total, heapValue) => total + outgoingRefs(heapValue).length,
    0
  );
  return fromStack + fromHeap;
}

// Tests -----------------------------------------------------------------------

suite('graph-model: nodes', () => {
  test('frames come first, in stack order, then objects ascending by address', () => {
    const elem = step(
      [frame('<module>', [local('xs', ref(7))]), frame('f', [local('ys', ref(2))])],
      { 7: list(int(1)), 2: list(int(2)) }
    );
    assert.deepStrictEqual(nodeIds(build(elem)), [
      frameNodeId(0),
      frameNodeId(1),
      objectNodeId(2),
      objectNodeId(7),
    ]);
  });

  test('address order is independent of heap insertion order, so steps stay stable', () => {
    const ascending = step([frame('<module>', [local('a', ref(1)), local('b', ref(9))])], {
      1: list(), 9: list(),
    });
    const descending = step([frame('<module>', [local('b', ref(9)), local('a', ref(1))])], {
      9: list(), 1: list(),
    });
    assert.deepStrictEqual(nodeIds(build(ascending)).slice(2), nodeIds(build(descending)).slice(2));
  });

  test('the last stack entry is the current frame, not the first', () => {
    const elem = step([frame('<module>', []), frame('g', []), frame('h', [])], {});
    assert.strictEqual(model(build(elem), frameNodeId(0)).kind, 'frame');
    assert.strictEqual(model(build(elem), frameNodeId(1)).kind, 'frame');
    assert.strictEqual(model(build(elem), frameNodeId(2)).kind, 'current-frame');
  });

  test('<module> is shown as Global, other frames keep their name', () => {
    const elem = step([frame('<module>', []), frame('createGradeList', [])], {});
    assert.strictEqual(model(build(elem), frameNodeId(0)).header, 'Global');
    assert.strictEqual(model(build(elem), frameNodeId(1)).header, 'createGradeList');
  });

  test('node kind and header follow the heap value; instances use their class name', () => {
    const elem = step(
      [frame('<module>', [local('a', ref(1)), local('b', ref(2)), local('c', ref(3)), local('d', ref(4)), local('e', ref(5))])],
      {
        1: list(int(1)),
        2: tuple(int(1)),
        3: set(int(1)),
        4: dict([[str('k'), int(1)]]),
        5: instance('Student', { name: str('lara') }),
      }
    );
    const viz = build(elem);
    const kinds = [1, 2, 3, 4, 5].map((address) => model(viz, objectNodeId(address)).kind);
    assert.deepStrictEqual(kinds, ['list', 'tuple', 'set', 'dict', 'instance']);
    assert.strictEqual(model(viz, objectNodeId(5)).header, 'Student');
    assert.strictEqual(model(viz, objectNodeId(1)).header, 'list');
  });

  test('only frames carry the layer constraint, and every node has fixed ports', () => {
    const elem = step([frame('<module>', [local('xs', ref(1))])], { 1: list() });
    const viz = build(elem);
    assert.strictEqual(
      node(viz, frameNodeId(0)).layoutOptions?.['elk.layered.layering.layerConstraint'],
      'FIRST_SEPARATE'
    );
    assert.strictEqual(
      node(viz, objectNodeId(1)).layoutOptions?.['elk.layered.layering.layerConstraint'],
      undefined
    );
    for (const child of viz.graph.children ?? []) {
      assert.strictEqual(child.layoutOptions?.['elk.portConstraints'], 'FIXED_POS');
    }
  });
});

suite('graph-model: rows', () => {
  test('list and tuple rows are indexed, set rows have no key', () => {
    assert.deepStrictEqual(
      rowsOfHeapValue(list(int(4), str('x'))).map((row) => row.key),
      ['[0]', '[1]']
    );
    assert.deepStrictEqual(rowsOfHeapValue(set(str('a'), str('b'))).map((row) => row.key), ['', '']);
  });

  test('instance rows are named after their fields', () => {
    const rows = rowsOfHeapValue(instance('Student', { name: str('lara'), age: int(21) }));
    assert.deepStrictEqual(rows.map((row) => row.key), ['name', 'age']);
    assert.deepStrictEqual(rows.map((row) => row.value), ['lara', '21']);
  });

  test('a reference cell has no text of its own, only a ref', () => {
    const rows = rowsOfHeapValue(list(ref(3)));
    assert.deepStrictEqual(rows, [{ key: '[0]', value: '', ref: 3 }]);
  });

  test('a dict key that is a reference is labelled [key] and recorded as keyRef', () => {
    const rows = rowsOfHeapValue(dict([[ref(8), str('even pair')], [str('plain'), int(1)]]));
    assert.deepStrictEqual(rows[0], { key: '[key]', value: 'even pair', ref: undefined, keyRef: 8 });
    assert.deepStrictEqual(rows[1], { key: 'plain', value: '1', ref: undefined, keyRef: undefined });
  });

  test('a local named return is flagged for highlighting', () => {
    const elem = step([frame('f', [local('x', int(1)), local('return', int(9))])], {});
    const rows = model(build(elem), frameNodeId(0)).rows;
    assert.strictEqual(rows[0].isReturn, false);
    assert.strictEqual(rows[1].isReturn, true);
  });

  test('formatValue renders None as None and leaves refs blank', () => {
    assert.strictEqual(formatValue(none()), 'None');
    assert.strictEqual(formatValue(ref(5)), '');
    assert.strictEqual(formatValue(int(3)), '3');
  });

  test('the summary counts rows and is singular for one', () => {
    const elem = step(
      [frame('<module>', [local('a', ref(1)), local('b', ref(2)), local('c', ref(3))])],
      { 1: list(int(1), int(2)), 2: dict([[str('k'), int(1)]]), 3: instance('S', { x: int(1) }) }
    );
    const viz = build(elem);
    assert.strictEqual(model(viz, objectNodeId(1)).summary, '2 elements');
    assert.strictEqual(model(viz, objectNodeId(2)).summary, '1 entry');
    assert.strictEqual(model(viz, objectNodeId(3)).summary, '1 field');
  });
});

suite('graph-model: ports and edges', () => {
  test('objects declare a west input port, frames do not', () => {
    const elem = step([frame('<module>', [local('xs', ref(1))])], { 1: list() });
    const viz = build(elem);
    assert.deepStrictEqual(portIds(viz, objectNodeId(1)), [inputPortId(objectNodeId(1))]);
    assert.deepStrictEqual(portIds(viz, frameNodeId(0)), [rowPortId(frameNodeId(0), 0)]);
  });

  test('only rows holding a reference get a row port', () => {
    const elem = step([frame('<module>', [local('xs', ref(1))])], {
      1: list(int(0), ref(2), int(0)),
      2: list(),
    });
    const viz = build(elem);
    assert.deepStrictEqual(portIds(viz, objectNodeId(1)), [
      inputPortId(objectNodeId(1)),
      rowPortId(objectNodeId(1), 1),
    ]);
  });

  test('a row with a reference key and a reference value gets both ports, key first', () => {
    const elem = step([frame('<module>', [local('d', ref(1))])], {
      1: dict([[ref(2), ref(3)]]),
      2: tuple(int(1)),
      3: list(),
    });
    const viz = build(elem);
    assert.deepStrictEqual(portIds(viz, objectNodeId(1)), [
      inputPortId(objectNodeId(1)),
      keyPortId(objectNodeId(1), 0),
      rowPortId(objectNodeId(1), 0),
    ]);
  });

  test('edges leave the referencing row and land on the input port of the target', () => {
    const elem = step([frame('<module>', [local('xs', ref(1))])], { 1: list(ref(2)), 2: list() });
    assert.deepStrictEqual(edges(build(elem)), [
      `${objectNodeId(1)}:0 -> ${inputPortId(objectNodeId(2))}`,
      `${frameNodeId(0)}:0 -> ${inputPortId(objectNodeId(1))}`,
    ].sort());
  });

  test('a dict key that is a reference gets its own edge', () => {
    // Regression: the key object used to be visible with nothing pointing at it, so ELK
    // laid it out as a root - left of the frames (elk-task/elk-plan.md 7.7).
    const heap = { 1: dict([[ref(2), str('even pair')]]), 2: tuple(int(1), int(2)) };
    const elem = step([frame('<module>', [local('byPair', ref(1))])], heap);
    const viz = build(elem);
    assert.deepStrictEqual(edges(viz), [
      `${frameNodeId(0)}:0 -> ${inputPortId(objectNodeId(1))}`,
      `${keyPortId(objectNodeId(1), 0)} -> ${inputPortId(objectNodeId(2))}`,
    ].sort());
    assert.strictEqual(refCount(elem, heap), edges(viz).length);
  });

  test('with nothing collapsed, edge count equals reference count', () => {
    // Definition of done, criterion 2.
    const heap: Record<number, HeapValue> = {
      1: list(ref(2), ref(3), int(0)),
      2: instance('Student', { friend: ref(3), age: int(21) }),
      3: dict([[ref(4), ref(2)], [str('k'), int(1)]]),
      4: tuple(int(1), int(2)),
    };
    const elem = step(
      [frame('<module>', [local('xs', ref(1)), local('n', int(3))]), frame('f', [local('s', ref(2))])],
      heap
    );
    const viz = build(elem);
    assert.strictEqual(edges(viz).length, refCount(elem, heap));
    assert.strictEqual(new Set(edges(viz)).size, edges(viz).length, 'no duplicate edges');
  });

  test('every edge endpoint is a port that exists on some node', () => {
    const heap: Record<number, HeapValue> = {
      1: list(ref(2)),
      2: dict([[ref(3), ref(1)]]),
      3: set(str('a')),
    };
    const elem = step([frame('<module>', [local('xs', ref(1))])], heap);
    const viz = build(elem);
    const declared = new Set(
      (viz.graph.children ?? []).flatMap((child) => (child.ports ?? []).map((port) => port.id))
    );
    for (const edge of viz.graph.edges ?? []) {
      assert.ok(declared.has(edge.sources[0]), `dangling source ${edge.sources[0]}`);
      assert.ok(declared.has(edge.targets[0]), `dangling target ${edge.targets[0]}`);
    }
  });

  test('a self-reference becomes a self-loop rather than being dropped', () => {
    const elem = step([frame('<module>', [local('xs', ref(1))])], { 1: list(ref(1)) });
    assert.deepStrictEqual(edges(build(elem)), [
      `${frameNodeId(0)}:0 -> ${inputPortId(objectNodeId(1))}`,
      `${objectNodeId(1)}:0 -> ${inputPortId(objectNodeId(1))}`,
    ].sort());
  });

  test('a cycle terminates and both directions are drawn', () => {
    const elem = step([frame('<module>', [local('left', ref(1))])], {
      1: list(ref(2)),
      2: list(ref(1)),
    });
    assert.strictEqual(edges(build(elem)).length, 3);
  });
});

suite('graph-model: collapsing', () => {
  test('a collapsed object keeps its input port but loses its row ports and edges', () => {
    const elem = step([frame('<module>', [local('xs', ref(1))])], { 1: list(ref(2)), 2: list() });
    const viz = build(elem, [1]);
    assert.deepStrictEqual(portIds(viz, objectNodeId(1)), [inputPortId(objectNodeId(1))]);
    assert.deepStrictEqual(edges(viz), [`${frameNodeId(0)}:0 -> ${inputPortId(objectNodeId(1))}`]);
  });

  test('a collapsed node keeps its rows in the model, for the summary and for re-expanding', () => {
    const elem = step([frame('<module>', [local('xs', ref(1))])], { 1: list(int(1), int(2)) });
    const collapsedModel = model(build(elem, [1]), objectNodeId(1));
    assert.strictEqual(collapsedModel.collapsed, true);
    assert.strictEqual(collapsedModel.rows.length, 2);
    assert.strictEqual(collapsedModel.summary, '2 elements');
  });

  test('collapsing removes exclusively downstream nodes but keeps shared ones', () => {
    const elem = step(
      [frame('<module>', [local('xs', ref(1)), local('shared', ref(3))])],
      { 1: list(ref(2), ref(3)), 2: list(), 3: list() }
    );
    const ids = nodeIds(build(elem, [1]));
    assert.ok(!ids.includes(objectNodeId(2)), 'anonymous child should be gone');
    assert.ok(ids.includes(objectNodeId(3)), 'child with another root should stay');
  });

  test('collapsing an address that is not on screen changes nothing', () => {
    const elem = step([frame('<module>', [local('xs', ref(1))])], { 1: list(int(1)) });
    assert.deepStrictEqual(nodeIds(build(elem, [99])), nodeIds(build(elem)));
    assert.deepStrictEqual(edges(build(elem, [99])), edges(build(elem)));
  });

  test('frames are never collapsible', () => {
    const elem = step([frame('<module>', [local('n', int(1))])], {});
    const frameModel = model(build(elem), frameNodeId(0));
    assert.strictEqual(frameModel.address, undefined);
    assert.strictEqual(frameModel.collapsed, false);
  });
});
