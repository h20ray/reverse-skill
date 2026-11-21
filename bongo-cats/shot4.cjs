const puppeteer = require('puppeteer-core');
(async()=>{
  const b = await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:'new'});
  const p = await b.newPage();
  await p.setViewport({width:400,height:600,deviceScaleFactor:2});
  await p.goto('http://localhost:8777/index.html',{waitUntil:'networkidle0'});
  await new Promise(r=>setTimeout(r,600));
  await p.evaluate(()=>{document.body.style.background='#fff';});
  // tight crop to cat union rect (CSS px) => DSF2 doubles it
  const clip = {x:210, y:400, width:170, height:105};
  const snap=async(n)=>p.screenshot({path:n, clip});
  await snap('z-idle.png');
  await p.evaluate(()=>document.querySelector('.bongo').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})));
  await new Promise(r=>setTimeout(r,80)); await snap('z-punch1.png');
  await new Promise(r=>setTimeout(r,200));
  await p.evaluate(()=>document.querySelector('.bongo').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})));
  await new Promise(r=>setTimeout(r,80)); await snap('z-punch2.png');
  await b.close(); console.log('done');
})();
