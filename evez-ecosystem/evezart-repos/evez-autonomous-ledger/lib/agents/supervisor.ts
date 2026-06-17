export async function pickAgentForTask(task: string) {
  const t = task.toLowerCase();

  if (/(code|bug|build|deploy|typescript|api)/.test(t)) {
    return {
      type: 'coding',
      plan: async () => [],
      execute: async () => ({ ok: true, type: 'coding' }),
    };
  }

  if (/(write|copy|email|thread|post|bio)/.test(t)) {
    return {
      type: 'writing',
      plan: async () => [],
      execute: async () => ({ ok: true, type: 'writing' }),
    };
  }

  if (/(audit|validate|check|test|qa)/.test(t)) {
    return {
      type: 'qa',
      plan: async () => [],
      execute: async () => ({ ok: true, type: 'qa' }),
    };
  }

  return {
    type: 'research',
    plan: async () => [],
    execute: async () => ({ ok: true, type: 'research' }),
  };
}
