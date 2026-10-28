const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const css = fs.readFileSync(path.join(__dirname,'fonts','fonts.css'),'utf8').replace(/url\(([^)]+\.ttf)\)/g,(m,f)=>`url(file://${path.join(__dirname,'fonts',f)})`);
const items=[['01-kufic','01','الكوفي المربّع','Square Kufic','مستوحى من «الشرق بودكاست»: شبكة هندسية صارمة، ألف بقطع حربة، وإبرة بوصلة نحاسية داخل عين الميم.'],
['02-topo-compass','02','خطوط الخرائط','Topographic Compass','مستوحى من «بصمة»: حروف ثقيلة فوق دائرة بوصلة من خطوط كنتور الخرائط الطبوغرافية.'],
['03-needle','03','إبرة البوصلة','Compass Needle','مستوحى من «قرار حوار»: الألف تتحوّل إلى إبرة بوصلة تشير للشمال، وحروف مائلة بزاوية واحدة توحي بالاندفاع.'],
['04-badge','04','الختم السالب','Negative Badge','مستوحى من «أو» و«نبرة»: حروف محفورة في ختم كحلي تخرج عن حدوده، ونجمة اتجاهات رباعية داخل الميم.'],
['05-blade','05','النصل والرمح','Blade & Spear','مستوحى من «رواق»: خط حرّ بنهايات رمحية حادة، والراء تمتد نصلاً يحتضن الكلمة كاملة.']];
const card=([f,n,ar,en,d])=>`<div class="c"><img src="file://${path.join(__dirname,'out',f+'.png')}"><div class="m"><span class="n">${n}</span><div><h3>${ar} <em>${en}</em></h3><p>${d}</p></div></div></div>`;
const html=`<!doctype html><meta charset=utf-8><style>${css}
body{margin:0;background:#0F1D30;font-family:Tajawal;color:#EEE8DD;width:2400px;padding:90px 100px;box-sizing:border-box;direction:rtl}
header{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2px solid #B8743F;padding-bottom:36px;margin-bottom:60px}
h1{font-size:74px;margin:0;font-weight:800} h1 span{color:#D3925C} .sub{font-size:30px;color:#8C96A5;margin-top:8px}
.en{font-family:'Barlow Condensed';letter-spacing:6px;font-size:26px;color:#8C96A5;direction:ltr;text-align:left}
.g{display:grid;grid-template-columns:repeat(6,1fr);gap:48px}.c{grid-column:span 3;background:#172941;border-radius:6px;overflow:hidden}
.c:first-child{grid-column:span 6}.c:first-child img{aspect-ratio:16/10}
.c:nth-child(n+2):nth-child(-n+3){grid-column:span 3}
img{width:100%;display:block;aspect-ratio:1;object-fit:cover}.m{display:flex;gap:24px;padding:30px 34px 36px;align-items:flex-start}
.n{font-family:'Barlow Condensed';font-weight:700;font-size:56px;color:#D3925C;line-height:1}
h3{margin:0 0 8px;font-size:36px}h3 em{font-style:normal;font-family:'Barlow Condensed';color:#8C96A5;font-size:26px;letter-spacing:3px;margin-right:10px}
p{margin:0;font-size:26px;line-height:1.6;color:#C9CED6}


</style>
<header><div><h1>رام <span>|</span> RAM</h1><div class=sub>رام للدراسات العسكرية والاستراتيجية — «نقرأ القوة، ونحلل الصراع»</div></div><div class=en>LOGO CONCEPTS · 5 DIRECTIONS<br>NAVY · SLATE · COPPER</div></header>
<div class=g>${items.map(card).join('')}</div>`;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:2400,height:1000}});
fs.writeFileSync(path.join(__dirname,'board.html'),html);await p.goto('file://'+path.join(__dirname,'board.html'));await p.evaluate(()=>document.fonts.ready);
await p.screenshot({path:path.join(__dirname,'out','00-board.png'),fullPage:true});await b.close();})();
