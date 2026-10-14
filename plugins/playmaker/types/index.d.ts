export type TaskState = 'todo' | 'doing' | 'done' | 'waiting'

export type Task = {
  /** M2-T1 같은 안정 ID (goaljaby 0.7+ 체크리스트) */
  id?: string
  text: string
  state: TaskState
  /** 체크리스트가 아니라 마일스톤 상태에서 추정한 상태 */
  inferred: boolean
}

export type Milestone = {
  id: string
  name: string
  status: 'todo' | 'current' | 'done'
  /** 진행 중이지만 사람 판단·외부 입력을 기다리는 중 */
  waiting: boolean
  tasks: Task[]
  doneWhen: string
  /** checklist: PLAN 체크리스트 / legacy: PROGRESS·범위에서 추정 */
  source: 'checklist' | 'legacy'
}

export type Board = {
  dir: string
  goal: string
  milestones: Milestone[]
  failed: number
  lastValidation: string
  allDone: boolean
  /** PLAN 체크리스트와 PROGRESS가 서로 다르게 말하는 곳 */
  mismatch: string[]
  updatedAt: number
  /** 끝나지 않았고 최근 7일 안에 PLAN 또는 PROGRESS가 바뀐 골 */
  active?: boolean
  /** band·자동 표시 여부 (자동: active, /playmaker 실행 시 항상) */
  show?: boolean
}

declare module 'claude-code' {
  // 카드에서 세션에 보낸 지시: 그 턴이 끝날 때까지 다른 카드 행동을 잠근다
  type Pending = { task: string; label: string; at: number; started: boolean }

  interface PluginState {
    playmaker: {
      board: Board | null
      view: 'state' | 'milestone'
      expandDone: boolean
      pending: Pending | null
      selected: { key: string; compose: boolean } | null
      webUrl: string | null
    }
  }
}
