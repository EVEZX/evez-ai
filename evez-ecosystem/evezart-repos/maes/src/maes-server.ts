import Fastify from 'fastify';
import { EventStore }         from './event-store';
import { AgentRuntime }       from './agent-runtime';
import { VerificationEngine } from './verification-engine';
import { CheckpointManager }  from './checkpoint-manager';

const app     = Fastify({ logger: true });
const store   = new EventStore();
const runtime = new AgentRuntime(store);
const vEngine = new VerificationEngine(store);
const cpMgr   = new CheckpointManager(store);

app.post('/agents/spawn', async (req) => {
  const body = req.body as { type?: string };
  const agent = runtime.spawn({ type: (body?.type as any) ?? 'npc' });
  return { agentId: agent.id, type: agent.type };
});

app.post<{ Params: { id: string } }>('/agents/:id/tick', async (req) => {
  const { id } = req.params;
  const { observations = [] } = req.body as { observations?: any[] };
  return { decisions: runtime.tick(id, observations) };
});

app.get<{ Params: { id: string } }>('/agents/:id/verify', async (req) => {
  return vEngine.evaluate(req.params.id);
});

app.post<{ Params: { id: string } }>('/agents/:id/checkpoint', async (req, reply) => {
  const agent = runtime.getAgent(req.params.id);
  if (!agent) return reply.code(404).send({ error: 'Not found' });
  const cp = cpMgr.create(`agent:${req.params.id}`, agent.state);
  return { checkpoint: cp, token: cpMgr.issueToken(req.params.id) };
});

app.post('/sync', async (req) => {
  const { agentId, position } = req.body as { agentId: string; position: number };
  const events = store.readStream(`agent:${agentId}`, position + 1);
  return { events, count: events.length };
});

app.get('/events', async (req) => {
  const { from = 0 } = req.query as { from?: number };
  return { events: store.readAll(from) };
});

app.get('/agents', async () => ({
  agents: runtime.listAgents().map(a => ({
    id: a.id, type: a.type, eventCount: a.eventCount,
    playerStatus: vEngine.getCached(a.id) ?? null,
  })),
  count: runtime.listAgents().length,
}));

app.get('/health', async () => ({ status: 'ok', ts: Date.now() }));

app.listen({ port: 3000, host: '0.0.0.0' }, (err, address) => {
  if (err) throw err;
  console.log(`MAES running at ${address}`);
});
