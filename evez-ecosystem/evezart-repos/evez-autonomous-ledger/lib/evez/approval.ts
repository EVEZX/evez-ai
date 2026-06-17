export type ApprovalRisk = 'low' | 'medium' | 'high' | 'critical';
export type ApprovalKind = 'payment_link_create' | 'invoice_prepare' | 'invoice_finalize' | 'refund' | 'trade_proposal' | 'trade_execute';

export type ApprovalRequest = {
  id: string;
  kind: ApprovalKind;
  risk: ApprovalRisk;
  actor: string;
  summary: string;
  payload: Record<string, unknown>;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: string;
  approvedAt?: string;
  rejectedAt?: string;
  approver?: string;
};

const approvals = new Map<string, ApprovalRequest>();

export function requiresApproval(kind: ApprovalKind, risk: ApprovalRisk) {
  if (kind === 'trade_execute') return true;
  if (kind === 'refund') return true;
  if (kind === 'invoice_finalize') return true;
  return risk === 'high' || risk === 'critical';
}

export function createApprovalRequest(input: Omit<ApprovalRequest, 'id' | 'status' | 'createdAt'>) {
  const request: ApprovalRequest = {
    id: crypto.randomUUID(),
    status: 'pending',
    createdAt: new Date().toISOString(),
    ...input,
  };
  approvals.set(request.id, request);
  return request;
}

export function listApprovals() {
  return Array.from(approvals.values()).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export function respondToApproval(id: string, decision: 'approve' | 'reject', approver: string) {
  const current = approvals.get(id);
  if (!current) return null;
  const next: ApprovalRequest = decision === 'approve'
    ? { ...current, status: 'approved', approver, approvedAt: new Date().toISOString() }
    : { ...current, status: 'rejected', approver, rejectedAt: new Date().toISOString() };
  approvals.set(id, next);
  return next;
}
