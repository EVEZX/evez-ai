import { NextResponse } from 'next/server';
import { DEFAULT_AGENT_REGISTRY } from '@/lib/agents/registry';

export const runtime = 'nodejs';
export const maxDuration = 60;

export async function POST(req: Request) {
  const body = await req.json();
  const objective = String(body.objective ?? body.task ?? '');

  const enabledAgents = DEFAULT_AGENT_REGISTRY.filter((agent) => agent.enabled);

  const phases = [
    {
      phase: 'intake',
      agent: 'supervisor',
      action: 'normalize-objective',
    },
    {
      phase: 'research',
      agent: 'research',
      action: 'gather-context',
    },
    {
      phase: 'execution',
      agent: /code|build|deploy|api/i.test(objective) ? 'coding' : 'writing',
      action: 'produce-primary-work',
    },
    {
      phase: 'validation',
      agent: 'qa',
      action: 'validate-output',
    },
    {
      phase: 'handoff',
      agent: 'synthesis',
      action: 'merge-and-return',
    },
  ];

  return NextResponse.json({
    ok: true,
    objective,
    agents: enabledAgents.map((a) => a.type),
    phases,
    ts: new Date().toISOString(),
  });
}
