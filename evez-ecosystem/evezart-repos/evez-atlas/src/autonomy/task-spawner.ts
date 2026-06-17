import { EventSpine } from "../circuit/event-spine/event-spine";
import { AgentNavigation, NavigationResult, Agent } from "./navigation";

interface Task {
  id: string;
  agentId: string;
  input: any;
  status: "pending" | "running" | "completed" | "failed";
  result?: any;
  error?: string;
  createdAt: string;
  completedAt?: string;
}

interface DelegationResult {
  taskId: string;
  agentId: string;
  chain: string[];
  result?: any;
  error?: string;
  success: boolean;
}

class AutonomousTaskSpawner {
  private nav: AgentNavigation;
  private spine: EventSpine;
  private activeTasks: Map<string, Task> = new Map();
  private taskIdCounter: number = 0;

  constructor(nav: AgentNavigation, spine?: EventSpine) {
    this.nav = nav;
    this.spine = spine || new EventSpine();
  }

  private generateTaskId(): string {
    return `task-${Date.now()}-${++this.taskIdCounter}`;
  }

  async spawnTask(agentId: string, input: any): Promise<Task> {
    if (!this.nav.canSpawn()) {
      throw new Error("Agent spawning is disabled in manifest");
    }

    const taskId = this.generateTaskId();
    const task: Task = {
      id: taskId,
      agentId,
      input,
      status: "pending",
      createdAt: new Date().toISOString(),
    };

    this.activeTasks.set(taskId, task);

    this.spine.append({
      domain: "autonomy",
      kind: "TASK_SPAWNED",
      payload: { taskId, agentId, input }
    });

    return task;
  }

  async delegate(agentId: string, input: any, depth: number = 0): Promise<DelegationResult> {
    const maxDepth = 3;
    
    if (depth > maxDepth) {
      return {
        taskId: "",
        agentId,
        chain: [],
        error: "Max delegation depth exceeded",
        success: false,
      };
    }

    const discoverResult = this.nav.discover(agentId, depth);
    
    if (!discoverResult.found || !discoverResult.agent) {
      const fallback = this.nav.getFallbackChain(agentId);
      if (fallback.length > 0) {
        return this.delegate(fallback[0], input, depth + 1);
      }
      return {
        taskId: "",
        agentId,
        chain: discoverResult.chain,
        error: `Agent ${agentId} not found and no fallback available`,
        success: false,
      };
    }

    const task = await this.spawnTask(agentId, input);
    
    const delegates = this.nav.getDelegates(agentId);
    
    if (delegates.length > 0 && discoverResult.agent.delegatable) {
      for (const delegate of delegates) {
        const subResult = await this.delegate(delegate.id, input, depth + 1);
        if (subResult.success) {
          task.status = "completed";
          task.result = subResult.result;
          task.completedAt = new Date().toISOString();
          
          this.spine.append({
            domain: "autonomy",
            kind: "TASK_COMPLETED",
            payload: { taskId: task.id, agentId, delegateResult: subResult }
          });
          
          return {
            taskId: task.id,
            agentId,
            chain: discoverResult.chain,
            result: subResult.result,
            success: true,
          };
        }
      }
    }

    task.status = "completed";
    task.result = { executed: true, agent: discoverResult.agent.role };
    task.completedAt = new Date().toISOString();

    this.spine.append({
      domain: "autonomy",
      kind: "TASK_COMPLETED",
      payload: { taskId: task.id, agentId }
    });

    return {
      taskId: task.id,
      agentId,
      chain: discoverResult.chain,
      result: task.result,
      success: true,
    };
  }

  getTask(taskId: string): Task | undefined {
    return this.activeTasks.get(taskId);
  }

  getActiveTasks(): Task[] {
    return Array.from(this.activeTasks.values());
  }

  getTasksByAgent(agentId: string): Task[] {
    return Array.from(this.activeTasks.values()).filter(t => t.agentId === agentId);
  }

  async executeWithFallback(
    primaryAgentId: string,
    input: any,
    fallbackAgentIds: string[]
  ): Promise<DelegationResult> {
    const result = await this.delegate(primaryAgentId, input);
    
    if (result.success) {
      return result;
    }

    for (const fallbackId of fallbackAgentIds) {
      const fallbackResult = await this.delegate(fallbackId, input);
      if (fallbackResult.success) {
        this.spine.append({
          domain: "autonomy",
          kind: "FALLBACK_USED",
          payload: { primary: primaryAgentId, fallback: fallbackId }
        });
        return fallbackResult;
      }
    }

    return {
      taskId: "",
      agentId: primaryAgentId,
      chain: [],
      error: "All agents and fallbacks failed",
      success: false,
    };
  }
}

export { AutonomousTaskSpawner, Task, DelegationResult };