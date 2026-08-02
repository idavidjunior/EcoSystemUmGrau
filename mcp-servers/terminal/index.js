'use strict';
const { exec } = require('child_process');
const { McpServer } = require('../lib/mcp-core');

const DANGEROUS = /\b(rm\s+-rf|rmdir\s+\/s|format\s+|diskpart|del\s+\/f\s+\/s|shutdown|reg\s+delete|taskkill\s+\/f|Remove-Item\s+-Recurse|Clear-Content|Stop-Process)\b/i;

function runShell(command, cwd, timeoutMs) {
  return new Promise((resolve) => {
    exec(command, { cwd, timeout: timeoutMs || 30000, shell: 'powershell.exe', encoding: 'utf8' }, (err, stdout, stderr) => {
      const code = err ? (err.code ?? 1) : 0;
      resolve({ code, stdout: (stdout || '').slice(0, 20000), stderr: (stderr || '').slice(0, 20000) });
    });
  });
}

const tools = [
  {
    name: 'run-command',
    description: 'Run a shell command (PowerShell) in a working directory. Blocks destructive commands (rm -rf, format, diskpart, shutdown, registry deletes).',
    inputSchema: { type: 'object', properties: { command: { type: 'string' }, cwd: { type: 'string' }, timeoutMs: { type: 'number' } }, required: ['command'] },
    async handler(args) {
      if (!args.command || !args.command.trim()) return 'Empty command';
      if (DANGEROUS.test(args.command)) {
        return JSON.stringify({ error: 'BLOCKED: destructive command detected. Refusing to run.', command: args.command });
      }
      const result = await runShell(args.command, args.cwd || process.cwd(), args.timeoutMs);
      return JSON.stringify(result, null, 2);
    },
  },
  {
    name: 'shell-status',
    description: 'Show current shell: version, cwd, PATH basics.',
    inputSchema: { type: 'object', properties: {} },
    async handler() {
      const pwsh = await runShell('$PSVersionTable.PSVersion.ToString()', process.cwd(), 10000);
      return JSON.stringify({
        shell: 'powershell',
        version: (pwsh.stdout || '').trim(),
        cwd: process.cwd(),
        node: process.version,
      }, null, 2);
    },
  },
];

const server = new McpServer({
  name: 'eco-terminal',
  version: '1.0.0',
  tools,
});

server.listen();
