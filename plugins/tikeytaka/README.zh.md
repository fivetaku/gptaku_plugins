[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Español](README.es.md) | 中文

# tikeytaka

API 密钥中央保险库插件 — 把散落在各个 `.env` 中的密钥整合进一个加密保险库，注册新密钥时不在聊天中暴露，一次更新即可传播到所有项目。当你与 AI「踢踏配合」时，密钥会被自动查询并接入。

## Quick Start

### 1. 添加市场

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. 安装

```
/plugin install tikeytaka
```

### 3. 重启 Claude Code

（新命令需重启后才会注册。）

### 4. 运行

```
/tikeytaka
```

然后在自己的终端里执行一次 `bash <插件路径>/bin/tkt init`（命令会告诉你确切路径），再用 `/tikeytaka:scan` 整合现有密钥。

## 为什么选 tikeytaka

一次真实的主目录扫描发现了 **45 个 `.env` 文件**，同一个密钥在 6 个文件中有 3 种不同的值 — 大多已失效。密钥散落意味着无法轮换、无法吊销，甚至不知道自己有什么。tikeytaka 让一个加密文件成为唯一事实来源，让每个 `.env` 变成由机器刷新的副本。

- **零注册**: 自动检测你已在用的云文件夹（iCloud Drive / Google Drive / OneDrive / Dropbox），只同步一个加密文件。没有则进入本地单设备模式。所选路径会被固定，绝不悄悄切换。
- **结构性安全**: AES-256-CBC + PBKDF2（60 万次迭代、SHA-256）+ 内建完整性哈希（TKT2 格式）。损坏或未同步完的保险库会被检测并立即停止 — **绝不覆盖原件**，且每次变更前保留一代 `.bak`。
- **系统集成**: 解密口令保存在 macOS 钥匙串 / Linux secret-tool / Windows DPAPI。三者皆无时，仅在明确同意（`TKT_ALLOW_FILE_FALLBACK=1`）下回退到 0600 文件。
- **最小暴露**: 密钥值只通过终端隐藏输入（`tkt setp`）或 stdin（`set-stdin`）进入 — 绝不经过聊天、shell 历史或进程参数（argv）。

## 工作原理

```
你 / Claude  ──►  bin/tkt（单文件 bash CLI）
                    ├── secrets.enc   加密保险库 — 经你的云文件夹传输
                    ├── 系统钥匙串     唯一口令 — 永不离开设备
                    └── map.tsv       设备本地接线 — 哪个 .env 用哪个密钥
```

云端只承载密文，打开它的钥匙从不离开你的设备。`tkt sync` 只解密一次、校验完整性，然后在保留文件权限的前提下刷新所有映射的 `.env`。

## 命令

| 命令 | 功能 |
|---|---|
| `/tikeytaka` | 状态摘要（密钥数、保险库位置、待传播项） |
| `/tikeytaka:use` | **任务需要 API 密钥时先查保险库 → 自动接线并测试**（不追问） |
| `/tikeytaka:scan` | 发现现有项目的 `.env` → 整合注册密钥并接线（含活性实测验证） |
| `/tikeytaka:add` | 注册新密钥且不在聊天中暴露 |
| `/tikeytaka:list` | 管理中的服务与项目连接情况 |
| `/tikeytaka:sync` | 保险库 → 传播到所有已连接的 `.env` |

## 连接新设备

1. 等待云文件夹同步（保险库文件到达）
2. `bash <插件路径>/bin/tkt init` — 输入相同的保险库口令
3. 项目接线按设备进行: `/tikeytaka:scan`（或 `tkt map-add`）为本设备的 `.env` 接线（`map.tsv` 依设计为设备本地）
4. `tkt sync`

## 要求

- `bash`、`openssl`（macOS、Linux、Git for Windows 均自带 — Claude Code 的 Windows shell 即 Git Bash）
- 一个秘密存储: macOS 钥匙串 / Linux `secret-tool` / Windows PowerShell（DPAPI）

| 平台 | 状态 |
|---|---|
| macOS（钥匙串 + iCloud 等） | 已验证 |
| Windows（Git Bash + OneDrive/Google Drive + DPAPI） | 已实现，暂定 |
| Linux（secret-tool + Dropbox，或手动 `TIKEYTAKA_DIR`） | 已实现，暂定 |

## 已知限制（诚实披露）

- **禁止并发编辑**: 两台设备同时 `set`/`del` 时，一侧会因冲突检测而停止（数据安全）。设计上为单用户工具。
- macOS 钥匙串注册（`security -w`）在 init 时口令会经过一次进程参数 — 工具本身的限制。
- 这是个人保险库。需要团队共享、权限控制或审计日志时，请使用秘密管理 SaaS（如 Infisical）。
- 账户本身已被入侵的环境（键盘记录器等），任何本地保险库都无法保护。

## 源码

https://github.com/fivetaku/tikeytaka — [gptaku-plugins](https://github.com/fivetaku/gptaku_plugins) 市场成员。

## 许可证

[MIT](./LICENSE) — 另见 [DISCLAIMER.md](./DISCLAIMER.md)。
