<script>
(function(){
  function ensureHandle(){
    var handle = document.getElementById('mk-resize');
    if (!handle) {
      handle = document.createElement('div');
      handle.id = 'mk-resize';
      document.body.appendChild(handle);
    }
    return handle;
  }
  function updateHandle(){
    var handle = ensureHandle();
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
  updateHandle();
  window.addEventListener('resize', updateHandle);
})();
</script>