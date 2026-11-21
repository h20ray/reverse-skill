const puppeteer = require('puppeteer-core');
(async()=>{
  const b = await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:'new'});
  const p = await b.newPage();
  await p.setViewport({width:400,height:600,deviceScaleFactor:1});
  const url = 'http://localhost:8777/index.html';
  await p.goto(url,{waitUntil:'networkidle0'});
  await new Promise(r=>setTimeout(r,400));
  // crop bottom-right region where cat sits
  const clip = {x:120, y:380, width:280, height:220};
  await p.screenshot({path:'cat-idle.png', clip});
  await p.evaluate(()=>{const c=document.querySelector('.bongo'); c.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}));});
  await new Promise(r=>setTimeout(r,80));
  await p.screenshot({path:'cat-punch.png', clip});
  await b.close();
  console.log('done');
})();
