[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | Español | [中文](README.zh.md)

# tikeytaka

Plugin de bóveda central de claves API — consolida las claves dispersas en archivos `.env` en una única bóveda cifrada, registra claves nuevas sin exponerlas en el chat y propaga una sola actualización a todos los proyectos. Mientras haces tiki-taka con la IA, las claves se consultan y conectan automáticamente.

## Quick Start

### 1. Añade el marketplace

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. Instala

```
/plugin install tikeytaka
```

### 3. Reinicia Claude Code

(Los comandos nuevos solo se registran tras reiniciar.)

### 4. Ejecuta

```
/tikeytaka
```

Después ejecuta una vez `bash <ruta-del-plugin>/bin/tkt init` en tu propia terminal (el comando te indica la ruta exacta) y consolida tus claves existentes con `/tikeytaka:scan`.

## ¿Por qué tikeytaka?

Un escaneo real del directorio home encontró **45 archivos `.env`**, con la misma clave presente en 6 archivos bajo 3 valores distintos — la mayoría muertas. Con claves dispersas no puedes rotar, no puedes revocar y ni siquiera sabes qué tienes. tikeytaka convierte un archivo cifrado en la fuente de verdad y cada `.env` en una copia refrescada por la máquina.

- **Sin registro**: detecta automáticamente una carpeta en la nube que ya uses (iCloud Drive / Google Drive / OneDrive / Dropbox) y sincroniza un único archivo cifrado. Si no hay, modo local de un solo dispositivo. La ruta elegida queda fijada y nunca cambia en silencio.
- **Seguro por construcción**: AES-256-CBC + PBKDF2 (600k iteraciones, SHA-256) con hash de integridad integrado (formato TKT2). Una bóveda corrupta o a medio sincronizar se detecta y la herramienta se detiene — **nunca sobrescribe el original** y conserva una generación `.bak` antes de cada cambio.
- **Integración con el SO**: la frase de descifrado vive en el Llavero de macOS / secret-tool de Linux / DPAPI de Windows. El respaldo en archivo 0600 solo existe con consentimiento explícito (`TKT_ALLOW_FILE_FALLBACK=1`).
- **Exposición mínima**: los valores entran solo por entrada oculta de terminal (`tkt setp`) o stdin (`set-stdin`) — nunca por chat, historial del shell ni argv de procesos.

## Cómo funciona

```
tú / Claude  ──►  bin/tkt (CLI bash único)
                    ├── secrets.enc   bóveda cifrada — viaja por tu carpeta en la nube
                    ├── llavero SO    guarda la única frase — nunca sale del dispositivo
                    └── map.tsv       cableado local: qué .env recibe qué clave
```

Por la nube solo circula texto cifrado; la llave para abrirlo nunca sale de tus dispositivos. `tkt sync` descifra una vez, verifica la integridad y refresca cada `.env` mapeado preservando los permisos del archivo.

## Comandos

| Comando | Qué hace |
|---|---|
| `/tikeytaka` | Resumen de estado (nº de claves, ubicación de la bóveda, propagación pendiente) |
| `/tikeytaka:use` | **Cuando una tarea necesita una clave, consulta primero la bóveda → conecta y prueba automáticamente** (sin preguntar) |
| `/tikeytaka:scan` | Descubre archivos `.env` existentes → consolida claves en la bóveda (con validación de claves vivas) |
| `/tikeytaka:add` | Registra una clave nueva sin exposición en el chat |
| `/tikeytaka:list` | Servicios gestionados y conexiones de proyectos |
| `/tikeytaka:sync` | Propaga la bóveda a cada `.env` conectado |

## Conectar un dispositivo nuevo

1. Espera a que la carpeta en la nube sincronice (llega el archivo de la bóveda)
2. `bash <ruta-del-plugin>/bin/tkt init` — introduce la misma frase de la bóveda
3. Cablea los proyectos de este dispositivo: `/tikeytaka:scan` (o `tkt map-add`) — la lista de mapeos es local por diseño
4. `tkt sync`

## Requisitos

- `bash`, `openssl` (incluidos en macOS, Linux y Git for Windows — el shell de Windows de Claude Code)
- Un almacén de secretos: Llavero de macOS / `secret-tool` de Linux / PowerShell de Windows (DPAPI)

| Plataforma | Estado |
|---|---|
| macOS (Llavero + iCloud/otros) | Verificado |
| Windows (Git Bash + OneDrive/Google Drive + DPAPI) | Implementado, provisional |
| Linux (secret-tool + Dropbox, o `TIKEYTAKA_DIR` manual) | Implementado, provisional |

## Límites conocidos (divulgación honesta)

- **Sin edición concurrente**: `set`/`del` simultáneos desde dos dispositivos hacen que un lado se detenga por detección de conflicto (los datos quedan a salvo). Herramienta monousuario por diseño.
- El registro en el Llavero de macOS (`security -w`) pasa la frase por argv una vez durante init — limitación de la herramienta.
- Es una bóveda personal. Para compartir en equipo, control de acceso o auditoría, usa un SaaS de secretos (p. ej. Infisical).
- Ninguna bóveda local protege una cuenta ya comprometida (keyloggers, etc.).

## Código fuente

https://github.com/fivetaku/tikeytaka — parte del marketplace [gptaku-plugins](https://github.com/fivetaku/gptaku_plugins).

## Licencia

[MIT](./LICENSE) — véase también [DISCLAIMER.md](./DISCLAIMER.md).
