import { NextResponse } from 'next/server';
import { chooseRoute } from '@/lib/orchestration/router';

export const runtime = 'nodejs';
export const maxDuration = 60;

export async function POST(req: Request) {
  const body = await req.json();
  const task = String(body.task ?? '');

  const context = { hydrated: true, task };
  const route = await chooseRoute({ task, context });

  return NextResponse.json({
    ok: true,
    mode: 'autopilot',
    task,
    route,
    context,
  });
}
