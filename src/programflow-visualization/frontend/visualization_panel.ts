import * as vscode from 'vscode';
import { nextLineExecuteHighlightType } from '../constants';
import path = require('path');
import { HTMLGenerator } from './HTMLGenerator';
import { MessagePort } from 'worker_threads';
import { cacheTrace } from '../trace_cache';

const FRONTEND_RESOURCE_PATH = 'media/programflow-visualization';

export class VisualizationPanel {
  private _panel: vscode.WebviewPanel | undefined;
  private readonly _style: vscode.Uri;
  private readonly _script: vscode.Uri;
  private readonly _linkerlineBundle: vscode.Uri;
  private readonly _fileHash: string;
  private readonly _tracePort: MessagePort | null;
  private _backendTrace: PartialBackendTrace;
  private _trace: FrontendTrace;
  private _traceIndex: number;
  private _tracePortSelfClose: boolean;
  private _outChannel: vscode.OutputChannel;

  private constructor(
    context: vscode.ExtensionContext,
    outChannel: vscode.OutputChannel,
    filePath: string,
    fileHash: string,
    trace: BackendTrace,
    tracePort: MessagePort | null
  ) {
    this._outChannel = outChannel;
    this._fileHash = fileHash;
    this._tracePort = tracePort;
    this._backendTrace = { trace: trace, complete: trace.length > 0 };
    this._trace = [];
    const htmlGenerator = new HTMLGenerator();
    trace.forEach(traceElement => {
      this._trace.push(htmlGenerator.generateHTML(traceElement));
    });
    this._traceIndex = 0;
    const panel = vscode.window.createWebviewPanel(
      'programflow-visualization',
      `Visualization: ${path.basename(filePath)}`,
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        localResourceRoots: [
          vscode.Uri.file(path.join(context.extensionPath, FRONTEND_RESOURCE_PATH)),
          vscode.Uri.file(path.join(context.extensionPath, 'out')),
        ],
      }
    );

    // Get path to resource on disk
    const stylesFile = vscode.Uri.file(path.join(context.extensionPath, FRONTEND_RESOURCE_PATH, 'webview.css'));
    const scriptFile = vscode.Uri.file(path.join(context.extensionPath, FRONTEND_RESOURCE_PATH, 'webview.js'));
    const linkerlineFile = vscode.Uri.file(path.join(context.extensionPath, 'out/linkerline.bundle.js'));
    // And get the special URI to use with the webview
    this._style = panel.webview.asWebviewUri(stylesFile);
    this._script = panel.webview.asWebviewUri(scriptFile);
    this._linkerlineBundle = panel.webview.asWebviewUri(linkerlineFile);
    this._panel = panel;

    this._panel.onDidChangeViewState(async (e) => {
      if (e.webviewPanel.active) {
        await this.postMessagesToWebview('updateContent');
      }
    });

    this._tracePortSelfClose = false;
    this._panel.onDidDispose(
      async () => {
        this._tracePortSelfClose = true;
        this._tracePort?.close();
        this.updateLineHighlight(true);
        this._panel = undefined;
      },
      null,
      context.subscriptions
    );

    vscode.window.onDidChangeActiveTextEditor(_ => {
      if (this._panel?.active) {
        this.updateLineHighlight();
      }
    }, undefined, context.subscriptions);


    // Message Receivers
    this._panel.webview.onDidReceiveMessage(
      (msg) => {
        switch (msg.command) {
          case 'onClick':
            return this.onClick(msg.type);
          case 'onSlide':
            return this.onSlide(msg.sliderValue);
        }
      },
      undefined,
      context.subscriptions
    );

    this.updateLineHighlight();
    this.initWebviewContent();

    this._tracePort?.on('message', async (backendTraceElem) => {
      const firstElement = this._trace.length === 0;
      this._backendTrace.trace.push(backendTraceElem);
      this._trace.push((new HTMLGenerator()).generateHTML(backendTraceElem));
      await this.postMessagesToWebview('updateButtons', 'updateContent');
      if (firstElement) {
        this.updateLineHighlight();
      }
    });
    this._tracePort?.on('close', async () => {
      if (!this._tracePortSelfClose) {
        this._backendTrace.complete = true;
        await cacheTrace(context, this._fileHash, this._backendTrace.trace);
        await this.postMessagesToWebview('updateContent');
      }
    });
  }

  public dispose() {
    this._panel?.dispose();
  }

  public static async getVisualizationPanel(
    context: vscode.ExtensionContext,
    outChannel: vscode.OutputChannel,
    filePath: string,
    fileHash: string,
    trace: BackendTrace,
    tracePort: MessagePort | null
  ): Promise<VisualizationPanel | undefined> {
    return new VisualizationPanel(context, outChannel, filePath, fileHash, trace, tracePort);
  }

  // TODO: Look if Typescript is possible OR do better documentation in all files
  public initWebviewContent() {
    this._panel!.webview.html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <link rel="stylesheet" href="${this._style}">
          <script src="${this._linkerlineBundle}"></script>
          <script src="${this._script}"></script>
          <title>Code Visualization</title>
      </head>
      <body onload="onLoad()">
        <div class="column scrollable" id="viz">
          <div class="row">
            <div class="column title">
              Frames
              <div class="divider"></div>
            </div>
            <div class="row title">
              Objects
              <div class="divider"></div>
            </div>
          </div>
          <div class="row">
            <div class="column floating-left" id="frames">
            </div>
            <div class="column floating-right" id="objects">
            </div>
          </div>
        </div>
        <div class="row" id="bottom-area">
          <div class="column floating-left">
            <div class="slidecontainer">
              <input type="range" min="0" max="0" value="0" class="slider" id="traceSlider" oninput="onSlide(this.value)">
            </div>
            <div class="row margin-vertical">
              <p>Step&nbsp;</p>
              <p id="indexCounter">0</p>
              <p id="traceMax">/?</p>
            </div>
            <div class="row margin-vertical">
              <button class="margin-horizontal" id="firstButton" type="button" onclick="onClick('first')">&#9198</button>
              <button class="margin-horizontal" id="prevButton" type="button" onclick="onClick('prev')">&#9664</button>
              <button class="margin-horizontal" id="nextButton" type="button" onclick="onClick('next')">&#9654</button>
              <button class="margin-horizontal" id="lastButton" type="button" onclick="onClick('last')">&#9197</button>
            </div>
          </div>
          <div class="column floating-right">
            <pre class="scrollable" id="stdout-log"></pre>
          </dev>
        </div>
      </body>
      </html>
      `;
  }

  private async updateLineHighlight(remove: boolean = false) {
    if (this._trace.length === 0) {
      return;
    }
    let editor: vscode.TextEditor | undefined = vscode.window.visibleTextEditors.filter(
      editor => path.basename(editor.document.uri.path) === path.basename(this._trace[this._traceIndex][3]!)
    )[0];

    const openPath = vscode.Uri.parse(this._trace[this._traceIndex][3]!);
    if (!editor || editor.document.uri.path !== openPath.path) {
      await vscode.commands.executeCommand('workbench.action.focusFirstEditorGroup');
      const document = await vscode.workspace.openTextDocument(openPath);
      editor = await vscode.window.showTextDocument(document);
    }

    if (remove || editor.document.lineCount < this._trace[this._traceIndex][0]) {
      editor.setDecorations(nextLineExecuteHighlightType, []);
    } else {
      this.setNextLineHighlighting(editor);
    }
  }

  private setNextLineHighlighting(editor: vscode.TextEditor) {
    if (this._trace.length === 0) {
      return;
    }
    const nextLine = this._trace[this._traceIndex][0] - 1;

    if (nextLine > -1) {
      this.setEditorDecorations(editor, nextLineExecuteHighlightType, nextLine);
    }
  }

  private setEditorDecorations(editor: vscode.TextEditor, highlightType: vscode.TextEditorDecorationType, line: number) {
    editor.setDecorations(
      highlightType,
      this.createDecorationOptions(
        new vscode.Range(new vscode.Position(line, 0), new vscode.Position(line, 999))
      )
    );
  }

  private async onClick(type: string) {
    this.updateTraceIndex(type);
    await this.postMessagesToWebview('updateButtons', 'updateContent');
    this.updateLineHighlight();
  }

  private async onSlide(sliderValue: number) {
    this._traceIndex = Number(sliderValue);
    await this.postMessagesToWebview('updateButtons', 'updateContent');
    this.updateLineHighlight();
  }

  private updateTraceIndex(actionType: string) {
    switch (actionType) {
      case 'next': ++this._traceIndex;
        break;
      case 'prev': --this._traceIndex;
        break;
      case 'first': this._traceIndex = 0;
        break;
      case 'last': this._traceIndex = this._trace.length - 1;
        break;
      default:
        break;
    }
  }

  private async postMessagesToWebview(...args: string[]) {
    for (const message of args) {
      switch (message) {
        case 'updateButtons':
          const nextActive = this._traceIndex < this._trace.length - 1;
          const prevActive = this._traceIndex > 0;
          const firstActive = this._traceIndex > 0;
          const lastActive = this._traceIndex !== this._trace.length - 1;
          await this._panel!.webview.postMessage({
            command: 'updateButtons',
            next: nextActive,
            prev: prevActive,
            first: firstActive,
            last: lastActive,
          });
          break;
        case 'updateContent':
          await this._panel!.webview.postMessage({
            command: 'updateContent',
            traceComplete: this._backendTrace.complete,
            traceElem: this._trace[this._traceIndex],
            traceIndex: this._traceIndex,
            traceLen: this._trace.length,
          });
          break;
      }
    };
  }

  private createDecorationOptions(range: vscode.Range): vscode.DecorationOptions[] {
    return [
      {
        range: range,
      },
    ];
  }
}
