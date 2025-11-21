/**
 * For better readable code
*/
type Try = Success | Failure;
type Success = { result: any };
type Failure = { errorMessage: string };

// State Types for the Frontend
type FrontendTrace = Array<FrontendTraceElem>;
// FIXME: what are this array elements? Why isn't there a type with named fields?
type FrontendTraceElem = [number, string, string, string, string];
// ############################################################################################
// State Types for the Backend
type PartialBackendTrace = {
  trace: BackendTrace;
  complete: boolean;
};
type BackendTrace = Array<BackendTraceElem>;
type BackendTraceElem = {
  line: number;
  filePath: string,
  stack: Array<StackElem>;
  heap: Map<Address, HeapValue>;
  stdout: string;
  traceback: string | undefined;
};

type Address = number;

type Value =
  | { type: 'int'; value: number }
  | { type: 'float'; value: number }
  | { type: 'str'; value: string }
  | { type: 'none'; value: string }
  | { type: 'bool'; value: string }
  | { type: 'type'; value: string }
  | { type: 'function'; value: string }
  | { type: 'ref'; value: Address };

type NamedValue = Value & {
  name: string;
};


type StackElem = {
  frameName: string;
  locals: Array<NamedValue>;
};

type HeapValue =
  | { type: 'list'; value: Array<Value> }
  | { type: 'tuple'; value: Array<Value> }
  | { type: 'set'; value: Array<Value> }
  | { type: 'dict'; keys: Map<any, Value>, value: Map<any, Value> }
  | { type: 'instance'; name: string, value: Map<string, Value> };
// wrapper type -> frontend list elements dodge

