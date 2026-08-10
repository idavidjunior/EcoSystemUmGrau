<script>
(function(){
  var MIN_W = 400, MIN_H = 300;
  function api(){
    return (window.pywebview && window.pywebview.api) ? window.pywebview.api : null;
  }
  function ensureDragBar(){
    var bar = document.getElementById('mk-drag');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'mk-drag';
      bar.title = 'Arraste para mover a janela';
      document.body.appendChild(bar);
    }
    return bar;
  }
  function ensureResizeHandle(){
    var handle = document.getElementById('mk-resize');
    if (!handle) {
      handle = document.createElement('div');
      handle.id = 'mk-resize';
      document.body.appendChild(handle);
    }
    return handle;
  }
  function updateHandle(){
    var handle = ensureResizeHandle();
    handle.style.position = 'fixed';
    handle.style.right = '0px';
    handle.style.bottom = '0px';
    handle.style.width = '18px';
    handle.style.height = '18px';
    handle.style.display = 'block';
    handle.style.zIndex = '10001';
    handle.style.cursor = 'nwse-resize';
    handle.style.background = 'rgba(203,166,247,0.15)';
    handle.style.borderTop = '2px solid rgba(203,166,247,0.4)';
    handle.style.borderLeft = '2px solid rgba(203,166,247,0.4)';
  }
  function initDrag(){
    var bar = ensureDragBar();
    bar.addEventListener('mousedown', function(ev){
      if (ev.button !== 0) return;
      ev.preventDefault();
      var sx = ev.screenX, sy = ev.screenY;
      var wx = window.screenX || 0, wy = window.screenY || 0;
      function onMove(me){
        var a = api();
        if (a && a.mover) a.mover(wx + (me.screenX - sx), wy + (me.screenY - sy));
      }
      function onUp(){
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
      }
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    });
  }
  function initResize(){
    var handle = ensureResizeHandle();
    handle.addEventListener('mousedown', function(ev){
      if (ev.button !== 0) return;
      ev.preventDefault();
      var sx = ev.screenX, sy = ev.screenY;
      var sw = window.innerWidth, sh = window.innerHeight;
      function onMove(me){
        var a = api();
        if (a && a.redimensionar) {
          var w = Math.max(MIN_W, sw + (me.screenX - sx));
          var h = Math.max(MIN_H, sh + (me.screenY - sy));
          a.redimensionar(w, h);
        }
      }
      function onUp(){
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
      }
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    });
  }
  updateHandle();
  initDrag();
  initResize();
  window.addEventListener('resize', updateHandle);
})();
</script>
