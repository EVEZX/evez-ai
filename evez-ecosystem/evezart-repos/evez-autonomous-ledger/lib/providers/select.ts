export interface ProviderProfile {
  id: string;
  name: string;
  enabled: boolean;
  healthy: boolean;
  supports: string[];
  priority: number;
  failoverOrder: number;
}

export async function listLiveProviders(): Promise<ProviderProfile[]> {
  const providers: ProviderProfile[] = [];

  if (process.env.OPENAI_API_KEY) {
    providers.push({
      id: 'openai',
      name: 'OpenAI',
      enabled: true,
      healthy: true,
      supports: ['supervisor', 'research', 'coding', 'writing', 'qa', 'synthesis'],
      priority: 1,
      failoverOrder: 1,
    });
  }

  if (process.env.ANTHROPIC_API_KEY) {
    providers.push({
      id: 'anthropic',
      name: 'Anthropic',
      enabled: true,
      healthy: true,
      supports: ['supervisor', 'research', 'coding', 'writing', 'qa', 'synthesis'],
      priority: 2,
      failoverOrder: 2,
    });
  }

  return providers;
}
