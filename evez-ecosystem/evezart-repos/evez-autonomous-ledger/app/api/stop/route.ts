import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req: Request) {
  const body = await req.json();

  return NextResponse.json({
    ok: true,
    action: 'stop',
    jobId: body.jobId ?? null,
    ts: new Date().toISOString(),
  });
}
