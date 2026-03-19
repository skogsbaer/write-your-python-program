# Communication
In `setupUi()` in [webview.ts](web/webview.ts#L276) EventListeners for clicks are attatched to Buttons, which dispatch new CustomEvent `programflow:onClick` including info on specific Button.

## Web

* [webview.ts](web/webview.ts#L241) adds an EventListener for that specific CustomEvent, if the application is running in a web environment
* In this EventListener `traceIndex` is adjusted depending on which Button was pressed
* `renderCurrent()` re-renders the application using the new `traceIndex`

## VSCode
* [vscode-host-adapter.ts](web/vscode-host-adapter.ts) adds EventListeners which forward the CustomEvents to the extension via `vscode.postMessage(...)`
* In [visualization_panel.ts](frontend/visualization_panel.ts#L88) the function `onClick` is then called asynchronously
* Here, the `traceIndex` is updated, the view is re-rendered via asynchronous `reset`-event and the VSCode highlighting is updated according to `new traceIndex`
* The `reset`-event, is caught by the EventListener in [vscode-host-adapter.ts](web/vscode-host-adapter.ts#L7), which handles incoming MessageEvents from the VSCode extension and dispatches CustomEvents for [webview.ts](web/webview.ts)
* In [webview.ts](web/webview.ts#L203) the actual re-rendering happens
* TLDR; [vscode-host-adapter.ts](web/vscode-host-adapter.ts) works as an event-bridge for messages between the extension and the view and keeps VSCode-specific code out of the webview component
