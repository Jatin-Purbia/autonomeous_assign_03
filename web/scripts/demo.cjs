// Record a genuine browser walkthrough. Run with npm run demo.
const { chromium } = require('@playwright/test');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '..', '..');
const docs = (file) => path.join(ROOT, 'docs', file);
(async () => {
  const server = spawn('python', ['server.py', '--port', '8138'], {
    cwd: ROOT,
    stdio: 'ignore',
    windowsHide: true,
  });
  let browser, context;
  try {
    for (let i = 0; i < 50; i++) {
      try {
        if ((await fetch('http://127.0.0.1:8138/')).ok) break;
      } catch {}
      await new Promise((r) => setTimeout(r, 200));
    }
    fs.mkdirSync(docs('demonstration'), { recursive: true });
    browser = await chromium.launch({
      headless: true,
      ...(process.env.E2E_BROWSER_PATH ? { executablePath: process.env.E2E_BROWSER_PATH } : {}),
    });
    context = await browser.newContext({
      viewport: { width: 1440, height: 1000 },
      recordVideo: { dir: docs('demonstration'), size: { width: 1440, height: 1000 } },
    });
    const page = await context.newPage();
    page.setDefaultTimeout(20000);
    const caption = async (text) => {
      await page.evaluate((text) => {
        let el = document.getElementById('demo-caption');
        if (!el) {
          el = document.createElement('div');
          el.id = 'demo-caption';
          el.style =
            'position:fixed;bottom:20px;left:270px;right:30px;padding:18px 24px;background:#233936;color:#e6f3ca;border-radius:10px;box-shadow:0 4px 30px #0003;z-index:9999;font:16px Segoe UI';
          document.body.append(el);
        }
        el.textContent = text;
      }, text);
      await page.waitForTimeout(2200);
    };
    await page.goto('http://127.0.0.1:8138/');
    await page.locator('#graph-count').filter({ hasText: '5 NODES / 4 ATTACKS' }).waitFor();
    await caption('Argument Lab | Autonomous Systems Assignment 03');
    await page.locator('#example').selectOption('book-5.1');
    await page.waitForTimeout(500);
    await caption(
      'Figure 5.1: the grounded extension is {a1, a3, a5}. Follow F from the empty set.',
    );
    await page.locator('#test-set').fill('a3, a5');
    await page.locator('#check-set').click();
    await page.locator('#set-results').scrollIntoViewIfNeeded();
    await caption('S = {a3, a5} is admissible but incomplete: it also defends a1.');
    await page.locator('#example').selectOption('book-5.2');
    await page.locator('#extension-cards').scrollIntoViewIfNeeded();
    await caption(
      'Figure 5.2: three complete extensions, two preferred extensions, and three legal labellings.',
    );
    await page.locator('#example').selectOption('book-5.10');
    await page.locator('[data-tab="strategy"]').click();
    await page.locator('#run-strategy').click();
    await page.locator('#strategy-summary .metric').waitFor();
    await caption('Example 5.10: under full revelation, utilities are x = 1, y = 0, z = 1.');
    await page
      .locator('#reports')
      .fill(JSON.stringify({ x: ['a4', 'a5'], y: ['a2'], z: ['a3'] }, null, 2));
    await page.locator('#run-strategy').click();
    await page.waitForTimeout(500);
    await caption(
      'When x hides a1, its utility increases from 1 to 2. The mechanism returns a profitable-deviation witness.',
    );
    await page.screenshot({ path: docs('screenshots/strategic-hiding.png'), fullPage: true });
    await page.locator('[data-tab="framework"]').click();
    await page.locator('#example').selectOption('book-5.11');
    await page.locator('[data-tab="strategy"]').click();
    await page.locator('#run-strategy').click();
    await page.waitForTimeout(500);
    await caption(
      'Example 5.11: a6 attacks a3. Exhaustive truthfulness holds even though the odd-walk condition fails.',
    );
    await page.locator('[data-tab="experiments"]').click();
    await page.locator('#load-results').click();
    await page.locator('.bar-row').first().waitFor();
    await page.locator('#experiment-results').scrollIntoViewIfNeeded();
    await caption(
      '5,000 seeded instances: no violations of the sufficient condition. Download every graph and audit witness.',
    );
    await page.screenshot({ path: docs('screenshots/experiments.png'), fullPage: true });
    await page.locator('#trial-category').selectOption('all');
    await page.locator('#open-trial').click();
    await page.waitForTimeout(500);
    await caption(
      'Each saved experiment can be reopened in the studio for inspection and independent verification.',
    );
    const video = page.video();
    await context.close();
    context = null;
    await video.saveAs(docs('demonstration/argument-lab-demo.webm'));
    const original = await video.path();
    if (path.resolve(original) !== path.resolve(docs('demonstration/argument-lab-demo.webm')))
      fs.unlinkSync(original);
    console.log('Saved docs/demonstration/argument-lab-demo.webm');
  } finally {
    if (context) await context.close();
    if (browser) await browser.close();
    server.kill();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
