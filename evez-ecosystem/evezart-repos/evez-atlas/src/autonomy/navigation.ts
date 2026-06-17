import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";

interface Agent {
  id: string;
  role: string;
  delegatable?: boolean;
  sub_agents?: string[];
  limit_handling?: Record<string, string>;
  spawns?: string[];
  autonomy_level?: string;
  detection_patterns?: string[];
  bypass_strategies?: Record<string, string[]>;
}

interface AgentManifest {
  manifest_version: string;
  root_operator: string;
  agent_system: string;
  delegation_enabled?: boolean;
  navigation?: {
    agent_registry: string;
    discovery_mode: string;
    fallback_chain: string[];
  };
  agents: Agent[];
  handoff_order: string[];
  global_rules: string[];
  autonomy_config?: {
    max_delegation_depth: number;
    require_confirmation_on: string[];
    auto_bypass_limits: boolean;
    spawn_agents_on_demand: boolean;
  };
}

interface NavigationResult {
  agent: Agent | null;
  chain: string[];
  found: boolean;
}

class AgentNavigation {
  private manifest: AgentManifest;
  private cache: Map<string, Agent> = new Map();

  constructor(manifestPath?: string) {
    const defaultPath = join(dirname(__filename), "agent_manifest.json");
    const path = manifestPath || defaultPath;
    
    if (!existsSync(path)) {
      throw new Error(`Agent manifest not found: ${path}`);
    }
    
    const content = readFileSync(path, "utf-8");
    this.manifest = JSON.parse(content);
    
    for (const agent of this.manifest.agents) {
      this.cache.set(agent.id, agent);
    }
  }

  discover(agentId: string, depth: number = 0): NavigationResult {
    const chain: string[] = [];
    
    if (depth > (this.manifest.autonomy_config?.max_delegation_depth || 3)) {
      return { agent: null, chain, found: false };
    }

    const agent = this.cache.get(agentId);
    
    if (agent) {
      chain.push(agentId);
      return { agent, chain, found: true };
    }

    for (const fallbackId of (this.manifest.navigation?.fallback_chain || [])) {
      const fallback = this.cache.get(fallbackId);
      if (fallback) {
        chain.push(fallbackId);
        return { agent: fallback, chain, found: true };
      }
    }

    return { agent: null, chain, found: false };
  }

  findByRole(rolePattern: string): Agent | null {
    const pattern = rolePattern.toLowerCase();
    
    for (const agent of this.manifest.agents) {
      if (agent.role.toLowerCase().includes(pattern)) {
        return agent;
      }
    }
    
    return null;
  }

  getDelegates(agentId: string): Agent[] {
    const agent = this.cache.get(agentId);
    if (!agent || !agent.delegatable || !agent.sub_agents) {
      return [];
    }
    
    return agent.sub_agents
      .map(id => this.cache.get(id))
      .filter((a): a is Agent => a !== undefined);
  }

  getFallbackChain(agentId: string): string[] {
    const agent = this.cache.get(agentId);
    if (!agent) {
      return this.manifest.navigation?.fallback_chain || [];
    }
    
    return this.manifest.handoff_order.slice(
      this.manifest.handoff_order.indexOf(agentId) + 1
    );
  }

  getAllAgents(): Agent[] {
    return this.manifest.agents;
  }

  getAgentById(id: string): Agent | undefined {
    return this.cache.get(id);
  }

  canSpawn(): boolean {
    return this.manifest.autonomy_config?.spawn_agents_on_demand || false;
  }

  shouldConfirm(action: string): boolean {
    const confirmList = this.manifest.autonomy_config?.require_confirmation_on || [];
    return confirmList.includes(action);
  }

  getLimitBypassStrategies(limitType: string): string[] {
    for (const agent of this.manifest.agents) {
      if (agent.bypass_strategies && agent.limit_handling) {
        for (const [key, strategies] of Object.entries(agent.bypass_strategies)) {
          if (key === limitType || agent.limit_handling[limitType]) {
            return strategies;
          }
        }
      }
    }
    return [];
  }

  detectLimitPattern(errorMessage: string): string | null {
    const patterns: Record<string, string[]> = {
      rate_limit: ["rate limit", "too many requests", "429"],
      auth_blocked: ["unauthorized", "forbidden", "auth", "proxy"],
      timeout: ["timeout", "timed out", "504"],
      quota_exhausted: ["quota", "limit exceeded", "insufficient"],
      proxy_unavailable: ["proxy", "unavailable", "connection refused"]
    };

    const lowerMessage = errorMessage.toLowerCase();
    
    for (const [limitType, keywords] of Object.entries(patterns)) {
      if (keywords.some(kw => lowerMessage.includes(kw))) {
        return limitType;
      }
    }
    
    return null;
  }
}

export { AgentNavigation, NavigationResult, Agent, AgentManifest };
