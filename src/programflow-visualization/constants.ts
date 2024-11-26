import * as vscode from 'vscode';

export namespace Variables {
  export const CACHED_TRACES = 'programflow-visualization.cached-traces';
  export const TRACE_CACHE_DIR = 'programflow-visualization.trace-cache-dir';
}

export const nextLineExecuteHighlightType = vscode.window.createTextEditorDecorationType({
  borderWidth: '1px',
  borderStyle: 'solid',
  isWholeLine: true,
  borderColor: 'rgb(40, 40, 40)',
  backgroundColor: 'rgba(248, 248, 181, 0.75)',
  dark: {
    borderColor: 'rgb(215, 215, 215)',
    backgroundColor: 'rgba(75, 75, 24, 0.75)',
  }
});
