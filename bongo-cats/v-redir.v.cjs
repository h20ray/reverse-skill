const puppeteer = require('puppeteer-core');
(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new' });
  const p = await b.newPage();
  const events = [];
  p.on('response', r => events.push(r.status() + ' ' + r.url()));
  p.on('requestfailed', r => events.push('FAILED ' + r.url()));
  const resp = await p.goto('http://localhost:5173/skins/TankMechaB.O.N.K./left.png', { waitUntil: 'networkidle0' });
  console.log('final status:', resp && resp.status(), '| url:', p.url());
  const app = await b.newPage();
  await app.goto('http://localhost:5173/', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  const imgInfo = await app.evaluate(() => {
    const i = [...document.querySelectorAll('img')].find(x => x.src.includes('TankMecha'));
    if (!i) return 'none';
    return { src: i.src, complete: i.complete, nW: i.naturalWidth };
  });
  console.log('app img:', JSON.stringify(imgInfo));
  console.log('--- mecha responses ---');
  events.filter(e => e.includes('Mecha')).forEach(e => console.log('  ', e));
  await b.close();
})();
