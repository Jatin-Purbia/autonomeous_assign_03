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
  const result = await api('/api/analyse', {
    ...framework(),
    set: split($('test-set').value),
    semantics: $('semantics').value,
  });
  analysis = result;
  renderAnalysis();
}
function renderAnalysis() {
  const descriptions = {
    grounded: 'Least complete extension',
    complete: 'All defended arguments included',
    preferred: 'Maximal complete sets',
    stable: 'Attacks everything outside',
    'semi-stable': 'Maximal complete range',
  };
  $('extension-cards').innerHTML = Object.entries(analysis.extensions)
    .map(
      ([name, sets]) =>
        `<article class="extension" data-semantics="${name}"><div class="extension-title">${name === 'semi-stable' ? 'Semi-stable' : name[0].toUpperCase() + name.slice(1)} <span class="extension-count">${sets.length}</span></div>${sets.length ? sets.map((s) => `<div class="set-chip">${esc(setText(s))}</div>`).join('') : '<p class="empty">No extensions</p>'}<p class="extension-desc">${descriptions[name]}</p></article>`,
    )
    .join('');
  $('trace').innerHTML =
    analysis.grounded_trace
      .map(
        (s, i) =>
          (i ? '<span class="trace-arrow">→</span>' : '') +
          `<span class="trace-step">${esc(setText(s))}</span>`,
      )
      .join('') + '<span class="tag">FIXED POINT</span>';
  const set = analysis.set_analysis;
  $('set-results').innerHTML =
    [
      ['Conflict-free', set.conflict_free],
      ['Admissible', set.admissible],
      ['Complete extension', set.complete],
    ]
      .map(
        ([label, value]) =>
          `<div class="result-line"><span>${label}</span><strong class="${value ? 'yes' : 'no'}">${value ? 'Yes' : 'No'}</strong></div>`,
      )
      .join('') +
    `<div class="result-line"><span>Defended · F(S)</span><strong>${esc(setText(set.defended))}</strong></div>`;
  $('acceptance').innerHTML =
    Object.entries(analysis.acceptance)
      .map(
        ([a, status]) =>
          `<div class="status-row"><b>${esc(a)}</b><span class="status-label">${esc(status)}</span></div>`,
      )
      .join('') || '<p class="empty">The framework is empty.</p>';
  $('labelling-count').textContent = analysis.labellings.length + ' LEGAL';
  $('labellings').innerHTML = table(
    ['Labelling', 'In', 'Out', 'Undecided'],
    analysis.labellings.map((l, i) => [i + 1, setText(l.in_), setText(l.out), setText(l.undec)]),
  );
  renderGraph();
}
function table(headers, rows) {
  return `<table><thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${esc(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
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
    '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#8c9691"/></marker></defs>';
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
    svg += `<g class="node ${ground.has(a) ? 'in' : out.has(a) ? 'out' : 'undec'} ${selected.has(a) ? 'selected' : ''}" data-argument="${esc(a)}" tabindex="0" role="button" aria-label="Toggle ${esc(a)} in test set" aria-pressed="${selected.has(a)}" transform="translate(${x},${y})"><circle r="27"/><text text-anchor="middle" dominant-baseline="central">${esc(a.length > 7 ? a.slice(0, 6) + '…' : a)}</text><title>${esc(a)}</title></g>`;
  });
  $('graph').innerHTML = svg;
  $('graph-count').textContent = `${args.length} NODES / ${attacks.length} ATTACKS`;
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
  $('agent').value = Object.keys(item.ownership)[0];
  $('test-set').value = '';
  $('strategy-summary').innerHTML =
    '<p>Evaluate this framework’s reports to see the strategic outcome.</p>';
  $('theorems').innerHTML = '';
  $('best-responses').innerHTML = '';
  await analyse();
}
async function evaluateStrategy() {
  const result = await api('/api/strategic', {
    ...framework(),
    ownership: JSON.parse($('ownership').value),
    reports: JSON.parse($('reports').value),
    agent: $('agent').value.trim(),
  });
  $('strategy-summary').innerHTML =
    `<div class="tiny-label">GROUNDED OUTCOME OF REVEALED GRAPH</div><div class="metric">${esc(setText(result.outcome))}</div><div class="utility-grid">${Object.entries(
      result.utilities,
    )
      .map(
        ([i, u]) =>
          `<div class="utility">${esc(i)}<strong>${u}</strong><span class="help">accepted arguments</span></div>`,
      )
      .join('')}</div>`;
  const sp = result.strategyproofness,
    condition = result.condition;
  $('theorems').innerHTML =
    `<h3>Truthfulness audit</h3><div class="result-line"><span>Theorem 5.3 · exhaustive</span><span class="badge ${sp.strategyproof ? '' : 'fail'}">${sp.strategyproof ? 'Strategyproof' : 'Manipulable'}</span></div><div class="result-line"><span>Theorem 5.4 · condition</span><span class="badge ${condition.holds ? '' : 'fail'}">${condition.holds ? 'Holds' : 'Fails'}</span></div><p class="help">${sp.comparisons} deviations checked${sp.strategyproof ? ' across every others profile.' : ' before finding a profitable deviation.'} The structural condition is sufficient, not necessary.</p>${sp.witness ? `<h3>Profitable deviation witness</h3><pre class="witness">${esc(JSON.stringify(sp.witness, null, 2))}</pre>` : ''}${condition.witness ? `<h3>Odd-walk witness</h3><p class="witness">${esc(condition.witness.agent)}: ${esc(condition.witness.walk.join(' → '))} (${condition.witness.length} attacks)</p>` : ''}`;
  const best = result.best_responses;
  const reports = new Set(best.best_reports.map((r) => JSON.stringify(r.report)));
  $('best-responses').innerHTML =
    `<p>Maximum utility for <b>${esc($('agent').value)}</b>: <b>${best.maximum_utility}</b> · ${best.best_reports.length} best report(s)</p>` +
    table(
      ['Revealed report', 'Grounded outcome', 'Utility', 'Best response'],
      best.all_reports.map((r) => [
        setText(r.report),
        setText(r.grounded),
        r.utility,
        reports.has(JSON.stringify(r.report)) ? 'Yes' : '—',
      ]),
    );
}
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
      '<p>No saved experiments yet. Run python -m argumentation.experiments.</p>';
    return;
  }
  const counterexamples = result.records.filter((r) => r.condition.holds && !r.strategyproof);
  const converse = result.records.filter((r) => r.strategyproof && !r.condition.holds);
  $('experiment-results').innerHTML =
    `<div class="two-grid"><section class="card"><h3>Fraction of strategyproof instances</h3><div class="bars">${result.summary.map((r) => `<div class="bar-row"><b>p = ${r.p}</b><div class="bar-track"><div class="bar-fill" style="width:${r.fraction * 100}%"></div></div><span>${(r.fraction * 100).toFixed(1)}%</span></div>`).join('')}</div><p class="help">Seed ${esc(result.config.seed)} · ${result.records.length} instances · ${result.elapsed_seconds}s</p></section><section class="card"><h3>What the condition tells us</h3><div class="result-line"><span>Condition holds, strategyproofness fails</span><b>${counterexamples.length}</b></div><div class="result-line"><span>Strategyproof, condition fails</span><b>${converse.length}</b></div><p class="help">A failed condition does not guarantee a profitable deviation. Direct conflicts can merely exchange accepted arguments, while extra defences can cancel indirect self-defeat. Inspect the saved graphs and exhaustive audit.</p></section></div><section class="card spaced"><h3>Results by attack probability</h3>${table(
      [
        'p',
        'Trials',
        'Strategyproof',
        'Fraction',
        'Condition holds',
        'Condition holds / not SP',
        'SP / condition fails',
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
    )}</section><section class="card spaced"><h3>Inspect individual instances</h3><label for="trial-category">Case category</label><select id="trial-category"><option value="converse">Strategyproof although condition fails</option><option value="violation">Condition holds although strategyproofness fails</option><option value="all">All saved instances</option></select><label for="trial-select">Saved graph (first 100 in category; download includes every record)</label><select id="trial-select"></select><button id="open-trial" class="button small">Open in studio</button><pre id="trial-details" class="witness"></pre></section>`;
  let filtered = [];
  function showTrial() {
    const r = filtered[Number($('trial-select').value)];
    $('trial-details').textContent = r
      ? JSON.stringify(r, null, 2)
      : 'No instances in this category.';
    $('open-trial').disabled = !r;
  }
  function filter() {
    filtered = (
      $('trial-category').value === 'converse'
        ? converse
        : $('trial-category').value === 'violation'
          ? counterexamples
          : result.records
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
function switchTab(name) {
  document.querySelectorAll('.tab-panel').forEach((el) => (el.hidden = el.id !== name));
  document.querySelectorAll('.nav').forEach((el) => {
    el.classList.toggle('active', el.dataset.tab === name);
    el.setAttribute('aria-current', el.dataset.tab === name ? 'page' : 'false');
  });
  $('page-title').textContent = {
    framework: 'Framework studio',
    strategy: 'Strategic playground',
    experiments: 'Experiments',
    guide: 'Project guide',
  }[name];
  error('');
  notify('');
}
document
  .querySelectorAll('[data-tab]')
  .forEach((button) => (button.onclick = () => switchTab(button.dataset.tab)));
$('analyse').onclick = action(analyse);
$('check-set').onclick = action(analyse);
$('semantics').onchange = action(analyse);
$('example').onchange = action(() => loadExample($('example').value));
$('run-strategy').onclick = action(evaluateStrategy);
$('truthful').onclick = action(() => {
  $('reports').value = JSON.stringify(JSON.parse($('ownership').value), null, 2);
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
