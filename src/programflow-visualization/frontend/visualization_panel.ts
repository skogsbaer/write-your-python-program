import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { MessagePort } from "worker_threads";

import { nextLineExecuteHighlightType } from "../constants";
import { cacheTrace, getTrace, traceAlreadyExists } from "../trace_cache";

import type { BackendTrace, BackendTraceElem, PartialBackendTrace,  } from "../types";

let singletonPanel: VisualizationPanel | undefined;

export class VisualizationPanel {
  private _panel: vscode.WebviewPanel | undefined;

  private readonly _context: vscode.ExtensionContext;
  private readonly _outChannel: vscode.OutputChannel;

  private readonly _filePath: string;
  private readonly _fileHash: string;

  private readonly _tracePort: MessagePort | null;
  private _tracePortSelfClose = false;

  private _backendTrace: PartialBackendTrace = { trace: [], complete: false };
  private _traceIndex = 0;

  private static readonly webComponentDir = "out/programflow-visualization/web";

  private constructor(
    context: vscode.ExtensionContext,
    outChannel: vscode.OutputChannel,
    filePath: string,
    fileHash: string,
    initialTrace: BackendTrace,
    tracePort: MessagePort | null
  ) {
    this._context = context;
    this._outChannel = outChannel;
    this._filePath = filePath;
    this._fileHash = fileHash;
    this._tracePort = tracePort;

    this._backendTrace = { trace: initialTrace, complete: initialTrace.length > 0 };
    this._traceIndex = 0;

    this._panel = vscode.window.createWebviewPanel(
      "programflow-visualization",
      `Visualization: ${path.basename(filePath)}`,
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        localResourceRoots: [
          vscode.Uri.file(path.join(context.extensionPath, VisualizationPanel.webComponentDir)),
        ],
      }
    );

    // Load index.html from web/ and rewrite resource URIs.
    this._panel.webview.html = this.getWebviewHtml(this._panel.webview);

    this._panel.onDidChangeViewState(async (e) => {
      if (e.webviewPanel.active) {
        await this.postReset();
        this.updateLineHighlight();
      }
    });

    this._panel.onDidDispose(
      async () => {
        this._tracePortSelfClose = true;
        this._tracePort?.close();
        this.updateLineHighlight(true);
        this._panel = undefined;
      },
      undefined,
      context.subscriptions
    );

    vscode.window.onDidChangeActiveTextEditor(
      () => {
        if (this._panel?.active) {this.updateLineHighlight();}
      },
      undefined,
      context.subscriptions
    );

    this._panel.webview.onDidReceiveMessage(
      async (msg) => {
        switch (msg?.command) {
          case "onClick":
            await this.onClick(String(msg.type));
            break;
          case "onSlide":
            await this.onSlide(Number(msg.sliderValue));
            break;
          case "select":
            if (typeof msg.filePath === "string" && typeof msg.line === "number") {
              await this.updateLineHighlight(false, msg.filePath, msg.line);
            }
            break;
        }
      },
      undefined,
      context.subscriptions
    );

    void this.postReset();
    this.updateLineHighlight();

    // Live trace streaming
    this._tracePort?.on("message", async (backendTraceElem: BackendTraceElem) => {
      const firstElement = this._backendTrace.trace.length === 0;

      this._backendTrace.trace.push(backendTraceElem);

      await this.postAppend(backendTraceElem);

      if (firstElement) {
        await this.updateLineHighlight();
      }
    });

    this._tracePort?.on("close", async () => {
      if (!this._tracePortSelfClose) {
        this._backendTrace.complete = true;
        await cacheTrace(context, this._fileHash, this._backendTrace.trace);
        await this.postReset();
      }
    });
  }

  // Replaces frontend.ts: load cache + enforce singleton panel
  public static async start(
    context: vscode.ExtensionContext,
    outChannel: vscode.OutputChannel,
    filePath: string,
    fileHash: string,
    tracePort: MessagePort | null
  ): Promise<void> {
    let trace: BackendTrace = [];
    if (await traceAlreadyExists(context, fileHash)) {
      trace = await getTrace(context, fileHash);
    }

    singletonPanel?.dispose();
    singletonPanel = new VisualizationPanel(context, outChannel, filePath, fileHash, trace, tracePort);
  }

  public dispose() {
    this._panel?.dispose();
  }

  // HTML loader: reads web/index.html and replaces placeholders
  private getWebviewHtml(webview: vscode.Webview): string {
    const webDir = path.join(this._context.extensionPath, VisualizationPanel.webComponentDir);
    const indexPath = path.join(webDir, "index.html");
    let html = fs.readFileSync(indexPath, "utf8");

    const cssUri = webview.asWebviewUri(vscode.Uri.file(path.join(webDir, "webview.css")));
    const jsUri = webview.asWebviewUri(vscode.Uri.file(path.join(webDir, "webview.js")));
    const adapterUri = webview.asWebviewUri(vscode.Uri.file(path.join(webDir, "vscode-host-adapter.js")));
    const nonce = getNonce();

    html = replaceAll(html, "{{WEBVIEW_CSS}}", String(cssUri));
    html = replaceAll(html, "{{VSCODE_HOST_ADAPTER_JS}}", String(adapterUri));
    html = replaceAll(html, "{{WEBVIEW_JS}}", String(jsUri));
    html = replaceAll(html, "{{NONCE}}", nonce);
    html = replaceAll(html, "{{CSP_SOURCE}}", webview.cspSource);

    return html;
  }

  // Posting data into the web component
  private async postReset() {
    if (!this._panel) {return;}

    await this._panel.webview.postMessage({
      command: "reset",
      trace: this._backendTrace.trace,
      complete: this._backendTrace.complete,
      index: this._traceIndex,
    });
  }

  private async postAppend(elem: BackendTraceElem) {
    if (!this._panel) {return;}

    await this._panel.webview.postMessage({
      command: "append",
      elem,
      complete: this._backendTrace.complete,
      index: this._traceIndex,
      len: this._backendTrace.trace.length,
    });
  }

  // Compatibility navigation handlers
  private async onClick(type: string) {
    this.updateTraceIndex(type);
    await this.postReset();
    this.updateLineHighlight();
  }

  private async onSlide(sliderValue: number) {
    this._traceIndex = Number(sliderValue);
    await this.postReset();
    this.updateLineHighlight();
  }

  private updateTraceIndex(actionType: string) {
    const max = Math.max(0, this._backendTrace.trace.length - 1);
    switch (actionType) {
      case "next":
        this._traceIndex = Math.min(max, this._traceIndex + 1);
        break;
      case "prev":
        this._traceIndex = Math.max(0, this._traceIndex - 1);
        break;
      case "first":
        this._traceIndex = 0;
        break;
      case "last":
        this._traceIndex = max;
        break;
    }
  }

  // Editor highlighting
  private async updateLineHighlight(remove: boolean = false, overrideFile?: string, overrideLine?: number) {
    try {
      if (this._backendTrace.trace.length === 0) {
        return;
      }

      const current = this._backendTrace.trace[this._traceIndex];
      const traceFile = overrideFile ?? current.filePath;
      const traceLine = overrideLine ?? current.line;

      const openPath = vscode.Uri.file(traceFile);

      let editor: vscode.TextEditor | undefined = vscode.window.visibleTextEditors.find(
        (ed) => ed.document.uri.fsPath === openPath.fsPath
      );

      if (!editor && !remove) {
        await vscode.commands.executeCommand("workbench.action.focusFirstEditorGroup");
        const doc = await vscode.workspace.openTextDocument(openPath);
        editor = await vscode.window.showTextDocument(doc, { preserveFocus: false });
        await new Promise((r) => setTimeout(r, 50));
      }

      if (!editor) {return;}

      if (remove) {
        editor.setDecorations(nextLineExecuteHighlightType, []);
        return;
      }

      const lineNo = traceLine - 1;
      if (lineNo < 0 || lineNo >= editor.document.lineCount) {
        editor.setDecorations(nextLineExecuteHighlightType, []);
        return;
      }

      const range = new vscode.Range(new vscode.Position(lineNo, 0), new vscode.Position(lineNo, 999));
      editor.revealRange(range, vscode.TextEditorRevealType.InCenterIfOutsideViewport);
      editor.setDecorations(nextLineExecuteHighlightType, [{ range }]);
    } catch (e: any) {
      this._outChannel.appendLine(`updateLineHighlight failed: ${e?.message ?? String(e)}`);
    }
  }
}

function getNonce(): string {
  const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let text = "";
  for (let i = 0; i < 32; i++) {text += possible.charAt(Math.floor(Math.random() * possible.length));}
  return text;
}

function replaceAll(str: string, search: string, replacement: string): string {
  return str.split(search).join(replacement);
}
