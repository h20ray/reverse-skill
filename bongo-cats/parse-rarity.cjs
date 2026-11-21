const fs = require('fs');
const P = 'C:/Program Files (x86)/Steam/userdata/64667282/inventorymsgcache/BEDAF4EE132800E385A8703F383F6767D6D700FE.cachedmsg';
const raw = fs.readFileSync(P, 'utf8');
let arr;
try {
  arr = JSON.parse(raw.replace(/\x00+$/, ''));
} catch (e) {
  console.error('JSON.parse failed:', e.message);
  console.error('length:', raw.length);
  // try to find the offending byte
  for (let i = 0; i < raw.length; i++) {
    const c = raw.charCodeAt(i);
    if (c < 32 && c !== 9 && c !== 10 && c !== 13) { console.error('control char at', i, c); break; }
  }
  process.exit(1);
}
console.log('total itemdefs:', arr.length);
const skins = [];
for (const it of arr) {
  const tags = (it.tags || '').split(';');
  const q = tags.find(t => t.startsWith('quality:'));
  const slot = tags.find(t => t.startsWith('itemslot:'));
  if (slot === 'itemslot:skin') skins.push({ name: it.name, quality: q ? q.split(':')[1] : null, itemdefid: it.itemdefid, name_color: it.name_color });
}
console.log('skins:', skins.length);
const byq = {};
for (const s of skins) byq[s.quality] = (byq[s.quality] || 0) + 1;
console.log('by quality:', JSON.stringify(byq));
fs.writeFileSync('C:/GitHub/reverse-skill/bongo-cats/skin-rarity.json', JSON.stringify(skins, null, 2));
console.log('written skin-rarity.json');
