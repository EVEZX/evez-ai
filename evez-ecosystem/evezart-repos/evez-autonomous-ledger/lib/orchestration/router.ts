import { getHotRoute, setHotRoute } from '@/lib/context/cache';
import { listLiveProviders } from '@/lib/providers/select';
import { pickAgentForTask } from '@/lib/agents/supervisor';

export async function chooseRoute(input: { task: string; context: unknown }) {
  const cacheKey = input.task.slice(0, 120).toLowerCase();
  const cached = await getHotRoute(cacheKey);
  if (cached) return cached;

  const providers = await listLiveProviders();
  const agent = await pickAgentForTask(input.task);
  const provider = providers.find(
    (p) => p.enabled && p.healthy && p.supports.includes(agent.type),
  );

  const route = {
    agent,
    provider,
    reasonTrace: [
      `agent=${agent.type}`,
      `provider=${provider?.name ?? 'none'}`,
      `providers_considered=${providers.length}`,
    ],
  };

  await setHotRoute(cacheKey, route, 300);
  return route;
}
