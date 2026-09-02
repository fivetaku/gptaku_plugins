[English](README.md) | [한국어](README.ko.md) | 中文 | [日本語](README.ja.md) | [Español](README.es.md)

<div align="center">

# GPTaku Plugins

**别再费口舌解释你想要什么——让 Claude Code 直接搞定。**

17 个插件：搜索被封锁的网站、从任意 URL 扒下设计系统、
审查你的代码、把粗糙的想法变成 PRD——全部在 Claude Code 里完成。

<p>
  <a href="#-全部插件按分类"><img src="https://img.shields.io/badge/plugins-17-6E56CF" alt="17 个插件"></a>
  <a href="https://docs.anthropic.com/en/docs/claude-code"><img src="https://img.shields.io/badge/platform-Claude_Code-D97757?logo=claude" alt="Claude Code"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-3FB950" alt="MIT"></a>
  <a href="https://github.com/fivetaku/insane-search/stargazers"><img src="https://img.shields.io/github/stars/fivetaku/insane-search?style=flat&color=F0B72F" alt="stars"></a>
</p>

<!-- Purpose-first hero banner with light/dark theme support -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-purpose-wallbreak.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-purpose-wallbreak.png">
  <img src="assets/hero-purpose-wallbreak.png" width="980" alt="GPTaku Plugins 电影感主视觉：一把插件钻头凿穿 Claude Code 的种种限制">
</picture>

<sub><a href="#-安装">安装</a> · <a href="#-从这里开始insane-系列">从这里开始</a> · <a href="#-全部插件按分类">全部插件</a> · <a href="#-信任与配置">信任</a></sub>

</div>

---

## ⚡ 安装

在 Claude Code 里运行这些命令：

```bash
# 1) Add the marketplace once
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git

# 2) Start with the lowest-friction flagship
/plugin install insane-search@gptaku-plugins

# 3) Apply without restarting the whole app
/reload-plugins
```

**第一次来？先装 `insane-search`。** 大多数插件只需要一个正在运行的 Claude Code 会话——少数几个要接外部服务（[详见信任与配置](#-信任与配置)）。

---

## 🔥 从这里开始——insane-* 系列

> 旗舰四件套。它们能凿穿其他工具全都卡住的那堵墙。

### 🔎 insane-search · <a href="https://github.com/fivetaku/insane-search/stargazers"><img src="https://img.shields.io/github/stars/fivetaku/insane-search?style=flat&color=F0B72F" alt="stars"></a>
**当 Claude Code 读不了被封锁的页面时，它照样能进去。**
撞上 WAF、403、CAPTCHA 还是登录墙？它会逐级升级手段——公共 API 阅读器、内容聚合网关、TLS 指纹伪装，再到一个真正的无头浏览器，一个个试，直到有一个突破为止。无需 API 密钥。

```bash
/plugin install insane-search@gptaku-plugins
```
> **试试：** *"去 Reddit 上找找大家对 Claude Code 的评价，把热门帖子总结一下。"*

### 🎨 insane-design
**从任意网站里扒出整套设计系统。一条命令搞定。**
它读取真实的 CSS，把关键的东西全都拽出来：配色、字体、间距、圆角、阴影、字型。最后给你一套干净的 token、一份 `design.md` 规范，外加一份点击即复制的 HTML 报告。

```bash
/plugin install insane-design@gptaku-plugins
```
> **试试：** *"从 https://stripe.com 提取设计系统。"*

### 🧠 insane-review
**GPT-5.5 Pro 没有 API。这个插件偏偏让你在 Claude Code 里用上它。**
它用 `repomix` 把相关代码精准打包，喂进你已登录的 ChatGPT Pro 网页会话，再把逐行审查结果带回来。

```bash
/plugin install insane-review@gptaku-plugins
```
> **试试：** *"让 GPT-5.5 Pro 审查一下 src/auth 里的认证流程。"*

### 📚 insane-research
**进去一个问题，出来一份带引用的多智能体研究报告。**
一条 7 阶段流水线：界定问题、派出专门的研究智能体、对每一个信源评级并交叉核验，最后编成一份结构化的 Markdown 报告。

```bash
/plugin install insane-research@gptaku-plugins
```
> **试试：** *"调研一下 2026 年用于 RAG 的最佳向量数据库，要附引用。"*

---

## 🧭 按你撞上的墙来选

<div align="center">
  <img src="assets/flow-transform.png" width="980" alt="前后对照图：Claude Code 撞上的各种墙，经 GPTaku Plugins 分流，分别通向已解锁的网页、专业级审查、AI 就绪的 PRD、精简的上下文，以及智能体团队等结果">
</div>

<table width="100%">
<tr>
  <td><strong>如果 Claude Code 卡在了……</strong></td>
  <td width="25%"><strong>装这个</strong></td>
</tr>
<tr>
  <td>被封锁的公开页面、空白 HTML，或平台专属的网页内容</td>
  <td><code>insane-search</code></td>
</tr>
<tr>
  <td>需要另一个强力模型来做代码审查</td>
  <td><code>insane-review</code></td>
</tr>
<tr>
  <td>想准确复用某个网站的样式</td>
  <td><code>insane-design</code></td>
</tr>
<tr>
  <td>需要附引用的宽泛研究问题</td>
  <td><code>insane-research</code></td>
</tr>
<tr>
  <td>一个模糊的 app 点子，还没有产品规格</td>
  <td><code>show-me-the-prd</code></td>
</tr>
<tr>
  <td>一份需要可验证 <code>/goal</code> 执行契约的 PRD</td>
  <td><code>goaljaby</code></td>
</tr>
<tr>
  <td>一个该拆给多个工人并行的大型构建</td>
  <td><code>pumasi</code> 或 <code>kkirikkiri</code></td>
</tr>
<tr>
  <td>一张截图、一段长日志，或复制好的参考资料</td>
  <td><code>dd</code></td>
</tr>
<tr>
  <td>需要官方文档支撑的库/API 问题</td>
  <td><code>docs-guide</code></td>
</tr>
<tr>
  <td>Gmail、日历、Drive、Docs、Sheets、Slides、Chat、Tasks 或 Meet</td>
  <td><code>nopal</code></td>
</tr>
<tr>
  <td>GitHub 像天书一样看不懂</td>
  <td><code>git-teacher</code></td>
</tr>
<tr>
  <td>想提升自己用 Claude Code 干活的方式</td>
  <td><code>vibe-sunsang</code></td>
</tr>
<tr>
  <td>想做出你自己的插件/技能/智能体</td>
  <td><code>skillers-suda</code></td>
</tr>
</table>

---

## 🔒 信任与配置

大多数插件只需要一个正在运行的 Claude Code 会话——**不需要额外的 API 密钥。** 少数要接外部服务的例外，都会在一开始就把话说清楚：

<table width="100%">
<tr>
  <td width="25%"><strong>Google Workspace OAuth</strong></td>
  <td><code>nopal</code>（需要一个 Google 账号，并通过 <code>gws</code> CLI 做一次性的登录验证）</td>
</tr>
<tr>
  <td width="25%"><strong>已登录的浏览器会话</strong></td>
  <td><code>insane-review</code>（需要一个处于活动状态、已登录的 ChatGPT Plus/Pro 网页会话；无需 API 密钥）</td>
</tr>
<tr>
  <td width="25%"><strong>外部 CLI</strong></td>
  <td><code>pumasi</code>（需要在你的主机系统上安装 Codex CLI）</td>
</tr>
</table>

所有插件均为开源。每个子模块的 README 都列明了它确切的命令边界、技能和依赖。

---

## 📦 全部插件按分类

### 🔎 研究与网页
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-search">insane-search</a></strong></td>
  <td>自动绕过被封锁的网站——WAF/403/CAPTCHA，无需 API 密钥。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-research">insane-research</a></strong></td>
  <td>多智能体深度研究——多源三角验证、引用可溯。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/docs-guide">docs-guide</a></strong></td>
  <td>基于官方文档作答——llms.txt + 68 个库。</td>
</tr>
</table>

### 🎨 设计与质量
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-design">insane-design</a></strong></td>
  <td>任意 URL → 设计 token + <code>design.md</code> + 交互式 HTML 报告。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-review">insane-review</a></strong></td>
  <td>在 Claude Code 里用 GPT-5.5 Pro 做代码审查（无需 API）。</td>
</tr>
</table>

### 🚀 规划与交付
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/show-me-the-prd">show-me-the-prd</a></strong></td>
  <td>一句话 → 4 份设计文档（PRD、数据模型、阶段拆分、项目规格）。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/goaljaby">goaljaby</a></strong></td>
  <td>PRD → 经审查的 <code>/goal</code> 工作流执行契约。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/pumasi">pumasi</a></strong></td>
  <td>Claude Code 当 PM + Codex CLI 当并行开发团队。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/kkirikkiri">kkirikkiri</a></strong></td>
  <td>一句话组建一支 AI 智能体团队。</td>
</tr>
</table>

### 🌱 学习与精进
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/git-teacher">git-teacher</a></strong></td>
  <td>用云服务作类比，带你入门 Git/GitHub。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/vibe-sunsang">vibe-sunsang</a></strong></td>
  <td>AI 导师——对话分析 + 成长报告。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/skillers-suda">skillers-suda</a></strong></td>
  <td>4 位专家智能体互相辩论，把你的点子打磨成一个能跑的技能。</td>
</tr>
</table>

### ⚙️ 工作空间
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/nopal">nopal</a></strong></td>
  <td>Google Workspace 编排——9 项服务。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/dd">dd</a></strong></td>
  <td>把剪贴板里的文字/图片直接丢进 Claude Code（<code>/dd</code>、<code>/ㅇㅇ</code>）。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/gaseo">gaseo</a></strong></td>
  <td>把你正在聊的 Claude Code 会话送进 Paseo (<code>/gaseo</code>).</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/tikeytaka">tikeytaka</a></strong></td>
  <td>中央 API 密钥保险库 — 把散落各处的 .env 密钥整合进加密云同步保险库，注册、接线、存活验证全程对话完成。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/ddiring">ddiring</a></strong></td>
  <td>多会话完成提醒 — 一条通知告诉你哪个文件夹、哪个终端、什么任务；点击即可跳转到对应应用。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/sangse">sangse</a></strong></td>
  <td>韩国电商详情页生成器 — 产品信息 → 经验证的图片切图长页（Kurly / Coupang / 智能商店风格），含合规过滤与三重门 QA（<code>/sangse</code>）。</td>
</tr>
</table>

---

## 环境要求

- 仅支持 **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)**——不支持 Codex / Antigravity / 其他终端界面。
- **Windows**：在 WSL2 上运行（`wsl --install`）· **macOS / Linux**：开箱即用。
- 部分插件会在需要时自动安装可选的 CLI 工具（`gh`、`yt-dlp`、Playwright MCP）。

## 为什么是 GPTaku？

每个插件都为你拆掉一堵在用 AI 搞开发的路上会撞到的特定的墙——一个被封锁的页面、一份空白的 PRD、一个你逆向不出来的设计。韩语优先，双语发布，可自由组合，没有注册套娃。

## 许可证

MIT

---

<div align="center">

**一次一堵墙，成为 AI Native。**

</div>
