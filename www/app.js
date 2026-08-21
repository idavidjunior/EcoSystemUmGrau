// widget_edge.js - Lógica do widget Edge
// Comunicação com backend Python via window.pywebbridge

// Estado do widget
const widgetState = {
  volume: 50,
  sleepTimer: 0,
  voiceActive: false,
  dots: { narr: false, tts: false, bridge: false }
};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
  // Bind eventos para controles da interface
  const volSelect = document.getElementById('volSlider');
  if (volSelect) {
    volSelect.addEventListener('change', function() {
      const val = parseInt(this.value);
      if (window.pywebbridge && typeof window.pywebbridge.setVolume === 'function') {
        window.pywebbridge.setVolume(val);
      }
    });
  }
  
  const sleepSelect = document.getElementById('sleepTimer');
  if (sleepSelect) {
    sleepSelect.addEventListener('change', function() {
      const val = parseInt(this.value);
      if (window.pywebbridge && typeof window.pywebbridge.setSleep === 'function') {
        window.pywebbridge.setSleep(val);
      }
    });
  }
  
  const btnVoz = document.getElementById('btnVoz');
  if (btnVoz) {
    btnVoz.addEventListener('click', function() {
      widgetState.voiceActive = !widgetState.voiceActive;
      this.classList.toggle('on', widgetState.voiceActive);
      if (window.pywebbridge && typeof window.pywebbridge.voiceToggle === 'function') {
        window.pywebbridge.voiceToggle();
      }
    });
  }
  
  // Atualização periódica de estado (a cada 3s)
  setInterval(function() {
    // Solicitar estado atual ao backend
    if (window.pywebbridge && typeof window.pywebbridge.getState === 'function') {
      window.pywebbridge.getState(function(state) {
        if (state) {
          widgetState.volume = state.volume || 50;
          widgetState.sleepTimer = state.sleepTimer || 0;
          widgetState.voiceActive = state.voiceActive || false;
          
          // Atualizar indicadores visuais
          const dots = widgetState.dots;
          if (window.pywebbridge && typeof window.pywebbridge.updateDots === 'function') {
            window.pywebbridge.updateDots(dots);
          }
        }
      });
    }
  }, 3000);
});

// Funções auxiliares para abertura/fechamento
function widgetMinimize() {
  if (window.pywebbridge && typeof window.pywebbridge.minimize === 'function') {
    window.pywebbridge.minimize();
  }
}

function widgetClose() {
  if (window.pywebbridge && typeof window.pywebbridge.close === 'function') {
    window.pywebbridge.close();
  }
}

// Expor funções globals para o Python (se necessário)
window.pywebbridge = widgetState;
// Expor estado para inspeção externa
window.widgetState = widgetState;