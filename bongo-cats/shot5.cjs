const puppeteer = require('puppeteer-core');
(async()=>{
  const b = await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:'new'});
  const p = await b.newPage();
  await p.setViewport({width:360,height:640,deviceScaleFactor:2});
  await p.goto('http://localhost:8777/index.html',{waitUntil:'networkidle0'});
  await new Promise(r=>setTimeout(r,600));
  // NO bg override — real dark page
  const clip = {x:170, y:330, width:170, height:150}; // around wrap (210,350 180x180): show cat
  const snap=async(n)=>p.screenshot({path:n, clip});
  await snap('real-idle.png');
  await p.evaluate(()=>document.querySelector('.bongo').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})));
  await new Promise(r=>setTimeout(r,80)); await snap('real-punch1.png');
  await new Promise(r=>setTimeout(r,200));
  await p.evaluate(()=>document.querySelector('.bongo').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})));
  await new Promise(r=>setTimeout(r,80)); await snap('real-punch2.png');
  await b.close(); console.log('done');
})();
