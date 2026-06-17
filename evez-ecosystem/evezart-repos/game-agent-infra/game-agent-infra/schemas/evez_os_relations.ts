import { relations } from "drizzle-orm";
import { users, agents, agentTasks } from "./evez_os_schema";

// ─── User Relations ───
export const usersRelations = relations(users, ({ many }) => ({
  agents: many(agents),
}));

// ─── Agent Relations ───
export const agentsRelations = relations(agents, ({ one, many }) => ({
  parentAgent: one(agents, {
    fields: [agents.parentAgentId],
    references: [agents.id],
    relationName: "agentHierarchy",
  }),
  childAgents: many(agents, { relationName: "agentHierarchy" }),
  tasks: many(agentTasks),
}));

// ─── Agent Task Relations ───
export const agentTasksRelations = relations(agentTasks, ({ one }) => ({
  agent: one(agents, {
    fields: [agentTasks.agentId],
    references: [agents.id],
  }),
}));

// Export types for MCP / EVEZ-OS bridge
export type AgentWithTasks = typeof agents.$inferSelect & {
  tasks: (typeof agentTasks.$inferSelect)[];
};

export type AgentHierarchy = typeof agents.$inferSelect & {
  parentAgent?: typeof agents.$inferSelect;
  childAgents: (typeof agents.$inferSelect)[];
};