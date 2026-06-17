import { resolveAwareness, TraceNode, ProcessingModeConfig } from './legion-registry';

describe('resolveAwareness', () => {
  const sampleTrace: TraceNode = {
    id: 'root',
    children: [
      {
        id: 'level1-a',
        children: [
          {
            id: 'level2-a',
            children: [
              { id: 'level3-a' },
            ],
          },
        ],
      },
      {
        id: 'level1-b',
      },
    ],
  };

  it('should redact all children for tier 0', () => {
    const result = resolveAwareness(sampleTrace, 0);
    expect(result.id).toBe('root');
    expect(result.children).toBeUndefined();
  });

  it('should include 1 level of children for tier 1', () => {
    const result = resolveAwareness(sampleTrace, 1);
    expect(result.id).toBe('root');
    expect(result.children).toHaveLength(2);
    expect(result.children![0].id).toBe('level1-a');
    expect(result.children![0].children).toBeUndefined();
  });

  it('should include 2 levels of children for tier 2', () => {
    const result = resolveAwareness(sampleTrace, 2);
    expect(result.id).toBe('root');
    expect(result.children).toHaveLength(2);
    expect(result.children![0].children).toHaveLength(1);
    expect(result.children![0].children![0].id).toBe('level2-a');
    expect(result.children![0].children![0].children).toBeUndefined();
  });

  it('should include full trace for tier 3', () => {
    const result = resolveAwareness(sampleTrace, 3);
    expect(result).toEqual(sampleTrace);
  });

  it('should use custom depth limits from config', () => {
    const config: ProcessingModeConfig = {
      mode: 'sequential',
      depthLimits: {
        0: 0,
        1: 5,
        2: 2,
        3: null,
      },
    };
    const result = resolveAwareness(sampleTrace, 1, config);
    expect(result.id).toBe('root');
    expect(result.children).toBeDefined();
    // With depth 5, we should get all levels of this trace
    expect(result.children![0].children![0].children![0].id).toBe('level3-a');
  });

  it('should throw error for swarm mode with tier < 3', () => {
    const config: ProcessingModeConfig = {
      mode: 'swarm',
      depthLimits: {},
    };
    expect(() => resolveAwareness(sampleTrace, 2, config)).toThrow(
      'Swarm mode requires tier 3 access'
    );
  });

  it('should allow swarm mode for tier 3', () => {
    const config: ProcessingModeConfig = {
      mode: 'swarm',
      depthLimits: {},
    };
    const result = resolveAwareness(sampleTrace, 3, config);
    expect(result).toEqual(sampleTrace);
  });

  it('should handle traces without children', () => {
    const simpleTrace: TraceNode = { id: 'single' };
    const result = resolveAwareness(simpleTrace, 1);
    expect(result.id).toBe('single');
    expect(result.children).toBeUndefined();
  });

  it('should handle empty trace children arrays', () => {
    const traceWithEmptyChildren: TraceNode = {
      id: 'root',
      children: [],
    };
    const result = resolveAwareness(traceWithEmptyChildren, 1);
    expect(result.id).toBe('root');
    expect(result.children).toEqual([]);
  });

  it('should preserve metadata at root level', () => {
    const traceWithMetadata: TraceNode = {
      id: 'root',
      metadata: { key: 'value' },
      children: [{ id: 'child' }],
    };
    const result = resolveAwareness(traceWithMetadata, 0);
    expect(result.id).toBe('root');
    expect(result.metadata).toBeUndefined();
  });
});
