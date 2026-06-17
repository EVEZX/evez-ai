import { createApprovalRequest, listApprovals, requiresApproval, type ApprovalKind, type ApprovalRisk } from '@/lib/evez/approval';

type AgentProposal = {
  kind: ApprovalKind;
  risk: ApprovalRisk;
  actor: string;
  summary: string;
  payload: Record<string, unknown>;
};

type AgentReceipt = {
  id: string;
  route: string;
  status: string;
  timestamp: string;
  payload?: unknown;
};

const receipts: AgentReceipt[] = [];

function writeReceipt(route: string, status: string, payload?: unknown) {
  const receipt: AgentReceipt = {
    id: crypto.randomUUID(),
    route,
    status,
    timestamp: new Date().toISOString(),
    payload,
  };
  receipts.unshift(receipt);
  return receipt;
}

export function listReceipts(limit = 25) {
  return receipts.slice(0, limit);
}

export function proposeAction(input: AgentProposal) {
  const approvalRequired = requiresApproval(input.kind, input.risk);
  const approval = createApprovalRequest({
    kind: input.kind,
    risk: input.risk,
    actor: input.actor,
    summary: input.summary,
    payload: input.payload,
  });
  const receipt = writeReceipt(`/agent/${input.kind}`, approvalRequired ? 'pending_approval' : 'prepared', {
    approvalId: approval.id,
    ...input,
  });
  return { approvalRequired, approval, receipt };
}

export function getAgentStatus() {
  const approvals = listApprovals();
  return {
    ok: true,
    checkedAt: new Date().toISOString(),
    approvalsPending: approvals.filter((a) => a.status === 'pending').length,
    approvals,
    receipts: listReceipts(10),
  };
}

export function runAgentCycle() {
  const status = getAgentStatus();
  const pending = status.approvalsPending;
  const receipt = writeReceipt('/agent/cycle', 'completed', { pending });
  return { status, receipt };
}
