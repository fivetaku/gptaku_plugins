# Changelog

## 0.2.0 — 2026-08-23

- **Vault engine rewritten (TKT2)** after an internal audit + GPT-5.6 Sol (Pro) review found the v0.1.0 streaming pipeline could overwrite the vault with empty content on a corrupted/half-synced file or a malformed service name. Writes are now transactional: decrypt → integrity-verify → edit → re-encrypt → round-trip compare → conflict check → keep a `.bak` generation → atomic rename. The original vault is never touched until every step succeeds.
- Encryption parameters made explicit and cross-platform: AES-256-CBC + PBKDF2 (600k iterations, SHA-256), verified round-trip between LibreSSL (macOS) and OpenSSL 3.
- Vault plaintext now carries a `#TKT2` magic + SHA-256 integrity hash — corruption and tampering are detected instead of silently accepted.
- Secrets no longer pass through process argv: openssl passphrase via stdin, new `set-stdin` command for automation, `setp` no longer re-executes a child process, `.env` rewriting moved from awk to pure bash.
- Input validation before any write: service/variable whitelists, tab/newline/quote rejection.
- `init` verifies the passphrase **before** storing it; the chosen cloud path is pinned in `vault.path`.
- `sync` preserves original `.env` permissions (0600 stays 0600), normalizes duplicate variable definitions, and distinguishes "vault unreadable" from "0 keys".
- New **`use` skill**: when a task needs an API key, the vault is checked first and the key is wired + live-tested automatically — the user is only asked if the vault doesn't have it. Official docs (via docs-guide, web-search fallback) are consulted for env var names and current model ids.
- Platform branches: Windows (Git Bash + DPAPI passphrase store, OneDrive/Google Drive/iCloud path detection incl. WSL `/mnt/c`), Linux (secret-tool). macOS verified; Windows/Linux provisional.
- Regression suite `tests/regression.sh` (31 cases) covering vault-destruction scenarios, ps exposure, permission preservation, and cross-implementation decryption.

## 0.1.0 — 2026-08-23

- Initial release: encrypted cloud-synced API key vault (`bin/tkt`) with scan / add / list / sync skills, zero-signup design (existing cloud folder + OS secret store).
