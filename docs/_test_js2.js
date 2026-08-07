  function clarear(hex, fator) {
    hex = hex.replace('#', '');
    const r = Math.min(255, Math.round(parseInt(hex.substring(0,2),16) * fator + 255 * (1 - fator)));
    const g = Math.min(255, Math.round(parseInt(hex.substring(2,4),16) * fator + 255 * (1 - fator)));
    const b = Math.min(255, Math.round(parseInt(hex.substring(4,6),16) * fator + 255 * (1 - fator)));
    return '#' + [r,g,b].map(x => x.toString(16).padStart(2,'0')).join('');
  }

  // --- Flash visual no clique do no ---
  // Pulsos de brilho branco/tema que se expandem e recolhem, com fade.
  var _flashAtivo = false;
  function flashNo(id, cor) {
    if (_flashAtivo) return;
    var orig = original[id];
    if (!orig) return;
    _flashAtivo = true;
    var c = cor || '#ffffff';
    nodes.update([{ id: id, color: c, size: Math.max(orig.size, 16) * 1.4, shadow: true, shadowSize: 42, shadowColor: c }]);
    setTimeout(function() {
      _flashAtivo = false;
      nodes.update([{ id: id, color: orig.color, size: orig.size, shadow: false, shadowSize: 0 }]);
    }, 750);
  }

  // --- Alternar modo 3D (onda viajante de profundidade) ---
  function _toggle3D(ativo) {
    _modo3D = ativo;
    if (typeof localStorage !== 'undefined') localStorage.setItem('modo3D', ativo);
    // se desativado, restaura a z base de todos os nos
    if (!ativo) {
      var agora = Date.now();
      nodes.get().forEach(function(n) {
        var z = _zBase[n.id] != null ? _zBase[n.id] : 0.5;
        var esc = 0.68 + 0.62 * z;
        var op = Math.min(1, 0.85 * (0.55 + 0.55 * z));
        nodes.update([{ id: n.id, size: Math.max(6, (original[n.id] ? original[n.id].size : 12) * esc), opacity: op }]);
      });
    }
  }

  // --- Alternar flash nos cliques ---
  function _toggleFlash(ativo) {
    _flashEnabled = ativo;
    if (typeof localStorage !== 'undefined') localStorage.setItem('flashEnabled', ativo ? 'true' : 'false');
  }

  // --- Click no no: flash + foco na vizinhanca ---
  network.on('click', function(params) {
    if (params.nodes && params.nodes.length > 0) {
      var nid = params.nodes[0];
      if (_flashEnabled) flashNo(nid, _glowCor || '#89b4fa');
      if (!_destacado) focarVizinhanca(nid, (original[nid] && original[nid].color) || '#89b4fa');
    }
  });


  const _fontLimpo = (function() {
    // respeita o padrao de labels ocultas (so 'false' mostra)
    var oc = (typeof localStorage !== 'undefined' && localStorage.getItem('labelsOcultos') !== 'false');
    return oc ? 0 : 11;
  })();
  function limpar() {
    _destacado = false; // libera de volta a decoracao viva (cerebro vivo)
    _flashAtivo = false;
    // reseta o estado do motor de avalanches: pausa correntes/residual
    _avalanche = { ativo: false, fila: [], maior: 0, size: 0 };
    _memb = {}; _refrat = {};
    nodes.get().forEach(function(n) { _memb[n.id] = Math.random() * _LIMIAR * 0.7; });
    _sinapsePorNo = null; // forca reconstrucao do cache de vizinhos
    document.querySelectorAll('.lg').forEach(b => b.classList.remove('active'));
    const atualizacoes = nodes.get().map(n => ({
      id: n.id, color: original[n.id].color, size: original[n.id].size,
      opacity: 1, borderWidth: 0, borderWidthSelected: 0, shadow: false,
      font: { size: _fontLimpo, color: '#cdd6f4', face: 'Segoe UI', bold: false }
    }));
    nodes.update(atualizacoes);
    const arestasUp = edges.get().map(e => ({
      id: e.id, color: arestaOriginal[e.id].color, width: arestaOriginal[e.id].width, opacity: 1
    }));
    edges.update(arestasUp);
    document.getElementById('painel').classList.remove('visivel');
    document.getElementById('painel').innerHTML = '';
  }

  function telaInicial() {
    limpar();
    if (viewInical && network.moveTo) {
      // restaura as posicoes originais dos nos e a visao inicial
      const atualizacoes = Object.keys(posIniciais).map(id => ({
        id, x: posIniciais[id].x, y: posIniciais[id].y, fixed: false
      }));
      nodes.update(atualizacoes);
      network.moveTo({
        position: viewInical,
        scale: scaleInical
      });
    } else {
      network.fit({ animation: true });
    }
  }

  function focarVizinhanca(id, corGrupo) {
    _destacado = true; // congela decoracao viva: preserva o efeito do clique
    // vizinhanca direta: nos de 1 pulo
    const viz = new Set([id]);
    edges.get().forEach(e => {
      if (e.from === id) viz.add(e.to);
      if (e.to === id) viz.add(e.from);
    });

    const corNo = clarear(corGrupo, 0.42);
    const corViz = clarear(corGrupo, 0.25);

    // no central: maior, brilhante, glow forte
    // vizinhos: cor viva, borda, glow
    // resto: apagado
    const atualizacoes = [];
    nodes.get().forEach(n => {
      if (n.id === id) {
        atualizacoes.push({
          id: n.id, color: corNo, borderColor: '#ffffff', borderWidth: 4, borderWidthSelected: 4,
          shadow: true, shadowColor: '#ffffff', shadowSize: 28,
          size: original[n.id].size + 16, font: { size: 16, color: '#ffffff', face: 'Segoe UI', bold: true }
        });
      } else if (viz.has(n.id)) {
        atualizacoes.push({
          id: n.id, color: corViz, borderColor: corNo, borderWidth: 2, borderWidthSelected: 2,
          shadow: true, shadowColor: corViz, shadowSize: 16,
          size: original[n.id].size + 6
        });
      } else {
        atualizacoes.push({ id: n.id, color: '#10101a', size: 3, opacity: 0.05,
                            borderWidth: 0, borderWidthSelected: 0, shadow: false, font: { size: 6, color: '#293241' } });
      }
    });
    nodes.update(atualizacoes);

    // arestas da vizinhanca brilhantes; resto apagado
    const arestasUp = [];
    edges.get().forEach(e => {
      const interno = viz.has(e.from) || viz.has(e.to);
      const central = (e.from === id) || (e.to === id);
      if (central) {
        arestasUp.push({ id: e.id, color: corNo, width: 4.5, opacity: 1 });
      } else if (interno) {
        arestasUp.push({ id: e.id, color: corViz, width: 2, opacity: 0.8 });
      } else {
        arestasUp.push({ id: e.id, color: '#2a2a3a', width: 0.3, opacity: 0.06 });
      }
    });
    edges.update(arestasUp);

    // zoom preciso na vizinhanca
    network.fit({
      nodes: Array.from(viz),
      animation: { duration: 600, easingFunction: 'easeInOutQuad' }
    });
  }

  function mostrarLista(grupo, corGrupo, titulo) {
    const painel = document.getElementById('painel');
    const itens = nodes.get()
      .filter(n => grupo.has(n.id))
      .sort((a, b) => (a.label || '').localeCompare(b.label || ''));

    let html = `<h2><span class="dot" style="background:${corGrupo}"></span>${titulo}
      <span class="count">(${itens.length})</span></h2><ul>`;
    itens.forEach(n => {
      const spec = (n.title || '').split('\n')[0];
      html += `<li data-id="${n.id}"><div class="titulo">${n.label}</div>
               <div class="spec">${spec}</div></li>`;
    });
    html += '</ul>';
    painel.innerHTML = html;
    painel.classList.add('visivel');

    // clique no item -> destaca o no + vizinhos e da zoom preciso
    painel.querySelectorAll('li').forEach(li => {
      li.addEventListener('click', () => {
        painel.querySelectorAll('li').forEach(x => x.classList.remove('sel'));
        li.classList.add('sel');
        focarVizinhanca(li.dataset.id, corGrupo);
      });
    });
  }

  function destacar(filtro, valor, corGrupo) {
    if (filtro === 'home') {
      telaInicial();
      return;
    }
    if (filtro === 'all') {
      limpar();
      return;
    }
    _destacado = true; // congela decoracao viva: preserva o destaque do grupo
    document.querySelectorAll('.lg').forEach(b => b.classList.remove('active'));
    const alvo = document.querySelector(`.lg[data-filter="${filtro}"][data-value="${valor}"]`);
    if (alvo) alvo.classList.add('active');

    // conjunto de nos do grupo
    const grupo = new Set();
    nodes.get().forEach(n => {
      if (filtro === 'cat' && n.cat === valor) grupo.add(n.id);
      else if (filtro === 'cl' && n.cl === valor) grupo.add(n.id);
      else if (filtro === 'st' && n.st === valor) grupo.add(n.id);
      else if (filtro === 'txt') {
        // busca por palavra no label, title (resumo) e tags — case-insensitive
        const termo = String(valor || '').toLowerCase();
        if (!termo) return;
        const alvoTexto =
          String(n.label || '') + ' ' + String(n.title || '') + ' ' +
          String(n.slug || n.id || '') + ' ' + (n.tags || []).join(' ');
        if (alvoTexto.toLowerCase().indexOf(termo) !== -1) grupo.add(n.id);
      }
      else if (filtro === 'dom') {
        const ehMCP = (n.tags || []).some(t => String(t).toLowerCase().indexOf('mcp') !== -1);
        const ehHub = n.cat === 'hub' || n.cat === 'geral';
        // 'mcp' -> notas com tag mcp; 'conhecimento' -> notas sem tag mcp
        // (hubs/categorias genericas nao entram no filtro de dominio)
        if (!ehHub && (valor === 'mcp' ? ehMCP : !ehMCP)) grupo.add(n.id);
      }
    });

    const corViva = clarear(corGrupo, 0.35);

    // nos: dentro do grupo ficam vivos; fora ficam apagados
    const atualizacoes = [];
    nodes.get().forEach(n => {
      if (grupo.has(n.id)) {
        atualizacoes.push({
          id: n.id,
          color: corViva,
          borderColor: '#ffffff',
          borderWidth: 3,
          borderWidthSelected: 3,
          shadow: true,
          shadowColor: corViva,
          shadowSize: 22,
          size: original[n.id].size + 8
        });
      } else {
        atualizacoes.push({ id: n.id, color: '#14141f', size: 3, opacity: 0.08,
                            borderWidth: 0, borderWidthSelected: 0, shadow: false });
      }
    });
    nodes.update(atualizacoes);

    // arestas: entre nos do grupo = cor do grupo e grossas; do grupo p/ fora = finas; fora = apagadas
    const arestasUp = [];
    edges.get().forEach(e => {
      const dentroDentro = grupo.has(e.from) && grupo.has(e.to);
      const dentroFora = grupo.has(e.from) !== grupo.has(e.to);
      if (dentroDentro) {
        arestasUp.push({ id: e.id, color: corViva, width: 3.5, opacity: 0.95 });
      } else if (dentroFora) {
        arestasUp.push({ id: e.id, color: '#888', width: 0.6, opacity: 0.35 });
      } else {
        arestasUp.push({ id: e.id, color: '#3a3a4a', width: 0.3, opacity: 0.10 });
      }
    });
    edges.update(arestasUp);
    network.fit({ animation: true });

    // lista dos itens do grupo
    const nome = alvo ? alvo.textContent.trim() : valor;
    mostrarLista(grupo, corGrupo, nome, corGrupo);
  }

  document.querySelectorAll('.lg').forEach(btn => {
    btn.addEventListener('click', () => destacar(btn.dataset.filter, btn.dataset.value, btn.dataset.color));
  });

  // =====================================================================
  // SISTEMA DE TEMAS ESTETICOS (Graph Styler + Graph Background)
  // Presets de um clique: Neon, Glow, Calmo, Padrao
  // Cada tema redefine cores de fundo, glow, sombras, forcas e animacoes
  // =====================================================================
  const TEMAS = {
    padrao: {
      nome: 'Padrao',
      icone: '◉',
      fundo: '#1e1e2e',
      headerBg: '#181825',
      headerBorda: '#313244',
      redeFundo: '#1e1e2e',
      noCor: null,
      arestaCor: '#666',
      sombraCor: 'rgba(137,180,250,0.35)',
      glowCor: '#89b4fa',
      pulsoForca: 1.0,
      pulsoSombra: 1.0,
      destaque: '#cba6f7',
      forca: { grav: -720, central: 0.30, mola: 0.045, amort: 0.82, velMax: 13, delta: 0.32 }
    },
    neon: {
      nome: 'Neon',
      icone: '⚡',
      fundo: '#0d0d1a',
      headerBg: '#0a0a15',
      headerBorda: '#cba6f7',
      statsFundo: '#0d0d1a',
      arestaCor: '#7c3aed',
      sombraCor: 'rgba(203,166,247,0.55)',
      glowCor: '#cba6f7',
      pulsoForza: 2.6,
      pulsoSombra: 2.0,
      respira: '#cba6f7',
      forca: { gravit: -10000, gravidade: 0.12, mola: 0.05, amort: 0.58, velMax: 22, delta: 0.24 }
    },
    glow: {
      nome: 'Glow',
      icone: '☀',
      fundo: '#12121f',
      headerBg: '#101018',
      headerBorda: '#89b4fa',
      statsFundo: '#12121f',
      arestaCor: '#6366f1',
      sombraCor: 'rgba(137,180,250,0.65)',
      glowCor: '#89b4fa',
      pulsoForza: 3.2,
      pulsoSombra: 2.5,
      respira: '#89b4fa',
      forca: { gravit: -560, gravidade: 0.12, mola: 0.043, amort: 0.75, velMax: 11, delta: 0.38 }
    },
    calm: {
      nome: 'Calmo',
      icone: '🌿',
      fundo: '#1a1f1f',
      headerBg: '#141818',
      headerBorda: '#5dade2aa',
      statsFundo: '#1a1f1f',
      arestaCor: '#5dade2',
      sombraCor: 'rgba(93,173,226,0.18)',
      glowCor: '#5dade2',
      pulsoForza: 0.5,
      pulsoSombra: 0.4,
      respira: '#5dade2',
      forca: { gravit: -400, gravidade: 0.08, mola: 0.03, amort: 0.88, velMax: 7, delta: 0.45 }
    }
  };

  // ---- Preset de forcas calibradas por tema ----
  function _aplicarForcasTema(tema) {
    var f = tema.forca;
    try {
      network.setOptions({
        physics: {
          barnesHut: {
            gravitationalConstant: f.gravit,
            centralGravity: f.gravidade,
            springConstant: f.mola,
            damping: f.amort
          },
          maxVelocity: f.velMax,
          timestep: f.delta
        }
      });
    } catch(e) { }
    // Desestabiliza propositalmente por 600ms
    network.stabilize(50);
  }

  function aplicarTema(nome) {
    var t = TEMAS[nome] || TEMAS.padrao;  // fallback seguro
    try {
      // Fundo do corpo
      document.body.style.background = t.fundo;
      // Header
      var hdr = document.getElementById('header');
      if (hdr) {
        hdr.style.background = t.headerBg || t.fundo;
        hdr.style.borderBottomColor = t.headerBorda || '#313244';
      }

      // Stats
      var stats = document.getElementById('stats');
      if (stats) stats.style.background = t.statsBg || t.fundo;

      // Arestas — cor base
      _corAresta = t.arestaCor;

      // Sombra dos nos 
      _sombraCor = t.sombraCor;
      _glowCor = t.glowCor;

      // Pulsos des crianças
      _pulsoForca = t.pulsoForca;
      _pulsoSombra = t.pulsoSombra;

      // Cor do destaque nos controles internos
      _corDestaque = t.respira || t.glowCor;

      // Cor da barra superior
      _headerCor = t.headerBorda || '#313244';

      // Aplica forcado calibrado
      _aplicarForcasTema(t);
      localStorage.setItem('temaGrafo', nome);
    } catch(e) { }
  }

  // Restaurar tema salvo
  (function() {
    var salvo = localStorage.getItem('temaGrafo') || 'glow';
    aplicarTema(salvo);
  })();
