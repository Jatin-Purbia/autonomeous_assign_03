'use strict';
const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );
const setText = (values) => (values.length ? `{${values.join(', ')}}` : '∅');
const split = (text) =>
  text
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean);
const NAMES = {
  grounded: 'Grounded',
  complete: 'Complete',
  preferred: 'Preferred',
  stable: 'Stable',
  'semi-stable': 'Semi-stable',
};
const DESCRIPTIONS = {
  grounded: 'The safest answer: only what is defended all the way down.',
  complete: 'Every consistent position that includes everything it defends.',
  preferred: 'The largest consistent positions.',
  stable: 'Positions that attack every argument they leave out.',
  'semi-stable': 'Complete positions that cover as many arguments as possible.',
};
let examples = {},
  analysis = null,
  experimentData = null;

async function api(path, data) {
  const response = await fetch(
    path,
    data === undefined
      ? {}
      : {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        },
  );
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed.');
  return result;
}
function error(message) {
  $('error').textContent = message;
  $('error').hidden = !message;
}
function notify(message) {
  $('notice').textContent = message;
  $('notice').hidden = !message;
}
function action(fn) {
  return async (event) => {
    error('');
    try {
      await fn(event);
    } catch (err) {
      error(err.message);
    }
  };
}
function table(headers, rows, bestRows = []) {
  const head = headers.map((h) => `<th>${esc(h)}</th>`).join('');
  const body = rows
    .map((row, i) => {
      const cells = row.map((cell) => `<td>${esc(cell)}</td>`).join('');
      return `<tr${bestRows.includes(i) ? ' class="best"' : ''}>${cells}</tr>`;
    })
    .join('');
  return `<div class="table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

/* ---------------- framework studio ---------------- */
function framework() {
  const attacks = $('attacks')
    .value.split('\n')
    .map((x) => x.trim())
    .filter(Boolean)
    .map((line) => {
      const pair = line.split(/\s*(?:->|→|,)\s*/);
      if (pair.length !== 2 || pair.some((x) => !x))
        throw new Error(`Invalid attack “${line}”. Use source -> target, one per line.`);
      return pair;
    });
  return { arguments: split($('arguments').value), attacks };
}
async function analyse() {
  analysis = await api('/api/analyse', {
    ...framework(),
    set: split($('test-set').value),
    semantics: $('semantics').value,
  });
  renderAnalysis();
}
function statusClass(status) {
  if (status.startsWith('skeptically')) return 'good';
  if (status.startsWith('credulously')) return 'maybe';
  return status === 'rejected' ? 'bad' : '';
}
function renderAnalysis() {
  const grounded = analysis.extensions.grounded[0] || [];
  $('headline').innerHTML = grounded.length
    ? `Accepted without doubt: <strong>${esc(setText(grounded))}</strong>. These arguments survive every attack (grounded extension).`
    : 'No argument is accepted without doubt: the grounded extension is empty.';
  $('extension-cards').innerHTML = Object.entries(analysis.extensions)
    .map(([name, sets]) => {
      const chips = sets.length
        ? sets.map((s) => `<span class="set-chip">${esc(setText(s))}</span>`).join('')
        : '<p class="empty">No extensions</p>';
      return `<article class="extension" data-semantics="${name}"><div class="extension-title">${NAMES[name]} <span class="extension-count">${sets.length} found</span></div>${chips}<p class="extension-desc">${DESCRIPTIONS[name]}</p></article>`;
    })
    .join('');
  $('trace').innerHTML = analysis.grounded_trace
    .map(
      (s, i) =>
        (i ? '<span class="trace-arrow">→</span>' : '') +
        `<span class="trace-step">${esc(setText(s))}</span>`,
    )
    .join('');
  const set = analysis.set_analysis;
  $('set-results').innerHTML =
    [
      ['Conflict-free', set.conflict_free],
      ['Admissible', set.admissible],
      ['Complete', set.complete],
    ]
      .map(
        ([label, value]) =>
          `<div class="check"><span>${label}</span><strong class="${value ? 'yes' : 'no'}">${value ? 'Yes' : 'No'}</strong></div>`,
      )
      .join('') +
    `<div class="check"><span>Defended</span><strong>${esc(setText(set.defended))}</strong></div>`;
  $('acceptance').innerHTML =
    Object.entries(analysis.acceptance)
      .map(
        ([a, status]) =>
          `<div class="status-row"><b>${esc(a)}</b><span class="status-label ${statusClass(status)}">${esc(status)}</span></div>`,
      )
      .join('') || '<p class="empty">The framework is empty.</p>';
  $('labelling-count').textContent = `${analysis.labellings.length} legal.`;
  $('labellings').innerHTML = table(
    ['#', 'In', 'Out', 'Undecided'],
    analysis.labellings.map((l, i) => [i + 1, setText(l.in_), setText(l.out), setText(l.undec)]),
  );
  renderGraph();
}
function renderGraph() {
  if (!analysis) return;
  const { arguments: args, attacks } = analysis.framework;
  const ground = new Set(analysis.extensions.grounded[0]);
  const out = new Set(attacks.filter(([a]) => ground.has(a)).map(([, b]) => b));
  const selected = new Set(split($('test-set').value));
  const positions = Object.fromEntries(
    args.map((a, i) => [
      a,
      args.length === 1
        ? [320, 165]
        : [
            320 + 220 * Math.cos(-Math.PI / 2 + (i * 2 * Math.PI) / args.length),
            170 + 118 * Math.sin(-Math.PI / 2 + (i * 2 * Math.PI) / args.length),
          ],
    ]),
  );
  let svg =
    '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#8590a0"/></marker></defs>';
  for (const [a, b] of attacks) {
    const [x, y] = positions[a],
      [xx, yy] = positions[b];
    if (a === b) {
      svg += `<path class="edge" d="M ${x - 15},${y - 22} C ${x - 65},${y - 85} ${x + 65},${y - 85} ${x + 17},${y - 23}" marker-end="url(#arrow)"/>`;
      continue;
    }
    const dx = xx - x,
      dy = yy - y,
      d = Math.hypot(dx, dy),
      ux = dx / d,
      uy = dy / d;
    const reverse = attacks.some(([s, t]) => s === b && t === a);
    const bend = reverse ? 22 : 0;
    svg += `<path class="edge" d="M ${x + ux * 29},${y + uy * 29} Q ${(x + xx) / 2 - uy * bend},${(y + yy) / 2 + ux * bend} ${xx - ux * 33},${yy - uy * 33}" marker-end="url(#arrow)"/>`;
  }
  args.forEach((a) => {
    const [x, y] = positions[a];
    const state = ground.has(a) ? 'in' : out.has(a) ? 'out' : 'undec';
    svg += `<g class="node ${state} ${selected.has(a) ? 'selected' : ''}" data-argument="${esc(a)}" tabindex="0" role="button" aria-label="Toggle ${esc(a)} in test set" aria-pressed="${selected.has(a)}" transform="translate(${x},${y})"><circle r="27"/><text text-anchor="middle" dominant-baseline="central">${esc(a.length > 7 ? a.slice(0, 6) + '…' : a)}</text><title>${esc(a)}</title></g>`;
  });
  $('graph').innerHTML = svg;
  $('graph-count').textContent = `${args.length} arguments · ${attacks.length} attacks`;
  $('graph')
    .querySelectorAll('.node')
    .forEach((node) => {
      const toggle = action(async () => {
        const a = node.dataset.argument;
        const values = new Set(split($('test-set').value));
        values.has(a) ? values.delete(a) : values.add(a);
        $('test-set').value = [...values].join(', ');
        await analyse();
      });
      node.addEventListener('click', toggle);
      node.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          toggle(event);
        }
      });
    });
}
async function loadExample(key) {
  const item = examples[key];
  $('arguments').value = item.arguments.join(', ');
  $('attacks').value = item.attacks.map((e) => e.join(' -> ')).join('\n');
  $('example-description').textContent = item.description;
  $('ownership').value = JSON.stringify(item.ownership, null, 2);
  $('reports').value = JSON.stringify(item.ownership, null, 2);
  $('test-set').value = '';
  $('agent').innerHTML = Object.keys(item.ownership)
    .map((name) => `<option>${esc(name)}</option>`)
    .join('');
  $('strategy-summary').innerHTML =
    '<p class="hint">Press <b>Evaluate</b> to see which arguments are accepted and how well each agent does.</p>';
  $('theorems').innerHTML = '';
  $('best-responses').innerHTML = '';
  renderAgents();
  await analyse();
}

/* ---------------- strategic playground ---------------- */
function renderAgents() {
  let ownership, reports;
  try {
    ownership = JSON.parse($('ownership').value);
    reports = JSON.parse($('reports').value);
  } catch {
    return;
  }
  $('agent-cards').innerHTML = Object.entries(ownership)
    .map(([agent, owned]) => {
      const shown = new Set(reports[agent] || []);
      const chips = owned.length
        ? owned
            .map(
              (a) =>
                `<button class="chip ${shown.has(a) ? '' : 'hidden-arg'}" data-agent="${esc(agent)}" data-arg="${esc(a)}" aria-pressed="${shown.has(a)}" title="${shown.has(a) ? 'Revealed. Click to hide.' : 'Hidden. Click to reveal.'}">${esc(a)}</button>`,
            )
            .join('')
        : '<span class="none">owns no arguments</span>';
      return `<div class="agent-card"><div class="agent-name">${esc(agent)}</div><div class="chips">${chips}</div></div>`;
    })
    .join('');
  $('agent-cards')
    .querySelectorAll('.chip')
    .forEach((chip) => {
      chip.onclick = action(async () => {
        const { agent, arg } = chip.dataset;
        const current = JSON.parse($('reports').value);
        const list = new Set(current[agent] || []);
        list.has(arg) ? list.delete(arg) : list.add(arg);
        current[agent] = JSON.parse($('ownership').value)[agent].filter((a) => list.has(a));
        $('reports').value = JSON.stringify(current, null, 2);
        await evaluateStrategy();
      });
    });
}
async function evaluateStrategy() {
  const result = await api('/api/strategic', {
    ...framework(),
    ownership: JSON.parse($('ownership').value),
    reports: JSON.parse($('reports').value),
    agent: $('agent').value.trim(),
  });
  renderAgents();
  const utilities = Object.entries(result.utilities)
    .map(([agent, u]) => `<div class="utility">${esc(agent)}<strong>${u}</strong></div>`)
    .join('');
  $('strategy-summary').innerHTML =
    `<div class="summary-label">Accepted arguments (grounded outcome of the revealed graph)</div><div class="metric">${esc(setText(result.outcome))}</div><div class="summary-label">Utility: how many of an agent’s own arguments are accepted</div><div class="utility-grid">${utilities}</div>`;
  const sp = result.strategyproofness,
    condition = result.condition;
  const spText = sp.strategyproof
    ? `Revealing everything is best for every agent. ${sp.comparisons} deviations were checked.`
    : `Some agent gains by hiding. Found after ${sp.comparisons} deviations.`;
  const w = sp.witness;
  const witness = w
    ? `<p class="example-box"><b>${esc(w.agent)}</b> reveals ${esc(setText(w.deviation))} instead of ${esc(setText(w.truthful_report))}. Accepted arguments change from ${esc(setText(w.truthful_outcome))} to ${esc(setText(w.deviation_outcome))}, raising ${esc(w.agent)}’s utility from <b>${w.truthful_utility}</b> to <b>${w.deviation_utility}</b>.</p>`
    : '';
  const walk = condition.witness
    ? `<p>Odd path for ${esc(condition.witness.agent)}: <b>${esc(condition.witness.walk.join(' → '))}</b></p>`
    : '';
  $('theorems').innerHTML =
    `<div class="verdict"><h3>Can any agent gain by hiding arguments? (Theorem 5.3)</h3><span class="badge ${sp.strategyproof ? '' : 'fail'}">${sp.strategyproof ? 'Strategyproof' : 'Manipulable'}</span><p>${spText}</p>${witness}</div>` +
    `<div class="verdict"><h3>Structural condition (Theorem 5.4)</h3><span class="badge ${condition.holds ? '' : 'fail'}">${condition.holds ? 'Holds' : 'Fails'}</span><p>${condition.holds ? 'This guarantees that truthful reporting is best.' : 'This is sufficient but not necessary, so a failure does not prove manipulation.'}</p>${walk}</div>`;
  const best = result.best_responses;
  const bestKeys = new Set(best.best_reports.map((r) => JSON.stringify(r.report)));
  const rows = best.all_reports.map((r) => [
    setText(r.report),
    setText(r.grounded),
    r.utility,
    bestKeys.has(JSON.stringify(r.report)) ? 'Yes' : '—',
  ]);
  const count = best.best_reports.length;
  $('best-responses').innerHTML =
    `<p>Maximum utility for <b>${esc($('agent').value)}</b>: <b>${best.maximum_utility}</b> (${count} best report${count === 1 ? '' : 's'}, highlighted)</p>` +
    table(
      ['Revealed', 'Accepted overall', 'Utility', 'Best'],
      rows,
      rows.flatMap((r, i) => (r[3] === 'Yes' ? [i] : [])),
    );
}

/* ---------------- experiments ---------------- */
function download(name, data) {
  const link = document.createElement('a'),
    url = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
    );
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function renderExperiments(result) {
  experimentData = result;
  $('download-results').disabled = false;
  if (!result.summary.length) {
    $('experiment-results').innerHTML =
      '<p class="hint empty-state">No saved experiments yet. Run python -m argumentation.experiments.</p>';
    return;
  }
  const total = result.records.length;
  const violations = result.records.filter((r) => r.condition.holds && !r.strategyproof);
  const converse = result.records.filter((r) => r.strategyproof && !r.condition.holds);
  const spTotal = result.records.filter((r) => r.strategyproof).length;
  const bars = result.summary
    .map(
      (r) =>
        `<div class="bar-row"><b>p = ${r.p}</b><div class="bar-track"><div class="bar-fill" style="width:${r.fraction * 100}%"></div></div><span>${(r.fraction * 100).toFixed(1)}%</span></div>`,
    )
    .join('');
  const summaryTable = table(
    [
      'p',
      'Trials',
      'Strategyproof',
      'Fraction',
      'Condition holds',
      'Holds, not SP',
      'SP, condition fails',
    ],
    result.summary.map((r) => [
      r.p,
      r.instances,
      r.strategyproof,
      r.fraction.toFixed(3),
      r.condition_holds,
      r.condition_holds_not_sp,
      r.sp_condition_fails,
    ]),
  );
  $('experiment-results').innerHTML = `
    <div class="subtabs">
      <button class="subtab active" data-sub="sub-overview">Overview</button>
      <button class="subtab" data-sub="sub-table">By probability</button>
      <button class="subtab" data-sub="sub-inspect">Inspect instances</button>
    </div>
    <div id="sub-overview" class="subpane">
      <div class="stat-row">
        <div class="stat"><strong>${total} instances</strong><span>seed ${esc(result.config.seed)}, ${result.elapsed_seconds}s</span></div>
        <div class="stat"><strong>${((spTotal / total) * 100).toFixed(1)}%</strong><span>strategyproof overall</span></div>
        <div class="stat"><strong>${violations.length}</strong><span>condition holds but manipulable</span></div>
        <div class="stat"><strong>${converse.length}</strong><span>strategyproof though condition fails</span></div>
      </div>
      <h3>Strategyproof instances by attack probability</h3>
      ${bars}
      <p class="hint">The structural condition is sufficient but not necessary: it never failed to protect, yet many instances are strategyproof without it.</p>
    </div>
    <div id="sub-table" class="subpane" hidden>${summaryTable}</div>
    <div id="sub-inspect" class="subpane" hidden>
      <div class="row-controls">
        <div><label for="trial-category">Category</label><select id="trial-category"><option value="converse">Strategyproof although condition fails</option><option value="violation">Condition holds although manipulable</option><option value="all">All saved instances</option></select></div>
        <div><label for="trial-select">Instance (first 100)</label><select id="trial-select"></select></div>
        <button id="open-trial" class="button primary">Open in studio</button>
      </div>
      <div id="trial-details" class="record"></div>
    </div>`;
  document.querySelectorAll('.subtab').forEach((tab) => {
    tab.onclick = () => {
      document.querySelectorAll('.subtab').forEach((t) => t.classList.toggle('active', t === tab));
      document.querySelectorAll('.subpane').forEach((p) => (p.hidden = p.id !== tab.dataset.sub));
    };
  });
  let filtered = [];
  function showTrial() {
    const r = filtered[Number($('trial-select').value)];
    $('open-trial').disabled = !r;
    if (!r) {
      $('trial-details').textContent = 'No instances in this category.';
      return;
    }
    const owners = Object.entries(r.ownership)
      .map(([k, v]) => `${k}: ${setText(v)}`)
      .join(' · ');
    $('trial-details').innerHTML = `<dl>
      <dt>Arguments</dt><dd>${esc(r.arguments.join(', '))}</dd>
      <dt>Attacks</dt><dd>${esc(r.attacks.map((e) => e.join(' → ')).join(', ') || 'none')}</dd>
      <dt>Ownership</dt><dd>${esc(owners)}</dd>
      <dt>Strategyproof</dt><dd>${r.strategyproof ? 'Yes' : 'No'} (${r.comparisons} deviations checked)</dd>
      <dt>Condition</dt><dd>${r.condition.holds ? 'Holds' : 'Fails'}</dd></dl>
      <details><summary>Raw JSON</summary><pre class="witness">${esc(JSON.stringify(r, null, 2))}</pre></details>`;
  }
  function filter() {
    const category = $('trial-category').value;
    filtered = (
      category === 'converse' ? converse : category === 'violation' ? violations : result.records
    ).slice(0, 100);
    $('trial-select').innerHTML = filtered
      .map((r, i) => `<option value="${i}">${esc(r.id)} · ${r.n} arguments</option>`)
      .join('');
    showTrial();
  }
  $('trial-category').onchange = filter;
  $('trial-select').onchange = showTrial;
  $('open-trial').onclick = action(async () => {
    const r = filtered[Number($('trial-select').value)];
    examples['saved-trial'] = {
      ...r,
      name: r.id,
      description:
        'Saved experiment instance. Re-evaluate strategy to independently inspect its audit.',
    };
    if (!$('example').querySelector('[value="saved-trial"]'))
      $('example').add(new Option('Saved trial', 'saved-trial'));
    $('example').value = 'saved-trial';
    await loadExample('saved-trial');
    switchTab('framework');
  });
  filter();
}
async function runExperiments() {
  const button = $('run-experiments');
  button.disabled = true;
  try {
    const { job_id } = await api('/api/experiments', {
      count: Number($('count').value),
      probabilities: split($('probabilities').value).map(Number),
      seed: Number($('seed').value),
      self_attacks: $('self-attacks').checked,
    });
    while (true) {
      const job = await api('/api/jobs/' + job_id);
      $('experiment-progress').innerHTML =
        `<p>${job.status === 'completed' ? 'Completed' : 'Running'}: ${job.done} / ${job.total} instances</p><progress value="${job.done}" max="${job.total}"></progress>`;
      if (job.status === 'failed') throw new Error(job.error);
      if (job.status === 'completed') {
        renderExperiments(job.result);
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 750));
    }
  } finally {
    button.disabled = false;
  }
}

/* ---------------- navigation and wiring ---------------- */
function switchTab(name) {
  document.querySelectorAll('.view').forEach((el) => (el.hidden = el.id !== name));
  document.querySelectorAll('.nav').forEach((el) => {
    el.classList.toggle('active', el.dataset.tab === name);
    el.setAttribute('aria-current', el.dataset.tab === name ? 'page' : 'false');
  });
  error('');
  notify('');
}
document
  .querySelectorAll('[data-tab]')
  .forEach((button) => (button.onclick = () => switchTab(button.dataset.tab)));
document.querySelectorAll('[data-result]').forEach((tab) => {
  tab.onclick = () => {
    document
      .querySelectorAll('[data-result]')
      .forEach((t) => t.classList.toggle('active', t === tab));
    document
      .querySelectorAll('.result-pane')
      .forEach((p) => (p.hidden = p.id !== tab.dataset.result));
  };
});
$('analyse').onclick = action(async () => {
  await analyse();
  notify('Analysis updated.');
  setTimeout(() => notify(''), 2500);
});
$('check-set').onclick = action(analyse);
$('semantics').onchange = action(analyse);
$('example').onchange = action(() => loadExample($('example').value));
$('run-strategy').onclick = action(evaluateStrategy);
$('agent').onchange = action(evaluateStrategy);
$('truthful').onclick = action(async () => {
  $('reports').value = JSON.stringify(JSON.parse($('ownership').value), null, 2);
  await evaluateStrategy();
});
$('export').onclick = action(() =>
  download('framework.json', { ...framework(), ownership: JSON.parse($('ownership').value) }),
);
$('import-file').onchange = action(async (event) => {
  try {
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 100000) throw new Error('Framework file is too large.');
    const data = JSON.parse(await file.text());
    await api('/api/analyse', data);
    if (data.arguments.some((a) => /[,\n\r]/.test(a)))
      throw new Error('The editor requires names without commas or newlines.');
    if (data.ownership) await api('/api/strategic', data);
    const owner = data.ownership || { 'Agent 1': data.arguments, 'Agent 2': [], 'Agent 3': [] };
    examples.imported = {
      ...data,
      ownership: owner,
      name: 'Imported framework',
      description: 'Imported from ' + file.name,
    };
    if (!$('example').querySelector('[value="imported"]'))
      $('example').add(new Option('Imported framework', 'imported'));
    $('example').value = 'imported';
    await loadExample('imported');
    notify('Framework imported.');
  } finally {
    event.target.value = '';
  }
});
$('run-experiments').onclick = action(runExperiments);
$('load-results').onclick = action(async () =>
  renderExperiments(await api('/api/saved-experiments')),
);
$('download-results').onclick = () => download('experiments.json', experimentData);
action(async () => {
  examples = await api('/api/examples');
  $('example').innerHTML = Object.entries(examples)
    .map(([key, item]) => `<option value="${esc(key)}">${esc(item.name)}</option>`)
    .join('');
  $('example').value = 'book-5.10';
  await loadExample('book-5.10');
})();
