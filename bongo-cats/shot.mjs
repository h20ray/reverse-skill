import puppeteer from 'puppeteer-core';
const b = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new' });
const p = await b.newPage();
await p.setViewport({ width: 375, height: 812, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
await p.goto('http://localhost:8781/index.html', { waitUntil: 'networkidle0' });
await p.evaluate(() => new Promise(r => setTimeout(r, 1200)));
const box = await p.evaluate(() => {
  const wrap = document.querySelector('.bongo-wrap');
  const bar = document.querySelector('.appbar');
  const wr = wrap.getBoundingClientRect();
  const br = bar.getBoundingClientRect();
  return { wrap: {x:wr.x,y:wr.y,w:wr.width,h:wr.height}, bar: {x:br.x,y:br.y,w:br.width,h:br.height} };
});
console.log('BOX ' + JSON.stringify(box));
await p.screenshot({ path: 'mobile-cat.png', fullPage: false });
await b.close();
