export interface ProcessingModeConfig {
  mode: "sequential" | "swarm";
  depthLimits: Record<number, number | null>;
}

export interface TraceNode {
  id: string;
  children?: TraceNode[];
  metadata?: Record<string, unknown>;
}

const DEFAULT_DEPTH_LIMITS: Record<number, number | null> = {
  0: 0,
  1: 1,
  2: 2,
  3: null,
};

const limitTraceDepth = (node: TraceNode, depth: number): TraceNode => {
  if (depth <= 0 || !node.children) {
    return { id: node.id };
  }
  return {
    id: node.id,
    children: node.children.map((child) => limitTraceDepth(child, depth - 1)),
  };
};

export const resolveAwareness = (
  trace: TraceNode,
  tier: number,
  config: ProcessingModeConfig = {
    mode: "sequential",
    depthLimits: DEFAULT_DEPTH_LIMITS,
  },
): TraceNode => {
  const depthLimit = tier in config.depthLimits 
    ? config.depthLimits[tier] 
    : (tier in DEFAULT_DEPTH_LIMITS ? DEFAULT_DEPTH_LIMITS[tier] : 0);

  if (config.mode === "swarm") {
    if (tier < 3) {
      throw new Error("Swarm mode requires tier 3 access");
    }
    return trace;
  }

  if (depthLimit === null) {
    return trace;
  }

  return limitTraceDepth(trace, depthLimit);
};
