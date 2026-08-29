/* TerminalWidget — terminal de logs em tempo real (Vanilla JS, sem build).
   Conexão WebSocket ws://127.0.0.1:8765/logs (bridge) com fallback polling
   http://127.0.0.1:8766/api/logs. Uso:
     var tw = new TerminalWidget({hospedeiro: el, cor: '#00ff00', buffer: 100});
     tw.conectar();
     tw.limpar(); tw.destruir(); */
(function(global){
  'use strict';

  var WS_URL  = 'ws://127.0.0.1:8765/logs';
  var HTTP_URL = 'http://127.0.0.1:8766/api/logs';
  var LOGS_PADRAO = ['bridge','narrador','edge','dialogo','preflight'];

  var CLI = {
    ws: null,
    intentoFechado: false,
  };

  var RUIDO = /(:\s*connection (open|closed)$|websockets\.server|websockets\.client|HTTP connection|PING|health-check)/i;

  function escapar(t){
    return String(t == null ? '' : t)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function nivelDeLinha(texto){
    var t = String(texto || '');
    if (/erro|error|falha|FATAL|CRITICAL|CRITICO|traceback|exception/i.test(t)) return 'erro';
    if (/aviso|warn|warning|aten|ALERT/i.test(t)) return 'aviso';
    if (/info|websockets/i.test(t)) return 'info';
    return null;
  }

  function ehRuido(nome, texto){
    var t = String(texto || '');
    if (/bridge/i.test(nome) && /websockets\.(server|client)/i.test(t)) return true;
    return RUIDO.test(t);
  }

  function horaDinamica(){
    var d = new Date(), p = function(n){ return (n < 10 ? '0' : '') + n; };
    return p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
  }

  function igualSets(a, b){
    if (a.length !== b.length) return false;
    return a.every(function(x){ return b.indexOf(x) >= 0; });
  }

  function TerminalWidget(opts){
    opts = opts || {};
    this.hospedeiro = opts.hospedeiro || null;
    this.cor = opts.cor || '#00ff00';
    this.buffer = opts.buffer || 100;
    this.arquivos = (opts.arquivos || LOGS_PADRAO).slice();
    this.onFechar = opts.onFechar || null;
    this._linhas = [];
    this._raf = null;
    this._tempo = null;
    this._backoff = 1000;
    this._falhas = 0;
    this._poll = null;
    this.status = 'parado';
    this._desde = Date.now();
    this._construir();
  }

  TerminalWidget.prototype._construir = function(){
    var self = this;
    if (!this.hospedeiro) return;
    var c = this.hospedeiro;
    c.classList.add('tw');
    c.setAttribute('data-tw', '1');
    c.style.setProperty('--tw-cor', this.cor);
    c.innerHTML =
      '<div class="tw-barra">' +
        '<span class="tw-titulo">logs &#8212; eco</span>' +
        '<span class="tw-legenda" title="Logs em tempo real do ecossistema. Fontes: bridge, narrador, edge, dialogo, preflight. Ultima linha no topo, buffer de 70.">&#9658; feed vivo, ultimo no topo</span>' +
        '<span class="tw-contador">0</span>' +
        '<span class="tw-status" data-status="parado">parado</span>' +
        '<span class="tw-cursor">&#9608;</span>' +
        '<button class="tw-botao" data-acao="limpar" title="Limpar">limpar</button>' +
        '<button class="tw-botao" data-acao="fechar" title="Fechar">&#10005;</button>' +
      '</div>' +
      '<div class="tw-tela"></div>';
    this._elBarra = c.querySelector('.tw-barra');
    this._elContador = this._elBarra.querySelector('.tw-contador');
    this._elStatus = this._elBarra.querySelector('.tw-status');
    this._elTela = c.querySelector('.tw-tela');
    this._elTela.addEventListener('click', function(e){
      var bt = e.target.closest && e.target.closest('[data-acao]');
      if (bt && bt.getAttribute('data-acao') === 'limpar') self.limpar();
    });
    this._elBarra.addEventListener('click', function(e){
      var bt = e.target.closest && e.target.closest('[data-acao]');
      if (bt && bt.getAttribute('data-acao') === 'fechar'){
        if (self.onFechar) self.onFechar();
        else self.destruir();
      }
    });
  };

  TerminalWidget.prototype._definirStatus = function(st){
    this.status = st;
    if (this._elStatus){
      this._elStatus.setAttribute('data-status', st);
      this._elStatus.textContent = ({
        parado:'parado', conectando:'conectando', online:'online',
        reconectando:'reconectando', polling:'polling', erro:'erro'
      })[st] || st;
    }
  };

  TerminalWidget.prototype._push = function(linhas){
    if (!linhas || !linhas.length) return;
    var self = this;
    this._linhas.push.apply(this._linhas, linhas);
    if (this._linhas.length > this.buffer){
      this._linhas.splice(0, this._linhas.length - this.buffer);
    }
    if (this._elContador) this._elContador.textContent = this._linhas.length;
    if (!this._raf){
      this._raf = requestAnimationFrame(function(){ self._render(); });
    }
  };

  TerminalWidget.prototype._criarLinha = function(linha){
    var nivel = nivelDeLinha(linha.texto);
    var nome = '<span class="tw-nome">' + escapar(linha.nome) + '</span>';
    var ts = linha.ts ? '<span class="tw-ts">' + escapar(linha.ts) + '</span> ' : '';
    var cls = nivel ? 'tw-linha tw-' + nivel : 'tw-linha';
    var div = document.createElement('div');
    div.className = cls;
    div.innerHTML = ts + nome + ' ' + escapar(linha.texto);
    return div;
  };

  TerminalWidget.prototype._render = function(){
    this._raf = null;
    if (!this._elTela) return;
    var noTopo = this._elTela.scrollTop < 24;
    var frag = document.createDocumentFragment();
    var linhas = this._linhas;
    for (var i = linhas.length - 1; i >= 0; i--){
      frag.appendChild(this._criarLinha(linhas[i]));
    }
    this._elTela.innerHTML = '';
    this._elTela.appendChild(frag);
    if (linhas.length === 0){
      var vazio = document.createElement('div');
      vazio.className = 'tw-vazio';
      vazio.textContent = 'sem linhas recebidas ainda';
      this._elTela.appendChild(vazio);
    }
    if (noTopo) this._elTela.scrollTop = 0;
  };

  TerminalWidget.prototype._parserLinha = function(nome, texto){
    /* tenta "YYYY-MM-DD HH:MM:SS,mmm LVL:resto" -> {ts, texto} */
    var m = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})[,\s].*?:\s*(.+)$/.exec(texto);
    if (m) return {ts: m[1], texto: m[2]};
    return {ts: null, texto: texto};
  };

  TerminalWidget.prototype._ingerir = function(nome, textos){
    var self = this;
    var out = [];
    (textos || []).forEach(function(t){
      if (ehRuido(nome, t)) return;
      var p = self._parserLinha(nome, t);
      out.push({nome: nome, ts: p.ts, texto: p.texto});
    });
    this._push(out);
  };

  TerminalWidget.prototype._slides = function(snap){
    for (var nome in snap){
      var s = snap[nome];
      if (s && s.linhas) this._ingerir(nome, s.linhas);
    }
  };

  TerminalWidget.prototype.conectar = function(){
    var self = this;
    if (!this.hospedeiro) return;
    if (this._ws) return;
    CLI.intentoFechado = false;
    this._definirStatus('conectando');
    var ws;
    try { ws = new WebSocket(WS_URL); }
    catch(e){ this._falhaAgora(); return; }
    this._ws = ws;
    ws.onopen = function(){
      self._falhas = 0;
      self._backoff = 1000;
      self._definirStatus('online');
      ws.send(JSON.stringify({tipo:'log_subscribe', arquivos: self.arquivos}));
    };
    ws.onmessage = function(ev){
      var msg;
      try { msg = JSON.parse(ev.data); }
      catch(e){ return; }
      if (msg.type === 'log_snapshot' && msg.logs) self._slides(msg.logs);
      else if (msg.type === 'log_lines' && msg.linhas){
        for (var nome in msg.linhas) self._ingerir(nome, msg.linhas[nome]);
      }
    };
    ws.onclose = function(){
      self._ws = null;
      self._agendarReconexao();
    };
    ws.onerror = function(){
      try { ws.close(); } catch(e){}
    };
  };

  TerminalWidget.prototype._agendarReconexao = function(){
    var self = this;
    if (this._poll || CLI.intentoFechado) return;
    this._falhas += 1;
    if (this._falhas >= 3){
      this._ligarPolling();
      return;
    }
    this._definirStatus('reconectando');
    clearTimeout(this._tempo);
    this._tempo = setTimeout(function(){ self.conectar(); }, this._backoff);
    this._backoff = Math.min(this._backoff * 2, 10000);
  };

  TerminalWidget.prototype._ligarPolling = function(){
    var self = this;
    if (this._poll) return;
    this._definirStatus('polling');
    this._poll = setInterval(function(){
      var arquivos = encodeURIComponent(self.arquivos.join(','));
      fetch(HTTP_URL + '?arquivos=' + arquivos + '&linhas=' + self.buffer)
        .then(function(r){ return r.json(); })
        .then(function(data){
          if (data && data.ok && data.logs) self._slides(data.logs);
        })
        .catch(function(){});
    }, 2000);
    /* segue tentando o WS; se voltar, desliga o polling */
    this._tempo = setTimeout(function(){
      if (!self._ws && !CLI.intentoFechado) self.conectar();
    }, 5000);
  };

  TerminalWidget.prototype._falhaAgora = function(){
    this._ws = null;
    this._agendarReconexao();
  };

  TerminalWidget.prototype.limpar = function(){
    this._linhas = [];
    if (this._elTela) this._elTela.innerHTML = '';
  };

  TerminalWidget.prototype.destruir = function(){
    CLI.intentoFechado = true;
    clearTimeout(this._tempo);
    if (this._poll){ clearInterval(this._poll); this._poll = null; }
    if (this._ws){ try{ this._ws.close(); }catch(e){} this._ws = null; }
    if (this._raf){ cancelAnimationFrame(this._raf); this._raf = null; }
    if (this.hospedeiro){
      this.hospedeiro.classList.remove('aberto');
      this.hospedeiro.innerHTML = '';
    }
    this._definirStatus('parado');
  };

  global.TerminalWidget = TerminalWidget;
})(window);