import { listIntelligenceProviders } from '@/lib/evez/intelligence-registry';
import { getAgentStatus } from '@/lib/evez/runtime';

export const runtime = 'nodejs';

export async function GET() {
  const providers = listIntelligenceProviders();
  const agent = getAgentStatus();

  return Response.json({
    ok: true,
    checkedAt: new Date().toISOString(),
    providers,
    providerCount: providers.length,
    approvalsPending: agent.approvalsPending,
    receipts: agent.receipts,
    universalRetention: {
      preserveSummary: true,
      preserveReasonTrace: true,
      preserveArtifacts: true,
    },
  });
}
