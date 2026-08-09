<script>
(function(){
  window.__widgetApiPoll = window.__widgetApiPoll || {
    lastTs: '',
    tick: function(){
      try {
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.perguntar === 'function') {
          window.pywebview.api.perguntar(this.lastTs).then(function(resp){
            if (resp && resp.ts) {
              this.lastTs = resp.ts;
              if (resp.changed) {
                // Vault mudou: recarrega a página para regenerar o grafo
                window.location.reload();
              }
            }
          }.bind(this)).catch(function(err) {
            console.warn('[widget] perguntar error:', err);
          });
        }
      } catch (e) {
        console.warn('[widget] tick error:', e);
      }
    }
  };
  setInterval(function(){ window.__widgetApiPoll.tick(); }, %POLL_MS%);
})();
</script>