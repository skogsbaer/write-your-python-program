/* eslint-disable @typescript-eslint/naming-convention */
// Heap addresses are numeric keys, so the fixtures below cannot use camelCase names.
import * as assert from 'assert';

import { outgoingRefs, rootRefs, visibleAddresses } from '../../programflow-visualization/reachability';
import type { Address, BackendTraceElem } from '../../programflow-visualization/types';
import { dict, frame, instance, int, list, local, ref, step, str } from './fixtures';

function visible(elem: BackendTraceElem, collapsed: Array<Address> = []): Array<Address> {
  return [...visibleAddresses(elem, new Set(collapsed))].sort((a, b) => a - b);
}

// Tests -----------------------------------------------------------------------

suite('reachability: traversal basics', () => {
  test('empty heap and empty stack yield nothing', () => {
    assert.deepStrictEqual(visible(step([frame('<module>', [])], {})), []);
  });

  test('non-reference locals are not roots', () => {
    const elem = step([frame('<module>', [local('count', int(3))])], { 0: list(int(1)) });
    assert.deepStrictEqual(visible(elem), []);
  });

  test('roots come from every frame, not only the current one', () => {
    const elem = step(
      [
        frame('<module>', [local('outer', ref(0))]),
        frame('helper', [local('inner', ref(1))]),
      ],
      { 0: list(int(1)), 1: list(int(2)) }
    );
    assert.deepStrictEqual(visible(elem), [0, 1]);
  });

  test('objects unreachable from the stack are dropped', () => {
    const elem = step([frame('<module>', [local('kept', ref(0))])], {
      0: list(int(1)),
      1: list(int(2)), // garbage: nothing points here
    });
    assert.deepStrictEqual(visible(elem), [0]);
  });

  test('references to addresses missing from the heap are ignored', () => {
    const elem = step([frame('<module>', [local('dangling', ref(7))])], {});
    assert.deepStrictEqual(visible(elem), []);
  });
});

suite('reachability: container types', () => {
  test('instance fields are followed', () => {
    const elem = step([frame('<module>', [local('subject', ref(0))])], {
      0: instance('Subject', { name: str('AuD'), students: ref(1) }),
      1: list(ref(2)),
      2: instance('Student', { name: str('Tim'), grade: int(1) }),
    });
    assert.deepStrictEqual(visible(elem), [0, 1, 2]);
  });

  test('dict reference keys and reference values are both followed', () => {
    const elem = step([frame('<module>', [local('byPair', ref(0))])], {
      0: dict([[ref(1), ref(2)]]),
      1: { type: 'tuple', value: [int(1), int(2)] },
      2: list(str('a')),
    });
    assert.deepStrictEqual(visible(elem), [0, 1, 2]);
  });

  test('set and tuple elements are followed', () => {
    const elem = step([frame('<module>', [local('mixed', ref(0))])], {
      0: { type: 'tuple', value: [ref(1), int(42), str('text')] },
      1: { type: 'set', value: [ref(2)] },
      2: list(int(1)),
    });
    assert.deepStrictEqual(visible(elem), [0, 1, 2]);
  });

  test('outgoingRefs reports only reference values', () => {
    assert.deepStrictEqual(outgoingRefs(list(int(1), ref(4), str('x'), ref(9))), [4, 9]);
    assert.deepStrictEqual(outgoingRefs(instance('S', { a: int(1), b: ref(3) })), [3]);
    assert.deepStrictEqual(outgoingRefs(dict([[str('k'), ref(5)]])), [5]);
  });

  test('rootRefs reports only reference locals', () => {
    const elem = step(
      [frame('<module>', [local('n', int(1)), local('a', ref(2)), local('b', ref(3))])],
      {}
    );
    assert.deepStrictEqual(rootRefs(elem), [2, 3]);
  });
});

suite('reachability: cycles terminate', () => {
  test('self-referencing list', () => {
    const elem = step([frame('<module>', [local('selfRef', ref(0))])], {
      0: list(ref(0)),
    });
    assert.deepStrictEqual(visible(elem), [0]);
  });

  test('two-object cycle', () => {
    const elem = step([frame('<module>', [local('left', ref(0))])], {
      0: list(ref(1)),
      1: list(ref(0)),
    });
    assert.deepStrictEqual(visible(elem), [0, 1]);
  });

  test('cycle reachable only through a collapsed object disappears', () => {
    const elem = step([frame('<module>', [local('outer', ref(0))])], {
      0: list(ref(1)),
      1: list(ref(2)),
      2: list(ref(1)),
    });
    assert.deepStrictEqual(visible(elem), [0, 1, 2]);
    assert.deepStrictEqual(visible(elem, [0]), [0]);
  });
});

suite('reachability: collapsing', () => {
  // Mirrors elk-task/example-anonymous.py: `data = [[1, 2], [3, 4]]`
  const anonymous = step([frame('<module>', [local('data', ref(0))])], {
    0: list(ref(1), ref(2)),
    1: list(int(1), int(2)),
    2: list(int(3), int(4)),
  });

  test('nothing is hidden while nothing is collapsed', () => {
    assert.deepStrictEqual(visible(anonymous), [0, 1, 2]);
  });

  test('the collapsed object itself stays visible', () => {
    assert.ok(visible(anonymous, [0]).includes(0));
  });

  test('exclusively downstream objects disappear', () => {
    assert.deepStrictEqual(visible(anonymous, [0]), [0]);
  });

  test('expanding again restores the full picture', () => {
    assert.deepStrictEqual(visible(anonymous, []), visible(anonymous));
  });

  // Mirrors elk-task/example.py: two subject lists sharing some students.
  const shared = step(
    [frame('<module>', [local('aud', ref(0)), local('prog1', ref(1))])],
    {
      0: list(ref(2), ref(3)), // aud    -> lara, tim
      1: list(ref(2)),         // prog1  -> lara
      2: instance('Student', { name: str('Lara') }),
      3: instance('Student', { name: str('Tim') }),
    }
  );

  test('collapsing one referrer keeps objects the other still reaches', () => {
    // lara (2) survives because prog1 still points at her, tim (3) does not.
    assert.deepStrictEqual(visible(shared, [0]), [0, 1, 2]);
  });

  test('collapsing every referrer removes the shared object', () => {
    assert.deepStrictEqual(visible(shared, [0, 1]), [0, 1]);
  });

  test('an object with its own name survives collapsing its container', () => {
    // elk-task/example-anonymous.py: `shared` is a global, `holder = [shared]`.
    const elem = step(
      [frame('<module>', [local('shared', ref(1)), local('holder', ref(0))])],
      {
        0: list(ref(1)),
        1: instance('Student', { name: str('Cleo') }),
      }
    );
    assert.deepStrictEqual(visible(elem, [0]), [0, 1]);
  });

  test('collapsing cuts only at the collapsed node, not above or below it', () => {
    // 0 -> 1 -> 2 -> 3, collapse the middle one.
    const chain = step([frame('<module>', [local('head', ref(0))])], {
      0: list(ref(1)),
      1: list(ref(2)),
      2: list(ref(3)),
      3: list(int(0)),
    });
    assert.deepStrictEqual(visible(chain, [1]), [0, 1]);
    assert.deepStrictEqual(visible(chain, [2]), [0, 1, 2]);
  });

  test('collapsing an object that is not in the heap changes nothing', () => {
    assert.deepStrictEqual(visible(anonymous, [99]), [0, 1, 2]);
  });
});
