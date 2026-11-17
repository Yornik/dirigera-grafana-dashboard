// Takes 1 screenshot of a dashboard from a local Grafana, for the README.
//
//   node tools/screenshot.js <dashboard uid> <dark|light> <from ms> <to ms> <viewport height> <out.png> [scale]
//
// The Grafana must listen on 127.0.0.1:13000, have the dashboards provisioned
// and read the Prometheus that holds the data of tools/testdata.py. It also
// writes <out.png>.json with the vertical position of a few panel titles, to
// crop the image by.
const { chromium } = require('playwright');
const [,, uid, theme, from, to, height, out, scale] = process.argv;
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1200, height: +height }, deviceScaleFactor: +(scale || 1), timezoneId: 'Europe/Amsterdam', locale: 'en-GB' });
  const page = await ctx.newPage();
  // A throwaway local Grafana with its factory sign-in; nothing else is reachable through it.
  const r = await page.request.post('http://127.0.0.1:13000/login', { data: { user: 'admin', password: 'admin' } });
  if (!r.ok()) throw new Error('login ' + r.status());
  await page.goto(`http://127.0.0.1:13000/d/${uid}/x?orgId=1&from=${from}&to=${to}&theme=${theme}&kiosk=true&refresh=`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(6000);
  await page.screenshot({ path: out });
  const marks = {};
  for (const t of ['Needs attention', 'Air purifier', 'Lights over time', 'Motion per hour', 'Powered by']) {
    const b = await page.getByText(t, { exact: t !== 'Powered by' }).first().boundingBox().catch(() => null);
    if (b) marks[t] = Math.round(b.y);
  }
  require('fs').writeFileSync(out + '.json', JSON.stringify(marks));
  const texts = await page.evaluate(() => Array.from(document.querySelectorAll('[data-testid*="Panel status error"], [aria-label*="error" i]')).length);
  console.log(out, 'error markers:', texts);
  await browser.close();
})().catch(e => { console.error('FAILED', e.message); process.exit(1); });
