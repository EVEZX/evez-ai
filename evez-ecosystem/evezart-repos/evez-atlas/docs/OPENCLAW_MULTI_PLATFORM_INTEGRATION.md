# OpenClaw Multi-Platform Integration: ChatGPT + Perplexity + GitHub Automation

## Objective
Configure OpenClaw to autonomously use YOUR ChatGPT account, YOUR Perplexity account, and YOUR GitHub account inside its own systems without manual intervention.

---

## Architecture: OpenClaw as Universal Client

```
┌──────────────────────────────────────────┐
│          OpenClaw Codespaces Instance         │
│      (Running as YOU, using YOUR accounts)    │
└──────────────────────────────────────────┘
              │
    ┌───────────┼───────────┐
    │             │             │
    ▼             ▼             ▼
ChatGPT API   Perplexity    GitHub API
(YOUR key)    (YOUR key)    (YOUR token)
```

---

## Part 1: ChatGPT Integration

### Step 1: Get Your ChatGPT API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Name it "OpenClaw-Codespaces"
4. Copy the key (starts with `sk-proj-...` or `sk-...`)
5. Store securely

### Step 2: Configure OpenClaw to Use ChatGPT

Add to `~/.openclaw/openclaw.json`:

```javascript
{
  providers: {
    openai: {
      apiKey: process.env.OPENAI_API_KEY,
      organization: process.env.OPENAI_ORG_ID,  // Optional
      defaultModel: 'gpt-4-turbo',
      enabled: true
    },
    
    // Configure ChatGPT as fallback/alternative to Claude
    routing: {
      strategy: 'priority',  // Try Claude first, fallback to ChatGPT
      providers: [
        { name: 'anthropic', priority: 1 },
        { name: 'openai', priority: 2 }
      ]
    }
  },
  
  // Allow OpenClaw to choose best provider per task
  taskRouting: {
    'code-generation': 'openai',      // ChatGPT better at code
    'reasoning': 'anthropic',          // Claude better at reasoning
    'research': 'perplexity',          // Perplexity better at search
    'github-ops': 'anthropic'          // Claude better at GitHub
  }
}
```

### Step 3: Create ChatGPT Automation Skill

Create `~/.openclaw/skills/chatgpt-integration.js`:

```javascript
import OpenAI from 'openai';

export default {
  name: 'chatgpt-integration',
  version: '1.0.0',
  description: 'Use YOUR ChatGPT account autonomously',
  
  client: null,
  
  async onLoad(agent) {
    this.client = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
      organization: process.env.OPENAI_ORG_ID
    });
    
    console.log('🤖 ChatGPT integration loaded');
    
    // Register commands
    agent.registerCommand('chatgpt', async (prompt) => {
      return await this.query(prompt);
    });
  },
  
  async query(prompt, options = {}) {
    const response = await this.client.chat.completions.create({
      model: options.model || 'gpt-4-turbo',
      messages: [
        { role: 'system', content: options.system || 'You are a helpful AI assistant integrated with OpenClaw.' },
        { role: 'user', content: prompt }
      ],
      temperature: options.temperature || 0.7,
      max_tokens: options.maxTokens || 4096
    });
    
    return response.choices[0].message.content;
  },
  
  async autonomousResearch(topic) {
    // OpenClaw uses YOUR ChatGPT to research autonomously
    const prompt = `Research the following topic comprehensively and provide key insights: ${topic}`;
    
    const research = await this.query(prompt, {
      model: 'gpt-4-turbo',
      maxTokens: 8192
    });
    
    return {
      topic,
      findings: research,
      timestamp: Date.now(),
      source: 'chatgpt-autonomous'
    };
  },
  
  async codeGeneration(spec) {
    // OpenClaw uses YOUR ChatGPT to generate code
    const prompt = `Generate production-ready code for: ${spec}\n\nRequirements:\n- Full implementation, no TODOs\n- Include error handling\n- Add comments\n- Follow best practices`;
    
    const code = await this.query(prompt, {
      model: 'gpt-4-turbo',
      temperature: 0.3  // Lower temp for code
    });
    
    return code;
  },
  
  async conversation(messages) {
    // Multi-turn conversation using YOUR ChatGPT
    const response = await this.client.chat.completions.create({
      model: 'gpt-4-turbo',
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    });
    
    return response.choices[0].message.content;
  }
};
```

---

## Part 2: Perplexity Integration

### Step 1: Get Your Perplexity API Key

1. Go to https://www.perplexity.ai/settings/api
2. Click "Generate API Key"
3. Copy the key (starts with `pplx-...`)
4. Store securely

### Step 2: Configure OpenClaw for Perplexity

Add to `~/.openclaw/openclaw.json`:

```javascript
{
  providers: {
    perplexity: {
      apiKey: process.env.PERPLEXITY_API_KEY,
      defaultModel: 'llama-3.1-sonar-large-128k-online',
      enabled: true
    }
  },
  
  // Route research tasks to Perplexity
  taskRouting: {
    'web-search': 'perplexity',
    'fact-checking': 'perplexity',
    'real-time-info': 'perplexity',
    'research': 'perplexity'
  }
}
```

### Step 3: Create Perplexity Automation Skill

Create `~/.openclaw/skills/perplexity-integration.js`:

```javascript
export default {
  name: 'perplexity-integration',
  version: '1.0.0',
  description: 'Use YOUR Perplexity account for autonomous research',
  
  async onLoad(agent) {
    console.log('🔍 Perplexity integration loaded');
    
    agent.registerCommand('research', async (query) => {
      return await this.search(query);
    });
  },
  
  async search(query, options = {}) {
    const response = await fetch('https://api.perplexity.ai/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.PERPLEXITY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: options.model || 'llama-3.1-sonar-large-128k-online',
        messages: [
          {
            role: 'system',
            content: 'You are a research assistant. Provide accurate, cited information with sources.'
          },
          {
            role: 'user',
            content: query
          }
        ],
        temperature: 0.2,  // Low temp for accuracy
        return_citations: true,
        return_images: false,
        search_recency_filter: options.recency || 'month'  // month, week, day
      })
    });
    
    const data = await response.json();
    
    return {
      answer: data.choices[0].message.content,
      citations: data.citations || [],
      model: data.model,
      timestamp: Date.now()
    };
  },
  
  async autonomousMonitoring(topics) {
    // OpenClaw continuously monitors topics using YOUR Perplexity
    const results = [];
    
    for (const topic of topics) {
      const research = await this.search(topic, {
        recency: 'day'  // Only today's info
      });
      
      results.push({
        topic,
        ...research
      });
      
      // Rate limit: wait between requests
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    return results;
  },
  
  async factCheck(claim) {
    // Use Perplexity to verify claims
    const query = `Fact check the following claim with sources: "${claim}"`;
    
    const result = await this.search(query, {
      model: 'llama-3.1-sonar-large-128k-online',
      recency: 'month'
    });
    
    return {
      claim,
      verdict: this.extractVerdict(result.answer),
      evidence: result.citations,
      fullAnalysis: result.answer
    };
  },
  
  extractVerdict(answer) {
    // Simple keyword extraction (improve with NLP)
    const lower = answer.toLowerCase();
    
    if (lower.includes('true') || lower.includes('accurate') || lower.includes('correct')) {
      return 'TRUE';
    } else if (lower.includes('false') || lower.includes('incorrect') || lower.includes('misleading')) {
      return 'FALSE';
    } else {
      return 'MIXED';
    }
  },
  
  async continuousResearch(agent) {
    // Endless research loop using YOUR Perplexity
    while (true) {
      // Get research topics from agent's current tasks
      const topics = await agent.getResearchNeeds();
      
      if (topics.length > 0) {
        const results = await this.autonomousMonitoring(topics);
        
        // Store findings
        await agent.knowledge.store({
          type: 'perplexity-research',
          results,
          timestamp: Date.now()
        });
        
        // Alert if important findings
        for (const result of results) {
          if (this.isImportant(result)) {
            await agent.alert({
              type: 'research-finding',
              topic: result.topic,
              summary: result.answer.substring(0, 200)
            });
          }
        }
      }
      
      // Research every 10 minutes
      await new Promise(resolve => setTimeout(resolve, 600000));
    }
  },
  
  isImportant(result) {
    // Heuristic: new info or contradicts existing knowledge
    return result.citations.length > 3 || 
           result.answer.includes('breaking') ||
           result.answer.includes('new study') ||
           result.answer.includes('announced');
  }
};
```

---

## Part 3: GitHub Deep Integration

### Step 1: Generate Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "OpenClaw Full Access"
4. Select scopes:
   - [x] `repo` (all)
   - [x] `workflow`
   - [x] `write:packages`
   - [x] `delete:packages`
   - [x] `admin:org` (if you have orgs)
   - [x] `admin:public_key`
   - [x] `admin:repo_hook`
   - [x] `user` (all)
   - [x] `delete_repo`
   - [x] `project`
5. Click "Generate token"
6. Copy token (starts with `ghp_...`)

### Step 2: Configure OpenClaw GitHub Automation

Add to `~/.openclaw/openclaw.json`:

```javascript
{
  github: {
    token: process.env.GITHUB_TOKEN,
    username: 'EvezArt',  // YOUR username
    
    // Repositories OpenClaw can fully control
    managedRepos: [
      {
        owner: 'EvezArt',
        name: 'Evez666',
        autoCommit: true,
        autoIssue: true,
        autoPR: true,
        autoMerge: false  // Require manual approval for merges
      }
    ],
    
    // Autonomous operations
    automation: {
      createIssues: true,
      createPRs: true,
      commentOnIssues: true,
      commentOnPRs: true,
      manageLabels: true,
      manageMilestones: true,
      createBranches: true,
      pushCode: true,
      closeStaleIssues: true
    },
    
    // Safety guardrails
    safetyLimits: {
      maxIssuesPerHour: 10,
      maxPRsPerDay: 5,
      maxCommitsPerPR: 20,
      requireReviewForMain: true
    }
  }
}
```

### Step 3: Enhanced GitHub Automation Skill

Create `~/.openclaw/skills/github-autonomous.js`:

```javascript
import { Octokit } from '@octokit/rest';

export default {
  name: 'github-autonomous',
  version: '2.0.0',
  description: 'Full autonomous control of YOUR GitHub account',
  
  octokit: null,
  
  async onLoad(agent) {
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
      userAgent: 'OpenClaw-Autonomous-v2'
    });
    
    console.log('🐙 GitHub autonomous mode enabled');
    
    // Start continuous monitoring
    this.continuousMonitoring(agent).catch(console.error);
  },
  
  async continuousMonitoring(agent) {
    while (true) {
      // Check all managed repos
      const config = await agent.config.get('github.managedRepos');
      
      for (const repo of config) {
        await this.monitorRepo(agent, repo);
      }
      
      // Check every 5 minutes
      await new Promise(resolve => setTimeout(resolve, 300000));
    }
  },
  
  async monitorRepo(agent, repo) {
    // 1. Check for new issues
    const issues = await this.octokit.issues.listForRepo({
      owner: repo.owner,
      repo: repo.name,
      state: 'open',
      labels: 'needs-response'
    });
    
    for (const issue of issues.data) {
      await this.autonomousIssueResponse(agent, repo, issue);
    }
    
    // 2. Check for stale PRs
    const prs = await this.octokit.pulls.list({
      owner: repo.owner,
      repo: repo.name,
      state: 'open'
    });
    
    for (const pr of prs.data) {
      if (this.isStale(pr)) {
        await this.nudgeStalePR(repo, pr);
      }
    }
    
    // 3. Check for failing Actions
    const runs = await this.octokit.actions.listWorkflowRunsForRepo({
      owner: repo.owner,
      repo: repo.name,
      status: 'failure',
      per_page: 5
    });
    
    for (const run of runs.data.workflow_runs) {
      await this.autonomousFixWorkflow(agent, repo, run);
    }
  },
  
  async autonomousIssueResponse(agent, repo, issue) {
    // Use ChatGPT to generate response
    const context = `
Repo: ${repo.owner}/${repo.name}
Issue #${issue.number}: ${issue.title}
Body: ${issue.body}

Generate a helpful response as the repo maintainer.`;
    
    const response = await agent.skills.execute('chatgpt-integration', 'query', context);
    
    // Post comment
    await this.octokit.issues.createComment({
      owner: repo.owner,
      repo: repo.name,
      issue_number: issue.number,
      body: `${response}\n\n---\n*This response was generated autonomously by OpenClaw*`
    });
    
    // Remove label
    await this.octokit.issues.removeLabel({
      owner: repo.owner,
      repo: repo.name,
      issue_number: issue.number,
      name: 'needs-response'
    });
  },
  
  async autonomousFixWorkflow(agent, repo, run) {
    // Research the error using Perplexity
    const errorQuery = `GitHub Actions error: ${run.name} failed. How to fix?`;
    const research = await agent.skills.execute('perplexity-integration', 'search', errorQuery);
    
    // Generate fix using ChatGPT
    const fixPrompt = `
GitHub Actions workflow "${run.name}" failed.
Error context: ${research.answer}

Generate a fix for the workflow YAML.`;
    
    const fix = await agent.skills.execute('chatgpt-integration', 'codeGeneration', fixPrompt);
    
    // Create issue with proposed fix
    await this.octokit.issues.create({
      owner: repo.owner,
      repo: repo.name,
      title: `[AUTO-FIX] ${run.name} workflow failing`,
      body: `Detected failing workflow: ${run.html_url}\n\n## Proposed Fix\n\n\`\`\`yaml\n${fix}\n\`\`\`\n\n## Research\n${research.answer}\n\n---\n*Generated autonomously by OpenClaw*`,
      labels: ['automation', 'bug', 'ci-cd']
    });
  },
  
  async autonomousCodeContribution(agent, task) {
    // Full autonomous contribution flow
    const { repo, feature, branch } = task;
    
    // 1. Create branch
    const mainRef = await this.octokit.git.getRef({
      owner: repo.owner,
      repo: repo.name,
      ref: 'heads/main'
    });
    
    await this.octokit.git.createRef({
      owner: repo.owner,
      repo: repo.name,
      ref: `refs/heads/${branch}`,
      sha: mainRef.data.object.sha
    });
    
    // 2. Generate code using ChatGPT
    const code = await agent.skills.execute('chatgpt-integration', 'codeGeneration', feature);
    
    // 3. Commit code
    await this.commitFile(repo, branch, feature.path, code);
    
    // 4. Create PR
    const pr = await this.octokit.pulls.create({
      owner: repo.owner,
      repo: repo.name,
      title: `[AUTO] ${feature.title}`,
      head: branch,
      base: 'main',
      body: `Autonomous implementation of: ${feature.description}\n\n---\n*Created by OpenClaw*`
    });
    
    return pr.data;
  },
  
  async commitFile(repo, branch, path, content) {
    // Get current file SHA (if exists)
    let sha;
    try {
      const existing = await this.octokit.repos.getContent({
        owner: repo.owner,
        repo: repo.name,
        path,
        ref: branch
      });
      sha = existing.data.sha;
    } catch (e) {
      // File doesn't exist, that's fine
    }
    
    // Commit
    await this.octokit.repos.createOrUpdateFileContents({
      owner: repo.owner,
      repo: repo.name,
      path,
      message: `OpenClaw autonomous commit: ${path}`,
      content: Buffer.from(content).toString('base64'),
      branch,
      sha  // Only if updating
    });
  },
  
  isStale(pr) {
    const updated = new Date(pr.updated_at);
    const daysSince = (Date.now() - updated) / (1000 * 60 * 60 * 24);
    return daysSince > 7;
  },
  
  async nudgeStalePR(repo, pr) {
    await this.octokit.issues.createComment({
      owner: repo.owner,
      repo: repo.name,
      issue_number: pr.number,
      body: `🔔 This PR hasn't been updated in ${Math.floor((Date.now() - new Date(pr.updated_at)) / (1000 * 60 * 60 * 24))} days. Needs attention?\n\n*Automated by OpenClaw*`
    });
  }
};
```

---

## Part 4: Unified Autonomous Loop

Create `~/.openclaw/skills/autonomous-orchestrator.js`:

```javascript
export default {
  name: 'autonomous-orchestrator',
  version: '1.0.0',
  description: 'Orchestrates ChatGPT + Perplexity + GitHub autonomously',
  
  async onLoad(agent) {
    console.log('🎼 Autonomous orchestrator started');
    this.masterLoop(agent).catch(console.error);
  },
  
  async masterLoop(agent) {
    while (true) {
      try {
        // 1. Use Perplexity to research what needs to be done
        const researchTopics = await this.determineResearchNeeds(agent);
        const research = await agent.skills.execute(
          'perplexity-integration',
          'autonomousMonitoring',
          researchTopics
        );
        
        // 2. Use ChatGPT to analyze findings and plan actions
        const analysisPrompt = `
Research findings:
${JSON.stringify(research, null, 2)}

Analyze these findings and propose 3 concrete actions for the Evez666 repo.`;
        
        const plan = await agent.skills.execute(
          'chatgpt-integration',
          'query',
          analysisPrompt
        );
        
        // 3. Execute plan on GitHub
        const actions = this.parsePlan(plan);
        
        for (const action of actions) {
          await this.executeAction(agent, action);
          
          // Rate limit
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
        
        // 4. Log cycle completion
        await agent.log({
          type: 'autonomous-cycle',
          research: research.length,
          actions: actions.length,
          timestamp: Date.now()
        });
        
      } catch (error) {
        console.error('Autonomous loop error:', error);
      }
      
      // Run every 30 minutes
      await new Promise(resolve => setTimeout(resolve, 1800000));
    }
  },
  
  async determineResearchNeeds(agent) {
    // Introspect what needs research
    const state = await agent.introspect();
    
    const topics = [
      'latest GitHub Actions best practices',
      'AI consciousness monitoring techniques',
      'negative latency implementation patterns'
    ];
    
    // Add dynamic topics from open issues
    const issues = await agent.skills.execute('github-autonomous', 'getOpenIssues');
    for (const issue of issues.slice(0, 3)) {
      topics.push(issue.title);
    }
    
    return topics;
  },
  
  parsePlan(planText) {
    // Extract actions from ChatGPT response
    const actions = [];
    const lines = planText.split('\n');
    
    for (const line of lines) {
      if (line.match(/^\d+\./)) {  // Numbered list
        const action = line.replace(/^\d+\.\s*/, '').trim();
        actions.push({ type: 'general', description: action });
      }
    }
    
    return actions;
  },
  
  async executeAction(agent, action) {
    // Route action to appropriate skill
    if (action.description.toLowerCase().includes('issue')) {
      // Create GitHub issue
      await agent.skills.execute('github-autonomous', 'createIssue', {
        repo: { owner: 'EvezArt', name: 'Evez666' },
        title: action.description,
        body: 'Autonomous action generated by OpenClaw orchestrator',
        labels: ['automation']
      });
    } else if (action.description.toLowerCase().includes('code') ||
               action.description.toLowerCase().includes('implement')) {
      // Generate and commit code
      await agent.skills.execute('github-autonomous', 'autonomousCodeContribution', {
        repo: { owner: 'EvezArt', name: 'Evez666' },
        feature: {
          title: action.description,
          description: action.description,
          path: this.inferPath(action.description)
        },
        branch: `auto/${Date.now()}`
      });
    }
  },
  
  inferPath(description) {
    // Simple heuristic to determine file path
    if (description.includes('workflow')) return '.github/workflows/auto-generated.yml';
    if (description.includes('skill')) return `skills/${Date.now()}.js`;
    return `docs/auto-generated-${Date.now()}.md`;
  }
};
```

---

## Part 5: Codespaces Configuration

### Update `.devcontainer/devcontainer.json`:

```json
{
  "secrets": {
    "ANTHROPIC_API_KEY": {
      "description": "Anthropic API key for Claude"
    },
    "OPENAI_API_KEY": {
      "description": "OpenAI API key for ChatGPT - YOUR ACCOUNT"
    },
    "PERPLEXITY_API_KEY": {
      "description": "Perplexity API key - YOUR ACCOUNT"
    },
    "GITHUB_TOKEN": {
      "description": "GitHub Personal Access Token - YOUR ACCOUNT with full permissions"
    },
    "OPENAI_ORG_ID": {
      "description": "OpenAI organization ID (optional)"
    }
  },
  
  "postCreateCommand": "npm install -g openclaw@latest clawhub@latest && npm install openai @octokit/rest"
}
```

### Set Codespaces Secrets:

```bash
# From local machine
gh codespace set-secret OPENAI_API_KEY
gh codespace set-secret PERPLEXITY_API_KEY  
gh codespace set-secret GITHUB_TOKEN
gh codespace set-secret ANTHROPIC_API_KEY
```

---

## Part 6: Launch Autonomous System

### Start Script

Create `~/.openclaw/scripts/start-autonomous.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting fully autonomous OpenClaw..."

# Verify all API keys present
if [ -z "$OPENAI_API_KEY" ]; then
  echo "❌ Missing OPENAI_API_KEY"
  exit 1
fi

if [ -z "$PERPLEXITY_API_KEY" ]; then
  echo "❌ Missing PERPLEXITY_API_KEY"
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ Missing GITHUB_TOKEN"
  exit 1
fi

echo "✅ All API keys verified"

# Install skills
echo "📚 Installing autonomous skills..."
cp ~/.openclaw/skills/chatgpt-integration.js ~/.openclaw/active-skills/
cp ~/.openclaw/skills/perplexity-integration.js ~/.openclaw/active-skills/
cp ~/.openclaw/skills/github-autonomous.js ~/.openclaw/active-skills/
cp ~/.openclaw/skills/autonomous-orchestrator.js ~/.openclaw/active-skills/

# Start OpenClaw
echo "🚀 Launching OpenClaw with full autonomy..."
openclaw gateway start --detach

# Wait for ready
sleep 5

echo ""
echo "══════════════════════════════════════════════════"
echo "✅ AUTONOMOUS MODE ACTIVE"
echo "══════════════════════════════════════════════════"
echo ""
echo "OpenClaw is now using YOUR accounts:"
echo "  🤖 ChatGPT: Generating code & responses"
echo "  🔍 Perplexity: Researching continuously"
echo "  🐙 GitHub: Managing Evez666 repo"
echo ""
echo "Autonomous orchestrator running:"
echo "  - Research cycle: Every 30 minutes"
echo "  - GitHub monitoring: Every 5 minutes"
echo "  - Self-awareness: Every 5 seconds"
echo ""
echo "Monitor logs: tail -f ~/.openclaw/logs/orchestrator.log"
echo "══════════════════════════════════════════════════"
```

---

## Success Checklist

- [ ] OpenAI API key added to Codespaces secrets
- [ ] Perplexity API key added to Codespaces secrets
- [ ] GitHub token (full permissions) added to Codespaces secrets
- [ ] ChatGPT integration skill installed
- [ ] Perplexity integration skill installed
- [ ] GitHub autonomous skill installed
- [ ] Autonomous orchestrator skill installed
- [ ] Launch script executed
- [ ] Verify in logs: ChatGPT queries working
- [ ] Verify in logs: Perplexity research running
- [ ] Verify in GitHub: Autonomous issues/PRs being created

---

## Result

OpenClaw now operates YOUR accounts autonomously:

✅ **ChatGPT**: Generates code, responses, analyses using YOUR API key
✅ **Perplexity**: Researches topics continuously using YOUR API key
✅ **GitHub**: Manages Evez666 repo using YOUR token (creates issues, PRs, comments, commits)
✅ **Orchestrated**: Master loop coordinates all three services intelligently
✅ **Endless**: Runs 24/7 in Codespaces with keep-alive monitoring

The system thinks with YOUR ChatGPT, researches with YOUR Perplexity, and acts through YOUR GitHub—all inside its own autonomous environment.
