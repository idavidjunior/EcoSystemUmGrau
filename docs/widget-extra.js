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

    // ===== BARRA SUPERIOR (topBar) =====
    var topBar = mk('div');
    topBar.id = 'mk-topbar';
    topBar.style.cssText = 'position:fixed;top:10px;left:12px;right:auto;z-index:99998;display:flex;align-items:center;gap:4px;pointer-events:auto;';

    var ctrl = mk('div');
    ctrl.id = 'mk-labels';
    ctrl.title = 'Alternar visibilidade das etiquetas';
    ctrl.textContent = 'T';
    ctrl.style.cssText = 'width:22px;height:22px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:11px;';

    var menuBtn = mk('div');
    menuBtn.id = 'mk-menu-btn';
    menuBtn.title = 'Mostrar/ocultar menus (barra superior)';
    menuBtn.textContent = '☰';
    menuBtn.style.cssText = 'width:22px;height:22px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:11px;';

    var resetBtn = mk('div');
    resetBtn.id = 'mk-btn-reset';
    resetBtn.title = 'Resetar preferências';
    resetBtn.textContent = '↺';
    resetBtn.style.cssText = 'width:22px;height:22px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:11px;';

    var actions = mk('div');
    actions.style.cssText = 'display:flex;gap:4px;border:1px solid ' + cores.destaque + ';border-radius:6px;padding:2px 4px;background:#313244;';
    actions.appendChild(ctrl);
    actions.appendChild(menuBtn);
    actions.appendChild(resetBtn);
    topBar.appendChild(actions);

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
    panel.style.cssText = 'position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:row;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;padding:8px 12px;border-radius:10px;background:rgba(24,24,37,0.82);border:1px solid rgba(145, 160, 198, 0.2);box-shadow:0 8px 22px rgba(0,0,0,0.32);backdrop-filter:blur(6px);';
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

    document.body.appendChild(topBar);
    document.body.appendChild(panel);

    // ===== FUNÇÕES =====
    function setLabelVisibility(visible) {
      var hidden = !visible;
      localStorage.setItem('labelsOcultos', hidden ? 'true' : 'false');
      try {
        if (typeof network !== 'undefined' && network) {
          var nodeSet = null;
          if (network.body && network.body.data && network.body.data.nodes && typeof network.body.data.nodes.get === 'function') {
            nodeSet = network.body.data.nodes;
          } else if (network.body && network.body.nodes && typeof network.body.nodes.get === 'function') {
            nodeSet = network.body.nodes;
          } else if (typeof nodes !== 'undefined' && nodes && typeof nodes.get === 'function') {
            nodeSet = nodes;
          }

          if (nodeSet && typeof nodeSet.get === 'function') {
            if (!window.__mkLabelBase) window.__mkLabelBase = {};
            var currentNodes = nodeSet.get();
            var payload = currentNodes.map(function(n) {
              if (!n || typeof n.id === 'undefined') return null;
              if (typeof window.__mkLabelBase[n.id] !== 'number' || window.__mkLabelBase[n.id] <= 0) {
                window.__mkLabelBase[n.id] = (n.font && typeof n.font.size === 'number' && n.font.size > 0) ? n.font.size : 13;
              }
              return {
                id: n.id,
                font: Object.assign({}, n.font || {}, { size: hidden ? 0 : window.__mkLabelBase[n.id] })
              };
            }).filter(Boolean);

            if (payload.length) {
              try { nodeSet.update(payload); } catch (e) { logError('nodeSet.update', e); }
            }
          }
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
        if (typeof window !== 'undefined') {
          window.__mkTemaAtual = theme;
          document.body.setAttribute('data-theme', theme);
        }
      } catch (e) { logError('applyTheme', e); }
    }

    function resetWidgetState() {
      topTheme.value = 'glow';
      speed.value = '1';
      orbit.value = '1';
      localStorage.setItem('temaGrafo', 'glow');
      localStorage.setItem('velGrafo', '1');
      localStorage.setItem('orbGrafo', '1');
      localStorage.setItem('labelsOcultos', 'false');
      localStorage.setItem('painelGrafoVisivel', 'true');
      applyTheme('glow');
      setLabelVisibility(true);
      syncControlsPanel(true);
      speedValue.textContent = 'x1.00';
      orbitValue.textContent = 'x1.0';
      try {
        if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(1);
      } catch (e) { logError('_aplicarVelocidade', e); }
      try {
        if (typeof _aplicarOrbita === 'function') _aplicarOrbita(1);
      } catch (e) { logError('_aplicarOrbita', e); }
      try {
        if (typeof network !== 'undefined' && network && network.fit) network.fit({ animation: true });
      } catch (e) { logError('network.fit', e); }
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

    // Estado do painel inferior (controlado APENAS pelo botão do olho)
    var panelVisible = localStorage.getItem('painelGrafoVisivel') !== 'false';
    function syncControlsPanel(show) {
      panelVisible = !!show;
      panel.style.display = panelVisible ? 'flex' : 'none';
      panel.hidden = !panelVisible;
      panel.setAttribute('aria-hidden', String(!panelVisible));
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

    // Menu (☰): controla APENAS a barra superior (mk-topbar)
    menuBtn.addEventListener('click', function(){
      var isHidden = topBar.style.display === 'none';
      topBar.style.display = isHidden ? 'flex' : 'none';
      menuBtn.textContent = isHidden ? '☰' : '…';
      menuBtn.title = isHidden ? 'Mostrar barra superior' : 'Ocultar barra superior';
    });

    // Botão T: alterna etiquetas dos nós (independente)
    ctrl.addEventListener('click', function(){
      var shouldShow = localStorage.getItem('labelsOcultos') !== 'true';
      setLabelVisibility(shouldShow);
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
    setLabelVisibility(localStorage.getItem('labelsOcultos') !== 'true');
    if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(parseFloat(speed.value));
    if (typeof _aplicarOrbita === 'function') _aplicarOrbita(parseFloat(orbit.value));
  }

  // DOM already loaded when this script runs at end of body
  mountWidgetUI();

  window.addEventListener('pywebviewready', mountWidgetUI, { once: true });
})();