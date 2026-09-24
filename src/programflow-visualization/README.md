# Architecture Overview

## Components

### **Webview (web/)**
The self-contained UI component that the user interacts with:
- **webview.ts**: Manages trace navigation, rendering, and local state. Navigation (prev/next/first/last) is fully local; after updating the visualization, it emits a `highlight` message for line highlighting in the editor. Also owns the set of collapsed heap objects.
- **elk-view.ts**: Runs one step through the pipeline (build → measure → lay out → draw) and caches the result per step, LRU-bounded.
- **measure.ts**: Measures the real node markup offscreen and writes sizes and port positions back into the graph, so the layout matches what is drawn.
- **graph-renderer.ts**: Positions the nodes from the ELK result and draws the edges as SVG paths.
- **node-view.ts**: The single definition of a node's markup, shared by measurement and rendering.
- **pan-zoom.ts**: Wheel zoom, drag panning and zoom-to-fit, applied as one CSS transform.
- **vscode-host-adapter.ts**: Bridges between the webview's custom events and the VS Code webview API. Non-VS Code environments work unchanged (mock postMessage).
- **index.html**: DOM structure, control buttons, and output panes.
- **webview.css**: Layout and styling.
- **example-trace-content.js**: Optional sample trace for design/development mode.

### **Graph model (graph-model.ts, reachability.ts)**
Outside `web/` because it is pure logic with no DOM, which is what makes it unit-testable
(`src/test/unit`):
- **graph-model.ts**: Turns one backend trace element into the ELK graph — one node per frame and per visible heap object, one port per row that holds a reference, one edge per reference.
- **reachability.ts**: Decides which heap objects a step shows, given the set of collapsed ones.

### **Panel (frontend/)**
The VS Code extension-side host that owns the webview:
- **visualization_panel.ts**: Creates and manages the webview panel lifecycle. Receives `reset` and `append` messages from the trace backend, posts them to the webview. Handles `highlight` messages from the webview to update editor line highlighting.

## Message Flow

```mermaid
graph TB
    subgraph backend["Backend (Python)"]
        trace["Trace Generator"]
    end

    subgraph extension["Extension Host (VS Code)"]
        panel["VisualizationPanel"]
    end

    subgraph webview["Webview (Sandboxed)"]
        ui["webview.ts<br/>(UI + Navigation)"]
        elk["elk-view.ts<br/>(build, measure, layout, draw)"]
    end

    subgraph editor["Editor"]
        highlight["Line Highlighting"]
    end

    trace -->|trace array via IPC| panel
    panel -->|postMessage reset/append| adapter

    webview -->|custom event: programflow:highlight| adapter["vscode-host-adapter.ts"]
    adapter -->|custom event: programflow:reset, programflow:append| webview
    adapter -->|postMessage highlight| panel
    panel -->|updateLineHighlight| editor

    ui -->|current step + collapsed set| elk
    elk -->|positioned nodes and edges| ui
```

## Data Flow

1. **Initial Load / Panel Refocus**: Panel sends full trace array to webview via `reset` message.
2. **Streaming Trace**: Backend sends trace elements; panel forwards via `append` message.
3. **User Navigation**: User clicks buttons or moves slider → local navigation in webview updates `traceIndex` → renders visualization → emits `highlight` message.
4. **Editor Synchronization**: Panel receives `highlight` message → opens file and highlights line in editor.
5. **Standalone Mode**: webview works standalone (desktop or browser) via static trace injection in development, no postMessage needed.


## WebDev

You can develop the design of the visualization using an example trace in your browser. For concrete instructions check out base-repo README.
