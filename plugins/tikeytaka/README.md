English | [한국어](README.ko.md)

# tikeytaka

Central API key vault plugin — consolidate keys scattered across `.env` files into one encrypted vault, register new keys without exposing them in chat, and propagate a single update to every project. While you tiki-taka with the AI, keys are looked up and wired in automatically.

- **Zero sign-up**: auto-detects a cloud folder you already use (iCloud Drive / Google Drive / OneDrive / Dropbox) and syncs one encrypted file through it. Falls back to local single-device mode. The chosen path is pinned and never silently switches.
- **Encryption**: AES-256-CBC + PBKDF2 (600k iterations, SHA-256) with a built-in integrity hash (TKT2 format). A corrupted or half-synced vault is detected and the tool halts — it **never overwrites the original**, and keeps a `.bak` generation before every change.
- **OS integration**: the decryption passphrase lives in macOS Keychain / Linux secret-tool / Windows DPAPI. A 0600 file fallback exists only behind explicit opt-in (`TKT_ALLOW_FILE_FALLBACK=1`).
- **Minimal exposure**: key values enter only via hidden terminal prompt (`tkt setp`) or stdin (`set-stdin`) — never chat, shell history, or process argv.

## Commands

| Command | What it does |
|---|---|
| `/tikeytaka` | Status summary (key count, vault location, pending propagation) |
| `/tikeytaka:use` | **Check the vault first when a task needs an API key → wire and test automatically** (no asking) |
| `/tikeytaka:scan` | Discover existing project `.env` files → consolidate keys into the vault (with live-key validation) |
| `/tikeytaka:add` | Register a new key without chat exposure |
| `/tikeytaka:list` | Managed services and project connections |
| `/tikeytaka:sync` | Propagate the vault to every connected `.env` |

## Connecting a new device

1. Wait for the cloud folder to sync (the vault file arrives)
2. `bash <plugin-path>/bin/tkt init` — enter the same vault passphrase
3. Wire this device's projects: `/tikeytaka:scan` (or `tkt map-add`) — the mapping list is device-local by design
4. `tkt sync`

## Platform support

| Platform | Status |
|---|---|
| macOS (Keychain + iCloud/others) | Verified |
| Windows (Git Bash + OneDrive/Google Drive + DPAPI) | Implemented, provisional |
| Linux (secret-tool + Dropbox, or manual `TIKEYTAKA_DIR`) | Implemented, provisional |

## Known limits (honest disclosure)

- **No concurrent editing**: simultaneous `set`/`del` from two devices makes one side halt on conflict detection (data stays safe). Single-user tool by design.
- macOS Keychain registration (`security -w`) passes the passphrase through process argv once during init — a tool limitation.
- This is a personal vault. For team sharing, access control, or audit logs, use a secrets SaaS (e.g. Infisical).
- No local vault protects an already-compromised account (keyloggers etc.).
