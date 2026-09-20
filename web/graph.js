/* Named-graph force map. No external graph library. */
(function (global) {
  const FILL = {
    person: "#3aa39a",
    department: "#6ecb8b",
    book: "#d4923a",
    course: "#8b7cf0",
    entity: "#8b98a8",
  };
  const EDGE = {
    hr: "#3aa39a",
    library: "#d4923a",
    registrar: "#8b7cf0",
  };
  const RADIUS = {
    person: 14,
    department: 11,
    book: 10,
    course: 10,
    entity: 8,
  };

  function createMap(canvas, handlers) {
    const ctx = canvas.getContext("2d");
    const state = {
      nodes: [],
      edges: [],
      transform: { x: 0, y: 0, k: 1 },
      drag: null,
      pan: null,
      selected: null,
      running: true,
      w: 0,
      h: 0,
    };

    function resize() {
      const parent = canvas.parentElement;
      const w = Math.max(parent.clientWidth, 100);
      const h = Math.max(parent.clientHeight, 240);
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      state.w = w;
      state.h = h;
    }

    function setData(payload) {
      const cx = state.w / 2 || 240;
      const cy = state.h / 2 || 200;
      const nodes = (payload.nodes || []).map((n) => ({
        ...n,
        x: cx,
        y: cy,
        vx: 0,
        vy: 0,
        r: RADIUS[n.kind] || 8,
      }));
      const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
      const edges = (payload.edges || [])
        .map((e) => ({ ...e, a: byId[e.source], b: byId[e.target] }))
        .filter((e) => e.a && e.b);
      const people = nodes.filter((n) => n.kind === "person");
      const others = nodes.filter((n) => n.kind !== "person");
      people.forEach((n, i) => {
        const angle = (2 * Math.PI * i) / Math.max(people.length, 1) - Math.PI / 2;
        n.x = cx + Math.cos(angle) * 90;
        n.y = cy + Math.sin(angle) * 90;
      });
      others.forEach((n, i) => {
        const angle = (2 * Math.PI * i) / Math.max(others.length, 1);
        n.x = cx + Math.cos(angle) * 170;
        n.y = cy + Math.sin(angle) * 170;
      });
      state.nodes = nodes;
      state.edges = edges;
      state.selected = null;
      state.transform = { x: 0, y: 0, k: 1 };
      for (let i = 0; i < 160; i++) tick();
      fit();
    }

    function fit() {
      const nodes = state.nodes;
      if (!nodes.length || !state.w) return;
      let minx = Infinity;
      let miny = Infinity;
      let maxx = -Infinity;
      let maxy = -Infinity;
      for (const n of nodes) {
        minx = Math.min(minx, n.x - n.r - 28);
        miny = Math.min(miny, n.y - n.r - 20);
        maxx = Math.max(maxx, n.x + n.r + 28);
        maxy = Math.max(maxy, n.y + n.r + 24);
      }
      const bw = Math.max(maxx - minx, 40);
      const bh = Math.max(maxy - miny, 40);
      const k = Math.min((state.w - 48) / bw, (state.h - 48) / bh, 1.8);
      state.transform.k = k;
      state.transform.x = state.w / 2 - k * ((minx + maxx) / 2);
      state.transform.y = state.h / 2 - k * ((miny + maxy) / 2);
    }

    function toWorld(sx, sy) {
      const t = state.transform;
      return { x: (sx - t.x) / t.k, y: (sy - t.y) / t.k };
    }

    function hit(sx, sy) {
      const p = toWorld(sx, sy);
      for (let i = state.nodes.length - 1; i >= 0; i--) {
        const n = state.nodes[i];
        const dx = p.x - n.x;
        const dy = p.y - n.y;
        if (dx * dx + dy * dy <= (n.r + 5) * (n.r + 5)) return n;
      }
      return null;
    }

    function tick() {
      const nodes = state.nodes;
      const n = nodes.length;
      if (!n) return;
      const cx = state.w / 2;
      const cy = state.h / 2;
      for (let i = 0; i < n; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < n; j++) {
          const b = nodes[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let d2 = dx * dx + dy * dy || 0.01;
          const min = a.r + b.r + 26;
          const f = Math.min(220 / d2, 1.8);
          dx *= f;
          dy *= f;
          if (d2 < min * min) {
            const d = Math.sqrt(d2);
            const push = (min - d) * 0.14;
            dx += ((a.x - b.x) / d) * push;
            dy += ((a.y - b.y) / d) * push;
          }
          if (a.fx == null) {
            a.vx += dx;
            a.vy += dy;
          }
          if (b.fx == null) {
            b.vx -= dx;
            b.vy -= dy;
          }
        }
      }
      for (const e of state.edges) {
        const dx = e.b.x - e.a.x;
        const dy = e.b.y - e.a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
        const rest = e.a.kind === "person" || e.b.kind === "person" ? 108 : 86;
        const k = (dist - rest) * 0.018;
        const fx = (dx / dist) * k;
        const fy = (dy / dist) * k;
        if (e.a.fx == null) {
          e.a.vx += fx;
          e.a.vy += fy;
        }
        if (e.b.fx == null) {
          e.b.vx -= fx;
          e.b.vy -= fy;
        }
      }
      for (const node of nodes) {
        if (node.fx != null) {
          node.x = node.fx;
          node.y = node.fy;
          node.vx = 0;
          node.vy = 0;
          continue;
        }
        node.vx += (cx - node.x) * 0.018;
        node.vy += (cy - node.y) * 0.018;
        node.vx *= 0.7;
        node.vy *= 0.7;
        node.x += node.vx;
        node.y += node.vy;
      }
    }

    function draw() {
      const { w, h, transform: t } = state;
      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.translate(t.x, t.y);
      ctx.scale(t.k, t.k);
      ctx.lineWidth = 1.4 / t.k;
      for (const e of state.edges) {
        ctx.beginPath();
        ctx.strokeStyle = EDGE[e.graph] || "rgba(232,238,244,0.28)";
        ctx.moveTo(e.a.x, e.a.y);
        ctx.lineTo(e.b.x, e.b.y);
        ctx.stroke();
      }
      for (const node of state.nodes) {
        ctx.beginPath();
        ctx.fillStyle = FILL[node.kind] || "#8b98a8";
        ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
        ctx.fill();
        if ((node.graphs || []).length > 1) {
          ctx.beginPath();
          ctx.strokeStyle = "#e8eef4";
          ctx.lineWidth = 2 / t.k;
          ctx.arc(node.x, node.y, node.r + 3, 0, Math.PI * 2);
          ctx.stroke();
          ctx.lineWidth = 1.4 / t.k;
        }
        if (state.selected && state.selected.id === node.id) {
          ctx.beginPath();
          ctx.strokeStyle = "#e8eef4";
          ctx.arc(node.x, node.y, node.r + 6, 0, Math.PI * 2);
          ctx.stroke();
        }
        ctx.fillStyle = "#e8eef4";
        ctx.font = `${11 / t.k}px "IBM Plex Mono", ui-monospace, monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        const label = (node.label || "").length > 26 ? node.label.slice(0, 24) + "…" : node.label;
        ctx.fillText(label, node.x, node.y + node.r + 3);
      }
      ctx.restore();
    }

    function loop() {
      if (state.running) tick();
      draw();
      requestAnimationFrame(loop);
    }

    function localPoint(ev) {
      const box = canvas.getBoundingClientRect();
      return { x: ev.clientX - box.left, y: ev.clientY - box.top };
    }

    canvas.addEventListener("pointerdown", (ev) => {
      canvas.setPointerCapture(ev.pointerId);
      const p = localPoint(ev);
      const node = hit(p.x, p.y);
      if (node) {
        state.drag = { node };
        const world = toWorld(p.x, p.y);
        node.fx = world.x;
        node.fy = world.y;
      } else {
        state.pan = { x: p.x, y: p.y, tx: state.transform.x, ty: state.transform.y };
      }
    });
    canvas.addEventListener("pointermove", (ev) => {
      const p = localPoint(ev);
      if (state.drag) {
        const world = toWorld(p.x, p.y);
        state.drag.node.fx = world.x;
        state.drag.node.fy = world.y;
        return;
      }
      if (state.pan) {
        state.transform.x = state.pan.tx + (p.x - state.pan.x);
        state.transform.y = state.pan.ty + (p.y - state.pan.y);
        return;
      }
      canvas.style.cursor = hit(p.x, p.y) ? "pointer" : "grab";
    });
    canvas.addEventListener("pointerup", (ev) => {
      const p = localPoint(ev);
      if (state.drag) {
        const node = state.drag.node;
        node.fx = null;
        node.fy = null;
        state.selected = node;
        if (handlers.onSelect) handlers.onSelect(node);
        state.drag = null;
      }
      state.pan = null;
      canvas.releasePointerCapture(ev.pointerId);
    });
    canvas.addEventListener(
      "wheel",
      (ev) => {
        ev.preventDefault();
        const p = localPoint(ev);
        const t = state.transform;
        const factor = ev.deltaY < 0 ? 1.08 : 0.92;
        const next = Math.min(3.5, Math.max(0.35, t.k * factor));
        const wx = (p.x - t.x) / t.k;
        const wy = (p.y - t.y) / t.k;
        t.k = next;
        t.x = p.x - wx * t.k;
        t.y = p.y - wy * t.k;
      },
      { passive: false }
    );

    const ro = new ResizeObserver(() => resize());
    ro.observe(canvas.parentElement);
    resize();
    loop();
    return { setData, resize };
  }

  global.createNamedGraphMap = createMap;
})(window);
