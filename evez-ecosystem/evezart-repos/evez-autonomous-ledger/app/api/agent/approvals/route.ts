import { listApprovals, respondToApproval } from '@/lib/evez/approval';

export const runtime = 'nodejs';

export async function GET() {
  return Response.json({ ok: true, approvals: listApprovals() });
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const id = body?.id;
  const decision = body?.decision;
  const approver = body?.approver ?? 'operator';

  if (!id || (decision !== 'approve' && decision !== 'reject')) {
    return Response.json({ ok: false, error: 'Missing valid id or decision' }, { status: 400 });
  }

  const result = respondToApproval(id, decision, approver);
  if (!result) {
    return Response.json({ ok: false, error: 'Approval request not found' }, { status: 404 });
  }

  return Response.json({ ok: true, result });
}
