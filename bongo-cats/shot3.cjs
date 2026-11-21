const puppeteer = require('puppeteer-core');
(async()=>{
  const b = await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:'new'});
  const p = await b.newPage();
  await p.setViewport({width:400,height:600,deviceScaleFactor:2});
  await p.goto('http://localhost:8777/index.html',{waitUntil:'networkidle0'});
  await new Promise(r=>setTimeout(r,500));
  // light bg so the black cat shows; crop tight to wrap box (210,350 180x180 at DSF1)
  await p.evaluate(()=>{ document.body.style.background='#e8e8e8'; });
  const clip = {x:200, y:340, width:200, height:200};
  await p.screenshot({path:'white-idle.png', clip});
  await p.evaluate(()=>{document.querySelector('.bongo').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}));});
  await new Promise(r=>setTimeout(r,80));
  await p.screenshot({path:'white-punch.png', clip});
  // second punch (alternate paw) after release
  await new Promise(r=>setTimeout(r,200));
  await p.evaluate(()=>{document.querySelector('.bongo').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}));});
  await new Promise(r=>setTimeout(r,80));
  await p.screenshot({path:'white-punch2.png', clip});
  await b.close(); console.log('done');
})();
