'use strict';
const fs = require('fs');
const path = require('path');
const { McpServer } = require('../lib/mcp-core');

const ECO_ROOT = process.env.ECO_ROOT || 'C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau';

const SOURCES = [
  { name: 'knowledge-graph', file: path.join(ECO_ROOT, 'ler-runtime', 'knowledge', 'knowledge_graph.json') },
  { name: 'conhecimento', file: path.join(ECO_ROOT, 'ler-runtime', 'CONHECIMENTO.md') },
  { name: 'memorias', file: path.join(ECO_ROOT, 'conhecimento', 'memoria', 'memories.json') },
  { name: 'habilidades', dir: path.join(ECO_ROOT, 'Habilidades') },
  { name: 'aprendizados', dir: path.join(ECO_ROOT, 'conhecimento', 'aprendizados') },
  { name: 'notas', dir: path.join(ECO_ROOT, 'conhecimento', 'notas') },
];

function tokenize(text) {
  return (text || '').toLowerCase().split(/[^a-z0-9à-ÿ]+/i).filter(w => w.length > 1);
}

function readSources() {
  const docs = [];
  for (const src of SOURCES) {
    if (src.file) {
      try {
        const raw = fs.readFileSync(src.file, 'utf8');
        docs.push({ name: src.name, path: src.file, text: raw });
      } catch { /* missing */ }
      continue;
    }
    if (src.dir && fs.existsSync(src.dir)) {
      const walk = (root, depth) => {
        if (depth > 6) return;
        let entries;
        try { entries = fs.readdirSync(root, { withFileTypes: true }); } catch { return; }
        for (const e of entries) {
          if (e.name === 'node_modules' || e.name === '.git') continue;
          const full = path.join(root, e.name);
          if (e.isDirectory()) { walk(full, depth + 1); continue; }
          if (!/\.(md|json|jsonc|py|txt)$/i.test(e.name)) continue;
          try { docs.push({ name: src.name, path: full, text: fs.readFileSync(full, 'utf8') }); }
          catch { /* skip */ }
        }
      };
      walk(src.dir, 0);
    }
  }
  return docs;
}

function searchDocs(docs, query) {
  const qTokens = new Set(tokenize(query));
  if (qTokens.size === 0) return [];
  const results = [];
  for (const doc of docs) {
    const text = doc.text;
    const lines = text.split('\n');
    let score = 0;
    const excerpts = [];
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineTokens = tokenize(line);
      let lineScore = 0;
      for (const tok of qTokens) {
        if (lineTokens.includes(tok)) lineScore += 1;
      }
      if (lineScore > 0) {
        score += lineScore;
        excerpts.push({ line: i + 1, text: line.trim().slice(0, 300) });
      }
    }
    if (score > 0) {
      results.push({ source: doc.name, path: doc.path, score, excerpts: excerpts.slice(0, 10) });
    }
  }
  results.sort((a, b) => b.score - a.score);
  return results.slice(0, 20);
}

const tools = [
  {
    name: 'semantic-search',
    description: 'BM25-style semantic search over knowledge graph, CONHECIMENTO.md, memories, Habilidades, aprendizados and notas.',
    inputSchema: { type: 'object', properties: { query: { type: 'string' }, limit: { type: 'number' } }, required: ['query'] },
    async handler(args) {
      const docs = readSources();
      const results = searchDocs(docs, args.query);
      const limit = args.limit || 20;
      if (results.length === 0) return `No results for: ${args.query}`;
      const lines = [];
      for (const r of results.slice(0, limit)) {
        lines.push(`[${r.source}] ${r.path} (score ${r.score})`);
        for (const ex of r.excerpts) lines.push(`  ${ex.line}: ${ex.text}`);
      }
      return lines.join('\n');
    },
  },
  {
    name: 'search-overview',
    description: 'Count documents and give a summary of each knowledge source available for search.',
    inputSchema: { type: 'object', properties: {} },
    async handler() {
      const docs = readSources();
      const bySource = {};
      for (const d of docs) bySource[d.source || 'unknown'] = (bySource[d.source || 'unknown'] || 0) + 1;
      return JSON.stringify(bySource, null, 2) + '\nTotal: ' + docs.length;
    },
  },
];

const server = new McpServer({
  name: 'eco-search',
  version: '1.0.0',
  tools,
});

server.listen();
