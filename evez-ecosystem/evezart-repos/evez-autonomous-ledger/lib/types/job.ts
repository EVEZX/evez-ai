export type JobStatus =
  | 'queued'
  | 'planning'
  | 'running'
  | 'waiting'
  | 'retrying'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'canceled';

export interface JobStep {
  id: string;
  ts: string;
  agent: string;
  provider?: string | null;
  state: string;
  summary: string;
}

export interface JobCheckpoint {
  id: string;
  jobId: string;
  stage: string;
  ts: string;
  summary: string;
}

export interface JobEnvelope {
  id: string;
  task: string;
  status: JobStatus;
  currentAgent?: string | null;
  currentProvider?: string | null;
  createdAt: string;
  updatedAt: string;
}
