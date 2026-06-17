import { NextResponse } from 'next/server';
import type { JobStep } from '@/lib/types/job';

export const runtime = 'nodejs';

export async function GET() {
  const steps: JobStep[] = [
    {
      id: 'step-intake',
      ts: new Date().toISOString(),
      agent: 'supervisor',
      provider: null,
      state: 'planning',
      summary: 'Supervisor normalized objective and prepared route handoff.',
    },
    {
      id: 'step-route',
      ts: new Date().toISOString(),
      agent: 'routing',
      provider: 'openai',
      state: 'routed',
      summary: 'Routing layer selected best available live provider and agent path.',
    },
  ];

  return NextResponse.json({
    ok: true,
    steps,
    ts: new Date().toISOString(),
  });
}
