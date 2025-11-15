import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const dataDir = path.dirname(new URL(import.meta.url).pathname);

function readJson(file) {
  const raw = fs.readFileSync(path.join(dataDir, file), 'utf8');
  return JSON.parse(raw);
}

function renderPrompt(template, variables) {
  return template.replace(/{{(.*?)}}/g, (_, key) => variables[key.trim()] ?? '');
}

function synthesizeArtifact(task) {
  const prompt = renderPrompt(task.prompt_template, task.variables);
  const id = crypto.createHash('sha1').update(task.task_id).digest('hex').slice(0, 10);
  return {
    artifact_id: `art_${id}`,
    task_id: task.task_id,
    status: 'ready',
    reviewer: {
      type: 'human',
      id: 'ops_reviewer_42'
    },
    provenance: {
      model: 'gpt-5-codex-large',
      prompt,
      temperature: task.guardrails?.temperature ?? 0.7,
      max_tokens: task.guardrails?.max_tokens ?? 256
    },
    content: {
      mime: 'text/plain',
      body: `${prompt}\n\n(Localized copy synthesized for ${task.variables.locale})`
    }
  };
}

function runSimulation() {
  const session = readJson('creation_codex_session.json');
  const tasks = readJson('creation_codex_tasks.json');

  console.log('--- Creation Codex Mass Generation Protocol Demo ---');
  console.log('Session objective:', session.objective);
  console.log('Policy pack:', session.policy_pack_id);
  console.log('Max tasks allowed:', session.max_tasks);
  console.log('--- Submitting tasks ---');

  tasks.forEach((task, idx) => {
    console.log(`Task ${idx + 1}: ${task.task_id} -> channels ${task.channels.join(', ')}`);
  });

  console.log('--- Generating artifacts ---');
  const artifacts = tasks.map(synthesizeArtifact);
  artifacts.forEach((artifact) => {
    console.log(`Artifact ${artifact.artifact_id} for ${artifact.task_id}`);
    console.log('  Reviewer:', artifact.reviewer.id);
    console.log('  Model:', artifact.provenance.model);
    console.log('  Content preview:', artifact.content.body.split('\n')[0]);
  });

  console.log('--- Session summary ---');
  const summary = {
    status: 'accepted',
    submitted_tasks: tasks.length,
    completed_tasks: artifacts.length,
    pending_review: 0
  };
  console.table(summary);

  return { session, tasks, artifacts, summary };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runSimulation();
}

export { runSimulation };
