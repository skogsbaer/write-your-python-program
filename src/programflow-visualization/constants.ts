import * as vscode from 'vscode';

export namespace Variables {
  export const CACHED_TRACES = 'programflow-visualization.cached-traces';
  export const TRACE_CACHE_DIR = 'programflow-visualization.trace-cache-dir';
}

export const nextLineExecuteHighlightType = vscode.window.createTextEditorDecorationType({
  backgroundColor: 'rgba(255, 255, 0, 0.25)', // Yellow
  isWholeLine: true,
});
