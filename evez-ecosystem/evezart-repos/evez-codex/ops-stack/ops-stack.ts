#!/usr/bin/env node
/**
 * Ops Stack - Composition of operational modules with golden hash tests
 */

import { validateMarketData, sampleMarketData } from './market-intelligence/index.js';
import { createNotification, sampleNotification } from './notifications/index.js';
import { executeWorkflow, sampleWorkflow } from './automation/index.js';
import { processPayment, samplePayment } from './monetization/index.js';
import { runInference, sampleInferenceRequest } from './ai-engine/index.js';

// Export all modules
export * from './market-intelligence/index.js';
export * from './notifications/index.js';
export * from './automation/index.js';
export * from './monetization/index.js';
export * from './ai-engine/index.js';

/**
 * Golden hash test fixture - expected canonical outputs
 * These are deterministic representations that should always match
 */
const goldenHashes = {
  marketData: '{"market":"cryptocurrency","price":50000,"ticker":"BTC-USD","timestamp":1234567890,"volume":1000000}',
  notification: '{"body":"This is a test notification","priority":"high","recipient":"user@example.com","subject":"Important Update","timestamp":1234567890,"type":"email"}',
  workflow: '{"environment":"production","id":"wf-001","name":"CI/CD Pipeline","steps":["checkout","build","test","deploy"],"timeout":3600}',
  payment: '{"amount":99.99,"currency":"USD","customer":"cust-12345","id":"pay-001","method":"credit_card","timestamp":1234567890}',
  inferenceRequest: '{"max_tokens":500,"model":"gpt-4-turbo","prompt":"Explain quantum computing","temperature":0.7,"timestamp":1234567890}'
};

/**
 * Runs golden hash tests to validate deterministic canonicalization
 * across all ops-stack modules
 * @returns true if all tests pass, false otherwise
 */
export function runGoldenHashTests(): boolean {
  console.log('🧪 Running Golden Hash Tests...\n');
  
  let allPassed = true;
  const tests = [
    {
      name: 'Market Intelligence',
      fn: () => validateMarketData(sampleMarketData),
      expected: goldenHashes.marketData
    },
    {
      name: 'Notifications',
      fn: () => createNotification(sampleNotification),
      expected: goldenHashes.notification
    },
    {
      name: 'Automation',
      fn: () => executeWorkflow(sampleWorkflow),
      expected: goldenHashes.workflow
    },
    {
      name: 'Monetization',
      fn: () => processPayment(samplePayment),
      expected: goldenHashes.payment
    },
    {
      name: 'AI Engine',
      fn: () => runInference(sampleInferenceRequest),
      expected: goldenHashes.inferenceRequest
    }
  ];

  for (const test of tests) {
    const result = test.fn();
    const passed = result === test.expected;
    
    if (passed) {
      console.log(`✅ ${test.name}: PASS`);
    } else {
      console.log(`❌ ${test.name}: FAIL`);
      console.log(`   Expected: ${test.expected}`);
      console.log(`   Got:      ${result}`);
      allPassed = false;
    }
  }

  console.log('\n' + (allPassed ? '✅ All golden hash tests passed!' : '❌ Some tests failed'));
  return allPassed;
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const passed = runGoldenHashTests();
  process.exit(passed ? 0 : 1);
}
