[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | 日本語 | [Español](README.es.md)

<div align="center">

# GPTaku Plugins

**やりたいことを説明するのはもう終わり — Claude Code に丸ごとやらせましょう。**

ブロックされたサイトを突破し、あらゆる URL からデザインシステムを抜き取り、
コードをレビューし、ざっくりしたアイデアを PRD に変える — それを全部 Claude Code の中でやる 15 個のプラグインです。

<p>
  <a href="#-全プラグイン一覧カテゴリ別"><img src="https://img.shields.io/badge/plugins-15-6E56CF" alt="15個のプラグイン"></a>
  <a href="https://docs.anthropic.com/en/docs/claude-code"><img src="https://img.shields.io/badge/platform-Claude_Code-D97757?logo=claude" alt="Claude Code"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-3FB950" alt="MIT"></a>
  <a href="https://github.com/fivetaku/insane-search/stargazers"><img src="https://img.shields.io/github/stars/fivetaku/insane-search?style=flat&color=F0B72F" alt="stars"></a>
</p>

<!-- Purpose-first hero banner with light/dark theme support -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-purpose-wallbreak.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-purpose-wallbreak.png">
  <img src="assets/hero-purpose-wallbreak.png" width="980" alt="プラグインのドリルが Claude Code の限界を突き破る GPTaku Plugins のシネマティックなヒーローバナー">
</picture>

<sub><a href="#-インストール">インストール</a> · <a href="#-まずはここから--insane-シリーズ">まずはここから</a> · <a href="#-全プラグイン一覧カテゴリ別">全プラグイン</a> · <a href="#-信頼性とセットアップ">信頼性</a></sub>

</div>

---

## ⚡ インストール

Claude Code の中で次のコマンドを実行します。

```bash
# 1) Add the marketplace once
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git

# 2) Start with the lowest-friction flagship
/plugin install insane-search@gptaku-plugins

# 3) Apply without restarting the whole app
/reload-plugins
```

**はじめてですか? まずは `insane-search` から入れてください。** ほとんどのプラグインは起動中の Claude Code セッションさえあれば動きます — 一部だけ外部サービスへの接続が必要です（[信頼性とセットアップ](#-信頼性とセットアップ)を参照）。

---

## 🔥 まずはここから — insane-* シリーズ

> 旗艦の 4 本。ほかのすべてが行き詰まる壁を、こいつらは突き破ります。

### 🔎 insane-search · <a href="https://github.com/fivetaku/insane-search/stargazers"><img src="https://img.shields.io/github/stars/fivetaku/insane-search?style=flat&color=F0B72F" alt="stars"></a>
**Claude Code がブロックされたページを読めないとき、こいつはとにかく中に入ります。**
WAF、403、CAPTCHA、ログイン壁にぶつかった? パブリック API リーダー、シンジケーションゲートウェイ、TLS なりすまし、本物のヘッドレスブラウザへと段階的にエスカレートし、どれかが通るまで順に試します。API キーは不要です。

```bash
/plugin install insane-search@gptaku-plugins
```
> **試してみる:** *「Reddit で Claude Code について話されていることを探して、上位スレッドを要約して。」*

### 🎨 insane-design
**どんなサイトからでもデザインシステムを抜き取ります。コマンド 1 つで。**
本物の CSS を読み込み、肝心なものを引き出します — 色、タイポグラフィ、スペーシング、角丸、シャドウ、フォント。出てくるのはきれいなトークンセット、`design.md` の仕様書、そしてクリックでコピーできる HTML レポートです。

```bash
/plugin install insane-design@gptaku-plugins
```
> **試してみる:** *「https://stripe.com からデザインシステムを抽出して」*

### 🧠 insane-review
**GPT-5.5 Pro には API がありません。それでもこのプラグインは Claude Code の中から使います。**
関係するコードを `repomix` でパッケージングし、ログイン済みの ChatGPT Pro ウェブセッションを通して走らせ、行単位のレビューを持ち帰ります。

```bash
/plugin install insane-review@gptaku-plugins
```
> **試してみる:** *「src/auth の認証フローを GPT-5.5 Pro にレビューさせて。」*

### 📚 insane-research
**質問を 1 つ放り込む。出てくるのは引用付きのマルチエージェント・リサーチレポート。**
7 フェーズのパイプライン — 質問のスコープを定め、専門のリサーチエージェントを立ち上げ、すべてのソースを採点・クロスチェックし、構造化された Markdown レポートにまとめ上げます。

```bash
/plugin install insane-research@gptaku-plugins
```
> **試してみる:** *「2026 年の RAG 向けベストなベクトルデータベースを、引用付きで調べて。」*

---

## 🧭 ぶつかった壁で選ぶ

<div align="center">
  <img src="assets/flow-transform.png" width="980" alt="Claude Code の壁を GPTaku Plugins 経由でルーティングし、ロック解除されたウェブ、プロのレビュー、AI 対応 PRD、軽量コンテキスト、エージェントチームへと変換する Before-After マップ">
</div>

<table width="100%">
<tr>
  <td><strong>Claude Code が行き詰まるのは…</strong></td>
  <td width="25%"><strong>これを入れる</strong></td>
</tr>
<tr>
  <td>ブロックされた公開ページ、空っぽの HTML、プラットフォーム固有のウェブコンテンツ</td>
  <td><code>insane-search</code></td>
</tr>
<tr>
  <td>もう 1 つの強力なモデルが必要なコードレビュー</td>
  <td><code>insane-review</code></td>
</tr>
<tr>
  <td>正確に再利用したいウェブサイトのスタイル</td>
  <td><code>insane-design</code></td>
</tr>
<tr>
  <td>引用が必要な広範なリサーチ課題</td>
  <td><code>insane-research</code></td>
</tr>
<tr>
  <td>製品仕様のない、ぼんやりしたアプリのアイデア</td>
  <td><code>show-me-the-prd</code></td>
</tr>
<tr>
  <td>検証済みの <code>/goal</code> 実行契約が必要な PRD</td>
  <td><code>goaljaby</code></td>
</tr>
<tr>
  <td>複数のワーカーに分割すべき大規模なビルド</td>
  <td><code>pumasi</code> または <code>kkirikkiri</code></td>
</tr>
<tr>
  <td>スクリーンショット、長いログ、コピーしたリファレンス</td>
  <td><code>dd</code></td>
</tr>
<tr>
  <td>公式ドキュメントが必要なライブラリ/API の疑問</td>
  <td><code>docs-guide</code></td>
</tr>
<tr>
  <td>Gmail、カレンダー、ドライブ、ドキュメント、スプレッドシート、スライド、チャット、ToDo、Meet</td>
  <td><code>nopal</code></td>
</tr>
<tr>
  <td>GitHub が外国語みたいに感じる</td>
  <td><code>git-teacher</code></td>
</tr>
<tr>
  <td>Claude Code との付き合い方そのものを良くしたい</td>
  <td><code>vibe-sunsang</code></td>
</tr>
<tr>
  <td>自分だけのプラグイン/スキル/エージェントを作りたい</td>
  <td><code>skillers-suda</code></td>
</tr>
</table>

---

## 🔒 信頼性とセットアップ

ほとんどのプラグインは起動中の Claude Code セッションさえあれば動きます — **追加の API キーは不要です。** 外部サービスに接続する数少ない例外は、最初からその旨をはっきり示しています。

<table width="100%">
<tr>
  <td width="25%"><strong>Google Workspace OAuth</strong></td>
  <td><code>nopal</code>（Google アカウントと、<code>gws</code> CLI を通じた一度きりのログイン検証が必要）</td>
</tr>
<tr>
  <td width="25%"><strong>ログイン済みブラウザセッション</strong></td>
  <td><code>insane-review</code>（ログイン状態でアクティブな ChatGPT Plus/Pro のウェブセッションが必要。API キーは不要）</td>
</tr>
<tr>
  <td width="25%"><strong>外部 CLI</strong></td>
  <td><code>pumasi</code>（ホストシステムに Codex CLI がインストールされている必要あり）</td>
</tr>
</table>

すべてのプラグインはオープンソースです。各サブモジュールの README に、正確なコマンドの境界、スキル、依存関係が記載されています。

---

## 📦 全プラグイン一覧（カテゴリ別）

### 🔎 リサーチ & ウェブ
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-search">insane-search</a></strong></td>
  <td>ブロックされたウェブサイトを自動突破 — WAF/403/CAPTCHA、API キー不要。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-research">insane-research</a></strong></td>
  <td>マルチエージェントによる深掘りリサーチ — ソース三角測量・引用裏付き。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/docs-guide">docs-guide</a></strong></td>
  <td>公式ドキュメントに根ざした回答 — llms.txt + 68 ライブラリ。</td>
</tr>
</table>

### 🎨 デザイン & 品質
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-design">insane-design</a></strong></td>
  <td>どんな URL でも → デザイントークン + <code>design.md</code> + インタラクティブな HTML レポート。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-review">insane-review</a></strong></td>
  <td>Claude Code の中から GPT-5.5 Pro でコードレビュー（API 不要）。</td>
</tr>
</table>

### 🚀 計画 & 出荷
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/show-me-the-prd">show-me-the-prd</a></strong></td>
  <td>一文 → 4 つの設計ドキュメント（PRD、データモデル、フェーズ、プロジェクト仕様）。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/goaljaby">goaljaby</a></strong></td>
  <td>PRD → レビュー済みの <code>/goal</code> ワークフロー実行契約。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/pumasi">pumasi</a></strong></td>
  <td>Claude Code を PM に、Codex CLI を並列の開発チームに。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/kkirikkiri">kkirikkiri</a></strong></td>
  <td>一文から AI エージェントチームを組み上げる。</td>
</tr>
</table>

### 🌱 学んで、もっと上手に作る
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/git-teacher">git-teacher</a></strong></td>
  <td>クラウドサービスのたとえで Git/GitHub をオンボーディング。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/vibe-sunsang">vibe-sunsang</a></strong></td>
  <td>AI メンター — 会話分析 + 成長レポート。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/skillers-suda">skillers-suda</a></strong></td>
  <td>4 人の専門エージェントがあなたのアイデアを議論し、動くスキルに仕上げる。</td>
</tr>
</table>

### ⚙️ ワークスペース
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/nopal">nopal</a></strong></td>
  <td>Google Workspace のオーケストレーション — 9 サービス。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/dd">dd</a></strong></td>
  <td>クリップボードのテキスト/画像を Claude Code に放り込む（<code>/dd</code>、<code>/ㅇㅇ</code>）。</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/gaseo">gaseo</a></strong></td>
  <td>いま話している Claude Code セッションを Paseo へ送る (<code>/gaseo</code>).</td>
</tr>
</table>

---

## 動作要件

- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** のみ — Codex / Antigravity / その他のターミナルインターフェースは対象外です。
- **Windows**: WSL2（`wsl --install`）で実行 · **macOS / Linux**: そのまま動きます。
- 一部のプラグインは、必要に応じてオプションの CLI ツール（`gh`、`yt-dlp`、Playwright MCP）を自動でインストールします。

## なぜ GPTaku?

各プラグインは、AI でものづくりを学ぶ過程でぶつかる、ある特定の壁を 1 つずつ取り除きます — ブロックされたページ、真っ白な PRD、リバースエンジニアできないデザイン。韓国語ファースト、バイリンガルで出荷、組み合わせ自在、サインアップのループもなし。

## ライセンス

MIT

---

<div align="center">

**壁を 1 つずつ越えて、AI ネイティブになろう。**

</div>
