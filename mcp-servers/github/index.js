'use strict';
const { exec } = require('child_process');
const { McpServer } = require('../lib/mcp-core');

function gh(args, timeoutMs) {
  return new Promise((resolve) => {
    exec(`gh ${args}`, { timeout: timeoutMs || 30000, encoding: 'utf8' }, (err, stdout, stderr) => {
      const code = err ? (err.code ?? 1) : 0;
      resolve({ code, stdout: (stdout || '').slice(0, 20000), stderr: (stderr || '').slice(0, 20000) });
    });
  });
}

const tools = [
  {
    name: 'gh-auth-status',
    description: 'Check GitHub CLI authentication status.',
    inputSchema: { type: 'object', properties: {} },
    async handler() {
      const r = await gh('auth status');
      return JSON.stringify({ authenticated: r.code === 0, output: (r.stdout + r.stderr).trim() }, null, 2);
    },
  },
  {
    name: 'gh-repo-list',
    description: 'List repos of the authenticated GitHub user (default: idavidjunior).',
    inputSchema: { type: 'object', properties: { owner: { type: 'string' } } },
    async handler() {
      const owner = args => args.owner || 'idavidjunior';
      const r = await gh(`repo list ${owner(this)} --limit 50`);
      return r.code === 0 ? r.stdout : JSON.stringify(r, null, 2);
    },
  },
  {
    name: 'gh-recent-commits',
    description: 'List recent commits of a repo.',
    inputSchema: { type: 'object', properties: { repo: { type: 'string' }, limit: { type: 'number' } }, required: ['repo'] },
    async handler(args) {
      const n = args.limit || 10;
      const r = await gh(`api repos/${args.repo}/commits --paginate --jq '.[0:${n}][] | {sha: .sha[0:7], message: (.commit.message | split("\\n")[0]), author: .commit.author.name}'`);
      return r.code === 0 ? r.stdout : JSON.stringify(r, null, 2);
    },
  },
  {
    name: 'gh-repo-status',
    description: 'Get status (open issues, stars, language, last push) of a repo.',
    inputSchema: { type: 'object', properties: { repo: { type: 'string' } }, required: ['repo'] },
    async handler(args) {
      const r = await gh(`repo view ${args.repo} --json name,description,language,defaultBranchRef,updatedAt,stargazerCount,isArchived --jq .`);
      return r.code === 0 ? r.stdout : JSON.stringify(r, null, 2);
    },
  },
];

const server = new McpServer({
  name: 'eco-github',
  version: '1.0.0',
  tools,
});

server.listen();
