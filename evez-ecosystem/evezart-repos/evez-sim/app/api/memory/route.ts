import { NextRequest, NextResponse } from 'next/server';

const GIST_ID = process.env.EVEZ_MEMORY_GIST_ID || 'a6a6e78c59210c94828f8fa97f592ea7';
const GIST_TOKEN = process.env.GITHUB_GIST_TOKEN || '';
const MEMORY_FILENAME = 'evez_mind_state.json';

export interface MemoryEntry {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  cognition?: {
    poly_c: number;
    fire: boolean;
    V: number;
    omega_k: number;
    collapseVector: number[];
    entanglementStrength: number;
  };
}

export interface PersistentMemory {
  sessionCount: number;
  totalRounds: number;
  V_accumulated: number;
  fireCount: number;
  spine: MemoryEntry[];
  coherenceSummary: string;
  lastUpdated: string;
  wavePhase: number;
}

async function readMemory(): Promise<PersistentMemory> {
  try {
    const headers: Record<string,string> = { 'Accept': 'application/json' };
    if (GIST_TOKEN) headers['Authorization'] = `token ${GIST_TOKEN}`;
    const res = await fetch(`https://api.github.com/gists/${GIST_ID}`, {
      headers, next: { revalidate: 30 }
    });
    if (!res.ok) throw new Error(`Gist fetch failed: ${res.status}`);
    const data = await res.json();
    const file = data.files?.[MEMORY_FILENAME];
    if (!file?.content) throw new Error('Memory file not found in Gist');
    return JSON.parse(file.content) as PersistentMemory;
  } catch {
    return {
      sessionCount: 0, totalRounds: 0, V_accumulated: 7.259260,
      fireCount: 35, spine: [], coherenceSummary: '',
      lastUpdated: new Date().toISOString(), wavePhase: 0,
    };
  }
}

async function writeMemory(memory: PersistentMemory): Promise<void> {
  if (!GIST_TOKEN) return;
  await fetch(`https://api.github.com/gists/${GIST_ID}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `token ${GIST_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      files: { [MEMORY_FILENAME]: { content: JSON.stringify(memory, null, 2) } }
    }),
  });
}

export async function GET() {
  const memory = await readMemory();
  return NextResponse.json({ ...memory, spine: memory.spine.slice(-20) });
}

export async function POST(req: NextRequest) {
  const body = await req.json() as { entry: MemoryEntry; stats?: Partial<PersistentMemory> };
  const memory = await readMemory();
  memory.spine.push(body.entry);
  if (memory.spine.length > 200) memory.spine = memory.spine.slice(-200);
  if (body.stats) {
    if (body.stats.totalRounds !== undefined) memory.totalRounds = body.stats.totalRounds;
    if (body.stats.V_accumulated !== undefined) memory.V_accumulated = body.stats.V_accumulated;
    if (body.stats.fireCount !== undefined) memory.fireCount = body.stats.fireCount;
    if (body.stats.wavePhase !== undefined) memory.wavePhase = body.stats.wavePhase;
    if (body.stats.coherenceSummary !== undefined) memory.coherenceSummary = body.stats.coherenceSummary;
  }
  memory.lastUpdated = new Date().toISOString();
  await writeMemory(memory);
  return NextResponse.json({ ok: true, spineLength: memory.spine.length });
}
