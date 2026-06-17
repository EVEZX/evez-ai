const { chromium } = require('/usr/lib/node_modules/openclaw/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const dir = '/home/openclaw/evez-ecosystem/marketing/images';
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));
  
  for (const file of files) {
    const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
    await page.goto('file://' + path.join(dir, file), { timeout: 10000 });
    await page.screenshot({ path: path.join(dir, file.replace('.html', '.png')), fullPage: false });
    await page.close();
    console.log('✅ ' + file.replace('.html', '.png'));
  }
  
  await browser.close();
})();
