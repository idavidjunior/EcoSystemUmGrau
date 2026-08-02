'use strict';
const fs = require('fs');
const path = require('path');
const { McpServer } = require('../lib/mcp-core');

const ECO_ROOT = process.env.ECO_ROOT || 'C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau';

function safeResolve(p) {
  if (!p) return ECO_ROOT;
  const abs = path.isAbsolute(p) ? p : path.join(ECO_ROOT, p);
  const rel = path.relative(ECO_ROOT, abs);
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    const err = new Error(`Forbidden: path outside ecosystem root: ${p}`);
    err.code = 'EACCES';
    throw err;
  }
  return abs;
}

function listRecursive(root, depth, maxDepth) {
  if (depth > maxDepth) return [];
  const out = [];
  let entries = [];
  try {
    entries = fs.readdirSync(root, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    if (e.name === 'node_modules' || e.name === '.git' || e.name === '.obsidian') continue;
    const full = path.join(root, e.name);
    out.push({ name: e.name, type: e.isDirectory() ? 'directory' : 'file', path: full });
    if (e.isDirectory()) out.push(...listRecursive(full, depth + 1, maxDepth));
  }
  return out;
}

const tools = [
  {
    name: 'list-dir',
    description: 'List directory contents under the ecosystem root.',
    inputSchema: { type: 'object', properties: { path: { type: 'string' }, recursive: { type: 'boolean' } } },
    async handler(args) {
      const abs = safeResolve(args.path);
      if (args.recursive) {
        const items = listRecursive(abs, 0, 6);
        return JSON.stringify({ count: items.length, items: items.map(i => `${i.type}: ${i.path}`).slice(0, 500) }, null, 2);
      }
      const entries = fs.readdirSync(abs, { withFileTypes: true });
      return entries.map(e => (e.isDirectory() ? '[dir] ' : '[file] ') + e.name).join('\n');
    },
  },
  {
    name: 'read-file',
    description: 'Read a text file inside the ecosystem root.',
    inputSchema: { type: 'object', properties: { path: { type: 'string' }, offset: { type: 'number' }, limit: { type: 'number' } } },
    async handler(args) {
      const abs = safeResolve(args.path);
      const maxLines = args.limit || 2000;
      const content = fs.readFileSync(abs, 'utf8');
      const lines = content.split('\n');
      const start = args.offset || 0;
      const slice = lines.slice(start, start + maxLines);
      return slice.join('\n') + (lines.length > start + maxLines ? `\n... (${lines.length} total lines)` : '');
    },
  },
  {
    name: 'write-file',
    description: 'Write/overwrite a text file inside the ecosystem root. Creates parent dirs.',
    inputSchema: { type: 'object', properties: { path: { type: 'string' }, content: { type: 'string' } }, required: ['path', 'content'] },
    async handler(args) {
      const abs = safeResolve(args.path);
      fs.mkdirSync(path.dirname(abs), { recursive: true });
      fs.writeFileSync(abs, args.content, 'utf8');
      return `Written ${Buffer.byteLength(args.content, 'utf8')} bytes to ${abs}`;
    },
  },
  {
    name: 'file-exists',
    description: 'Check whether a file or directory exists under the ecosystem root.',
    inputSchema: { type: 'object', properties: { path: { type: 'string' } }, required: ['path'] },
    async handler(args) {
      const abs = safeResolve(args.path);
      const exists = fs.existsSync(abs);
      let type = null;
      if (exists) type = fs.statSync(abs).isDirectory() ? 'directory' : 'file';
      return JSON.stringify({ path: abs, exists, type });
    },
  },
  {
    name: 'search-in-files',
    description: 'Grep-like search for a string in text files under the ecosystem root.',
    inputSchema: { type: 'object', properties: { pattern: { type: 'string' }, dir: { type: 'string' } }, required: ['pattern'] },
    async handler(args) {
      const abs = safeResolve(args.dir || '');
      const re = new RegExp(args.pattern, 'i');
      const hits = [];
      const walk = (root, depth) => {
        if (depth > 8) return;
        let entries;
        try { entries = fs.readdirSync(root, { withFileTypes: true }); } catch { return; }
        for (const e of entries) {
          if (e.name === 'node_modules' || e.name === '.git' || e.name === '.obsidian') continue;
          const full = path.join(root, e.name);
          if (e.isDirectory()) { walk(full, depth + 1); continue; }
          if (!/\.(md|json|jsonc|js|ts|py|ps1|bat|kt|java|xml|gradle|txt|yml|yaml|html|css|ps1)$/i.test(e.name)) continue;
          try {
            const text = fs.readFileSync(full, 'utf8');
            const lines = text.split('\n');
            lines.forEach((line, i) => {
              if (re.test(line)) hits.push(`${path.relative(abs, full)}:${i + 1}: ${line.trim().slice(0, 200)}`);
            });
          } catch { /* binary/undecodable */ }
        }
      };
      walk(abs, 0);
      return hits.slice(0, 200).join('\n') || `No matches for: ${args.pattern}`;
    },
  },
];

const server = new McpServer({
  name: 'eco-filesystem',
  version: '1.0.0',
  tools,
  extraCapabilities: { filesystem: {} },
});

server.listen();
