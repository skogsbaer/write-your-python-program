// Pan and zoom for the visualization canvas. See elk-task/elk-plan.md 6.5.
//
// Everything ELK produced lives in one absolutely positioned canvas, so a single
// `transform` on that element moves the node divs and the SVG edge overlay together --
// no re-layout, no coordinate recomputation, and GPU-composited.

/** Discrete steps: fractional scales make text look soft. */
const ZOOM_STEPS = [0.25, 0.33, 0.5, 0.67, 0.75, 0.9, 1, 1.1, 1.25, 1.5, 1.75, 2, 2.5, 3];

/** Pointer movement beyond this counts as a pan, and the trailing click is swallowed. */
const DRAG_THRESHOLD_PX = 3;

const FIT_PADDING_PX = 16;

export type PanZoom = {
  /** Scale the content to fit the viewport and centre it, and re-enable auto-fitting. */
  fit(width: number, height: number): void;
  /**
   * Same, but does nothing once the user has panned or zoomed. Until then every render
   * re-frames the graph, which matters because a trace grows from one node to dozens.
   */
  autoFit(width: number, height: number): void;
  /** One step up the zoom ladder, anchored on the middle of the viewport. */
  zoomIn(): void;
  /** One step down the zoom ladder, anchored on the middle of the viewport. */
  zoomOut(): void;
};

/** Events on the floating toolbar are UI, not canvas gestures. */
function isUi(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest("[data-elk-ui]") !== null;
}

function nearestStep(scale: number): number {
  return ZOOM_STEPS.reduce((best, step) =>
    Math.abs(step - scale) < Math.abs(best - scale) ? step : best
  );
}

function stepFrom(scale: number, direction: 1 | -1): number {
  const index = ZOOM_STEPS.indexOf(nearestStep(scale));
  return ZOOM_STEPS[Math.min(ZOOM_STEPS.length - 1, Math.max(0, index + direction))];
}

export function attachPanZoom(viewport: HTMLElement, canvas: HTMLElement): PanZoom {
  let scale = 1;
  let translateX = 0;
  let translateY = 0;
  /** Set once the user takes the view over, which switches auto-fitting off. */
  let touched = false;
  /** Size of the last graph drawn, so a resize can re-fit without being told again. */
  let lastWidth = 0;
  let lastHeight = 0;

  const apply = () => {
    canvas.style.transformOrigin = "0 0";
    canvas.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
  };

  /**
   * One step along the ladder, keeping the graph point at (anchorX, anchorY) -- both
   * relative to the viewport -- exactly where it is.
   */
  const zoomStep = (direction: 1 | -1, anchorX: number, anchorY: number) => {
    const next = stepFrom(scale, direction);
    if (next === scale) {
      return;
    }
    touched = true;
    translateX = anchorX - ((anchorX - translateX) / scale) * next;
    translateY = anchorY - ((anchorY - translateY) / scale) * next;
    scale = next;
    apply();
  };

  const zoomFromCentre = (direction: 1 | -1) => {
    const box = viewport.getBoundingClientRect();
    zoomStep(direction, box.width / 2, box.height / 2);
  };

  viewport.addEventListener(
    "wheel",
    (event: WheelEvent) => {
      if (isUi(event.target)) {
        return;
      }
      event.preventDefault();
      const box = viewport.getBoundingClientRect();
      zoomStep(
        event.deltaY < 0 ? 1 : -1,
        event.clientX - box.left,
        event.clientY - box.top
      );
    },
    { passive: false }
  );

  let pointerId: number | null = null;
  let startX = 0;
  let startY = 0;
  let dragged = false;

  const onMove = (event: PointerEvent) => {
    if (pointerId !== event.pointerId) {
      return;
    }
    const nextX = event.clientX - startX;
    const nextY = event.clientY - startY;
    if (
      !dragged &&
      Math.abs(nextX - translateX) < DRAG_THRESHOLD_PX &&
      Math.abs(nextY - translateY) < DRAG_THRESHOLD_PX
    ) {
      return;
    }
    dragged = true;
    touched = true;
    viewport.classList.add("elk-panning");
    translateX = nextX;
    translateY = nextY;
    apply();
  };

  const onUp = (event: PointerEvent) => {
    if (pointerId !== event.pointerId) {
      return;
    }
    pointerId = null;
    viewport.classList.remove("elk-panning");
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
    window.removeEventListener("pointercancel", onUp);
  };

  viewport.addEventListener("pointerdown", (event: PointerEvent) => {
    if (event.button !== 0 || isUi(event.target)) {
      return;
    }
    pointerId = event.pointerId;
    startX = event.clientX - translateX;
    startY = event.clientY - translateY;
    dragged = false;
    // Listening on window, not the viewport, keeps a drag alive when the cursor
    // leaves the canvas -- same effect as pointer capture, without the capture API.
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
  });

  // A pan that ends on a node header must not also toggle it.
  viewport.addEventListener(
    "click",
    (event: MouseEvent) => {
      if (dragged) {
        event.stopPropagation();
        event.preventDefault();
        dragged = false;
      }
    },
    true
  );

  const fit = (width: number, height: number) => {
    const box = viewport.getBoundingClientRect();
    if (width <= 0 || height <= 0 || box.width <= 0 || box.height <= 0) {
      return;
    }
    lastWidth = width;
    lastHeight = height;
    const raw = Math.min(
      (box.width - FIT_PADDING_PX) / width,
      (box.height - FIT_PADDING_PX) / height
    );
    // Never zoom *in* to fit: a two-node graph blown up to full width is unreadable.
    scale = raw >= 1 ? 1 : nearestStep(raw);
    translateX = Math.max(0, (box.width - width * scale) / 2);
    translateY = Math.max(0, (box.height - height * scale) / 2);
    apply();
  };

  // Resizing the panel changes what "fits", so re-frame while auto-fitting is still on.
  new ResizeObserver(() => {
    if (!touched) {
      fit(lastWidth, lastHeight);
    }
  }).observe(viewport);

  return {
    fit(width, height) {
      // An explicit Fit is also a request to go back to being framed automatically.
      touched = false;
      fit(width, height);
    },
    autoFit(width, height) {
      if (!touched) {
        fit(width, height);
      }
    },
    zoomIn() {
      zoomFromCentre(1);
    },
    zoomOut() {
      zoomFromCentre(-1);
    },
  };
}
