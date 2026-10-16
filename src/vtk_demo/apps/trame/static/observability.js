// Client side observability shared by the demos (served by vtk_demo/apps/trame/observability.py).
//
// Counts the frames the page actually presents, whatever renders them:
//
//   - local:  a WebGL or WebGPU canvas drew something (VTK.wasm or vtk.js)
//   - remote: a streamed image (blob: or data: URL) finished loading
//
// Draw calls only set a flag; a requestAnimationFrame loop turns the flags into
// at most one frame per display refresh. Measured frames are therefore capped by
// the display rate and their timestamps are accurate to about one refresh.
//
// From that it reports, to the server (trigger "obs_report") and on window.__obs:
//
//   - first_frame: ms from navigation start (or from a local/remote switch) until
//                  the full scene is on screen. For the local view that is the
//                  view's "scene loaded" event + GPU work done + next animation
//                  frame; for the remote view, the first streamed image.
//   - interaction: fps and frame time percentiles while the user drags or scrolls
//                  in the view, plus the delay before the first frame responds.
(function () {
  if (window.__obs) {
    return;
  }

  const now = () => performance.now();
  const round = (v) => (v === null ? null : Math.round(v * 10) / 10);

  // Draw hooks ---------------------------------------------------------------

  const flags = { local: null, remote: false }; // local: API of the latest draw
  let lastCtx = null;
  let lastApi = null;

  const GL_DRAWS = [
    "clear",
    "drawArrays",
    "drawElements",
    "drawArraysInstanced",
    "drawElementsInstanced",
    "drawRangeElements",
    "blitFramebuffer",
  ];
  function hookGL(proto, api) {
    if (!proto) {
      return;
    }
    for (const name of GL_DRAWS) {
      const fn = proto[name];
      if (!fn) {
        continue;
      }
      proto[name] = function () {
        flags.local = api;
        lastCtx = this;
        lastApi = api;
        return fn.apply(this, arguments);
      };
    }
  }
  hookGL(window.WebGLRenderingContext?.prototype, "webgl");
  hookGL(window.WebGL2RenderingContext?.prototype, "webgl2");

  if (window.GPUCanvasContext) {
    const fn = GPUCanvasContext.prototype.getCurrentTexture;
    GPUCanvasContext.prototype.getCurrentTexture = function () {
      flags.local = "webgpu";
      lastCtx = this;
      lastApi = "webgpu";
      return fn.call(this);
    };
  }

  // Images do not bubble "load", so listen in the capture phase
  document.addEventListener(
    "load",
    (e) => {
      const el = e.target;
      if (el.tagName === "IMG" && /^(blob|data):/.test(el.src)) {
        flags.remote = true;
      }
    },
    true
  );

  // Wait until the GPU is done with what the local view submitted so far
  function gpuDone() {
    if (lastApi === "webgpu") {
      const device = lastCtx.getConfiguration?.()?.device;
      return device ? device.queue.onSubmittedWorkDone() : Promise.resolve();
    }
    if (lastApi === "webgl2") {
      const gl = lastCtx;
      const pbo = gl.getParameter(gl.PIXEL_PACK_BUFFER_BINDING);
      gl.bindBuffer(gl.PIXEL_PACK_BUFFER, null);
      gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));
      gl.bindBuffer(gl.PIXEL_PACK_BUFFER, pbo);
    } else if (lastApi === "webgl") {
      lastCtx.readPixels(0, 0, 1, 1, lastCtx.RGBA, lastCtx.UNSIGNED_BYTE, new Uint8Array(4));
    }
    return Promise.resolve();
  }

  const nextFrame = () => new Promise(requestAnimationFrame);

  function percentile(sorted, q) {
    return sorted.length ? sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))] : null;
  }

  // Measurements -------------------------------------------------------------

  const obs = {
    mode: null, // 'local' or 'remote'
    api: { local: null, remote: "image" }, // what actually presented the frames
    activation: null, // { mode, t0, initial, done, waiting }
    interaction: null,
    recent: { local: [], remote: [] }, // frame times of the last second, for the HUD
    firstFrame: { local: null, remote: null },
    lastFps: { local: null, remote: null },
    events: [],

    report(event) {
      this.events.push(event);
      console.info("[obs]", JSON.stringify(event));
      window.trame?.trigger?.("obs_report", [event])?.catch?.(() => {});
    },

    // Called by the app when the rendering mode is set or toggled
    setMode(mode) {
      if (mode === this.mode) {
        return;
      }
      this.endInteraction();
      const initial = this.mode === null;
      this.mode = mode;
      this.activation = { mode, t0: initial ? 0 : now(), initial, done: false, waiting: false };
      // A local view that stays mounted does not reload its scene when switched
      // back to: its next frame is the full scene
      if (!initial && mode === "local" && this.localPersistent) {
        this.activation.waitFrame = true;
      }
    },

    // Called by the local view once its whole scene is loaded
    async sceneReady(mode = "local") {
      const a = this.activation;
      if (!a || a.mode !== mode || a.done || a.waiting) {
        return;
      }
      a.waiting = true;
      if (!lastApi) {
        a.waitFrame = true; // nothing drawn yet: the next presented frame completes it
        return;
      }
      await gpuDone();
      await nextFrame();
      this.firstFrameDone(mode, now());
    },

    // trame-vtk's VtkRemoteLocalView does not forward "afterSceneLoaded" from its
    // vtk.js view, so catch it on the view helper it provides
    hookVtkjs(ref) {
      this.localPersistent = true;
      const timer = setInterval(() => {
        const view = window.trame?.refs?.[ref]?.localViewRef?.$?.provides?.view;
        if (!view?.vueCtx) {
          return;
        }
        clearInterval(timer);
        const emit = view.vueCtx.emit;
        view.vueCtx.emit = (name, ...args) => {
          if (name === "afterSceneLoaded") {
            this.sceneReady("local");
          }
          return emit(name, ...args);
        };
        if (view.renderer?.getActors().length) {
          this.sceneReady("local"); // loaded before the hook was in place
        }
      }, 20);
    },

    firstFrameDone(mode, t) {
      const a = this.activation;
      if (!a || a.mode !== mode || a.done) {
        return;
      }
      a.done = true;
      const ms = t - a.t0;
      if (a.initial) {
        this.firstFrame[mode] = ms;
      }
      this.report({
        type: "first_frame",
        mode,
        api: this.api[mode],
        ms: round(ms),
        since: a.initial ? "navigation" : "switch",
      });
    },

    onFrame(kind, t) {
      const recent = this.recent[kind];
      recent.push(t);
      while (recent.length && t - recent[0] > 1000) {
        recent.shift();
      }
      if (kind !== this.mode) {
        return;
      }
      const a = this.activation;
      if (a && !a.done && (kind === "remote" || a.waitFrame)) {
        this.firstFrameDone(kind, t);
      }
      if (this.interaction) {
        this.interaction.frames.push(t);
      }
    },

    startInteraction(input) {
      clearTimeout(this.endTimer);
      if (!this.interaction && this.mode) {
        this.interaction = { mode: this.mode, input, start: now(), frames: [] };
      }
    },

    // Keep collecting for a little while: remote frames lag behind the input
    scheduleEnd(delay) {
      clearTimeout(this.endTimer);
      this.endTimer = setTimeout(() => this.endInteraction(), delay);
    },

    endInteraction() {
      clearTimeout(this.endTimer);
      const it = this.interaction;
      this.interaction = null;
      if (!it || !it.frames.length) {
        return;
      }
      const f = it.frames;
      const deltas = f.slice(1).map((t, i) => t - f[i]).sort((a, b) => a - b);
      const span = f[f.length - 1] - f[0];
      const fps = deltas.length && span > 0 ? (deltas.length * 1000) / span : null;
      this.lastFps[it.mode] = fps;
      this.report({
        type: "interaction",
        mode: it.mode,
        api: this.api[it.mode],
        input: it.input,
        frames: f.length,
        duration_ms: round(f[f.length - 1] - it.start),
        first_response_ms: round(f[0] - it.start),
        fps: round(fps),
        frame_ms_p50: round(percentile(deltas, 0.5)),
        frame_ms_p95: round(percentile(deltas, 0.95)),
        frame_ms_max: round(deltas.length ? deltas[deltas.length - 1] : null),
      });
    },

    summary() {
      return {
        mode: this.mode,
        api: { ...this.api },
        firstFrame: { ...this.firstFrame },
        lastFps: { ...this.lastFps },
        events: [...this.events],
      };
    },
  };

  function tick() {
    const t = now();
    if (flags.local) {
      obs.api.local = flags.local;
      flags.local = null;
      obs.onFrame("local", t);
    }
    if (flags.remote) {
      flags.remote = false;
      obs.onFrame("remote", t);
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // Interactions: drag or scroll in the view, not on the UI around it ----------

  const UI = "button, input, .v-btn, .v-switch, .v-toolbar, .v-card, .v-chip, .v-list";
  const inView = (e) => !(e.target instanceof Element && e.target.closest(UI));
  document.addEventListener(
    "pointerdown",
    (e) => inView(e) && obs.startInteraction("drag"),
    true
  );
  document.addEventListener(
    "pointerup",
    () => obs.interaction?.input === "drag" && obs.scheduleEnd(250),
    true
  );
  document.addEventListener(
    "pointercancel",
    () => obs.interaction && obs.scheduleEnd(250),
    true
  );
  document.addEventListener(
    "wheel",
    (e) => {
      if (inView(e) && obs.interaction?.input !== "drag") {
        obs.startInteraction("wheel");
        obs.scheduleEnd(300);
      }
    },
    { capture: true, passive: true }
  );

  // HUD ----------------------------------------------------------------------

  const hud = document.createElement("div");
  hud.style.cssText =
    "position:fixed;left:8px;z-index:10000;pointer-events:none;" +
    "font:12px/1.4 ui-monospace,monospace;color:#fff;background:rgba(0,0,0,.6);" +
    "padding:4px 8px;border-radius:4px;white-space:pre;";
  const fmt = (v, unit) => (v === null ? "–" : `${Math.round(v)}${unit}`);
  setInterval(() => {
    const show = window.trame?.state?.get?.("obs_hud") !== false && obs.mode;
    if (!show) {
      hud.remove();
      return;
    }
    if (!hud.isConnected) {
      document.body.appendChild(hud);
    }
    hud.style.bottom = `${window.trame?.state?.get?.("obs_hud_bottom") ?? 8}px`;
    const m = obs.mode;
    const recent = obs.recent[m].filter((t) => now() - t <= 1000);
    hud.textContent =
      `${m} · ${obs.api[m] || "?"} · first frame ${fmt(obs.firstFrame[m], " ms")}\n` +
      `${recent.length} fps now · last interaction ${fmt(obs.lastFps[m], " fps")}`;
  }, 250);

  window.__obs = obs;
})();
