import { getAgentStatus } from '@/lib/evez/runtime';

export const runtime = 'nodejs';

export async function GET() {
  return Response.json(getAgentStatus());
}
