/**
 * Widget JS - Init Controls
 * Injected into <head> for early initialization
 */
(function(){
  function initWidgetControls() {
    if (document.getElementById('mk-controles')) return;
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.test_bridge === 'function') {
      try {
        window.pywebview.api.test_bridge().catch(function(err) {
          console.warn('[widget] test_bridge error:', err);
        });
      } catch (e) {
        console.warn('[widget] initWidgetControls error:', e);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidgetControls, { once: true });
  } else {
    initWidgetControls();
  }

  window.addEventListener('pywebviewready', initWidgetControls, { once: true });
})();