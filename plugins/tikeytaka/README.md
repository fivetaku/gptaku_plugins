English | [한국어](README.ko.md)

# tikeytaka

Central API key vault plugin — consolidate keys scattered across `.env` files into one encrypted vault, register new keys without exposing them in chat, and propagate a single update to every project.

- **Zero sign-up**: auto-detects a cloud folder you already use (iCloud Drive / Google Drive / OneDrive / Dropbox) and syncs one AES-256 encrypted file through it. Falls back to local single-device mode.
- **OS integration**: the decryption passphrase lives in macOS Keychain / Linux secret-tool.
- **Leak-proof registration**: key values are only ever entered via a hidden terminal prompt (`tkt setp`) — never pasted into chat or shell history.

## Commands

| Command | What it does |
|---|---|
| `/tikeytaka` | Status summary (key count, vault location, pending propagation) |
| `/tikeytaka:scan` | Discover existing project `.env` files → consolidate keys into the vault (with live-key validation) |
| `/tikeytaka:add` | Register a new key without chat exposure |
| `/tikeytaka:list` | Managed services and project connections |
| `/tikeytaka:sync` | Propagate the vault to every connected `.env` |

## Connecting a new device

1. Wait for the cloud folder to sync (the vault file arrives)
2. `bash <plugin-path>/bin/tkt init` — enter the same vault passphrase
3. `tkt sync` — done
