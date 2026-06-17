import { buildIntelligenceRoute } from '@/lib/evez/intelligence-router';

export const runtime = 'nodejs';

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const task = String(body?.task ?? '');

  if (!task) {
    return Response.json({ ok: false, error: 'Missing task' }, { status: 400 });
  }

  const plan = buildIntelligenceRoute(task);
  return Response.json({ ok: true, plan });
}
