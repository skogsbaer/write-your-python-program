// Bridge messages between the VS Code host API and webview custom events
declare const acquireVsCodeApi: undefined | (() => { postMessage: (msg: any) => void });

type HighlightMsg = { command: "highlight"; filePath: string; line: number };

const vscode = typeof acquireVsCodeApi === "function"
  ? acquireVsCodeApi()
  : { postMessage: (_: any) => {} };

window.addEventListener("message", (event: MessageEvent) => {
  const msg = event.data;
  if (!msg?.command) {return;}

  switch (msg.command) {
    case "reset":
      window.dispatchEvent(new CustomEvent("programflow:reset", { detail: msg }));
      break;
    case "append":
      window.dispatchEvent(new CustomEvent("programflow:append", { detail: msg }));
      break;
  }
});

window.addEventListener("programflow:highlight", (e: Event) => {
  const ce = e as CustomEvent<{ filePath: string; line: number }>;
  const msg: HighlightMsg = { command: "highlight", ...ce.detail };
  vscode.postMessage(msg);
});
