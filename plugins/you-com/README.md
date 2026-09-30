# you-com

You.com web search for Claude Code.

Adds the You.com MCP server as an optional plugin so a session can run current
web search, read URLs, and produce cited answers without leaving Claude Code.

- **Keyless by default** — the plugin registers `https://api.you.com/mcp?profile=free`,
  which exposes the `you-search` tool. No API key, no signup.
- **Optional upgrade** — set `YDC_API_KEY` and point the server at
  `https://api.you.com/mcp` to also get `you-contents` (full URL extraction)
  and `you-research` (one-shot cited synthesis). Get a key at
  [you.com/platform/api-keys](https://you.com/platform/api-keys).

## Install

```bash
/plugin install you-com@gptaku-plugins
```

## Use

Ask for current information or cited sources:

> Use you-web to find the current stable version of Node.js and cite sources.

> Search the web for recent changes to the MCP spec and summarize with links.

The `you-web` skill routes the request to the available You.com MCP tools and
falls back gracefully: with the keyless server only `you-search` is available,
so results are gathered by search and pages are read with the host's web-fetch
tool.

## Scope

- Commands/skills: `you-web` (search, URL reading, cited synthesis routing)
- MCP: `you` server (`https://api.you.com/mcp?profile=free`, keyless)
- No dependencies, no hooks, no background processes. Nothing runs until the
  user invokes the skill or an MCP tool.

## Upstream

Skill content is adapted from the
[youdotcom-oss/agent-skills](https://github.com/youdotcom-oss/agent-skills)
`you-web` skill. MIT licensed.
