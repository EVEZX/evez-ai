import { EventSpineRecord } from "../event-spine/event-spine";

export interface ProjectionState {
  lastIndex: number;
  domains: Record<string, number>;
}

export class ProjectionBus {
  project(records: EventSpineRecord[]): ProjectionState {
    const state: ProjectionState = {
      lastIndex: -1,
      domains: {}
    };

    for (const rec of records) {
      state.lastIndex = rec.index;
      state.domains[rec.domain] = (state.domains[rec.domain] || 0) + 1;
    }

    return state;
  }
}
