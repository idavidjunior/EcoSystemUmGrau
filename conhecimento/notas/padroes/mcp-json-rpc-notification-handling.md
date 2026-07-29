---
tags: [padrao, sessionsession]
aliases: [MCP JSON-RPC notification handling]
date: 2026-07-29
---

# MCP JSON-RPC notification handling

**Fonte:** session+session

MCP server must NOT respond to JSON-RPC notifications (requests without id field). Check req_id = request.get(id) - if None, return None from handle_request and skip writing to stdout in run().
