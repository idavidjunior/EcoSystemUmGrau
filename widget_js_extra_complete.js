WIDGET_JS_EXTRA = """
<script>
    console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");
        // Test echo method
        if(window.pywebview && window.pywebview.api && window.pywebview.api.echo){
          console.log(">>> Testing echo...");
          window.pywebview.api.echo("test123").then(function(v){
            console.log(">>> echo() returned:", v);
            if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
              window.pywebview.api.debug_log("ECHO_TEST: " + v);
            }
          }).catch(function(e){ console.log(">>> ECHO ERROR:", e); });
        }
        // Test ping method
        if(window.pywebview && window.pywebview.api && window.pywebview.api.ping){
          console.log(">>> Testing ping...");
          window.pywebview.api.ping().then(function(v){
            console.log(">>> ping() returned:", v);
            if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
              window.pywebview.api.debug_log("PING_TEST: " + v);
            }
          }).catch(function(e){ console.log(">>> PING ERROR:", e); });
        }
        // Test: write to localStorage and check
        try {
          localStorage.setItem("widget_js_test", Date.now().toString());
          console.log(">>> localStorage write OK");
        } catch(e) { console.log(">>> localStorage ERROR:", e); }
        // Force initWidgetControls call with error handling
        setTimeout(function(){
          try {
            console.log(">>> Timeout: calling initWidgetControls");
            initWidgetControls();
            console.log(">>> initWidgetControls returned");
          } catch(e) { console.log(">>> initWidgetControls ERROR:", e); }
        }, 100);
        // Write test file via fetch to /test endpoint
        fetch("/test_js_exec", {method: "POST", body: "OK"}).then(function(){
          console.log(">>> Test endpoint called");
        }).catch(function(e){ console.log(">>> FETCH ERROR:", e); });
        // Simple bridge accessibility test
        try {
          var hasPywebview = typeof window.pywebview !== "undefined";
          var hasApi = hasPywebview && typeof window.pywebview.api !== "undefined";
          var hasDebugLog = hasApi && typeof window.pywebview.api.debug_log === "function";
          console.log(">>> Bridge check: pywebview=" + hasPywebview + ", api=" + hasApi + ", debug_log=" + hasDebugLog);
          if(hasDebugLog){ window.pywebview.api.debug_log("BRIDGE_ACCESSIBLE"); }
        } catch(e) { console.log(">>> BRIDGE CHECK ERROR:", e); }
        // localStorage test
        try {
          localStorage.setItem("js_test_executed", "true");
          console.log(">>> localStorage test set");
        } catch(e) { console.log(">>> localStorage ERROR:", e); }
        // Alert to verify JS execution
        alert("JS EXECUTING - check this alert");
        // Write test file to verify JS execution
        try {
          fetch("test_js_execution.txt", {method: "POST", body: "JS_EXECUTED"});
        } catch(e) { console.log(">>> FETCH ERROR:", e); }
        console.log(">>> WIDGET_JS_EXTRA: About to call initWidgetControls");
        // Test bridge with file write
        if(window.pywebview && window.pywebview.api){
          console.log(">>> Testing bridge write_file...");
          window.pywebview.api.debug_log("JS_BRIDGE_TEST: Widget JS executed");
        }
    console.log(">>> Document readyState:", document.readyState);
    console.log(">>> pywebview:", window.pywebview);
    console.log(">>> pywebview.api:", window.pywebview && window.pywebview.api);
    console.log(">>> WIDGET_JS_EXTRA LOADED AND EXECUTING");
    // DEBUG LOG
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: START");
    }

  function initWidgetControls() {
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      // File write test to verify initWidgetControls execution
      try {
        fetch("/initwidgetcontrols_test", {method: "POST", body: "initWidgetControls_called"});
        console.log(">>> initWidgetControls: fetch test sent");
      } catch(e) { console.log(">>> initWidgetControls fetch ERROR:", e); }
      try {
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls called");
        console.log(">>> initWidgetControls START");
        console.log(">>> pywebview:", window.pywebview);
        console.log(">>> pywebview.api:", window.pywebview && window.pywebview.api);
        if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
          window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls BRIDGE TEST");
        }
        // Direct bridge test
        if(window.pywebview && window.pywebview.api){
          window.pywebview.api.versao().then(function(v){ console.log("versao:", v); });
        }
    console.log("INIT WIDGET CONTROLS RUNNING");
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls CONSOLE LOG TEST");
        // Direct synchronous bridge test
        try {
          console.log(">>> Testing bridge versao()...");
          window.pywebview.api.versao().then(function(v) {
            console.log(">>> versao() returned:", v);
            if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
              window.pywebview.api.debug_log("WIDGET_JS_EXTRA: versao() returned " + v);
        // Test test_bridge method
        try {
          console.log(">>> Testing bridge test_bridge()...");
          window.pywebview.api.test_bridge().then(function(v) {
            console.log(">>> test_bridge() returned:", v);
            if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
              window.pywebview.api.debug_log("WIDGET_JS_EXTRA: test_bridge() returned " + v);
            }
          }).catch(function(e) { console.log(">>> test_bridge() ERROR:", e); });
        } catch(e) { console.log(">>> SYNC ERROR test_bridge:", e); }
            }
          }).catch(function(e) { console.log(">>> versao() ERROR:", e); });
        } catch(e) { console.log(">>> SYNC ERROR:", e); }
    }
    }
      } catch(e) { console.log(">>> initWidgetControls ERROR:", e); }

  (function(){
    // ERROR HANDLER GLOBAL
    window.addEventListener('error', function(ev){
      if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
        window.pywebview.api.debug_log('JS_ERROR: ' + (ev.message||'') + ' @ ' + (ev.filename||'') + ':' + (ev.lineno||''));
      }
    });
    window.addEventListener('unhandledrejection', function(ev){
      if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
        window.pywebview.api.debug_log('UNHANDLED_REJECTION: ' + (ev.reason||(ev.reason&&ev.reason.message)||''));
      }
    });
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
    menuBtn.innerHTML = '\\u2630';

    var layoutGroup = mkEl('div');
    layoutGroup.style.cssText =
      'display:flex;gap:6px;border:1px solid ' + cores.destaque + ';' +
      'border-radius:6px;padding:3px;background:#313244;';
    layoutGroup.appendChild(ctrl);
    layoutGroup.appendChild(menuBtn);

    // ---- Grupo 3D: toggle + slider de intensidade ----
    var btn3D = mkEl('div');
    btn3D.id = 'mk-btn-3d';
    btn3D.title = 'Alternar modo 3D (onda viajante de profundidade)';
    btn3D.style.cssText =
      'width:30px;height:30px;border-radius:4px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-size:14px;user-select:none;transition:all .3s ease;' +
      'background:#313244;border:1px solid ' + cores.destaque + ';';
    btn3D.innerHTML = '\\u1F34D'; // onda de serpente (3D ativo)
    var modo3DAtivo = (typeof localStorage !== 'undefined' && localStorage.getItem('modo3D') === 'true');
    btn3D._ativo = modo3DAtivo;
    btn3D.style.boxShadow = btn3D._ativo ? '0 0 12px ' + cores.destaque : 'none';
    btn3D.addEventListener('click', function() {
      btn3D._ativo = !btn3D._ativo;
      btn3D.innerHTML = btn3D._ativo ? '\\u1F34D' : '\\u2605'; // serpente vs estrela
      btn3D.style.background = btn3D._ativo ? cores.fundo : '#313244';
      btn3D.style.boxShadow = btn3D._ativo ? '0 0 14px ' + cores.destaque : 'none';
      if (typeof _toggle3D === 'function') _toggle3D(btn3D._ativo);
    });

    // Botao flash
    var btnFlash = mkEl('div');
    btnFlash.id = 'mk-btn-flash';
    btnFlash.title = 'Alternar flash nos cliques nos nos';
    btnFlash.style.cssText = btn3D.style.cssText;
    btnFlash.innerHTML = '\\u26A1';
    btnFlash._ativo = (typeof localStorage !== 'undefined' && localStorage.getItem('flashEnabled') !== 'false');
    btnFlash.style.boxShadow = btnFlash._ativo ? '0 0 12px ' + cores.destaque : 'none';
    btnFlash.addEventListener('click', function() {
      btnFlash._ativo = !btnFlash._ativo;
      btnFlash.style.opacity = btnFlash._ativo ? '1' : '0.4';
      btnFlash.style.boxShadow = btnFlash._ativo ? '0 0 14px ' + cores.destaque : 'none';
      if (typeof _toggleFlash === 'function') _toggleFlash(btnFlash._ativo);
    });

    var label3D = mkEl('span');
    label3D.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:40px;';
    label3D.textContent = '3D';
    var slider3D = mkEl('input');
    slider3D.type = 'range';
    slider3D.min = '0';
    slider3D.max = '3';
    slider3D.step = '0.1';
    slider3D.value = String(parseFloat((typeof localStorage !== 'undefined' && localStorage.getItem('waveIntensidade')) || '1') || 1);
    slider3D.style.cssText = 'width:100px;accent-color:' + cores.destaque + ';';
    slider3D.addEventListener('input', function() {
      var v = parseFloat(slider3D.value);
      if (typeof _aplicarWaveIntensidade === 'function') _aplicarWaveIntensidade(v);
    });
    var grupo3D = mkEl('div');
    grupo3D.style.cssText = 'display:flex;align-items:center;gap:6px;';
    grupo3D.appendChild(label3D);
    grupo3D.appendChild(slider3D);
    grupo3D.appendChild(btn3D);
    grupo3D.appendChild(btnFlash);

    // ---- Botao reset (🔄) alinhado ao lado do painel ----
    var btnReset = mkEl('div');
    btnReset.id = 'mk-btn-reset';
    btnReset.title = 'Resetar preferencias do grafo (tema, velocidade, orbita) e recarregar';
    btnReset.style.cssText =
      'width:28px;height:28px;border-radius:4px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-size:14px;user-select:none;color:' + cores.destaque + ';' +
      'background:#313244;border:1px solid ' + cores.destaque + ';';
    btnReset.innerHTML = '\\u21BB'; // seta ciclo (reset)
    btnReset.addEventListener('click', function() {
      if (confirm('\\u1EAFResetar todas as preferencias do cerebro para o padrao?')) {
        var chaves = ['temaGrafo','modo3D','flashEnabled','waveIntensidade','labelsAnimated','orbAmplGlobal'];
        chaves.forEach(function(k) { try { localStorage.removeItem(k); } catch(e){} });
        location.reload();
      }
    });

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
      { nome: 'Neon',    valor: 'neon',  icone: '\\u26A1' },
      { nome: 'Glow',    valor: 'glow',  icone: '\\u2600' },
      { nome: 'Calmo',   valor: 'calm',  icone: '\\uD83C\\uDF3F' },
      { nome: 'Padrao',  valor: 'padrao',icone: '\\u25C9' }
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
      'position:fixed;right:10px;top:70px;z-index:9999;display:flex;' +
      'flex-direction:column;gap:8px;padding:8px 10px;border-radius:8px;' +
      'background:rgba(30,30,46,0.88);border:1px solid ' + cores.borda + ';' +
      'box-shadow:0 2px 10px rgba(0,0,0,0.5);';
    painel.appendChild(temaGroup);
    painel.appendChild(velGroup);
    painel.appendChild(orbGroup);
    painel.appendChild(grupo3D);
    painel.appendChild(flashGroup);
    painel.appendChild(buscaGroup);
    painel.appendChild(tamGroup);
    layoutGroup.appendChild(btnReset);
    painel.appendChild(layoutGroup);
    
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: appending painel");
    }
document.body.appendChild(painel);

    // ---- Botao hide panel (olho) ----
    var painelToggle = mkEl('div');
    painelToggle.id = 'mk-painel-toggle';
    painelToggle.title = 'Ocultar/mostrar painel de controles';
    painelToggle.style.cssText =
      'position:fixed;top:22px;left:10px;z-index:99998;width:28px;height:28px;' +
      'border-radius:4px;cursor:pointer;display:flex;align-items:center;' +
      'justify-content:center;font-size:14px;user-select:none;' +
      'background:rgba(30,30,46,0.7);border:1px solid ' + cores.borda + ';';
    painelToggle.innerHTML = '\\u1F441'; // olho
    painelToggle._visivel = true;
    painelToggle.onclick = function() {
      painelToggle._visivel = !painelToggle._visivel;
      painel.style.display = painelToggle._visivel ? 'flex' : 'none';
      painelToggle.innerHTML = painelToggle._visivel ? '\\u1F441' : '\\u1F442';
    };
    document.body.appendChild(painelToggle);

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
      menuBtn.innerHTML = oculto ? '\\u2630' : '\\u2026';
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
  }
</script>
"""