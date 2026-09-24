/* eslint-disable @typescript-eslint/naming-convention */
// Heap addresses are numeric keys, so the fixtures below cannot use camelCase names.
//
// Shared by reachability.test.ts and graph-model.test.ts. Not a `.test.ts` file on
// purpose: the mocha glob is `out/test/unit/**/*.test.js`, so this is never run as a suite.
import type { Address, BackendTraceElem, HeapValue, NamedValue, StackElem, Value } from '../../programflow-visualization/types';

export function ref(address: Address): Value {
  return { type: 'ref', value: address };
}

export function int(value: number): Value {
  return { type: 'int', value };
}

export function str(value: string): Value {
  return { type: 'str', value };
}

export function none(): Value {
  return { type: 'none', value: 'None' };
}

export function local(name: string, value: Value): NamedValue {
  return { ...value, name };
}

export function frame(frameName: string, locals: Array<NamedValue>): StackElem {
  return { frameName, locals };
}

export function list(...values: Array<Value>): HeapValue {
  return { type: 'list', value: values };
}

export function tuple(...values: Array<Value>): HeapValue {
  return { type: 'tuple', value: values };
}

export function set(...values: Array<Value>): HeapValue {
  return { type: 'set', value: values };
}

export function instance(name: string, fields: Record<string, Value>): HeapValue {
  return { type: 'instance', name, value: fields as unknown as Map<string, Value> };
}

export function dict(entries: Array<[Value, Value]>): HeapValue {
  const keys: Record<string, Value> = {};
  const values: Record<string, Value> = {};
  entries.forEach(([key, value], index) => {
    keys[index] = key;
    values[index] = value;
  });
  return {
    type: 'dict',
    keys: keys as unknown as Map<any, Value>,
    value: values as unknown as Map<any, Value>,
  };
}

/**
 * `heap` is declared as a `Map` but arrives as a plain object after IPC/JSON -
 * the fixtures deliberately reproduce the runtime shape, not the declared one.
 */
export function step(stack: Array<StackElem>, heap: Record<number, HeapValue>): BackendTraceElem {
  return {
    line: 1,
    filePath: 'example.py',
    stack,
    heap: heap as unknown as BackendTraceElem['heap'],
    stdout: '',
    traceback: undefined,
  };
}
