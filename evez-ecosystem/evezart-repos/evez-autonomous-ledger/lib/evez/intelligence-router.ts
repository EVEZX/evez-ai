import { listIntelligenceProviders, type IntelligenceCapability } from '@/lib/evez/intelligence-registry';

export type IntelligenceRoutePlan = {
  task: string;
  category: IntelligenceCapability;
  primary: string | null;
  fallbacks: string[];
  universalRetention: {
    preserveSummary: true;
    preserveReasonTrace: true;
    preserveArtifacts: true;
  };
  reasonTrace: string[];
};

function classifyTask(task: string): IntelligenceCapability {
  const t = task.toLowerCase();
  if (/(code|bug|build|deploy|typescript|api|refactor|test)/.test(t)) return 'coding';
  if (/(write|copy|thread|post|bio|email)/.test(t)) return 'writing';
  if (/(audit|validate|check|qa|verify)/.test(t)) return 'qa';
  if (/(research|study|discover|paper|academic)/.test(t)) return 'research';
  if (/(plan|roadmap|strategy|schedule)/.test(t)) return 'planning';
  return 'synthesis';
}

export function buildIntelligenceRoute(task: string): IntelligenceRoutePlan {
  const category = classifyTask(task);
  const providers = listIntelligenceProviders()
    .filter((provider) => provider.strengths.includes(category) || provider.strengths.includes('synthesis'))
    .sort((a, b) => b.multiplier - a.multiplier);

  const primary = providers[0] ?? null;
  const fallbacks = providers.slice(1).map((provider) => provider.id);

  return {
    task,
    category,
    primary: primary?.id ?? null,
    fallbacks,
    universalRetention: {
      preserveSummary: true,
      preserveReasonTrace: true,
      preserveArtifacts: true,
    },
    reasonTrace: [
      `category=${category}`,
      `providers=${providers.map((provider) => provider.id).join(',') || 'none'}`,
      `primary=${primary?.id ?? 'none'}`,
      'universal_retention=enabled',
    ],
  };
}
