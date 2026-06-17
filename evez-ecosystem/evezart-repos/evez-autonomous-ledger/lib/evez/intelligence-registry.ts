export type IntelligenceCapability =
  | 'supervisor'
  | 'research'
  | 'coding'
  | 'writing'
  | 'qa'
  | 'synthesis'
  | 'planning'
  | 'memory';

export type IntelligenceProvider = {
  id: string;
  name: string;
  envKey: string;
  enabled: boolean;
  healthy: boolean;
  strengths: IntelligenceCapability[];
  latencyClass: 'fast' | 'balanced' | 'deep';
  retentionBias: 'high' | 'medium' | 'low';
  multiplier: number;
};

function providerEnabled(envKey: string) {
  return Boolean(process.env[envKey]);
}

export function listIntelligenceProviders(): IntelligenceProvider[] {
  const providers: IntelligenceProvider[] = [
    {
      id: 'openai',
      name: 'OpenAI',
      envKey: 'OPENAI_API_KEY',
      enabled: providerEnabled('OPENAI_API_KEY'),
      healthy: true,
      strengths: ['supervisor', 'research', 'coding', 'writing', 'qa', 'synthesis', 'planning', 'memory'],
      latencyClass: 'balanced',
      retentionBias: 'high',
      multiplier: 1.0,
    },
    {
      id: 'anthropic',
      name: 'Anthropic',
      envKey: 'ANTHROPIC_API_KEY',
      enabled: providerEnabled('ANTHROPIC_API_KEY'),
      healthy: true,
      strengths: ['supervisor', 'research', 'writing', 'synthesis', 'planning', 'memory'],
      latencyClass: 'deep',
      retentionBias: 'high',
      multiplier: 1.05,
    },
    {
      id: 'openrouter',
      name: 'OpenRouter',
      envKey: 'OPENROUTER_API_KEY',
      enabled: providerEnabled('OPENROUTER_API_KEY'),
      healthy: true,
      strengths: ['supervisor', 'research', 'coding', 'writing', 'qa', 'synthesis', 'planning'],
      latencyClass: 'balanced',
      retentionBias: 'medium',
      multiplier: 1.08,
    },
    {
      id: 'groq',
      name: 'Groq',
      envKey: 'GROQ_API_KEY',
      enabled: providerEnabled('GROQ_API_KEY'),
      healthy: true,
      strengths: ['qa', 'coding', 'writing', 'synthesis'],
      latencyClass: 'fast',
      retentionBias: 'medium',
      multiplier: 0.94,
    },
    {
      id: 'huggingface',
      name: 'Hugging Face',
      envKey: 'HUGGINGFACE_API_KEY',
      enabled: providerEnabled('HUGGINGFACE_API_KEY'),
      healthy: true,
      strengths: ['research', 'coding', 'qa', 'synthesis'],
      latencyClass: 'balanced',
      retentionBias: 'medium',
      multiplier: 0.9,
    },
    {
      id: 'xai',
      name: 'xAI',
      envKey: 'XAI_API_KEY',
      enabled: providerEnabled('XAI_API_KEY'),
      healthy: true,
      strengths: ['research', 'writing', 'synthesis', 'planning'],
      latencyClass: 'balanced',
      retentionBias: 'medium',
      multiplier: 0.97,
    },
  ];

  return providers.filter((provider) => provider.enabled);
}
