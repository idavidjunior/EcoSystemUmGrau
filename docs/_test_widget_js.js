
  (function(){
    var cores = {
      fundo: '#1e1e2e', borda: '#45475a', destaque: '#cba6f7',
      texto: '#cdd6f4', texto2: '#a6adc8'
    };

    function mkEl(tag, st) {
      var el = document.createElement(tag);
      if (st) el.style.cssText = st;
      return el;
    }

    // ---- Slider de velocidade (0.25x .. 3x) ----
    var velSlider = mkEl('input');
    velSlider.type = 'range';
    velSlider.min = '0.25'; velSlider.max = '3'; velSlider.step = '0.05';
    velSlider.value = localStorage.getItem('velGrafo') || '1';
    velSlider.style.cssText = 'width:110px;accent-color:#cba6f7;cursor:pointer;';
    velSlider.title = 'Velocidade do movimento';
    velSlider.addEventListener('input', function(){
      var v = parseFloat(velSlider.value);
      localStorage.setItem('velGrafo', String(v));
      try { if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(v); }
      catch(e){}
      velLbl.textContent = 'x' + v.toFixed(2);
    });

    var velLbl = mkEl('span');
    velLbl.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:34px;text-align:right;';
    velLbl.textContent = 'x' + parseFloat(velSlider.value).toFixed(2);

    var velGroup = mkEl('div');
    velGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    velGroup.appendChild(mkEl('span', 'font-size:10px;color:' + cores.texto2 + ';'));
    velGroup.firstChild.textContent = 'Velocidade';
    velGroup.appendChild(velSlider);
    velGroup.appendChild(velLbl);

    // ---- Slider de amplitude da deriva orbital (0 .. 3x) ----
    var orbSlider = mkEl('input');
    orbSlider.type = 'range';
    orbSlider.min = '0'; orbSlider.max = '3'; orbSlider.step = '0.1';
    orbSlider.value = localStorage.getItem('orbGrafo') || '1';
    orbSlider.style.cssText = 'width:110px;accent-color:#cba6f7;cursor:pointer;';
    orbSlider.title = 'Amplitude da flutuacao orbital';
    orbSlider.addEventListener('input', function(){
      var o = parseFloat(orbSlider.value);
      localStorage.setItem('orbGrafo', String(o));
      try { if (typeof _aplicarOrbita === 'function') _aplicarOrbita(o); }
      catch(e){}
      orbLbl.textContent = 'x' + o.toFixed(1);
      if (window.pywebview && window.pywebview.api && window.pywebview.api.guardar_orbGrafo) {
        try { window.pywebview.api.guardar_orbGrafo(o); } catch(e){}
      }
    });

    var orbLbl = mkEl('span');
    orbLbl.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:34px;text-align:right;';
    orbLbl.textContent = 'x' + parseFloat(orbSlider.value).toFixed(1);

    var orbGroup = mkEl('div');
    orbGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    orbGroup.appendChild(mkEl('span', 'font-size:10px;color:' + cores.texto2 + ';'));
    orbGroup.firstChild.textContent = 'Orbita';
    orbGroup.appendChild(orbSlider);
    orbGroup.appendChild(orbLbl);

    // ---- Busca por palavra no grafo ----
    var buscaInput = mkEl('input');
    buscaInput.type = 'text';
    buscaInput.placeholder = 'Buscar no grafo...';
    buscaInput.style.cssText =
      'width:100%;background:' + cores.fundo + ';color:' + cores.texto + ';' +
      'border:1px solid ' + cores.borda + ';border-radius:4px;font-size:11px;' +
      'padding:4px 6px;box-sizing:border-box;';
    buscaInput.addEventListener('input', function(){
      var termo = buscaInput.value.trim();
      try {
        if (typeof destacar === 'function') {
          if (termo) destacar('txt', termo, cores.destaque);
          else if (typeof limpar === 'function') limpar();
        }
      } catch(e){}
    });
    var buscaGroup = mkEl('div');
    buscaGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    buscaGroup.appendChild(mkEl('span', 'font-size:10px;color:' + cores.texto2 + ';'));
    buscaGroup.firstChild.textContent = 'Busca';
    buscaGroup.appendChild(buscaInput);

    // ---- Presets de tamanho do quadro ----
    var tamanhos = [
      { nome: 'Compacto',  w: 720,  h: 480 },
      { nome: 'Media',     w: 1024, h: 640 },
      { nome: 'Padrao',    w: 1280, h: 800 },
      { nome: 'Grande',    w: 1600, h: 1000 },
      { nome: 'Maxima',    w: 1920, h: 1200 },
    ];
    var tamSel = mkEl('select');
    tamSel.style.cssText =
      'background:' + cores.fundo + ';color:' + cores.texto + ';border:1px solid ' +
      cores.borda + ';border-radius:4px;font-size:11px;padding:2px 4px;cursor:pointer;';
    tamanhos.forEach(function(t){
      var op = mkEl('option');
      op.value = t.w + 'x' + t.h;
      op.textContent = t.nome + ' (' + t.w + 'x' + t.h + ')';
      tamSel.appendChild(op);
    });
    tamSel.addEventListener('change', function(){
      var wh = tamSel.value.split('x');
      localStorage.setItem('tamGrafo', tamSel.value);
      try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.redimensionar) {
          window.pywebview.api.redimensionar(parseInt(wh[0],10), parseInt(wh[1],10));
        }
      } catch(e){}
    });
    var tamLbl = mkEl('span');
    tamLbl.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    tamLbl.textContent = 'Quadro';
    var tamGroup = mkEl('div');
    tamGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    tamGroup.appendChild(tamLbl);
    tamGroup.appendChild(tamSel);

    // ---- Botoes de layout ----
    var ctrl = mkEl('div');
    ctrl.id = 'mk-labels';
    ctrl.title = 'Alternar visibilidade das etiquetas';
    ctrl.style.cssText =
      'width:30px;height:30px;border-radius:4px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-size:14px;user-select:none;color:' + cores.destaque + ';' +
      'background:#313244;border:1px solid ' + cores.destaque + ';';
    ctrl.innerHTML = 'T';

    var menuBtn = mkEl('div');
    menuBtn.id = 'mk-menu-btn';
    menuBtn.title = 'Mostrar/ocultar menus';
    menuBtn.style.cssText =
      'width:30px;height:30px;border-radius:4px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-size:14px;user-select:none;color:' + cores.destaque + ';' +
      'background:#313244;border:1px solid ' + cores.destaque + ';';
    menuBtn.innerHTML = '\u2630';

    var layoutGroup = mkEl('div');
    layoutGroup.style.cssText =
      'display:flex;gap:6px;border:1px solid ' + cores.destaque + ';' +
      'border-radius:6px;padding:3px;background:#313244;';
    layoutGroup.appendChild(ctrl);
    layoutGroup.appendChild(menuBtn);

    // ---- BANNER DE VERSAO - aparece por 4 segundos ----
    (function() {
      var banner = mkEl('div');
      banner.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:99999;' +
        'background:#cba6f7;color:#000;padding:8px 20px;border-radius:8px;font-size:13px;font-weight:bold;' +
        'box-shadow:0 4px 20px rgba(0,0,0,0.6);pointer-events:none;';
      banner.textContent = 'Cerebro Vivo v2 — Temas + Filtros — ' + new Date().toLocaleString('pt-BR');
      document.body.appendChild(banner);
      setTimeout(function() { banner.style.opacity = '0'; banner.style.transition = 'opacity 1s'; }, 3000);
      setTimeout(function() { if (banner.parentNode) banner.parentNode.removeChild(banner); }, 4000);
    })();

    // ---- Seletor de tema estetico (Neon / Glow / Calmo / Padrao) ----
    var temaSel = mkEl('select');
    temaSel.style.cssText =
      'background:' + cores.fundo + ';color:' + cores.texto + ';border:1px solid ' +
      cores.borda + ';border-radius:4px;font-size:11px;padding:2px 4px;cursor:pointer;';
    [
      { nome: 'Neon',    valor: 'neon',  icone: '\u26A1' },
      { nome: 'Glow',    valor: 'glow',  icone: '\u2600' },
      { nome: 'Calmo',   valor: 'calm',  icone: '\uD83C\uDF3F' },
      { nome: 'Padrao',  valor: 'padrao',icone: '\u25C9' }
    ].forEach(function(t){
      var op = mkEl('option');
      op.value = t.valor;
      op.textContent = t.icone + ' ' + t.nome;
      temaSel.appendChild(op);
    });
    var temaSalvo = localStorage.getItem('temaGrafo') || 'glow';
    temaSel.value = temaSalvo;
    temaSel.addEventListener('change', function(){
      try { if (typeof aplicarTema === 'function') aplicarTema(temaSel.value); }
      catch(e){}
    });
    var temaLbl = mkEl('span');
    temaLbl.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    temaLbl.textContent = 'Tema';
    var temaGroup = mkEl('div');
    temaGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    temaGroup.appendChild(temaLbl);
    temaGroup.appendChild(temaSel);

    var painel = mkEl('div');
    painel.id = 'mk-controles';
    painel.title = 'Controles do cerebro';
    painel.style.cssText =
      'position:fixed;right:10px;z-index:9999;display:flex;' +
      'flex-direction:column;gap:8px;padding:8px 10px;border-radius:8px;' +
      'background:rgba(30,30,46,0.88);border:1px solid ' + cores.borda + ';' +
      'box-shadow:0 2px 10px rgba(0,0,0,0.5);';
    painel.appendChild(temaGroup);
    painel.appendChild(velGroup);
    painel.appendChild(orbGroup);
    painel.appendChild(buscaGroup);
    painel.appendChild(tamGroup);
    painel.appendChild(layoutGroup);
    document.body.appendChild(painel);

    function reposicionarPainel() {
      var hdr = document.getElementById('header');
      var topo = 22;
      try {
        if (hdr && hdr.offsetParent !== null) {
          var r = hdr.getBoundingClientRect();
          if (r && r.bottom > 0) topo = Math.round(r.bottom) + 10;
        }
      } catch(e){}
      painel.style.top = topo + 'px';
    }
    window.addEventListener('resize', reposicionarPainel);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(reposicionarPainel, 400);
    } else {
      document.addEventListener('DOMContentLoaded', function(){ setTimeout(reposicionarPainel, 400); });
    }
    window.addEventListener('pywebviewready', function(){ setTimeout(reposicionarPainel, 400); });
    document.addEventListener('contextmenu', function(){ setTimeout(reposicionarPainel, 80); });

    function aplicarLabels() {
      if (typeof nodes === 'undefined') return;
      var oculto = localStorage.getItem('labelsOcultos') !== 'false';
      var tam = oculto ? 0 : 11;
      var upd = nodes.get().map(function(n){ return { id: n.id, font: Object.assign({}, n.font, { size: tam }) }; });
      nodes.update(upd);
    }

    ctrl.onmousedown = function(e) {
      e.preventDefault(); e.stopPropagation();
      // Toggle etiquetas: 'false' explicito = mostrar; qualquer outro = oculto
      var oculto = localStorage.getItem('labelsOcultos') !== 'false';
      localStorage.setItem('labelsOcultos', oculto ? 'false' : 'true');
      aplicarLabels();
      ctrl.style.opacity = oculto ? '1' : '0.55';
    };

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      aplicarLabels();
    } else {
      document.addEventListener('DOMContentLoaded', aplicarLabels);
    }
    window.addEventListener('pywebviewready', aplicarLabels);

    var lastCmdTs = 0;
    function buscarComandoVoz() {
      if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.comando_grafo) return;
      window.pywebview.api.comando_grafo(lastCmdTs).then(function(cmd) {
        if (cmd && cmd.filtro) {
          lastCmdTs = parseInt(cmd.ts || 0, 10);
          if (typeof destacar === 'function') {
            destacar(cmd.filtro, cmd.valor, cmd.cor);
          }
        }
      }).catch(function(){});
    }
    setInterval(buscarComandoVoz, 2500);
    if (document.readyState !== 'loading') { buscarComandoVoz(); }
    else { document.addEventListener('DOMContentLoaded', buscarComandoVoz); }

    function aplicarMenus() {
      var oculto = localStorage.getItem('menuOculto') === 'true';
      var hdr = document.getElementById('header');
      var painelLateral = document.getElementById('painel');
      var net = document.getElementById('net');
      if (hdr) hdr.style.display = oculto ? 'none' : '';
      if (painelLateral && oculto) painelLateral.classList.remove('visivel');
      if (net) net.style.height = oculto ? '100vh' : '';
      menuBtn.innerHTML = oculto ? '\u2630' : '\u2026';
      menuBtn.style.opacity = oculto ? '0.55' : '1';
      if (typeof network !== 'undefined' && network.redraw) { network.redraw(); }
      if (typeof reposicionarPainel === 'function') {
        setTimeout(reposicionarPainel, 60);
      }
    }
    menuBtn.onmousedown = function(e) {
      e.preventDefault(); e.stopPropagation();
      var nao = localStorage.getItem('menuOculto') !== 'true';
      localStorage.setItem('menuOculto', nao ? 'true' : 'false');
      aplicarMenus();
    };
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      aplicarMenus();
    } else {
      document.addEventListener('DOMContentLoaded', aplicarMenus);
    }
    window.addEventListener('pywebviewready', aplicarMenus);

    function aplicarPersistidos() {
      try {
        if (typeof _aplicarVelocidade === 'function') {
          var v = parseFloat(localStorage.getItem('velGrafo') || '1');
          _aplicarVelocidade(v);
        }
        if (typeof _aplicarOrbita === 'function') {
          var o = parseFloat(localStorage.getItem('orbGrafo') || '1');
          _aplicarOrbita(o);
        }
        if (typeof _atualizarStats === 'function') _atualizarStats();
      } catch(e){}
    }
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(aplicarPersistidos, 1500);
    } else {
      document.addEventListener('DOMContentLoaded', function(){ setTimeout(aplicarPersistidos, 1500); });
    }
    window.addEventListener('pywebviewready', aplicarPersistidos);
  })();
