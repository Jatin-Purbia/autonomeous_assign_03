const { test, expect } = require('@playwright/test');
const fs = require('node:fs');

async function example(page, key) {
  await page.locator('#example').selectOption(key);
  await expect(page.locator('#example-description')).not.toBeEmpty();
  await expect(page.locator('#error')).toBeHidden();
}
test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#graph-count')).toHaveText('5 NODES / 4 ATTACKS');
});

test('textbook defence and characteristic function', async ({ page }) => {
  await example(page, 'book-5.1');
  await expect(page.locator('[data-semantics="grounded"]')).toContainText('{a1, a3, a5}');
  await page.locator('#test-set').fill('a3, a5');
  await page.locator('#check-set').click();
  await expect(page.locator('#set-results')).toContainText('AdmissibleYes');
  await expect(page.locator('#set-results')).toContainText('Complete extensionNo');
  await expect(page.locator('#set-results')).toContainText('{a1, a3, a5}');
  await expect(page.locator('#trace .trace-step')).toHaveCount(3);
});
test('three complete extensions and legal labellings', async ({ page }) => {
  await example(page, 'book-5.2');
  await expect(page.locator('[data-semantics="complete"] .set-chip')).toHaveCount(3);
  await expect(page.locator('#labellings tbody tr')).toHaveCount(3);
  await page.locator('#semantics').selectOption('preferred');
  await expect(page.locator('#acceptance')).toContainText('a1credulously accepted');
  await expect(page.locator('#acceptance')).toContainText('a3skeptically accepted');
});
test('graph nodes edit the test set accessibly', async ({ page }) => {
  await example(page, 'chain');
  await expect(page.locator('#graph-count')).toHaveText('3 NODES / 2 ATTACKS');
  await page.getByRole('button', { name: 'Toggle a in test set', exact: true }).click();
  await expect(page.locator('#test-set')).toHaveValue('a');
  await expect(page.locator('#set-results')).toContainText('AdmissibleYes');
  await page.getByRole('button', { name: 'Toggle a in test set', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#test-set')).toHaveValue('');
});
test('odd cycle has no stable extension and undefined stable acceptance', async ({ page }) => {
  await example(page, 'odd-cycle');
  await expect(page.locator('[data-semantics="stable"]')).toContainText('No extensions');
  await page.locator('#semantics').selectOption('stable');
  await expect(page.locator('#acceptance')).toContainText('undefined (no extensions)');
  await expect(page.locator('#labellings')).toContainText('{a, b, c}');
});
test('profitable hiding reproduces corrected book example 5.10', async ({ page }) => {
  await page.getByRole('button', { name: 'Strategic playground' }).click();
  await page.locator('#run-strategy').click();
  await expect(page.locator('#strategy-summary .utility strong')).toHaveText(['1', '0', '1']);
  await expect(page.locator('#theorems')).toContainText('Manipulable');
  await expect(page.locator('#best-responses')).toContainText('Maximum utility for x: 2');
  await page.locator('#reports').fill(JSON.stringify({ x: ['a4', 'a5'], y: ['a2'], z: ['a3'] }));
  await page.locator('#run-strategy').click();
  await expect(page.locator('#strategy-summary .metric')).toHaveText('{a2, a4, a5}');
  await expect(page.locator('#strategy-summary .utility strong')).toHaveText(['2', '1', '0']);
});
test('book example 5.11 is strategyproof although condition fails', async ({ page }) => {
  await example(page, 'book-5.11');
  await expect(page.locator('#graph-count')).toHaveText('6 NODES / 5 ATTACKS');
  await page.getByRole('button', { name: 'Strategic playground' }).click();
  await page.locator('#run-strategy').click();
  await expect(page.locator('#strategy-summary .metric')).toHaveText('{a1, a4, a5, a6}');
  await expect(page.locator('#theorems')).toContainText('Strategyproof');
  await expect(page.locator('#theorems')).toContainText('Fails');
});
test('invalid graph and invalid agent reports have actionable errors', async ({ page }) => {
  await page.locator('#attacks').fill('a1 -> ghost');
  await page.locator('#analyse').click();
  await expect(page.getByRole('alert')).toContainText('Unknown attack endpoint');
  await page.locator('#attacks').fill('malformed');
  await page.locator('#analyse').click();
  await expect(page.getByRole('alert')).toContainText('Invalid attack');
  await example(page, 'book-5.10');
  await page.getByRole('button', { name: 'Strategic playground' }).click();
  await page.locator('#reports').fill(JSON.stringify({ x: ['a2'], y: ['a2'], z: ['a3'] }));
  await page.locator('#run-strategy').click();
  await expect(page.getByRole('alert')).toContainText('only reveal its own arguments');
});
test('framework export and import preserve graph and ownership', async ({ page }) => {
  const pending = page.waitForEvent('download');
  await page.locator('#export').click();
  const download = await pending;
  const data = JSON.parse(fs.readFileSync(await download.path(), 'utf8'));
  expect(data.arguments).toHaveLength(5);
  expect(data.ownership.x).toEqual(['a1', 'a4', 'a5']);
  await page.locator('#import-file').setInputFiles({
    name: 'custom.json',
    mimeType: 'application/json',
    buffer: Buffer.from(
      JSON.stringify({
        arguments: ['x', 'y'],
        attacks: [['x', 'y']],
        ownership: { A: ['x'], B: ['y'] },
      }),
    ),
  });
  await expect(page.locator('#graph-count')).toHaveText('2 NODES / 1 ATTACKS');
  await expect(page.locator('[data-semantics="grounded"]')).toContainText('{x}');
  await page.getByRole('button', { name: 'Strategic playground' }).click();
  await expect(page.locator('#ownership')).toHaveValue(/"A"/);
});
test('empty graph and self attacks are supported', async ({ page }) => {
  await page.locator('#arguments').fill('');
  await page.locator('#attacks').fill('');
  await page.locator('#analyse').click();
  await expect(page.locator('#graph-count')).toHaveText('0 NODES / 0 ATTACKS');
  await expect(page.locator('[data-semantics="stable"] .set-chip')).toHaveText('∅');
  await page.locator('#arguments').fill('a');
  await page.locator('#attacks').fill('a -> a');
  await page.locator('#analyse').click();
  await expect(page.locator('#graph-count')).toHaveText('1 NODES / 1 ATTACKS');
  await expect(page.locator('[data-semantics="stable"]')).toContainText('No extensions');
});
test('experiment job completes and exports reproducible raw results', async ({ page }) => {
  await page.getByRole('button', { name: 'Experiments', exact: true }).click();
  await page.locator('#count').fill('3');
  await page.locator('#probabilities').fill('0.1, 0.5');
  await page.locator('#seed').fill('42');
  await page.locator('#run-experiments').click();
  await expect(page.locator('#experiment-progress')).toContainText('Completed: 6 / 6');
  await expect(page.locator('#experiment-results')).toContainText('6 instances');
  const pending = page.waitForEvent('download');
  await page.locator('#download-results').click();
  const raw = JSON.parse(fs.readFileSync(await (await pending).path(), 'utf8'));
  expect(raw.records).toHaveLength(6);
  expect(raw.config.seed).toBe(42);
  await page.locator('#trial-category').selectOption('all');
  await page.locator('#open-trial').click();
  await expect(page.locator('#framework')).toBeVisible();
  await expect(page.locator('#example-description')).toContainText('Saved experiment');
});
test('submitted 5000 trials are available and category counts agree', async ({ page }) => {
  await page.getByRole('button', { name: 'Experiments', exact: true }).click();
  await page.locator('#load-results').click();
  await expect(page.locator('#experiment-results')).toContainText('5000 instances');
  await expect(page.locator('.bar-row')).toHaveCount(5);
  await page.locator('#trial-category').selectOption('violation');
  await expect(page.locator('#trial-details')).toHaveText('No instances in this category.');
});
test('responsive layout is usable and JavaScript has no runtime errors', async ({
  page,
}, testInfo) => {
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  await example(page, 'book-5.1');
  await expect(page.locator('#graph-count')).toHaveText('5 NODES / 4 ATTACKS');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Project guide' }).click();
  await expect(page.locator('#guide')).toContainText('a6');
  await page.getByRole('button', { name: 'Framework studio' }).click();
  fs.mkdirSync('docs/screenshots', { recursive: true });
  await page.screenshot({
    path: `docs/screenshots/${testInfo.project.name}-studio.png`,
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
