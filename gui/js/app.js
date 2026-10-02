(function () {
  "use strict";

  // Estado global de la aplicación
  const state = {
    backendOnline: false,
    activeTab: "overview",
    regex: "a(b|c)*d",
    data: null,
    rendererAfn: null,
    rendererAfd: null,
    rendererSim: null,

    // Simulación
    sim: {
      tipo: "afd",
      cadena: "ad",
      pasos: [],
      indice: 0,
      isPlaying: false,
      timer: null,
      speed: 800
    }
  };

  const PRESETS = [
    { label: "a(b|c)*d", str: "ad" },
    { label: "(a|b)*abb", str: "aabb" },
    { label: "a+b", str: "aaab" },
    { label: "ab*c", str: "abbc" },
    { label: "(0|1)*011", str: "10011" }
  ];

  // Inicialización
  async function init() {
    setupRenderers();
    setupEvents();
    renderPresets();
    await checkBackendStatus();
    await generarAutomatas();
  }

  function setupRenderers() {
    state.rendererAfn = new AutomataRenderer("canvas-afn");
    state.rendererAfd = new AutomataRenderer("canvas-afd");
    state.rendererSim = new AutomataRenderer("canvas-sim");

    window.onNodeClicked = (stateId) => {
      handleNodeClick(stateId);
    };
  }

  async function checkBackendStatus() {
    const pill = document.getElementById("status-pill");
    const text = document.getElementById("status-text");

    try {
      const res = await fetch("/api/status", { method: "GET" });
      if (res.ok) {
        state.backendOnline = true;
        pill.classList.remove("offline");
        text.textContent = "Conectado (Python)";
        return;
      }
    } catch (e) {
      // Backend desconectado
    }

    state.backendOnline = false;
    pill.classList.add("offline");
    text.textContent = "Sin conexión con Python";
  }

  // Eventos de interfaz
  function setupEvents() {
    // Pestañas
    document.querySelectorAll(".step-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        const target = tab.dataset.tab;
        switchTab(target);
      });
    });

    // Botón generar
    document.getElementById("btn-generar").addEventListener("click", () => {
      generarAutomatas();
    });

    const regexInput = document.getElementById("input-regex");
    regexInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") generarAutomatas();
    });

    // Teclas rápidas para operadores
    document.querySelectorAll(".helper-key").forEach(btn => {
      btn.addEventListener("click", () => {
        const char = btn.dataset.char;
        insertCharInInput(regexInput, char);
      });
    });

    // Simulación
    document.getElementById("btn-iniciar-sim").addEventListener("click", () => {
      iniciarSimulacion();
    });

    const cadenaInput = document.getElementById("input-cadena");
    cadenaInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") iniciarSimulacion();
    });

    // Selector de modo de simulación (AFD vs AFN)
    document.querySelectorAll(".btn-sim-mode").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".btn-sim-mode").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        state.sim.tipo = btn.dataset.mode;

        if (state.data) {
          const simAutomata = state.sim.tipo === "afn" ? state.data.afn : state.data.afd;
          state.rendererSim.render(simAutomata, simAutomata.svg);
        }

        iniciarSimulacion();
      });
    });

    // Controles de transporte
    document.getElementById("btn-step-prev").addEventListener("click", stepPrev);
    document.getElementById("btn-step-next").addEventListener("click", stepNext);
    document.getElementById("btn-play-pause").addEventListener("click", togglePlayPause);
    document.getElementById("btn-step-reset").addEventListener("click", resetSimulacion);

    // Velocidades
    document.querySelectorAll(".btn-speed").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".btn-speed").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        state.sim.speed = parseInt(btn.dataset.speed, 10);
        if (state.sim.isPlaying) {
          clearInterval(state.sim.timer);
          state.sim.timer = setInterval(stepNext, state.sim.speed);
        }
      });
    });

    // Controles de viewport por canvas
    setupViewportToolbar("afn", state.rendererAfn);
    setupViewportToolbar("afd", state.rendererAfd);
    setupViewportToolbar("sim", state.rendererSim);

    // Cambio de vistas dentro del panel de Construcción AFD (Tarjetas / Dtran / Trans / Texto)
    document.querySelectorAll(".view-toggle-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".view-toggle-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const view = btn.dataset.view;
        document.querySelectorAll(".subsets-view-panel").forEach(p => p.classList.remove("active"));
        document.getElementById(`panel-subsets-${view}`)?.classList.add("active");
      });
    });

    // Copiar texto del log AFD
    document.getElementById("btn-copy-afd-log")?.addEventListener("click", () => {
      if (state.data?.afd?.pasos) {
        const text = state.data.afd.pasos.join("\n");
        navigator.clipboard.writeText(text).then(() => {
          const btn = document.getElementById("btn-copy-afd-log");
          const original = btn.textContent;
          btn.textContent = "✓ ¡Copiado!";
          setTimeout(() => { btn.textContent = original; }, 1800);
        });
      }
    });

    // Atajos de teclado
    window.addEventListener("keydown", (e) => {
      if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;

      if (e.code === "Space") {
        e.preventDefault();
        togglePlayPause();
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        stepNext();
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        stepPrev();
      }
    });

    window.addEventListener("resize", () => {
      if (state.activeTab === "afn" && state.rendererAfn) state.rendererAfn.fitToView();
      else if (state.activeTab === "afd" && state.rendererAfd) state.rendererAfd.fitToView();
      else if (state.activeTab === "sim" && state.rendererSim) state.rendererSim.fitToView();
    });
  }

  function setupViewportToolbar(prefix, renderer) {
    document.getElementById(`btn-zoom-in-${prefix}`)?.addEventListener("click", () => renderer.zoom(1.2));
    document.getElementById(`btn-zoom-out-${prefix}`)?.addEventListener("click", () => renderer.zoom(0.8));
    document.getElementById(`btn-fit-${prefix}`)?.addEventListener("click", () => renderer.fitToView());
    document.getElementById(`btn-reset-${prefix}`)?.addEventListener("click", () => renderer.resetView());
    document.getElementById(`btn-export-png-${prefix}`)?.addEventListener("click", () => renderer.exportPNG());
  }

  function insertCharInInput(input, char) {
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const text = input.value;
    input.value = text.substring(0, start) + char + text.substring(end);
    input.focus();
    input.selectionStart = input.selectionEnd = start + char.length;
  }

  function renderPresets() {
    const container = document.getElementById("preset-chips");
    container.innerHTML = "";
    PRESETS.forEach(p => {
      const btn = document.createElement("button");
      btn.className = "chip-btn";
      btn.textContent = p.label;
      btn.addEventListener("click", () => {
        document.getElementById("input-regex").value = p.label;
        document.getElementById("input-cadena").value = p.str;
        generarAutomatas();
      });
      container.appendChild(btn);
    });
  }

  function switchTab(tabId) {
    state.activeTab = tabId;
    document.querySelectorAll(".step-tab").forEach(t => {
      t.classList.toggle("active", t.dataset.tab === tabId);
    });
    document.querySelectorAll(".tab-content").forEach(c => {
      c.classList.toggle("active", c.id === `tab-${tabId}`);
    });

    requestAnimationFrame(() => {
      setTimeout(() => {
        if (tabId === "afn" && state.rendererAfn) {
          state.rendererAfn.fitToView();
        } else if (tabId === "afd" && state.rendererAfd) {
          state.rendererAfd.fitToView();
        } else if (tabId === "sim" && state.rendererSim) {
          state.rendererSim.fitToView();
        }
      }, 40);
    });
  }

  // Generación de autómatas mediante Python
  async function generarAutomatas() {
    const regex = document.getElementById("input-regex").value.trim();

    if (!regex) {
      showError("Por favor ingresa una expresión regular.");
      return;
    }

    showError(null);

    try {
      const res = await fetch("/api/analizar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ regex })
      });
      const json = await res.json();
      if (json.success) {
        state.data = json;
        state.regex = regex;
        actualizarUI();
      } else {
        showError(`Error al procesar: ${json.error}`);
      }
    } catch (e) {
      showError("No se pudo conectar con el servidor Python (app.py). Asegúrate de que el servidor esté corriendo.");
    }
  }

  function showError(msg) {
    const banner = document.getElementById("banner-error");
    if (!msg) {
      banner.classList.remove("visible");
      banner.textContent = "";
      return;
    }
    banner.textContent = "⚠ " + msg;
    banner.classList.add("visible");
  }

  // Actualización de componentes visuales
  function actualizarUI() {
    const { infijo, concat, postfijo, afn, afd } = state.data;

    // Resumen
    document.getElementById("disp-infijo").textContent = infijo;
    document.getElementById("disp-concat").textContent = concat;
    document.getElementById("disp-postfijo").textContent = postfijo;

    document.getElementById("stat-afn-estados").textContent = afn.estados.length;
    document.getElementById("stat-afn-trans").textContent = afn.transiciones.length;
    document.getElementById("stat-afd-estados").textContent = afd.estados.length;
    document.getElementById("stat-afd-trans").textContent = afd.transiciones.length;
    document.getElementById("stat-sigma").textContent = afd.alfabeto.join(", ") || "—";

    document.getElementById("tuple-afn").textContent = afn.tupla;
    document.getElementById("tuple-afd").textContent = afd.tupla;

    // AFN
    renderTablaTransiciones("table-afn", afn);
    renderTerminalLog("log-afn", afn.pasos);
    state.rendererAfn.render(afn, afn.svg);

    // AFD
    renderTablaTransiciones("table-afd", afd);
    renderTerminalLog("log-afd", afd.pasos);
    renderSubconjuntosCards(afd);
    renderTablaDtran(afd);
    state.rendererAfd.render(afd, afd.svg);

    // Simulación
    const currentSimAutomata = state.sim.tipo === "afn" ? afn : afd;
    state.rendererSim.render(currentSimAutomata, currentSimAutomata.svg);

    iniciarSimulacion();
  }

  function renderTablaTransiciones(tableId, automata) {
    const tbody = document.getElementById(tableId).querySelector("tbody");
    tbody.innerHTML = "";

    const sorted = [...automata.transiciones].sort((a, b) => {
      const origA = a.origen ?? a.estadoOrigen?.id;
      const origB = b.origen ?? b.estadoOrigen?.id;
      if (origA !== origB) return origA - origB;
      return (a.simbolo > b.simbolo ? 1 : -1);
    });

    sorted.forEach(t => {
      const orig = t.origen ?? t.estadoOrigen?.id;
      const dest = t.destino ?? t.estadoDestino?.id;
      const esEps = t.simbolo === "ε" || t.esEpsilon;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong style="color:var(--text-main);">q${orig}</strong></td>
        <td><span class="${esEps ? 'symbol-eps' : 'symbol-char'}">${t.simbolo}</span></td>
        <td><strong style="color:var(--text-main);">q${dest}</strong></td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderTerminalLog(logId, pasos) {
    const logEl = document.getElementById(logId);
    logEl.innerHTML = "";

    if (!pasos || !pasos.length) {
      logEl.innerHTML = `<div class="log-entry">(Sin registros disponibles)</div>`;
      return;
    }

    pasos.forEach(p => {
      const div = document.createElement("div");
      div.className = "log-entry";
      let html = escapeHtml(p);

      html = html.replace(/\[ESTADO NUEVO\]/g, `<span class="badge-new">ESTADO NUEVO</span>`);
      html = html.replace(/'([^']+)'/g, `<span style="color:var(--accent-cyan); font-weight:600;">'$1'</span>`);
      html = html.replace(/q\d+(\(\*\))?/g, `<span style="color:var(--accent-amber); font-weight:600;">$&</span>`);

      div.innerHTML = html;
      logEl.appendChild(div);
    });
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderSubconjuntosCards(afd) {
    const container = document.getElementById("container-step-cards");
    const filtersContainer = document.getElementById("afd-step-filters");
    if (!container) return;

    container.innerHTML = "";
    if (filtersContainer) filtersContainer.innerHTML = "";

    const pasos = afd.pasosDetallados || [];
    if (!pasos.length) {
      container.innerHTML = `<div style="padding:16px; color:var(--text-muted); font-family:var(--font-mono); font-size:0.8rem;">No hay pasos detallados disponibles.</div>`;
      return;
    }

    // Configurar filtros por estado origen
    const estadosOrigen = new Set();
    pasos.forEach(p => {
      if (p.tipo === "inicio") estadosOrigen.add(p.estado_afd);
      else if (p.tipo === "transicion") estadosOrigen.add(p.origen_afd);
    });

    if (filtersContainer) {
      const allBtn = document.createElement("button");
      allBtn.className = "chip-filter active";
      allBtn.dataset.filter = "all";
      allBtn.textContent = `Todos (${pasos.length})`;
      filtersContainer.appendChild(allBtn);

      Array.from(estadosOrigen).sort((a, b) => a - b).forEach(stId => {
        const btn = document.createElement("button");
        btn.className = "chip-filter";
        btn.dataset.filter = String(stId);
        btn.textContent = `Desde q${stId}`;
        filtersContainer.appendChild(btn);
      });

      filtersContainer.querySelectorAll(".chip-filter").forEach(btn => {
        btn.addEventListener("click", () => {
          filtersContainer.querySelectorAll(".chip-filter").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          const filter = btn.dataset.filter;

          container.querySelectorAll(".subsets-step-card").forEach(card => {
            if (filter === "all" || card.dataset.origen === filter) {
              card.style.display = "block";
            } else {
              card.style.display = "none";
            }
          });
        });
      });
    }

    pasos.forEach((p, idx) => {
      const card = document.createElement("div");

      if (p.tipo === "inicio") {
        card.className = "subsets-step-card initial";
        card.dataset.origen = String(p.estado_afd);
        card.innerHTML = `
          <div class="step-card-header">
            <div class="step-trans-badge">
              <span class="step-pill afd-pill">q${p.estado_afd}</span>
              <span class="step-trans-type">ESTADO INICIAL DEL AFD</span>
            </div>
            <div class="step-status-badges">
              <span class="badge-status initial">Paso 0 · Arranque</span>
              ${p.es_aceptacion ? '<span class="badge-status final">★ Final</span>' : ''}
            </div>
          </div>
          <div class="step-card-body">
            <div class="step-calc-box">
              <div class="calc-row">
                <span class="calc-tag">1. Estado inicial del AFN:</span>
                <span class="calc-val"><strong style="color:var(--accent-purple);">q${p.afn_inicial}</strong></span>
              </div>
              <div class="calc-row">
                <span class="calc-tag">2. ε-clausura(q${p.afn_inicial}) [alcance sin consumir símbolos]:</span>
                <span class="calc-val set-badge closure">{ ${p.conjunto_afn.map(id => 'q' + id).join(', ')} }</span>
              </div>
            </div>
            <div class="step-explanation">
              Se calcula la <strong>ε-clausura</strong> del estado inicial del AFN (todos los estados alcanzables recorriendo aristas vacías ε). El subconjunto resultante define el estado de arranque <strong>q${p.estado_afd}</strong> del AFD.
            </div>
          </div>
        `;
      } else {
        card.className = "subsets-step-card";
        card.dataset.origen = String(p.origen_afd);
        card.dataset.destino = String(p.destino_afd);

        const statusTag = p.es_nuevo
          ? '<span class="badge-status new">✨ Nuevo Estado</span>'
          : '<span class="badge-status exist">↩ Ya Existente</span>';
        const finalTag = p.es_aceptacion ? '<span class="badge-status final">★ Final</span>' : '';

        card.innerHTML = `
          <div class="step-card-header">
            <div class="step-trans-badge">
              <span class="step-pill afd-pill">q${p.origen_afd}</span>
              <span class="step-arrow">── <span class="step-sym">'${escapeHtml(p.simbolo)}'</span> ──▶</span>
              <span class="step-pill afd-pill ${p.es_aceptacion ? 'final' : ''}">q${p.destino_afd}${p.es_aceptacion ? '★' : ''}</span>
            </div>
            <div class="step-status-badges">
              ${statusTag}
              ${finalTag}
            </div>
          </div>
          <div class="step-card-body">
            <div class="step-calc-box">
              <div class="calc-row">
                <span class="calc-tag">1. Subconjunto origen (q${p.origen_afd}):</span>
                <span class="calc-val set-badge orig">{ ${p.origen_conjunto.map(i => 'q' + i).join(', ')} }</span>
              </div>

              <div class="calc-row">
                <span class="calc-tag">2. mover({ q${p.origen_afd} }, '${escapeHtml(p.simbolo)}'):</span>
                <span class="calc-val set-badge move">{ ${p.movidos.length ? p.movidos.map(i => 'q' + i).join(', ') : '∅'} }</span>
                <span class="calc-note">Estados del AFN a los que se llega consumiendo '${escapeHtml(p.simbolo)}'</span>
              </div>

              <div class="calc-row">
                <span class="calc-tag">3. ε-clausura de alcanzados:</span>
                <span class="calc-val set-badge closure">{ ${p.clausura.map(i => 'q' + i).join(', ')} }</span>
                <span class="calc-note">Cerradura con saltos ε</span>
              </div>
            </div>

            <div class="step-explanation">
              ${p.es_nuevo
                ? `El subconjunto <code>{ ${p.clausura.map(i => 'q' + i).join(', ')} }</code> es <strong>nuevo</strong>. Se crea el estado <strong>q${p.destino_afd}</strong> en el AFD y se conecta: <code>δ(q${p.origen_afd}, '${escapeHtml(p.simbolo)}') = q${p.destino_afd}</code>.`
                : `El subconjunto ya coincide con el estado <strong>q${p.destino_afd}</strong>. Se reutiliza y se conecta: <code>δ(q${p.origen_afd}, '${escapeHtml(p.simbolo)}') = q${p.destino_afd}</code>.`
              }
            </div>
          </div>
        `;
      }

      // Interactividad con el canvas: resaltar nodos al hacer hover sobre la tarjeta
      card.addEventListener("mouseenter", () => {
        const dest = p.tipo === "inicio" ? p.estado_afd : p.destino_afd;
        state.rendererAfd.highlightStates([dest]);
      });
      card.addEventListener("mouseleave", () => {
        state.rendererAfd.highlightStates([]);
      });

      container.appendChild(card);
    });
  }

  function renderTablaDtran(afd) {
    const table = document.getElementById("table-dtran");
    const theadRow = document.getElementById("dtran-header-row");
    const tbody = document.getElementById("dtran-tbody");
    if (!table || !theadRow || !tbody) return;

    const alfabeto = afd.alfabeto || [];
    const filas = afd.tablaSubconjuntos || [];

    // Armar encabezados con los símbolos de entrada
    theadRow.innerHTML = `
      <th>Estado AFD</th>
      <th>Subconjunto AFN</th>
      ${alfabeto.map(s => `<th>Con '${escapeHtml(s)}'</th>`).join('')}
      <th>¿Final?</th>
    `;

    tbody.innerHTML = "";
    if (!filas.length) {
      tbody.innerHTML = `<tr><td colspan="${3 + alfabeto.length}" style="text-align:center; color:var(--text-dim);">(Sin datos)</td></tr>`;
      return;
    }

    filas.forEach(f => {
      const tr = document.createElement("tr");

      let estadoBadge = `<span class="badge-state-dtran ${f.es_inicial ? 'initial' : ''} ${f.es_aceptacion ? 'final' : ''}">q${f.id_afd}</span>`;
      if (f.es_inicial) estadoBadge += ' <span style="font-size:0.68rem; color:var(--accent-purple);">(inicial)</span>';

      const conjuntoStr = `{ ${f.conjunto_afn.map(i => 'q' + i).join(', ')} }`;

      const celdasSimbolos = alfabeto.map(sym => {
        const dest = f.transiciones[sym];
        if (dest !== undefined) {
          return `<td style="font-weight:600;"><span class="dtran-trans-dest">q${dest}</span></td>`;
        }
        return `<td><span class="dtran-empty">—</span></td>`;
      }).join('');

      const esFinalBadge = f.es_aceptacion
        ? '<span style="color:var(--accent-amber); font-weight:700;">★ Sí</span>'
        : '<span style="color:var(--text-dim);">No</span>';

      tr.innerHTML = `
        <td>${estadoBadge}</td>
        <td><span class="dtran-set-text">${conjuntoStr}</span></td>
        ${celdasSimbolos}
        <td>${esFinalBadge}</td>
      `;

      tr.addEventListener("mouseenter", () => {
        state.rendererAfd.highlightStates([f.id_afd]);
      });
      tr.addEventListener("mouseleave", () => {
        state.rendererAfd.highlightStates([]);
      });

      tbody.appendChild(tr);
    });
  }

  function handleNodeClick(stateId) {
    if (state.data?.afd?.mapeoSubconjuntos) {
      const afnIds = state.data.afd.mapeoSubconjuntos[stateId];
      if (afnIds && afnIds.length) {
        const info = `El estado q${stateId} del AFD agrupa los estados del AFN:\n{ ${afnIds.map(i => "q" + i).join(", ")} }`;
        alert(info);
      }
    }
  }

  // Simulación y cinta de ejecución
  async function iniciarSimulacion() {
    if (!state.data) return;
    const cadena = document.getElementById("input-cadena").value || "";
    state.sim.cadena = cadena;
    pause();

    try {
      const res = await fetch("/api/simular", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          regex: state.regex,
          cadena,
          tipo: state.sim.tipo
        })
      });
      const json = await res.json();
      if (json.success) {
        state.sim.pasos = json.pasos || [];
        state.sim.aceptada = json.aceptada;
        state.sim.indice = 0;
        prepararCinta(cadena);
        renderizarPasoSimulacion();
      } else {
        showError(`Error en simulación: ${json.error}`);
      }
    } catch (e) {
      showError("No se pudo ejecutar la simulación en Python.");
    }
  }

  function prepararCinta(cadena) {
    const cinta = document.getElementById("tape-cells");
    cinta.innerHTML = "";

    if (!cadena) {
      cinta.innerHTML = `<span style="font-family:var(--font-mono); font-size:0.85rem; color:var(--text-dim); padding:10px;">(Cadena vacía ε)</span>`;
      return;
    }

    for (let i = 0; i < cadena.length; i++) {
      const cell = document.createElement("div");
      cell.className = "tape-cell";
      cell.textContent = cadena[i];
      cell.id = `cell-${i}`;
      cinta.appendChild(cell);
    }
  }

  function renderizarPasoSimulacion() {
    if (!state.sim.pasos.length) return;

    const paso = state.sim.pasos[state.sim.indice];
    const { indice_simbolo, estado_id, estado_ids, texto, es_final } = paso;

    // Actualizar cinta de lectura
    document.querySelectorAll(".tape-cell").forEach((c, idx) => {
      c.classList.remove("head", "consumed");
      if (idx < indice_simbolo) c.classList.add("consumed");
      if (idx === indice_simbolo) c.classList.add("head");
    });

    // Actualizar detalle del paso
    document.getElementById("trace-step-text").textContent = texto;
    document.getElementById("sim-step-counter").textContent = `Paso ${state.sim.indice + 1} de ${state.sim.pasos.length}`;

    // Resaltar nodos activos en el canvas
    const nodosActivos = estado_ids || (estado_id !== undefined ? [estado_id] : []);
    state.rendererSim.highlightStates(nodosActivos);

    // Veredicto si finalizó
    const verdict = document.getElementById("verdict-banner");
    if (es_final) {
      verdict.className = `verdict-banner visible ${state.sim.aceptada ? "accepted" : "rejected"}`;
      verdict.innerHTML = state.sim.aceptada
        ? `<strong>✓ Cadena aceptada</strong> — "${state.sim.cadena}" pertenece al lenguaje regular.`
        : `<strong>✗ Cadena rechazada</strong> — "${state.sim.cadena}" no pertenece al lenguaje regular.`;
    } else {
      verdict.className = "verdict-banner";
    }

    // Navegación
    document.getElementById("btn-step-prev").disabled = state.sim.indice === 0;
    document.getElementById("btn-step-next").disabled = state.sim.indice >= state.sim.pasos.length - 1;
  }

  function stepNext() {
    if (state.sim.indice < state.sim.pasos.length - 1) {
      state.sim.indice++;
      renderizarPasoSimulacion();
    } else {
      pause();
    }
  }

  function stepPrev() {
    if (state.sim.indice > 0) {
      state.sim.indice--;
      renderizarPasoSimulacion();
    }
  }

  function togglePlayPause() {
    if (state.sim.isPlaying) {
      pause();
    } else {
      play();
    }
  }

  function play() {
    if (!state.sim.pasos.length) return;

    if (state.sim.indice >= state.sim.pasos.length - 1) {
      state.sim.indice = 0;
      renderizarPasoSimulacion();
    }

    state.sim.isPlaying = true;
    const btn = document.getElementById("btn-play-pause");
    btn.innerHTML = `<span class="icon">⏸</span> Pausar`;
    btn.classList.add("primary");

    clearInterval(state.sim.timer);
    state.sim.timer = setInterval(() => {
      stepNext();
    }, state.sim.speed);
  }

  function pause() {
    state.sim.isPlaying = false;
    clearInterval(state.sim.timer);
    const btn = document.getElementById("btn-play-pause");
    if (btn) {
      btn.innerHTML = `<span class="icon">▶</span> Reproducir`;
      btn.classList.remove("primary");
    }
  }

  function resetSimulacion() {
    pause();
    state.sim.indice = 0;
    if (state.sim.pasos.length) {
      renderizarPasoSimulacion();
    }
  }

  window.addEventListener("DOMContentLoaded", init);

})();
