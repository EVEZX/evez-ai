export const AGENT_TYPES = [
  'supervisor',
  'research',
  'coding',
  'writing',
  'operations',
  'summarization',
  'qa',
  'synthesis',
  'routing',
  'memory-distillation',
  'provider-health',
  'checkpoint-restore',
  'social-persona',
  'context-hydration',
] as const;

export type AgentType = (typeof AGENT_TYPES)[number];

export interface AgentProfile {
  type: AgentType;
  label: string;
  specialties: string[];
  outputStyle: 'compact' | 'balanced' | 'deep';
  enabled: boolean;
}

export const DEFAULT_AGENT_REGISTRY: AgentProfile[] = [
  {
    type: 'supervisor',
    label: 'Supervisor',
    specialties: ['routing', 'delegation', 'autopilot'],
    outputStyle: 'compact',
    enabled: true,
  },
  {
    type: 'research',
    label: 'Research',
    specialties: ['retrieval', 'analysis', 'discovery'],
    outputStyle: 'balanced',
    enabled: true,
  },
  {
    type: 'coding',
    label: 'Coding',
    specialties: ['implementation', 'patching', 'debugging'],
    outputStyle: 'compact',
    enabled: true,
  },
  {
    type: 'writing',
    label: 'Writing',
    specialties: ['drafting', 'copy', 'artifacts'],
    outputStyle: 'balanced',
    enabled: true,
  },
  {
    type: 'operations',
    label: 'Operations',
    specialties: ['health', 'retry', 'scheduling'],
    outputStyle: 'compact',
    enabled: true,
  },
  {
    type: 'qa',
    label: 'QA',
    specialties: ['validation', 'regression', 'checks'],
    outputStyle: 'compact',
    enabled: true,
  },
  {
    type: 'synthesis',
    label: 'Synthesis',
    specialties: ['merge', 'final-answer', 'handoff'],
    outputStyle: 'balanced',
    enabled: true,
  },
];
