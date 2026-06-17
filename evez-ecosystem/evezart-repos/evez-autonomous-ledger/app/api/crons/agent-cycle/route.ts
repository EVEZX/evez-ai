import { runAgentCycle } from '@/lib/evez/runtime';

export const runtime = 'nodejs';

export async function GET(req: Request) {
  if (req.headers.get('authorization') !== `Bearer ${process.env.CRON_SECRET}`) {
    return new Response('Unauthorized', { status: 401 });
  }

  const result = runAgentCycle();
  return Response.json({ ok: true, result });
}
