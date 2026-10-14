[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | Español

# playmaker (플레이메이커)

<p align="center">
  <img src="assets/playmaker-hero-01.png" alt="playmaker" width="320">
</p>

> **Un tablero de objetivos en vivo dentro de Claude Code: ve hasta dónde llegó tu objetivo, qué está en curso y qué te está esperando.**

goaljaby marca el gol; playmaker lee todo el partido. playmaker es un mod de Claude Code que lee el `PLAN.md` y el `PROGRESS.md` de una carpeta de objetivo de goaljaby y dibuja un tablero **en espera · en curso · hecho** en un panel lateral. Cada tarjeta es una tarea con la etiqueta de su hito, las tareas que necesitan a una persona se marcan con ⏸ y un resumen de una línea aparece sobre el prompt.

[Inicio rápido](#inicio-rápido) • [Lo que ves](#lo-que-ves) • [Lo que lee](#lo-que-lee) • [Comandos](#comandos) • [Requisitos](#requisitos)

---

## Inicio rápido

### 1. Añade el marketplace

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. Instala

```
/plugin install playmaker
```

### 3. Reinicia Claude Code

### 4. Abre el tablero

```
/playmaker
```

playmaker busca hasta dos niveles por debajo de la carpeta actual y abre la carpeta de objetivo modificada más recientemente. Si hay un objetivo en curso modificado en los últimos 7 días, el tablero se abre solo al iniciar la sesión.

---

## Lo que ves

```
인증까지 붙인 MVP를 배포한다.
골 1/3 · 진행 M2 · 작업 2/6 · ⏸ 사람 대기 1
[마일스톤별 보기] [완료 펼치기]

대기 (2)                 진행 (2)                      완료 (2)
· [M2] 마일스톤 검증 실행  ▶ [M2] OAuth 콜백을 연결한다   ✓ M1 2건
· [M3] 배포 설정을 만든다  ⏸ [M2] 운영자 승인 계정 대기
```

En la v0.1 las etiquetas del tablero están en coreano (대기 = en espera, 진행 = en curso, 완료 = hecho, 골 = objetivo, 작업 = tareas, 사람 대기 = esperando a una persona). El texto de las tareas se muestra tal como está en tu PLAN.md, en cualquier idioma.

- **Tres columnas de estado.** Una tarjeta por tarea, con la etiqueta de su hito como `[M2]`. Si varios hitos están en curso a la vez, aparecen todos.
- **Las esperas humanas destacan.** Las tareas marcadas con `[!]`, o los hitos del formato antiguo cuyo registro de progreso dice que esperan a una persona, se muestran con ⏸.
- **Los paneles estrechos se apilan.** Con menos de 72 columnas el tablero apila En curso, En espera y Hecho de arriba abajo, y Hecho se pliega a un recuento por hito.
- **Vista por hito.** Un botón cambia a una lista de comprobación por hito (`[ ] [>] [x] [!]`).
- **En vivo.** Los cambios en PLAN.md o PROGRESS.md aparecen en menos de 3 segundos.
- **Actúa desde la tarjeta.** Al pulsar una tarjeta se abre debajo una fila de acciones según su estado: aprobar y seguir / ¿qué debo revisar? / poner en pausa para una tarea que espera a una persona, ¿cómo va? / ¿hay bloqueos? para una en curso, y **Escribir…** para enviar tus propias palabras. La instrucción entra directamente en esta sesión, con el ID de la tarea. Hasta que la sesión termina de responder, las demás tarjetas quedan bloqueadas para que no se acumulen instrucciones contradictorias. playmaker sigue sin editar PLAN.md; el agente actualiza las marcas.
- **Abrir en el navegador · Cerrar.** El botón **Abrir en el navegador** del panel arranca el tablero web y lo abre en tu navegador predeterminado, dejando un enlace pulsable en el panel. **✕ Cerrar** oculta el panel y la línea de resumen; `/playmaker` los vuelve a mostrar.
- **Aviso de discrepancia.** Si la lista del PLAN y PROGRESS no coinciden, el tablero lo indica con ⚠ en lugar de adivinar.

---

## Lo que lee

| Carpeta de objetivo | De dónde sale el estado de las tareas |
|---|---|
| goaljaby 0.7+ | Lista por hito en PLAN.md: `- [>] M2-T1: tarea` (`[ ]` en espera · `[>]` en curso · `[x]` hecho · `[!]` necesita a una persona) |
| goaljaby 0.6 o anterior, PLAN escritos a mano | Se deduce del estado del hito en PROGRESS.md y de la línea Scope del hito. Las tarjetas deducidas se ven atenuadas |

También lee PLAN en forma de tabla (`| M1a nombre | alcance |`) y encabezados `### M2 nombre`. playmaker solo lee archivos; nunca escribe en tu carpeta de objetivo.

---

## Comandos

| Comando | Qué hace |
|---|---|
| `/playmaker` | Busca la carpeta de objetivo más reciente bajo la carpeta actual y abre el tablero |
| `/playmaker <carpeta>` | Abre el tablero de una carpeta de objetivo concreta |
| `/playmaker web [carpeta]` | Arranca el tablero en el navegador (abajo) y muestra su dirección |

El comando también devuelve un resumen en texto, así que sirve donde no se puede dibujar un panel.

---

## Requisitos

- [Claude Code](https://code.claude.com/docs/en/plugins/mods/overview) **v2.1.287+** (mods), en la terminal o en la pestaña Code de la app de escritorio
- En la terminal, el panel se acopla junto a la conversación en `/tui fullscreen` con 110+ columnas; si no, se abre sobre el prompt
- En los hosts que no dibujan paneles (Paseo, `claude -p`, el chat de VS Code, sesiones en la nube) `/playmaker` responde con un resumen en texto, y `/playmaker web` sirve el mismo tablero como página web local (solo 127.0.0.1, se actualiza cada 2 segundos, requiere Node 22.18+)
- **Paseo:** playmaker detecta que se ejecuta en Paseo, arranca el tablero web cuando hay un objetivo en curso y lo abre como pestaña del navegador de Paseo (la reutiliza después; basta con moverla una vez a una división a la derecha). En el tablero web, elige la sesión de Paseo que trabaja en el objetivo y pulsa una tarjeta para enviarle las mismas acciones
- En la terminal, los clics del ratón funcionan en `/tui fullscreen`; si no, pulsa Ctrl+X y luego Tab para entrar en el panel y usa las flechas y Enter

### Funciona mejor con

| Plugin | Qué añade |
|--------|--------------|
| `goaljaby` 0.7+ | Escribe la lista por tarea que lee playmaker |

---

## Licencia

MIT · [Aviso legal](DISCLAIMER.md)

---

<div align="center">

**Marca con goaljaby. Lee el partido con playmaker.**

</div>
