import * as esbuild from "esbuild";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const _dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(_dirname, "..");

const webSrc = path.join(root, "src/programflow-visualization/web");
const webOut = path.join(root, "out/programflow-visualization/web");
const watch = process.argv.includes("--watch");

fs.mkdirSync(webOut, { recursive: true });

// Bundle webview.ts -> out/.../webview.js
const webviewCtx = await esbuild.context({
  entryPoints: [path.join(webSrc, "webview.ts")],
  bundle: true,
  platform: "browser",
  format: "iife",      // classic <script src="...">
  sourcemap: true,
  outfile: path.join(webOut, "webview.js"),
});

// Bundle vscode-host-adapter.ts -> out/.../vscode-host-adapter.js
const adapterCtx = await esbuild.context({
  entryPoints: [path.join(webSrc, "vscode-host-adapter.ts")],
  bundle: true,
  platform: "browser",
  format: "iife",
  sourcemap: true,
  outfile: path.join(webOut, "vscode-host-adapter.js"),
});

if (watch) {
  await webviewCtx.watch();
  await adapterCtx.watch();
  fs.watch(webSrc, (event, filename) => {
    if (!filename) {return;}

    if (filename.endsWith(".css") || filename.endsWith(".html") || filename.endsWith(".js")) {
      copyStatic();
    }
  });
} else {
  await webviewCtx.rebuild();
  await adapterCtx.rebuild();
  await webviewCtx.dispose();
  await adapterCtx.dispose();
  copyStatic();
}

function copyStatic() {
  // Generate browser-dev index.web.html by replacing placeholders
  let html = fs.readFileSync(path.join(webSrc, "index.html"), "utf8");
  const replaceAll = (s, from, to) => s.split(from).join(to);
  html = html.replace(
    /<meta http-equiv="Content-Security-Policy"[\s\S]*?\/>\s*/m,
    ""
  );
  html = replaceAll(html, "{{WEBVIEW_CSS}}", "./webview.css");
  html = replaceAll(html, "{{WEBVIEW_JS}}", "./webview.js");
  html = replaceAll(html, "{{VSCODE_HOST_ADAPTER_JS}}", "./vscode-host-adapter.js");

  html = replaceAll(html, 'nonce="{{NONCE}}"', "");
  html = replaceAll(html, "nonce=\"{{NONCE}}\"", "");

  html = replaceAll(html, "{{NONCE}}", "");
  html = replaceAll(html, "{{CSP_SOURCE}}", "");

  fs.writeFileSync(path.join(webOut, "index.web.html"), html, "utf8");

  fs.copyFileSync(path.join(webSrc, "index.html"), path.join(webOut, "index.html"));
  fs.copyFileSync(path.join(webSrc, "webview.css"), path.join(webOut, "webview.css"));
  fs.copyFileSync(path.join(webSrc, "example-trace-content.js"), path.join(webOut, "example-trace-content.js"));
}
copyStatic();

console.log(watch ? "watching web build..." : "web build done");