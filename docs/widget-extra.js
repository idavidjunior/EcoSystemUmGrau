/**
 * Widget JS Extra - Full UI Logic
 * Injected at end of <body>
 */
(function(){
  function mk(tag, styles) {
    var el = document.createElement(tag);
    if (styles) el.style.cssText = styles;
    return el;
  }

  function logError(context, err) {
    console.warn('[widget] ' + context + ':', err);
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.debug_log) {
        window.pywebview.api.debug_log('JS-ERROR: ' + context + ': ' + err);
      }
    } catch (e) {}
  }

  function mountWidgetUI() {
    if (document.getElementById('mk-controles')) return;

    var cores = { fundo: '#1e1e2e', borda: '#45475a', destaque: '#cba6f7', texto: '#cdd6f4', texto2: '#a6adc8' };

    // ===== BOTOES DE ACAO (vivem no painel inferior) =====
    var ctrl = mk('div');
    ctrl.id = 'mk-labels';
    ctrl.title = 'Alternar visibilidade das etiquetas';
    ctrl.textContent = 'T';
    ctrl.style.cssText = 'width:22px;height:22px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:11px;';

    var resetBtn = mk('div');
    resetBtn.id = 'mk-btn-reset';
    resetBtn.title = 'Resetar preferências';
    resetBtn.textContent = '↺';
    resetBtn.style.cssText = 'width:22px;height:22px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:11px;';

    var actions = mk('div');
    actions.style.cssText = 'display:flex;gap:4px;border:1px solid ' + cores.destaque + ';border-radius:6px;padding:2px 4px;background:#313244;';
    actions.appendChild(ctrl);
    actions.appendChild(resetBtn);

    var topTheme = mk('select');
    topTheme.style.cssText = 'background:' + cores.fundo + ';color:' + cores.texto + ';border:1px solid ' + cores.borda + ';border-radius:4px;font-size:11px;padding:2px 4px;';
    [{ nome: 'Neon', valor: 'neon' }, { nome: 'Glow', valor: 'glow' }, { nome: 'Calmo', valor: 'calm' }, { nome: 'Padrao', valor: 'padrao' }].forEach(function(item){
      var opt = mk('option');
      opt.value = item.valor;
      opt.textContent = item.nome;
      topTheme.appendChild(opt);
    });
    topTheme.value = localStorage.getItem('temaGrafo') || 'glow';

    var themeWrap = mk('div');
    themeWrap.style.cssText = 'display:flex;align-items:center;gap:6px;';
    var themeLabel = mk('span');
    themeLabel.textContent = 'Tema';
    themeLabel.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    themeWrap.appendChild(themeLabel);
    themeWrap.appendChild(topTheme);

    var speed = mk('input');
    speed.type = 'range'; speed.min = '0.25'; speed.max = '3'; speed.step = '0.05'; speed.value = localStorage.getItem('velGrafo') || '1';
    speed.style.cssText = 'width:110px;accent-color:' + cores.destaque + ';cursor:pointer;';
    var speedValue = mk('span');
    speedValue.textContent = 'x' + parseFloat(speed.value).toFixed(2);
    speedValue.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:34px;text-align:right;';
    speed.addEventListener('input', function(){
      speedValue.textContent = 'x' + parseFloat(speed.value).toFixed(2);
      localStorage.setItem('velGrafo', speed.value);
    });
    var speedWrap = mk('div');
    speedWrap.style.cssText = 'display:flex;align-items:center;gap:6px;';
    var speedLabel = mk('span');
    speedLabel.textContent = 'Velocidade';
    speedLabel.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    speedWrap.appendChild(speedLabel);
    speedWrap.appendChild(speed);
    speedWrap.appendChild(speedValue);

    var orbit = mk('input');
    orbit.type = 'range'; orbit.min = '0'; orbit.max = '3'; orbit.step = '0.1'; orbit.value = localStorage.getItem('orbGrafo') || '1';
    orbit.style.cssText = 'width:110px;accent-color:' + cores.destaque + ';cursor:pointer;';
    var orbitValue = mk('span');
    orbitValue.textContent = 'x' + parseFloat(orbit.value).toFixed(1);
    orbitValue.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:34px;text-align:right;';
    orbit.addEventListener('input', function(){
      orbitValue.textContent = 'x' + parseFloat(orbit.value).toFixed(1);
      localStorage.setItem('orbGrafo', orbit.value);
    });
    var orbitWrap = mk('div');
    orbitWrap.style.cssText = 'display:flex;align-items:center;gap:6px;';
    var orbitLabel = mk('span');
    orbitLabel.textContent = 'Orbita';
    orbitLabel.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    orbitWrap.appendChild(orbitLabel);
    orbitWrap.appendChild(orbit);
    orbitWrap.appendChild(orbitValue);

    // ===== PAINEL INFERIOR (mk-controles) =====
    var panel = mk('div');
    panel.id = 'mk-controles';
    panel.title = 'Controles do grafo';
    panel.style.cssText = 'position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:row;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;padding:8px 12px;border-radius:10px;background:var(--mk-panel-bg, rgba(24,24,37,0.82));border:1px solid rgba(145, 160, 198, 0.2);box-shadow:0 8px 22px rgba(0,0,0,0.32);backdrop-filter:blur(6px);';
    panel.appendChild(actions);
    panel.appendChild(themeWrap);
    panel.appendChild(speedWrap);
    panel.appendChild(orbitWrap);

    // Botão do Olho DENTRO do painel inferior (único controle de visibilidade global da área)
    var eye = mk('div');
    eye.id = 'mk-painel-toggle';
    eye.title = 'Ocultar/mostrar painel de controles';
    eye.textContent = '👁';
    eye.style.cssText = 'width:28px;height:28px;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;background:#313244;border:1px solid ' + cores.destaque + ';color:' + cores.destaque + ';font-size:13px;box-shadow:0 4px 12px rgba(0,0,0,0.22);transition:transform .12s ease, box-shadow .12s ease, background .12s ease;flex-shrink:0;';
    panel.appendChild(eye);

    document.body.appendChild(panel);

    // ===== FUNÇÕES =====
    function setLabelVisibility(visible) {
      var hidden = !visible;
      localStorage.setItem('labelsOcultos', hidden ? 'true' : 'false');
      try {
        if (typeof network !== 'undefined' && network) {
          if (hidden) {
            // Ocultar: zera o font.size de cada no do dataset.
            var nodeSet = null;
            if (network.body && network.body.data && network.body.data.nodes && typeof network.body.data.nodes.get === 'function') {
              nodeSet = network.body.data.nodes;
            } else if (network.body && network.body.nodes && typeof network.body.nodes.get === 'function') {
              nodeSet = network.body.nodes;
            } else if (typeof nodes !== 'undefined' && nodes && typeof nodes.get === 'function') {
              nodeSet = nodes;
            }
            if (nodeSet && typeof nodeSet.get === 'function') {
              // Preenche a base apenas se ainda nao existir — nunca sobrescreve
              // a base REAL semeada pelo grafo com um valor poluido por zoom.
              if (!window.__mkLabelBase) window.__mkLabelBase = {};
              var currentNodes = nodeSet.get();
              var payload = currentNodes.map(function(n) {
                if (!n || typeof n.id === 'undefined') return null;
                if (typeof window.__mkLabelBase[n.id] !== 'number' || window.__mkLabelBase[n.id] <= 0) {
                  window.__mkLabelBase[n.id] = (n.font && typeof n.font.size === 'number' && n.font.size > 0) ? n.font.size : 13;
                }
                return {
                  id: n.id,
                  font: Object.assign({}, n.font || {}, { size: 0 })
                };
              }).filter(Boolean);
              if (payload.length) {
                try { nodeSet.update(payload); } catch (e) { logError('nodeSet.update', e); }
              }
            }
          } else {
            // Mostrar: delega ao _ajustarFontes do grafo, que usa a base REAL
            // (hubs 14, demais 13) compensada pelo zoom atual — nunca o cache
            // poluido por um zoom antigo. Fallback: restaura __mkLabelBase.
            var ajustado = false;
            try { if (typeof _ajustarFontes === 'function') { _ajustarFontes(); ajustado = true; } } catch (e) { logError('_ajustarFontes', e); }
            if (!ajustado) {
              var nodeSet2 = null;
              if (network.body && network.body.data && network.body.data.nodes && typeof network.body.data.nodes.get === 'function') {
                nodeSet2 = network.body.data.nodes;
              } else if (network.body && network.body.nodes && typeof network.body.nodes.get === 'function') {
                nodeSet2 = network.body.nodes;
              } else if (typeof nodes !== 'undefined' && nodes && typeof nodes.get === 'function') {
                nodeSet2 = nodes;
              }
              if (nodeSet2 && typeof nodeSet2.get === 'function') {
                var cur = nodeSet2.get();
                var pl = cur.map(function(n) {
                  if (!n || typeof n.id === 'undefined') return null;
                  var base = (window.__mkLabelBase && typeof window.__mkLabelBase[n.id] === 'number' && window.__mkLabelBase[n.id] > 0) ? window.__mkLabelBase[n.id] : 13;
                  return { id: n.id, font: Object.assign({}, n.font || {}, { size: base }) };
                }).filter(Boolean);
                if (pl.length) { try { nodeSet2.update(pl); } catch (e) { logError('nodeSet.update (show)', e); } }
              }
            }
          }
          // Etiquetas de cluster nodes respeitam o mesmo estado
          try { if (typeof _sincronizarClusterLabels === 'function') _sincronizarClusterLabels(); } catch (e) { logError('_sincronizarClusterLabels', e); }
          if (typeof network.redraw === 'function') network.redraw();
        }
      } catch (e) { logError('setLabelVisibility', e); }

      // Atualiza aparência do botão T
      ctrl.style.opacity = hidden ? '0.6' : '1';
      ctrl.style.borderColor = hidden ? '#7c7f93' : cores.destaque;
      ctrl.style.background = hidden ? '#2b2d3a' : '#313244';
      ctrl.title = visible ? 'Ocultar etiquetas' : 'Mostrar etiquetas';
    }

    function applyTheme(theme) {
      theme = theme || 'glow';
      localStorage.setItem('temaGrafo', theme);
      try {
        // Aplica o preset COMPLETO do grafo (glow, arestas, forcas e fisica)
        if (typeof aplicarTema === 'function') aplicarTema(theme);
      } catch (e) { logError('aplicarTema', e); }
      try {
        window.__mkTemaAtual = theme;
        document.body.setAttribute('data-theme', theme);
      } catch (e) { logError('applyTheme', e); }
    }

    function resetWidgetState() {
      topTheme.value = 'glow';
      speed.value = '1';
      orbit.value = '1';
      localStorage.setItem('temaGrafo', 'glow');
      localStorage.setItem('velGrafo', '1');
      localStorage.setItem('orbGrafo', '1');
      localStorage.setItem('labelsOcultos', 'true');
      localStorage.setItem('painelGrafoVisivel', 'true');
      try { localStorage.removeItem('modo3D'); } catch (e) {}
      try { localStorage.removeItem('waveIntensidade'); } catch (e) {}
      try { localStorage.setItem('flashEnabled', 'true'); } catch (e) {}
      applyTheme('glow');
      setLabelVisibility(false); // padrao: etiquetas desativadas
      syncControlsPanel(true);
      speedValue.textContent = 'x1.00';
      orbitValue.textContent = 'x1.0';
      try { if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(1); } catch (e) { logError('_aplicarVelocidade', e); }
      try { if (typeof _aplicarOrbita === 'function') _aplicarOrbita(1); } catch (e) { logError('_aplicarOrbita', e); }
      try { if (typeof _toggle3D === 'function') _toggle3D(false); } catch (e) { logError('_toggle3D', e); }
      try { if (typeof _aplicarWaveIntensidade === 'function') _aplicarWaveIntensidade(1); } catch (e) { logError('_aplicarWaveIntensidade', e); }
      try { if (typeof _toggleFlash === 'function') _toggleFlash(true); } catch (e) { logError('_toggleFlash', e); }
      try { if (typeof limpar === 'function') limpar(); } catch (e) { logError('limpar', e); }
      try { if (typeof network !== 'undefined' && network && network.fit) network.fit({ animation: true }); } catch (e) { logError('network.fit', e); }
    }

    topTheme.addEventListener('change', function(){
      applyTheme(topTheme.value);
    });

    speed.addEventListener('input', function(){
      speedValue.textContent = 'x' + parseFloat(speed.value).toFixed(2);
      localStorage.setItem('velGrafo', speed.value);
      try {
        if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(parseFloat(speed.value));
      } catch (e) { logError('_aplicarVelocidade (speed)', e); }
    });

    orbit.addEventListener('input', function(){
      orbitValue.textContent = 'x' + parseFloat(orbit.value).toFixed(1);
      localStorage.setItem('orbGrafo', orbit.value);
      try {
        if (typeof _aplicarOrbita === 'function') _aplicarOrbita(parseFloat(orbit.value));
      } catch (e) { logError('_aplicarOrbita (orbit)', e); }
    });

    // Estado do painel inferior (controlado APENAS pelo botão do olho).
    // O olho vive DENTRO do painel: ao ocultar os controles mantemos o painel
    // minimo com apenas o olho, para nunca perder a forma de re-exibir.
    var panelVisible = localStorage.getItem('painelGrafoVisivel') !== 'false';
    function syncControlsPanel(show) {
      panelVisible = !!show;
      themeWrap.style.display = panelVisible ? 'flex' : 'none';
      speedWrap.style.display = panelVisible ? 'flex' : 'none';
      orbitWrap.style.display = panelVisible ? 'flex' : 'none';
      panel.style.display = 'flex'; // painel nunca some: vira o "puxador" do olho
      panel.hidden = false;
      panel.classList.toggle('mk-painel-min', !panelVisible);
      // Olho SEMPRE visível - só muda ícone/title
      eye.title = panelVisible ? 'Ocultar painel de controles' : 'Mostrar painel de controles';
      eye.textContent = panelVisible ? '👁' : '👁️';
      eye.style.background = panelVisible ? '#313244' : '#45475a';
      eye.style.boxShadow = panelVisible ? '0 4px 12px rgba(0,0,0,0.22)' : '0 0 0 2px rgba(203,166,247,0.2), 0 6px 14px rgba(0,0,0,0.24)';
      localStorage.setItem('painelGrafoVisivel', panelVisible ? 'true' : 'false');
    }

    syncControlsPanel(panelVisible);

    // ===== EVENT LISTENERS (estados independentes) =====
    
    // Olho: controla APENAS o painel inferior (mk-controles)
    eye.addEventListener('click', function(){
      syncControlsPanel(!panelVisible);
    });

    // Botão T: alterna etiquetas dos nós (independente)
    ctrl.addEventListener('click', function(){
      // Alterna: mostrar se estiver oculto, ocultar se estiver visivel
      var estaOculto = localStorage.getItem('labelsOcultos') === 'true';
      setLabelVisibility(estaOculto ? true : false);
    });

    resetBtn.addEventListener('click', function(){
      resetWidgetState();
    });

    window.__mkWidgetApi = {
      applyTheme: applyTheme,
      setLabelVisibility: setLabelVisibility,
      resetWidgetState: resetWidgetState
    };

    applyTheme(topTheme.value);
    // Padrao: etiquetas DESATIVADAS. So 'false' explicito mostra.
    setLabelVisibility(localStorage.getItem('labelsOcultos') === 'false');
    if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(parseFloat(speed.value));
    if (typeof _aplicarOrbita === 'function') _aplicarOrbita(parseFloat(orbit.value));
  }

  // DOM already loaded when this script runs at end of body
  mountWidgetUI();

  window.addEventListener('pywebviewready', mountWidgetUI, { once: true });
})();