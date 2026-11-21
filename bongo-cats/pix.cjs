const puppeteer = require('puppeteer-core');
(async()=>{
  const b = await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:'new'});
  const p = await b.newPage();
  await p.setViewport({width:400,height:600,deviceScaleFactor:1});
  await p.goto('http://localhost:8777/index.html',{waitUntil:'networkidle0'});
  await new Promise(r=>setTimeout(r,500));
  // 1) sprite alpha stats from the <img> via canvas
  const sp = await p.evaluate(()=>{
    function stats(img){const c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;const x=c.getContext('2d');x.drawImage(img,0,0);const d=x.getImageData(0,0,c.width,c.height).data;let n=0,op=0,sum=0,min=255,max=0;for(let i=0;i<d.length;i+=4){const a=d[i+3];if(a>0){n++;sum+=d[i];if(a<min)min=a;if(a>max)max=a;if(a>200)op++;}}const t=c.width*c.height;return {nw:c.width,nh:c.height,pixN:n,total:t,opaqueFrac:(op/t*100).toFixed(1)+'%',alphaMin:min,alphaMax:max,avgR:(sum/n|0)};}
    return [...document.querySelectorAll('.bongo img')].map(i=>({cls:i.className,...stats(i)}));
  });
  console.log('SPRITES='+JSON.stringify(sp));
  // 2) screenshot the body img's own rect, on white
  await p.evaluate(()=>{document.body.style.background='#fff';});
  const rect = await p.evaluate(()=>{const i=document.querySelector('.bongo .body');const r=i.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};});
  console.log('bodyRect='+JSON.stringify(rect));
  await p.screenshot({path:'px-body.png', clip:{x:Math.round(rect.x),y:Math.round(rect.y),width:Math.round(rect.w),height:Math.round(rect.h)}});
  await b.close(); console.log('ok');
})();
