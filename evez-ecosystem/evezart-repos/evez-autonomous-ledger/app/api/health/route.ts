export const runtime = 'nodejs';

export async function GET() {
  return Response.json({
    ok: true,
    service: 'evez-operator',
    env: process.env.NEXT_PUBLIC_VERCEL_ENV ?? 'unknown',
    target: process.env.NEXT_PUBLIC_VERCEL_TARGET_ENV ?? 'unknown',
    ts: new Date().toISOString(),
  });
}
