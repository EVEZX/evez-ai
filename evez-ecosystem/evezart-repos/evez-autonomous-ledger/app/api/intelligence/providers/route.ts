import { listIntelligenceProviders } from '@/lib/evez/intelligence-registry';

export const runtime = 'nodejs';

export async function GET() {
  const providers = listIntelligenceProviders();
  return Response.json({
    ok: true,
    providerCount: providers.length,
    providers,
    universalRetention: {
      preserveSummary: true,
      preserveReasonTrace: true,
      preserveArtifacts: true,
    },
  });
}
