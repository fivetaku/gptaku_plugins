English | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md)

# playmaker (플레이메이커)

<p align="center">
  <img src="assets/playmaker-hero-01.png" alt="playmaker" width="320">
</p>

> **A live goal board inside Claude Code — see where your goal is, what is in progress, and what is waiting on you.**

goaljaby scores the goal; playmaker reads the whole pitch. playmaker is a Claude Code mod that reads the `PLAN.md` and `PROGRESS.md` of a goaljaby goal folder and draws a **waiting · doing · done** board in a side pane. Each card is one task tagged with its milestone, tasks that need a human are marked ⏸, and a one-line summary sits above your prompt.

[Quick Start](#quick-start) • [What you see](#what-you-see) • [What it reads](#what-it-reads) • [Commands](#commands) • [Requirements](#requirements)

---

## Quick Start

### 1. Add the marketplace

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. Install

```
/plugin install playmaker
```

### 3. Restart Claude Code

### 4. Open the board

```
/playmaker
```

playmaker looks two levels down from the current folder and opens the goal folder that changed most recently. If a goal is in progress and was touched in the last 7 days, the board opens by itself when the session starts.

---

## What you see

```
인증까지 붙인 MVP를 배포한다.
골 1/3 · 진행 M2 · 작업 2/6 · ⏸ 사람 대기 1
[마일스톤별 보기] [완료 펼치기]

대기 (2)                 진행 (2)                      완료 (2)
· [M2] 마일스톤 검증 실행  ▶ [M2] OAuth 콜백을 연결한다   ✓ M1 2건
· [M3] 배포 설정을 만든다  ⏸ [M2] 운영자 승인 계정 대기
```

Board labels are Korean in v0.1 (대기 = waiting, 진행 = doing, 완료 = done, 골 = goal, 작업 = tasks, 사람 대기 = waiting on a human). Task text is shown as written in your PLAN.md, in any language.

- **Three status columns.** One card per task, tagged `[M2]` with its milestone. Several milestones in progress at once all show up.
- **Human waits stand out.** Tasks marked `[!]`, or legacy milestones whose progress note says they are waiting on a person, show as ⏸.
- **Narrow panes stack.** Below 72 columns the board stacks Doing, Waiting, Done top to bottom, and Done collapses to a per-milestone count.
- **By-milestone view.** One button switches to a checklist per milestone (`[ ] [>] [x] [!]`).
- **Live.** Edits to PLAN.md or PROGRESS.md show up within 3 seconds.
- **Act on a card.** Press a card and an action row opens under it, by task status: approve / what should I check? / put on hold for a task waiting on you, progress? / blocked? for one in progress, plus **Write…** for your own words. The instruction goes straight into this session, tagged with the task ID. Until the session finishes answering, the other cards stay locked so two contradicting instructions never pile up. playmaker still never edits PLAN.md; the agent updates the markers.
- **Open in browser · Close.** The pane's **Open in browser** button starts the web board and opens it in your default browser, leaving a clickable link in the pane. **✕ Close** hides the pane and the summary line; `/playmaker` brings them back.
- **Mismatch warning.** When the PLAN checklist and PROGRESS disagree, the board says so with ⚠ instead of guessing.

---

## What it reads

| Goal folder | Task status comes from |
|---|---|
| goaljaby 0.7+ | PLAN.md checklist per milestone: `- [>] M2-T1: task` (`[ ]` waiting · `[>]` doing · `[x]` done · `[!]` needs human) |
| goaljaby 0.6 and earlier, hand-written PLANs | Inferred from milestone status in PROGRESS.md and the milestone's Scope line. Inferred cards are drawn dimmed |

Table-style PLANs (`| M1a name | scope |`) and `### M2 name` headings are read too. playmaker only reads files; it never writes to your goal folder.

---

## Commands

| Command | What it does |
|---|---|
| `/playmaker` | Find the most recent goal folder under the current folder and open the board |
| `/playmaker <folder>` | Open the board for a specific goal folder |
| `/playmaker web [folder]` | Start the browser board (below) and print its address |

The command also returns a text summary, so it is useful where no pane can be drawn.

---

## Requirements

- [Claude Code](https://code.claude.com/docs/en/plugins/mods/overview) **v2.1.287+** (mods), in the terminal or the desktop app's Code tab
- The pane docks beside the transcript in `/tui fullscreen` at 110+ columns; otherwise it opens above the prompt
- Hosts that draw no panes (Paseo, `claude -p`, the VS Code chat, cloud sessions) run mods but cannot show the pane. There `/playmaker` answers with a text summary, and `/playmaker web` serves the same board as a local web page (127.0.0.1 only, refreshes every 2 seconds, needs Node 22.18+)
- **Paseo:** playmaker notices it runs under Paseo, starts the web board when a goal is in progress and opens it as a Paseo browser tab (reusing the tab next time; drag it to a right split once). On the web board, pick the Paseo session working on the goal and press a card to send it the same actions
- In the terminal, mouse clicks work in `/tui fullscreen`; otherwise press Ctrl+X then Tab to move into the pane and use arrows and Enter

### Works best with

| Plugin | What it adds |
|--------|--------------|
| `goaljaby` 0.7+ | Writes the per-task checklist playmaker reads |

---

## License

MIT · [Disclaimer](DISCLAIMER.md)

---

<div align="center">

**Score with goaljaby. Read the game with playmaker.**

</div>
