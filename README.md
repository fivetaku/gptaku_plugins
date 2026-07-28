English | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md)

<div align="center">

# GPTaku Plugins

**Stop explaining what you want — let Claude Code do it.**

14 plugins that search blocked sites, rip design systems from any URL,
review your code, and turn rough ideas into PRDs — all inside Claude Code.

<p>
  <a href="#-all-plugins-by-category"><img src="https://img.shields.io/badge/plugins-14-6E56CF" alt="14 plugins"></a>
  <a href="https://docs.anthropic.com/en/docs/claude-code"><img src="https://img.shields.io/badge/platform-Claude_Code-D97757?logo=claude" alt="Claude Code"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-3FB950" alt="MIT"></a>
  <a href="https://github.com/fivetaku/insane-search/stargazers"><img src="https://img.shields.io/github/stars/fivetaku/insane-search?style=flat&color=F0B72F" alt="stars"></a>
</p>

<!-- Purpose-first hero banner with light/dark theme support -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-purpose-wallbreak.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-purpose-wallbreak.png">
  <img src="assets/hero-purpose-wallbreak.png" width="980" alt="GPTaku Plugins cinematic hero showing a plugin drill breaking through Claude Code limits">
</picture>

<sub><a href="#-install">Install</a> · <a href="#-start-here--the-insane-series">Start here</a> · <a href="#-all-plugins-by-category">All plugins</a> · <a href="#-trust--setup">Trust</a></sub>

</div>

---

## ⚡ Install

Run these inside Claude Code:

```bash
# 1) Add the marketplace once
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git

# 2) Start with the lowest-friction flagship
/plugin install insane-search@gptaku-plugins

# 3) Apply without restarting the whole app
/reload-plugins
```

**New here? Install `insane-search` first.** Most plugins need only a running Claude Code session — a few connect an external service ([see Trust & setup](#-trust--setup)).

---

## 🔥 Start here — the insane-* series

> The flagship four. They break through the walls everything else stops at.

### 🔎 insane-search · <a href="https://github.com/fivetaku/insane-search/stargazers"><img src="https://img.shields.io/github/stars/fivetaku/insane-search?style=flat&color=F0B72F" alt="stars"></a>
**When Claude Code can't read a blocked page, this gets in anyway.**
Hit a WAF, 403, CAPTCHA, or login wall? It escalates through public API readers, syndication gateways, TLS impersonation, and a real headless browser, trying each until one gets through. No API keys.

```bash
/plugin install insane-search@gptaku-plugins
```
> **Try:** *"Find what people are saying about Claude Code on Reddit and summarize the top threads."*

### 🎨 insane-design
**Rips the design system out of any website. In one command.**
It reads the real CSS and pulls what matters: color, type, spacing, radius, shadow, fonts. Out comes a clean token set, a `design.md` spec, and a click-to-copy HTML report.

```bash
/plugin install insane-design@gptaku-plugins
```
> **Try:** *"Extract the design system from https://stripe.com"*

### 🧠 insane-review
**GPT-5.5 Pro has no API. This plugin uses it from inside Claude Code anyway.**
It packs the relevant code with `repomix`, runs it through your logged-in ChatGPT Pro web session, and brings back a line-by-line review.

```bash
/plugin install insane-review@gptaku-plugins
```
> **Try:** *"Have GPT-5.5 Pro review the auth flow in src/auth."*

### 📚 insane-research
**One question in. A cited, multi-agent research report out.**
A 7-phase pipeline: it scopes the question, spawns specialized research agents, grades and cross-checks every source, then compiles a structured Markdown report.

```bash
/plugin install insane-research@gptaku-plugins
```
> **Try:** *"Research the best vector database for RAG in 2026, with citations."*

---

## 🧭 Pick by the wall you hit

<div align="center">
  <img src="assets/flow-transform.png" width="980" alt="Before-to-after map showing Claude Code walls routed through GPTaku Plugins into unlocked web, pro review, AI-ready PRD, lean context, and agent team outcomes">
</div>

<table width="100%">
<tr>
  <td><strong>If Claude Code gets stuck on...</strong></td>
  <td width="25%"><strong>Install this</strong></td>
</tr>
<tr>
  <td>A blocked public page, empty HTML, or platform-specific web content</td>
  <td><code>insane-search</code></td>
</tr>
<tr>
  <td>Code review that needs another strong model</td>
  <td><code>insane-review</code></td>
</tr>
<tr>
  <td>A website style you want to reuse accurately</td>
  <td><code>insane-design</code></td>
</tr>
<tr>
  <td>A broad research question that needs citations</td>
  <td><code>insane-research</code></td>
</tr>
<tr>
  <td>A vague app idea with no product spec</td>
  <td><code>show-me-the-prd</code></td>
</tr>
<tr>
  <td>A PRD that needs a verified <code>/goal</code> execution contract</td>
  <td><code>goaljaby</code></td>
</tr>
<tr>
  <td>A large build that should be split across workers</td>
  <td><code>pumasi</code> or <code>kkirikkiri</code></td>
</tr>
<tr>
  <td>A screenshot, long log, or copied reference</td>
  <td><code>dd</code></td>
</tr>
<tr>
  <td>A library/API question that needs official docs</td>
  <td><code>docs-guide</code></td>
</tr>
<tr>
  <td>Gmail, Calendar, Drive, Docs, Sheets, Slides, Chat, Tasks, or Meet</td>
  <td><code>nopal</code></td>
</tr>
<tr>
  <td>GitHub feels like a foreign language</td>
  <td><code>git-teacher</code></td>
</tr>
<tr>
  <td>You want to improve how you work with Claude Code</td>
  <td><code>vibe-sunsang</code></td>
</tr>
<tr>
  <td>You want to create your own plugin/skill/agent</td>
  <td><code>skillers-suda</code></td>
</tr>
</table>

---

## 🔒 Trust & setup

Most plugins need only a running Claude Code session — **no additional API key.** The few exceptions that connect to external services say so up front:

<table width="100%">
<tr>
  <td width="25%"><strong>Claude Code only</strong><br><em>(No credentials needed)</em></td>
  <td><code>insane-search</code>, <code>insane-design</code>, <code>insane-research</code>, <code>docs-guide</code>, <code>git-teacher</code>, <code>show-me-the-prd</code>, <code>goaljaby</code>, <code>kkirikkiri</code>, <code>skillers-suda</code>, <code>vibe-sunsang</code>, <code>dd</code></td>
</tr>
<tr>
  <td width="25%"><strong>Google Workspace OAuth</strong></td>
  <td><code>nopal</code> (requires a Google account and a one-time login validation through the <code>gws</code> CLI)</td>
</tr>
<tr>
  <td width="25%"><strong>Logged-in Browser Session</strong></td>
  <td><code>insane-review</code> (requires an active, logged-in ChatGPT Plus/Pro web session; no API keys)</td>
</tr>
<tr>
  <td width="25%"><strong>External CLI</strong></td>
  <td><code>pumasi</code> (requires the Codex CLI to be installed on your host system)</td>
</tr>
</table>

All plugins are open source. Every submodule README lists its exact command boundaries, skills, and dependencies.

---

## 📦 All plugins by category

### 🔎 Research & web
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-search">insane-search</a></strong></td>
  <td>Auto-bypass for blocked websites — WAF/403/CAPTCHA, no API keys.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-research">insane-research</a></strong></td>
  <td>Multi-agent deep research — source-triangulated, citation-backed.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/docs-guide">docs-guide</a></strong></td>
  <td>Answers grounded in official docs — llms.txt + 68 libraries.</td>
</tr>
</table>

### 🎨 Design & quality
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-design">insane-design</a></strong></td>
  <td>Any URL → design tokens + <code>design.md</code> + interactive HTML report.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-review">insane-review</a></strong></td>
  <td>GPT-5.5 Pro code review from inside Claude Code (no API).</td>
</tr>
</table>

### 🚀 Plan & ship
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/show-me-the-prd">show-me-the-prd</a></strong></td>
  <td>One sentence → 4 design documents (PRD, data model, phases, project spec).</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/goaljaby">goaljaby</a></strong></td>
  <td>PRD → reviewed <code>/goal</code> workflow execution contract.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/pumasi">pumasi</a></strong></td>
  <td>Claude Code as PM + Codex CLI as a parallel dev team.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/kkirikkiri">kkirikkiri</a></strong></td>
  <td>Assemble an AI agent team from a single sentence.</td>
</tr>
</table>

### 🌱 Learn & build better
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/git-teacher">git-teacher</a></strong></td>
  <td>Git/GitHub onboarding via cloud-service analogies.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/vibe-sunsang">vibe-sunsang</a></strong></td>
  <td>AI mentor — conversation analysis + growth reports.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/skillers-suda">skillers-suda</a></strong></td>
  <td>4 expert agents debate your idea into a working skill.</td>
</tr>
</table>

### ⚙️ Workspace
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/nopal">nopal</a></strong></td>
  <td>Google Workspace orchestration — 9 services.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/dd">dd</a></strong></td>
  <td>Drop clipboard text/image into Claude Code (<code>/dd</code>, <code>/ㅇㅇ</code>).</td>
</tr>
</table>

---

## Requirements

- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** only — no Codex / Antigravity / other terminal interfaces.
- **Windows**: Run on WSL2 (`wsl --install`) · **macOS / Linux**: Works out of the box.
- Some plugins auto-install optional CLI tools (`gh`, `yt-dlp`, Playwright MCP) when needed.

## Why GPTaku?

Each plugin removes one specific wall you hit while learning to build with AI — a blocked page, a blank PRD, a design you can't reverse-engineer. Korean-first, shipped bilingual, composable, no signup loops.

**Become AI Native, one wall at a time.**

## License

MIT
