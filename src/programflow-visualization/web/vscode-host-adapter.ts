declare const acquireVsCodeApi: undefined | (() => { postMessage: (msg: any) => void });

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

    case "updateButtons":
      window.dispatchEvent(new CustomEvent("programflow:updateButtons", { detail: msg }));
      break;
    case "updateContent":
      window.dispatchEvent(new CustomEvent("programflow:updateContent", { detail: msg }));
      break;
  }
});

window.addEventListener("programflow:select", (e: Event) => {
  const ce = e as CustomEvent<any>;
  vscode.postMessage({ command: "select", ...ce.detail });
});

window.addEventListener("programflow:onClick", (e: Event) => {
  const ce = e as CustomEvent<{ type: string }>;
  vscode.postMessage({ command: "onClick", type: ce.detail.type });
});

window.addEventListener("programflow:onSlide", (e: Event) => {
  const ce = e as CustomEvent<{ value: string }>;
  vscode.postMessage({ command: "onSlide", sliderValue: ce.detail.value });
});