const puppeteer = require('puppeteer-core'), fs=require('fs');
const SRC=256, DIR='extracted/skins/Cat/';
const FRAMES = {
  body: { idle:{src:'left.png',x:20.0,y:56.0,w:229.9,h:111.9}, punch:{src:'left_punch.png',x:7.1,y:17.1,w:242.9,h:150.9} },
  front:{ idle:{src:'right.png',x:162.0,y:57.1,w:60.9,h:70.8}, puck:{src:'right_punch.png',x:147.1,y:16.1,w:98.8,h:76.9} },
};
const b64 = m=>'data:image/png;base64,'+fs.readFileSync(DIR+m).toString('base64');
const IMGDATA = { 'left.png':b64('left.png'),'left_punch.png':b64('left_punch.png'),'right.png':b64('right.png'),'right_punch.png':b64('right_punch.png') };
(async()=>{
  const b = await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:'new'});
  const p = await b.newPage();
  await p.setViewport({width:256,height:256,deviceScaleFactor:2});
  const data = JSON.stringify(IMGDATA);
  await p.setContent('<canvas id="c" width="256" height="256"></canvas>');
  const res = await p.evaluate(async (data)=>{
    const d=JSON.parse(data);
    const load=src=>new Promise((ok,fail)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=fail;i.src=d[src];});
    const imgs={};
    for(const k of Object.keys(d)){imgs[k]=await load(k);}
    window.__imgs=imgs; return Object.keys(imgs).map(k=>[k,imgs[k].naturalWidth,imgs[k].naturalHeight]);
  }, data);
  console.log('loaded='+JSON.stringify(res));
  async function draw(name, body, front){
    const png = await p.evaluate(({body,front})=>{
      const c=document.getElementById('c'),x=c.getContext('2d');
      x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);
      function put(f){const img=window.__imgs[f.src];if(!img)throw new Error('no '+f.src);
        const cx=f.x+f.w/2, cy=f.y+f.h/2, dx=cx-128, dy=cy-128;
        x.drawImage(img, 128+dx-f.w/2, 128-dy-f.h/2, f.w, f.h);
      }
      put(body); put(front);
      return c.toDataURL('image/png');
    },{body,front});
    fs.writeFileSync(name, Buffer.from(png.split(',')[1],'base64'));
    console.log('wrote '+name);
  }
  await draw('comp-idle.png', FRAMES.body.idle, FRAMES.front.idle);
  await draw('comp-punch-far.png', FRAMES.body.punch, FRAMES.front.idle);
  await draw('comp-punch-near.png', FRAMES.body.idle, FRAMES.front.puck);
  await b.close(); console.log('done');
})();
