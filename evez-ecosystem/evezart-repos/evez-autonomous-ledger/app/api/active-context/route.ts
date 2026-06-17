import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function GET() {
  return NextResponse.json({
    ok: true,
    context: {
      summary: 'Autopilot operator context is hydrated from recent task state, route hints, and enabled agent registry.',
      memory: [
        'Supervisor should act first and ask less.',
        'Prefer compact outputs with visible routing traces.',
        'Use live configured providers only when available.',
      ],
      sources: ['agent-registry', 'route-cache', 'operator-policy'],
    },
    ts: new Date().toISOString(),
  });
}
