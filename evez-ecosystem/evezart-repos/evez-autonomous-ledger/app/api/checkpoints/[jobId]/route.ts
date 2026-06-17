import { NextResponse } from 'next/server';
import type { JobCheckpoint } from '@/lib/types/job';

export const runtime = 'nodejs';

export async function GET(
  _req: Request,
  context: { params: { jobId: string } },
) {
  const { jobId } = context.params;

  const checkpoints: JobCheckpoint[] = [
    {
      id: `${jobId}-cp-1`,
      jobId,
      stage: 'planned',
      ts: new Date().toISOString(),
      summary: 'Objective normalized and execution route prepared.',
    },
    {
      id: `${jobId}-cp-2`,
      jobId,
      stage: 'routed',
      ts: new Date().toISOString(),
      summary: 'Provider and specialist agent selected for next execution stage.',
    },
  ];

  return NextResponse.json({
    ok: true,
    jobId,
    checkpoints,
    ts: new Date().toISOString(),
  });
}
