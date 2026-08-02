'use strict';
const readline = require('readline');

class McpServer {
  constructor({ name, version, tools, extraCapabilities = {} }) {
    this.info = { name, version };
    this.tools = tools;
    this.capabilities = Object.assign({ tools: {} }, extraCapabilities);
  }

  async handle(req) {
    const rid = req.id;
    const method = req.method || '';
    const params = req.params || {};

    if (method === 'initialize') {
      return this.ok(rid, {
        protocolVersion: '2024-11-05',
        serverInfo: this.info,
        capabilities: this.capabilities,
      });
    }

    if (method === 'ping') {
      return this.ok(rid, {});
    }

    if (method === 'tools/list') {
      return this.ok(rid, { tools: this.tools.map(t => ({ name: t.name, description: t.description, inputSchema: t.inputSchema })) });
    }

    if (method === 'tools/call') {
      const tool = this.tools.find(t => t.name === params.name);
      if (!tool) {
        return this.err(rid, -32601, `Tool not found: ${params.name}`);
      }
      try {
        const text = await tool.handler(params.arguments || {});
        return this.ok(rid, { content: [{ type: 'text', text }] });
      } catch (e) {
        return this.err(rid, -32603, String(e && e.message || e));
      }
    }

    if (rid !== undefined && rid !== null) {
      return this.ok(rid, {});
    }
    return null;
  }

  ok(id, result) {
    return { jsonrpc: '2.0', id: id ?? null, result };
  }

  err(id, code, message) {
    return { jsonrpc: '2.0', id: id ?? null, error: { code, message } };
  }

  listen() {
    const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
    rl.on('line', async (line) => {
      line = line.trim();
      if (!line) return;
      let req;
      try {
        req = JSON.parse(line);
      } catch {
        return;
      }
      const resp = await this.handle(req);
      if (resp) {
        process.stdout.write(JSON.stringify(resp) + '\n');
      }
    });
  }
}

module.exports = { McpServer };
