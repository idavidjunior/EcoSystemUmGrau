import ForceGraph3D from 'force-graph-3d';
import * as THREE from 'three';

// ============ CONFIG ============
const BRIDGE_WS_URL = 'http://localhost:8765';
const BRIDGE_API_URL = 'http://localhost:8766';
const HALF_LIFE = {
  erro: 90,
  decisao: 30,
  padrao: 60,
  episodio: 7,
  preferencia: 365,
  experiencia: 180,
  melhoria: 120
};

const KIND_COLOR = {
  erro: '#ff4444',
  decisao: '#4488ff',
  padrao: '#44cc44',
  episodio: '#ffaa00',
  preferencia: '#aa44ff',
  experiencia: '#00cccc',
  melhoria: '#ff44aa'
};

const KIND_LABEL = {
  erro: 'Erro',
  decisao: 'Decisão',
  padrao: 'Padrão',
  episodio: 'Episódio',
  preferencia: 'Preferência',
  experiencia: 'Experiência',
  melhoria: 'Melhoria'
};

const KIND_SIZE = {
  erro: 7,
  decisao: 6.5,
  padrao: 6,
  episodio: 5.5,
  preferencia: 5,
  experiencia: 5.5,
  melhoria: 6
};

// ============ STATE ============
let allNodes = [];
let allLinks = [];
let graph = null;
let currentTimeFilter = 30;
let visibleKinds = new Set(Object.keys(KIND_COLOR));
let searchQuery = '';

// ============ DOM ELEMENTS ============
const graphContainer = document.getElementById('graph-container');
const statsEl = document.getElementById('stats');
const timeFilter = document.getElementById('timeFilter');
const timeFilterValue = document.getElementById('timeFilterValue');
const timeFilterDays = document.getElementById('timeFilterDays');
const kindFiltersEl = document.getElementById('kindFilters');
const searchInput = document.getElementById('searchInput');
const resetViewBtn = document.getElementById('resetView');
const exportGraphBtn = document.getElementById('exportGraph');
const tooltip = document.getElementById('tooltip');

// ============ UTILS ============
function decayScore(node, now = Date.now()) {
  const halfLife = HALF_LIFE[node.kind] || 14;
  const lastAcc = new Date(node.last_accessed || node.created_at).getTime();
  const days = (now - lastAcc) / 864e5;
  return Math.max(0.01, node.strength * Math.pow(0.5, days / halfLife));
}

function daysSinceLastAccess(node) {
  const lastAcc = new Date(node.last_accessed || node.created_at).getTime();
  return (Date.now() - lastAcc) / 864e5;
}

function buildLinks(nodes) {
  const links = [];
  const tagIndex = new Map();
  const projectIndex = new Map();
  
  nodes.forEach((n, i) => {
    n.tags?.forEach(tag => {
      if (!tagIndex.has(tag)) tagIndex.set(tag, []);
      tagIndex.get(tag).push(i);
    });
    if (n.project) {
      if (!projectIndex.has(n.project)) projectIndex.set(n.project, []);
      projectIndex.get(n.project).push(i);
    }
  });
  
  // Links por tags compartilhadas (peso = tags em comum)
  tagIndex.forEach((indices, tag) => {
    if (indices.length > 1) {
      for (let i = 0; i < indices.length; i++) {
        for (let j = i + 1; j < indices.length; j++) {
          const existing = links.find(l => 
            (l.source === indices[i] && l.target === indices[j]) ||
            (l.source === indices[j] && l.target === indices[i])
          );
          if (existing) {
            existing.weight = (existing.weight || 1) + 1;
          } else {
            links.push({ source: indices[i], target: indices[j], weight: 1, type: 'tag', tag });
          }
        }
      }
    }
  });
  
  // Links por projeto (peso menor)
  projectIndex.forEach((indices, project) => {
    if (indices.length > 1) {
      for (let i = 0; i < indices.length; i++) {
        for (let j = i + 1; j < indices.length; j++) {
          const existing = links.find(l => 
            (l.source === indices[i] && l.target === indices[j]) ||
            (l.source === indices[j] && l.target === indices[i])
          );
          if (existing) {
            existing.weight = (existing.weight || 1) + 0.5;
          } else {
            links.push({ source: indices[i], target: indices[j], weight: 0.5, type: 'project', project });
          }
        }
      }
    }
  });
  
  return links;
}

function filterNodes() {
  const now = Date.now();
  return allNodes.filter(n => {
    // Filtro temporal
    const days = daysSinceLastAccess(n);
    if (days > currentTimeFilter) return false;
    
    // Filtro por decay score mínimo
    const score = decayScore(n, now);
    if (score < 0.05) return false;
    
    // Filtro por kind
    if (!visibleKinds.has(n.kind)) return false;
    
    // Filtro por busca
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const inTitle = n.title.toLowerCase().includes(q);
      const inSummary = n.summary.toLowerCase().includes(q);
      const inTags = n.tags?.some(t => t.toLowerCase().includes(q));
      const inProject = n.project?.toLowerCase().includes(q);
      if (!inTitle && !inSummary && !inTags && !inProject) return false;
    }
    
    return true;
  });
}

function filterLinks(links, filteredNodes) {
  const ids = new Set(filteredNodes.map(n => n.id));
  return links.filter(l => ids.has(l.source) && ids.has(l.target));
}

function updateStats() {
  const filtered = filterNodes();
  const filteredLinks = filterLinks(allLinks, filtered);
  statsEl.textContent = `${filtered.length} nós · ${filteredLinks.length} conexões · ${allNodes.length} total`;
}

function updateGraph() {
  const filteredNodes = filterNodes();
  const filteredLinks = filterLinks(allLinks, filteredNodes);
  
  // Atualiza decayScore nos nós filtrados
  const now = Date.now();
  filteredNodes.forEach(n => {
    n.decayScore = decayScore(n, now);
    n.color = KIND_COLOR[n.kind] || '#888';
    n.size = KIND_SIZE[n.kind] || 4;
    n.label = n.decayScore > 0.3 ? n.title : '';
  });
  
  graph.graphData({ nodes: filteredNodes, links: filteredLinks });
  updateStats();
}

function createKindFilters() {
  kindFiltersEl.innerHTML = '';
  Object.entries(KIND_COLOR).forEach(([kind, color]) => {
    const btn = document.createElement('div');
    btn.className = 'kind-filter active';
    btn.dataset.kind = kind;
    btn.innerHTML = `<span class="dot" style="background:${color}"></span>${KIND_LABEL[kind]}`;
    btn.onclick = () => {
      if (visibleKinds.has(kind)) {
        visibleKinds.delete(kind);
        btn.classList.remove('active');
      } else {
        visibleKinds.add(kind);
        btn.classList.add('active');
      }
      updateGraph();
      debouncedSave();
    };
    kindFiltersEl.appendChild(btn);
  });
}

// ============ STATE PERSISTENCE ============
async function loadState() {
  try {
    const res = await fetch(`${BRIDGE_API_URL}/api/ecow/state`);
    if (res.ok) {
      const data = await res.json();
      const state = data.state || {};
      
      if (state.timeFilter !== undefined) {
        currentTimeFilter = state.timeFilter;
        timeFilter.value = currentTimeFilter;
        timeFilterValue.textContent = `${currentTimeFilter} dias`;
        timeFilterDays.textContent = currentTimeFilter;
      }
      if (state.visibleKinds) {
        visibleKinds = new Set(state.visibleKinds);
        // Update UI checkboxes
        kindFiltersEl.querySelectorAll('.kind-filter').forEach(btn => {
          const kind = btn.dataset.kind;
          if (visibleKinds.has(kind)) {
            btn.classList.add('active');
          } else {
            btn.classList.remove('active');
          }
        });
      }
      if (state.searchQuery) {
        searchQuery = state.searchQuery;
        searchInput.value = searchQuery;
      }
      if (state.cameraPosition && graph) {
        // Will apply after graph init
        setTimeout(() => {
          if (graph) {
            graph.cameraPosition(
              state.cameraPosition,
              { x: 0, y: 0, z: 0 },
              0
            );
          }
        }, 100);
      }
    }
  } catch (err) {
    console.warn('Failed to load EcoW state:', err);
  }
}

async function saveState() {
  if (!graph) return;
  
  const cam = graph.camera();
  const state = {
    timeFilter: currentTimeFilter,
    visibleKinds: Array.from(visibleKinds),
    searchQuery: searchQuery,
    cameraPosition: {
      x: cam.position.x,
      y: cam.position.y,
      z: cam.position.z
    }
  };
  
  try {
    await fetch(`${BRIDGE_API_URL}/api/ecow/state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state })
    });
  } catch (err) {
    console.warn('Failed to save EcoW state:', err);
  }
}

// Debounced save
let saveTimeout = null;
function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(saveState, 500);
}

// ============ FETCH DATA ============
async function loadMemories() {
  try {
    // Load saved state first
    await loadState();
    
    const res = await fetch(`${BRIDGE_API_URL}/api/memories?limit=200`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    allNodes = data.nodes || [];
    allLinks = data.links || buildLinks(allNodes);
    
    // Garante IDs numéricos
    allNodes.forEach((n, i) => { if (n.id === undefined) n.id = i; });
    
    initGraph();
    createKindFilters();
    updateGraph();
  } catch (err) {
    console.error('Erro ao carregar memórias:', err);
    statsEl.textContent = 'Erro ao conectar no bridge. Verifique se jarvis_bridge.py está rodando na porta 8765.';
    statsEl.style.color = '#ff4444';
  }
}

// ============ GRAPH INIT ============
function initGraph() {
  graph = ForceGraph3D()(graphContainer)
    .backgroundColor('#0a0e17')
    .nodeColor(n => n.color)
    .nodeRelSize(n => n.size)
    .nodeLabel(n => n.label)
    .nodeLabelVisibility(true)
    .nodeLabelColor('#e8eaed')
    .nodeLabelFont('12px monospace')
    .nodeThreeObjectExtend(true)
    .nodeThreeObject(node => {
      // Geometria customizada por kind
      const geometry = new THREE.IcosahedronGeometry(1, 0);
      const material = new THREE.MeshBasicMaterial({
        color: node.color,
        transparent: true,
        opacity: 0.9
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.scale.setScalar(node.size * 0.8);
      return mesh;
    })
    .linkColor(l => l.type === 'tag' ? '#4488ff44' : '#44cc4444')
    .linkWidth(l => Math.max(0.5, (l.weight || 1) * 1.5))
    .linkOpacity(0.4)
    .d3Force('link')
      .id(d => d.id)
      .distance(120)
      .strength(0.8)
    .d3Force('charge')
      .strength(-400)
    .d3Force('center')
      .x(0).y(0).z(0)
    .d3AlphaDecay(0.02)
    .d3VelocityDecay(0.4)
    .useWebWorkers(true)
    .onNodeClick(node => {
      // Click: abre arquivo no editor
      if (node.filePath) {
        fetch(`${BRIDGE_API_URL}/open-file`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: node.filePath })
        }).catch(console.error);
      }
      // Animação de câmera para o nó
      graph.cameraPosition(
        { x: node.x * 1.5, y: node.y * 1.5, z: node.z * 1.5 },
        node,
        800
      );
    })
    .onNodeHover(node => {
      // Hover: tooltip rico
      if (!node) {
        tooltip.classList.remove('visible');
        return;
      }
      
      const score = decayScore(node);
      const days = daysSinceLastAccess(node);
      
      tooltip.innerHTML = `
        <div class="title">${node.title}</div>
        <div>${node.summary.slice(0, 180)}${node.summary.length > 180 ? '...' : ''}</div>
        <div class="meta">
          <span class="kind-badge kind-${node.kind}">${KIND_LABEL[node.kind]}</span>
          <span>Decay: ${(score * 100).toFixed(0)}%</span>
          <span>Último acesso: ${days.toFixed(1)} dias</span>
          ${node.project ? `<span>Projeto: ${node.project}</span>` : ''}
          ${node.tags?.length ? `<span>Tags: ${node.tags.slice(0, 5).join(', ')}${node.tags.length > 5 ? '...' : ''}</span>` : ''}
        </div>
      `;
      
      tooltip.classList.add('visible');
      positionTooltip(node);
    })
    .onNodeDragEnd(node => {
      // Fix position after drag
      node.fx = node.x;
      node.fy = node.y;
      node.fz = node.z;
    });

  // Controles de câmera suaves
  graph.controls().enableDamping = true;
  graph.controls().dampingFactor = 0.05;
  graph.controls().rotateSpeed = 0.5;
  graph.controls().zoomSpeed = 1.2;
  graph.controls().panSpeed = 0.8;
  
  // Save camera position on change (debounced)
  graph.controls().addEventListener('change', debouncedSave);
}

function positionTooltip(node) {
  // Converte posição 3D para 2D na tela
  const vector = new THREE.Vector3(node.x, node.y, node.z);
  vector.project(graph.camera());
  
  const x = (vector.x * 0.5 + 0.5) * window.innerWidth;
  const y = (-vector.y * 0.5 + 0.5) * window.innerHeight;
  
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y - 20}px`;
}

// ============ EVENT LISTENERS ============
timeFilter.addEventListener('input', e => {
  currentTimeFilter = +e.target.value;
  timeFilterValue.textContent = `${currentTimeFilter} dias`;
  timeFilterDays.textContent = currentTimeFilter;
  updateGraph();
  debouncedSave();
});

searchInput.addEventListener('input', e => {
  searchQuery = e.target.value.trim();
  updateGraph();
  debouncedSave();
});

resetViewBtn.addEventListener('click', () => {
  graph.cameraPosition({ x: 0, y: 0, z: 500 }, { x: 0, y: 0, z: 0 }, 1000);
  debouncedSave();
});

exportGraphBtn.addEventListener('click', () => {
  const filteredNodes = filterNodes();
  const filteredLinks = filterLinks(allLinks, filteredNodes);
  const data = { nodes: filteredNodes, links: filteredLinks };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ecow-graph-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

// Fecha tooltip ao clicar fora
document.addEventListener('click', e => {
  if (!tooltip.contains(e.target)) {
    tooltip.classList.remove('visible');
  }
});

// Redimensiona canvas
window.addEventListener('resize', () => {
  if (graph) graph.width(window.innerWidth).height(window.innerHeight);
});

// ============ INIT ============
loadMemories();