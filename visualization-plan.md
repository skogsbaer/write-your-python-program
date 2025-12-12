# Current approach

- hardcoded HTML in src/programflow-visualization/frontend/visualization_panel.ts
- links to CSS in ./media/programflow-visualization/webview.css
- links to JS in ./media/programflow-visualization/linkerline.js (external lib for arrows) and
  ./media/programflow-visualization/webview.js
- webview.js listens to updateButtons and updateContents events. These events are generated
  whenever a new trace element arrives and if the user klicks a button (yes, the buttons
  in the HTML are sent back to the vscode)

# Goal

- HTML page should be self-contained with links
  - CSS files for styling
  - JS files with logic (generated from typescript)
  - a link to a JS file with the frontend trace content
- The HTML page and the linked stuff is a self-contained component with no dependencies back to vscode
- vscode plugin should not generate HTML code anymore: src/programflow-visualization/frontend/HTMLGenerator.ts
  belongs to the new component
- OPTIONAL (if partial traces are necessary for performance): the components reacts
  to an event to append new trace elements or to reset the whole trace
- The frontend part in vscode is able to store the frontend trace so that a designer can just take
  the visualization with a static trace and do a good design

## Benefits

- easier to understand, deps just one-way
- HTML can be tuned for visual appearence independently from vscode
  - we just need a dump of the JS file with the trace content
