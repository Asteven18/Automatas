// Renderizado y manipulación visual del canvas de autómatas


class AutomataRenderer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.viewportContent = this.container.querySelector(".viewport-content");
    
    this.scale = 1.0;
    this.panX = 30;
    this.panY = 40;
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;
    
    this.currentSvgElement = null;
    this.activeNodes = new Set();
    this.automataData = null;

    this.vbX = 0;
    this.vbY = 0;
    this.vbWidth = 800;
    this.vbHeight = 400;
    this.pendingFit = false;

    this._initEvents();
  }

  _initEvents() {
    // Paneo con el ratón
    this.container.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return; // solo botón izquierdo
      this.isDragging = true;
      this.startX = e.clientX - this.panX;
      this.startY = e.clientY - this.panY;
      this.container.style.cursor = "grabbing";
    });

    window.addEventListener("mousemove", (e) => {
      if (!this.isDragging) return;
      this.panX = e.clientX - this.startX;
      this.panY = e.clientY - this.startY;
      this._applyTransform();
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
      this.container.style.cursor = "grab";
    });

    // Zoom con rueda de ratón
    this.container.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
      this.zoom(zoomFactor, e.clientX, e.clientY);
    }, { passive: false });
  }

  zoom(factor, clientX = null, clientY = null) {
    const oldScale = this.scale;
    const newScale = Math.min(Math.max(this.scale * factor, 0.2), 3.5);

    if (clientX !== null && clientY !== null) {
      const rect = this.container.getBoundingClientRect();
      const mouseX = clientX - rect.left;
      const mouseY = clientY - rect.top;

      this.panX = mouseX - (mouseX - this.panX) * (newScale / oldScale);
      this.panY = mouseY - (mouseY - this.panY) * (newScale / oldScale);
    }

    this.scale = newScale;
    this._applyTransform();
  }

  resetView() {
    this.scale = 1.0;
    this.panX = 30;
    this.panY = 40;
    this._applyTransform();
  }

  fitToView() {
    if (!this.currentSvgElement || !this.vbWidth || !this.vbHeight) return;

    const contW = this.container.clientWidth;
    const contH = this.container.clientHeight;

    // Si el contenedor está oculto en una pestaña inactiva, postergar el fit
    if (!contW || !contH || contW < 50 || contH < 50) {
      this.pendingFit = true;
      return;
    }

    this.pendingFit = false;
    const pad = 36;
    const scaleX = (contW - pad * 2) / this.vbWidth;
    const scaleY = (contH - pad * 2) / this.vbHeight;

    this.scale = Math.min(Math.max(Math.min(scaleX, scaleY), 0.2), 1.8);

    // Centrar con respecto al origen del viewBox
    this.panX = Math.round((contW - this.vbWidth * this.scale) / 2 - (this.vbX || 0) * this.scale);
    this.panY = Math.round((contH - this.vbHeight * this.scale) / 2 - (this.vbY || 0) * this.scale);

    this._applyTransform();
  }

  _applyTransform() {
    this.viewportContent.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.scale})`;
  }

  /**
   * Renderiza el autómata. Si viene con SVG de Graphviz lo inyecta y escala,
   * de lo contrario genera el SVG con layout jerárquico cliente.
   */
  render(automataData, svgString = null) {
    this.automataData = automataData;
    this.activeNodes.clear();

    if (svgString && svgString.includes("<svg")) {
      this._renderGraphvizSvg(svgString);
    } else {
      this._renderClientSvg(automataData);
    }
  }

  _renderGraphvizSvg(svgString) {
    this.viewportContent.innerHTML = svgString;
    const svg = this.viewportContent.querySelector("svg");
    if (!svg) return;

    this.currentSvgElement = svg;

    // Extraer coordenadas exactas del viewBox
    let vbX = 0, vbY = 0, vbWidth = 900, vbHeight = 400;
    const vbStr = svg.getAttribute("viewBox");
    if (vbStr) {
      const parts = vbStr.trim().split(/[\s,]+/).map(Number);
      if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
        [vbX, vbY, vbWidth, vbHeight] = parts;
      }
    }
    this.vbX = vbX;
    this.vbY = vbY;
    this.vbWidth = vbWidth;
    this.vbHeight = vbHeight;

    // Fijar dimensiones reales para que no colapse a 0px en CSS
    svg.setAttribute("width", vbWidth);
    svg.setAttribute("height", vbHeight);
    svg.style.width = vbWidth + "px";
    svg.style.height = vbHeight + "px";
    svg.style.display = "block";
    svg.style.overflow = "visible";

    this.viewportContent.style.width = vbWidth + "px";
    this.viewportContent.style.height = vbHeight + "px";

    // Asociar eventos y data-state-id a cada nodo de Graphviz
    const nodes = svg.querySelectorAll("g.node");
    nodes.forEach(node => {
      const title = node.querySelector("title");
      if (!title) return;
      const textId = title.textContent.trim();
      const numId = parseInt(textId.replace(/\D/g, ""), 10);
      if (isNaN(numId)) return;

      node.setAttribute("data-state-id", numId);
      node.style.cursor = "pointer";

      node.addEventListener("mouseenter", () => {
        if (!this.activeNodes.has(numId)) {
          node.style.filter = "drop-shadow(0 0 10px rgba(56, 189, 248, 0.9))";
        }
      });
      node.addEventListener("mouseleave", () => {
        if (!this.activeNodes.has(numId)) {
          node.style.filter = "none";
        }
      });
      node.addEventListener("click", (e) => {
        e.stopPropagation();
        if (window.onNodeClicked) {
          window.onNodeClicked(numId);
        }
      });
    });

    this.fitToView();
  }

  _renderClientSvg(automata) {
    const layout = this._computeHierarchicalLayout(automata);
    const svgHTML = this._generateSvgMarkup(automata, layout);
    this.viewportContent.innerHTML = svgHTML;
    this.currentSvgElement = this.viewportContent.querySelector("svg");

    this.vbX = 0;
    this.vbY = 0;
    this.vbWidth = layout.width;
    this.vbHeight = layout.height;

    if (this.currentSvgElement) {
      this.currentSvgElement.setAttribute("width", layout.width);
      this.currentSvgElement.setAttribute("height", layout.height);
      this.currentSvgElement.style.width = layout.width + "px";
      this.currentSvgElement.style.height = layout.height + "px";
      this.currentSvgElement.style.display = "block";
      this.currentSvgElement.style.overflow = "visible";
    }

    this.viewportContent.style.width = layout.width + "px";
    this.viewportContent.style.height = layout.height + "px";

    // Asociar clics a los nodos cliente
    const nodes = this.currentSvgElement.querySelectorAll("g.node");
    nodes.forEach(node => {
      const sId = parseInt(node.getAttribute("data-state-id"), 10);
      if (isNaN(sId)) return;
      node.style.cursor = "pointer";
      node.addEventListener("click", (e) => {
        e.stopPropagation();
        if (window.onNodeClicked) window.onNodeClicked(sId);
      });
    });

    this.fitToView();
  }

  /**
   * Resalta dinámicamente uno o varios estados activos durante la simulación.
   */
  highlightStates(stateIds) {
    this.activeNodes = new Set(stateIds || []);
    if (!this.currentSvgElement) return;

    const nodes = this.currentSvgElement.querySelectorAll("[data-state-id]");
    nodes.forEach(node => {
      const sId = parseInt(node.getAttribute("data-state-id"), 10);
      const isActive = this.activeNodes.has(sId);

      const ellipses = node.querySelectorAll("ellipse, circle");
      const texts = node.querySelectorAll("text");

      if (isActive) {
        node.style.filter = "drop-shadow(0 0 16px rgba(245, 158, 11, 0.95))";
        ellipses.forEach((el, idx) => {
          el.setAttribute("fill", idx === 0 ? "#fef08a" : "none");
          el.setAttribute("stroke", "#f59e0b");
          el.setAttribute("stroke-width", "3.5");
        });
        texts.forEach(t => {
          t.setAttribute("fill", "#0f172a");
          t.style.fill = "#0f172a";
          t.style.fontWeight = "bold";
        });
      } else {
        node.style.filter = "none";
        const isAcceptance = this.automataData?.aceptacion?.includes(sId);
        ellipses.forEach((el, idx) => {
          el.setAttribute("fill", isAcceptance ? (idx === 0 ? "#1e293b" : "none") : "#0f172a");
          el.setAttribute("stroke", isAcceptance ? "#f59e0b" : "#38bdf8");
          el.setAttribute("stroke-width", "2");
        });
        texts.forEach(t => {
          t.setAttribute("fill", "#f8fafc");
          t.style.fill = "#f8fafc";
          t.style.fontWeight = "normal";
        });
      }
    });
  }

  /**
   * Algoritmo de Layout Jerárquico Dirigido (Sugiyama/Dagre en JS)
   */
  _computeHierarchicalLayout(automata) {
    const estados = automata.listaEstados || automata.estados || [];
    const transiciones = automata.listaTransiciones || automata.transiciones || [];
    const inicial = automata.estadoInicial?.id ?? automata.inicial ?? 0;

    // Asignación de rangos (capas)
    const capas = new Map();
    capas.set(inicial, 0);

    const cola = [inicial];
    const visitados = new Set([inicial]);

    while (cola.length) {
      const curr = cola.shift();
      const currNivel = capas.get(curr);

      const salientes = transiciones.filter(t => (t.estadoOrigen?.id ?? t.origen) === curr);
      for (const t of salientes) {
        const dest = t.estadoDestino?.id ?? t.destino;
        if (!capas.has(dest) || capas.get(dest) < currNivel + 1) {
          capas.set(dest, currNivel + 1);
        }
        if (!visitados.has(dest)) {
          visitados.add(dest);
          cola.push(dest);
        }
      }
    }

    // Para nodos no alcanzados desde inicio
    estados.forEach(e => {
      const eid = e.id ?? e;
      if (!capas.has(eid)) capas.set(eid, 0);
    });

    // Agrupar por capa
    const porCapa = new Map();
    for (const [id, capa] of capas.entries()) {
      if (!porCapa.has(capa)) porCapa.set(capa, []);
      porCapa.get(capa).push(id);
    }

    const xGap = 160;
    const yGap = 96;
    const marginX = 80;
    const marginY = 80;

    let maxInLayer = 0;
    for (const arr of porCapa.values()) {
      if (arr.length > maxInLayer) maxInLayer = arr.length;
    }
    const totalHeight = marginY * 2 + Math.max(1, maxInLayer) * yGap;

    const posiciones = new Map();
    for (const [capa, ids] of porCapa.entries()) {
      const h = (ids.length - 1) * yGap;
      const startY = marginY + (totalHeight - marginY * 2 - h) / 2;
      ids.forEach((id, idx) => {
        posiciones.set(id, {
          x: marginX + capa * xGap,
          y: startY + idx * yGap
        });
      });
    }

    const maxCapa = Math.max(...capas.values(), 0);
    return {
      posiciones,
      width: marginX * 2 + maxCapa * xGap + 80,
      height: totalHeight + 40
    };
  }

  _generateSvgMarkup(automata, layout) {
    const { posiciones, width, height } = layout;
    const R = 22;
    const estados = automata.listaEstados || automata.estados || [];
    const transiciones = automata.listaTransiciones || automata.transiciones || [];
    const inicial = automata.estadoInicial?.id ?? automata.inicial ?? 0;

    const parts = [];
    parts.push(`<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`);
    parts.push(`<defs>
      <marker id="arrow-wire" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="#38bdf8" /></marker>
      <marker id="arrow-eps" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="#a78bfa" /></marker>
    </defs>`);

    // Flecha de entrada al estado inicial
    const pIni = posiciones.get(inicial) || { x: 60, y: 60 };
    parts.push(`<line x1="${pIni.x - 45}" y1="${pIni.y}" x2="${pIni.x - R - 3}" y2="${pIni.y}" stroke="#38bdf8" stroke-width="2.2" marker-end="url(#arrow-wire)" />`);

    // Agrupar transiciones
    const grupos = new Map();
    for (const t of transiciones) {
      const orig = t.estadoOrigen?.id ?? t.origen;
      const dest = t.estadoDestino?.id ?? t.destino;
      const key = `${orig}->${dest}`;
      if (!grupos.has(key)) grupos.set(key, { orig, dest, simbolos: [] });
      grupos.get(key).simbolos.push(t.simbolo);
    }

    // Dibujar aristas
    for (const { orig, dest, simbolos } of grupos.values()) {
      const p1 = posiciones.get(orig);
      const p2 = posiciones.get(dest);
      if (!p1 || !p2) continue;

      const esEps = simbolos.every(s => s === "ε");
      const color = esEps ? "#a78bfa" : "#38bdf8";
      const marker = esEps ? "url(#arrow-eps)" : "url(#arrow-wire)";
      const dash = esEps ? `stroke-dasharray="5,4"` : "";
      const labelText = simbolos.join(", ");

      // Lazo (Self-loop)
      if (orig === dest) {
        const topY = p1.y - R - 34;
        parts.push(`<path d="M ${p1.x - R * 0.6},${p1.y - R * 0.8} C ${p1.x - R * 0.8},${topY} ${p1.x + R * 0.8},${topY} ${p1.x + R * 0.6},${p1.y - R * 0.8}" fill="none" stroke="${color}" stroke-width="2" ${dash} marker-end="${marker}" />`);
        parts.push(`<text x="${p1.x}" y="${topY - 4}" text-anchor="middle" fill="${color}" font-family="system-ui, sans-serif" font-size="12" font-weight="600">${labelText}</text>`);
        continue;
      }

      // Arista entre dos nodos distintos
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const ux = dx / dist;
      const uy = dy / dist;

      const sx = p1.x + ux * R;
      const sy = p1.y + uy * R;
      const ex = p2.x - ux * R;
      const ey = p2.y - uy * R;

      const isBack = dx < -10;
      const isVertical = Math.abs(dx) < 15;
      const curvature = isBack ? 52 : (isVertical ? 42 : 18);
      const sign = isBack ? -1 : 1;

      const midX = (sx + ex) / 2;
      const midY = (sy + ey) / 2;
      const cx = midX - uy * curvature * sign;
      const cy = midY + ux * curvature * sign;

      parts.push(`<path d="M ${sx},${sy} Q ${cx},${cy} ${ex},${ey}" fill="none" stroke="${color}" stroke-width="2" ${dash} marker-end="${marker}" />`);
      parts.push(`<text x="${cx}" y="${cy - 4}" text-anchor="middle" fill="#cbd5e1" font-family="system-ui, sans-serif" font-size="11.5" font-weight="600">${labelText}</text>`);
    }

    // Dibujar nodos
    estados.forEach(e => {
      const eid = e.id ?? e;
      const esAcept = e.esAceptacion ?? (automata.aceptacion && automata.aceptacion.includes(eid));
      const p = posiciones.get(eid);
      if (!p) return;

      const stroke = esAcept ? "#f59e0b" : "#38bdf8";
      const fill = esAcept ? "#1e293b" : "#0f172a";

      parts.push(`<g class="node" data-state-id="${eid}">`);
      if (esAcept) {
        parts.push(`<circle cx="${p.x}" cy="${p.y}" r="${R + 4}" fill="none" stroke="${stroke}" stroke-width="1.8" />`);
      }
      parts.push(`<circle cx="${p.x}" cy="${p.y}" r="${R}" fill="${fill}" stroke="${stroke}" stroke-width="2" />`);
      parts.push(`<text x="${p.x}" y="${p.y + 4.5}" text-anchor="middle" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="12" font-weight="700">q${eid}</text>`);
      parts.push(`</g>`);
    });

    parts.push(`</svg>`);
    return parts.join("");
  }

  exportSVG() {
    if (!this.currentSvgElement) return;
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(this.currentSvgElement);
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `automata_${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }

  exportPNG() {
    if (!this.currentSvgElement) return;
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(this.currentSvgElement);
    const img = new Image();
    const svgBlob = new Blob([svgStr], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      const canvas = document.createElement("canvas");
      const scaleFactor = 2;
      canvas.width = (this.vbWidth || 800) * scaleFactor;
      canvas.height = (this.vbHeight || 600) * scaleFactor;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#080c14";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      const pngUrl = canvas.toDataURL("image/png");
      const a = document.createElement("a");
      a.href = pngUrl;
      a.download = `automata_${Date.now()}.png`;
      a.click();
      URL.revokeObjectURL(url);
    };
    img.src = url;
  }
}

window.AutomataRenderer = AutomataRenderer;
