/**
 * For better readable code
*/
export type Try = Success | Failure;
export type Success = { result: any };
export type Failure = { errorMessage: string };

// State Types for the Frontend
export type FrontendTrace = Array<FrontendTraceElem>;

export type FrontendTraceElem = {
  lineNumber: number, // 1-based
  stackHTML: string,
  heapHTML: string,
  filename: string,
  outputState: string,
};

// ############################################################################################
// State Types for the Backend
export type PartialBackendTrace = {
  trace: BackendTrace;
  complete: boolean;
};
export type BackendTrace = Array<BackendTraceElem>;
export type BackendTraceElem = {
  line: number;
  filePath: string,
  stack: Array<StackElem>;
  heap: Map<Address, HeapValue>;
  stdout: string;
  traceback: string | undefined;
};

export type Address = number;

export type Value =
  | { type: 'int'; value: number }
  | { type: 'float'; value: number }
  | { type: 'str'; value: string }
  | { type: 'none'; value: string }
  | { type: 'bool'; value: string }
  | { type: 'type'; value: string }
  | { type: 'function'; value: string }
  | { type: 'ref'; value: Address };

export type NamedValue = Value & {
  name: string;
};


export type StackElem = {
  frameName: string;
  locals: Array<NamedValue>;
};

export type HeapValue =
  | { type: 'list'; value: Array<Value> }
  | { type: 'tuple'; value: Array<Value> }
  | { type: 'set'; value: Array<Value> }
  | { type: 'dict'; keys: Map<any, Value>, value: Map<any, Value> }
  | { type: 'instance'; name: string, value: Map<string, Value> };
// wrapper type -> frontend list elements dodge

