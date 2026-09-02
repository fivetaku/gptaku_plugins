[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | Español

<div align="center">

# GPTaku Plugins

**Deja de explicar lo que quieres — que Claude Code lo haga.**

17 plugins que buscan en sitios bloqueados, extraen sistemas de diseño de cualquier URL,
revisan tu código y convierten ideas en bruto en PRDs — todo dentro de Claude Code.

<p>
  <a href="#-todos-los-plugins-por-categoría"><img src="https://img.shields.io/badge/plugins-17-6E56CF" alt="17 plugins"></a>
  <a href="https://docs.anthropic.com/en/docs/claude-code"><img src="https://img.shields.io/badge/platform-Claude_Code-D97757?logo=claude" alt="Claude Code"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-3FB950" alt="MIT"></a>
  <a href="https://github.com/fivetaku/insane-search/stargazers"><img src="https://img.shields.io/github/stars/fivetaku/insane-search?style=flat&color=F0B72F" alt="stars"></a>
</p>

<!-- Purpose-first hero banner with light/dark theme support -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-purpose-wallbreak.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/hero-purpose-wallbreak.png">
  <img src="assets/hero-purpose-wallbreak.png" width="980" alt="Banner cinematográfico de GPTaku Plugins que muestra un taladro-plugin atravesando los límites de Claude Code">
</picture>

<sub><a href="#-instalación">Instalación</a> · <a href="#-empieza-aquí--la-serie-insane">Empieza aquí</a> · <a href="#-todos-los-plugins-por-categoría">Todos los plugins</a> · <a href="#-confianza--configuración">Confianza</a></sub>

</div>

---

## ⚡ Instalación

Ejecuta esto dentro de Claude Code:

```bash
# 1) Add the marketplace once
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git

# 2) Start with the lowest-friction flagship
/plugin install insane-search@gptaku-plugins

# 3) Apply without restarting the whole app
/reload-plugins
```

**¿Nuevo por aquí? Instala `insane-search` primero.** La mayoría de los plugins solo necesitan una sesión de Claude Code en marcha — unos pocos conectan un servicio externo ([ver Confianza y configuración](#-confianza--configuración)).

---

## 🔥 Empieza aquí — la serie insane-*

> Los cuatro buques insignia. Rompen los muros donde todo lo demás se queda parado.

### 🔎 insane-search · <a href="https://github.com/fivetaku/insane-search/stargazers"><img src="https://img.shields.io/github/stars/fivetaku/insane-search?style=flat&color=F0B72F" alt="stars"></a>
**Cuando Claude Code no puede leer una página bloqueada, este entra igual.**
¿Te topaste con un WAF, un 403, un CAPTCHA o un muro de inicio de sesión? Va escalando a través de lectores de API públicas, gateways de sindicación, suplantación TLS y un navegador headless real, probando uno tras otro hasta que alguno pasa. Sin claves de API.

```bash
/plugin install insane-search@gptaku-plugins
```
> **Prueba:** *"Busca qué dice la gente sobre Claude Code en Reddit y resume los hilos más populares."*

### 🎨 insane-design
**Extrae el sistema de diseño de cualquier sitio web. En un solo comando.**
Lee el CSS real y saca lo que importa: color, tipografía, espaciado, radios, sombras, fuentes. El resultado es un set de tokens limpio, una especificación `design.md` y un reporte HTML con copiar-al-clic.

```bash
/plugin install insane-design@gptaku-plugins
```
> **Prueba:** *"Extrae el sistema de diseño de https://stripe.com"*

### 🧠 insane-review
**GPT-5.5 Pro no tiene API. Este plugin lo usa desde dentro de Claude Code de todos modos.**
Empaqueta el código relevante con `repomix`, lo pasa por tu sesión web de ChatGPT Pro con sesión iniciada y trae de vuelta una revisión línea por línea.

```bash
/plugin install insane-review@gptaku-plugins
```
> **Prueba:** *"Haz que GPT-5.5 Pro revise el flujo de autenticación en src/auth."*

### 📚 insane-research
**Entra una pregunta. Sale un informe de investigación multiagente con citas.**
Un pipeline de 7 fases: delimita la pregunta, despliega agentes de investigación especializados, califica y contrasta cada fuente, y luego compila un informe estructurado en Markdown.

```bash
/plugin install insane-research@gptaku-plugins
```
> **Prueba:** *"Investiga la mejor base de datos vectorial para RAG en 2026, con citas."*

---

## 🧭 Elige según el muro con el que te topes

<div align="center">
  <img src="assets/flow-transform.png" width="980" alt="Mapa de antes-y-después que muestra los muros de Claude Code enrutados a través de GPTaku Plugins hacia web desbloqueada, revisión pro, PRD listo para IA, contexto ligero y resultados de equipos de agentes">
</div>

<table width="100%">
<tr>
  <td><strong>Si Claude Code se atasca en...</strong></td>
  <td width="25%"><strong>Instala esto</strong></td>
</tr>
<tr>
  <td>Una página pública bloqueada, HTML vacío o contenido web específico de una plataforma</td>
  <td><code>insane-search</code></td>
</tr>
<tr>
  <td>Una revisión de código que necesita otro modelo potente</td>
  <td><code>insane-review</code></td>
</tr>
<tr>
  <td>El estilo de un sitio web que quieres reutilizar con precisión</td>
  <td><code>insane-design</code></td>
</tr>
<tr>
  <td>Una pregunta de investigación amplia que necesita citas</td>
  <td><code>insane-research</code></td>
</tr>
<tr>
  <td>Una idea de app vaga sin especificación de producto</td>
  <td><code>show-me-the-prd</code></td>
</tr>
<tr>
  <td>Un PRD que necesita un contrato de ejecución <code>/goal</code> verificado</td>
  <td><code>goaljaby</code></td>
</tr>
<tr>
  <td>Un desarrollo grande que conviene repartir entre varios workers</td>
  <td><code>pumasi</code> o <code>kkirikkiri</code></td>
</tr>
<tr>
  <td>Una captura de pantalla, un log largo o una referencia copiada</td>
  <td><code>dd</code></td>
</tr>
<tr>
  <td>Una duda sobre una librería/API que necesita docs oficiales</td>
  <td><code>docs-guide</code></td>
</tr>
<tr>
  <td>Gmail, Calendar, Drive, Docs, Sheets, Slides, Chat, Tasks o Meet</td>
  <td><code>nopal</code></td>
</tr>
<tr>
  <td>GitHub te suena a otro idioma</td>
  <td><code>git-teacher</code></td>
</tr>
<tr>
  <td>Quieres mejorar tu forma de trabajar con Claude Code</td>
  <td><code>vibe-sunsang</code></td>
</tr>
<tr>
  <td>Quieres crear tu propio plugin/skill/agente</td>
  <td><code>skillers-suda</code></td>
</tr>
</table>

---

## 🔒 Confianza & configuración

La mayoría de los plugins solo necesitan una sesión de Claude Code en marcha — **sin clave de API adicional.** Las pocas excepciones que se conectan a servicios externos lo dicen de entrada:

<table width="100%">
<tr>
  <td width="25%"><strong>OAuth de Google Workspace</strong></td>
  <td><code>nopal</code> (requiere una cuenta de Google y una validación de inicio de sesión única a través del CLI <code>gws</code>)</td>
</tr>
<tr>
  <td width="25%"><strong>Sesión de navegador con sesión iniciada</strong></td>
  <td><code>insane-review</code> (requiere una sesión web activa de ChatGPT Plus/Pro con sesión iniciada; sin claves de API)</td>
</tr>
<tr>
  <td width="25%"><strong>CLI externo</strong></td>
  <td><code>pumasi</code> (requiere tener instalado el Codex CLI en tu sistema)</td>
</tr>
</table>

Todos los plugins son de código abierto. El README de cada submódulo detalla sus límites de comandos exactos, sus skills y sus dependencias.

---

## 📦 Todos los plugins por categoría

### 🔎 Investigación & web
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-search">insane-search</a></strong></td>
  <td>Bypass automático para sitios web bloqueados — WAF/403/CAPTCHA, sin claves de API.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-research">insane-research</a></strong></td>
  <td>Investigación profunda multiagente — triangulada por fuentes, respaldada por citas.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/docs-guide">docs-guide</a></strong></td>
  <td>Respuestas ancladas en docs oficiales — llms.txt + 68 librerías.</td>
</tr>
</table>

### 🎨 Diseño & calidad
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-design">insane-design</a></strong></td>
  <td>Cualquier URL → tokens de diseño + <code>design.md</code> + reporte HTML interactivo.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/insane-review">insane-review</a></strong></td>
  <td>Revisión de código con GPT-5.5 Pro desde dentro de Claude Code (sin API).</td>
</tr>
</table>

### 🚀 Planifica & entrega
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/show-me-the-prd">show-me-the-prd</a></strong></td>
  <td>Una frase → 4 documentos de diseño (PRD, modelo de datos, fases, especificación del proyecto).</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/goaljaby">goaljaby</a></strong></td>
  <td>PRD → contrato de ejecución de workflow <code>/goal</code> revisado.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/pumasi">pumasi</a></strong></td>
  <td>Claude Code como PM + Codex CLI como equipo de desarrollo en paralelo.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/kkirikkiri">kkirikkiri</a></strong></td>
  <td>Arma un equipo de agentes de IA a partir de una sola frase.</td>
</tr>
</table>

### 🌱 Aprende & construye mejor
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/git-teacher">git-teacher</a></strong></td>
  <td>Onboarding a Git/GitHub mediante analogías con servicios en la nube.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/vibe-sunsang">vibe-sunsang</a></strong></td>
  <td>Mentor de IA — análisis de conversaciones + informes de progreso.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/skillers-suda">skillers-suda</a></strong></td>
  <td>4 agentes expertos debaten tu idea hasta convertirla en una skill funcional.</td>
</tr>
</table>

### ⚙️ Espacio de trabajo
<table width="100%">
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/nopal">nopal</a></strong></td>
  <td>Orquestación de Google Workspace — 9 servicios.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/dd">dd</a></strong></td>
  <td>Suelta texto/imagen del portapapeles en Claude Code (<code>/dd</code>, <code>/ㅇㅇ</code>).</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/gaseo">gaseo</a></strong></td>
  <td>Manda a Paseo la sesión de Claude Code en la que estás (<code>/gaseo</code>).</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/tikeytaka">tikeytaka</a></strong></td>
  <td>Bóveda central de claves API — consolida las claves .env dispersas en una bóveda cifrada sincronizada en la nube; registra, conecta y verifica claves conversando.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/ddiring">ddiring</a></strong></td>
  <td>Alertas de finalización multisesión — qué carpeta, qué terminal y qué tarea en una sola notificación; clic para saltar a esa app.</td>
</tr>
<tr>
  <td width="25%"><strong><a href="https://github.com/fivetaku/sangse">sangse</a></strong></td>
  <td>Páginas de detalle para e-commerce coreano — datos del producto → hoja de cortes de imagen verificada (estilo Kurly / Coupang / Smart Store) con filtros de cumplimiento y QA de 3 puertas (<code>/sangse</code>).</td>
</tr>
</table>

---

## Requisitos

- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** únicamente — sin Codex / Antigravity / otras interfaces de terminal.
- **Windows**: Ejecútalo en WSL2 (`wsl --install`) · **macOS / Linux**: Funciona sin más.
- Algunos plugins instalan automáticamente herramientas CLI opcionales (`gh`, `yt-dlp`, Playwright MCP) cuando hace falta.

## ¿Por qué GPTaku?

Cada plugin derriba un muro concreto con el que te topas mientras aprendes a construir con IA — una página bloqueada, un PRD en blanco, un diseño que no logras aplicar ingeniería inversa. Pensado primero en coreano, publicado bilingüe, combinable, sin bucles de registro.

## Licencia

MIT

---

<div align="center">

**Vuélvete AI Native, un muro a la vez.**

</div>
