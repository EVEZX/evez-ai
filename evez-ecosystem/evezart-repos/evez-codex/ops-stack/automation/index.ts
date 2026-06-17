import { canonicalize } from 'json-canonicalize';

/**
 * Executes a workflow and returns canonical representation
 * @param workflow - Workflow definition
 * @returns Canonical JSON string for hashing
 */
export function executeWorkflow(workflow: Record<string, any>): string {
  const canonical = canonicalize(workflow);
  return canonical;
}

/**
 * Example workflow data for testing
 */
export const sampleWorkflow = {
  id: 'wf-001',
  name: 'CI/CD Pipeline',
  steps: ['checkout', 'build', 'test', 'deploy'],
  environment: 'production',
  timeout: 3600
};
