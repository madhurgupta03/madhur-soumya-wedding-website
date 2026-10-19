import json, os, re
from playwright.sync_api import sync_playwright
S=os.getcwd(); H=S+'/deliver/soumya-madhur-invite/index.html'
html=open(H).read()
model=json.load(open('site/model.json'))
res={}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':810,'height':1440})
    pg.goto('file://'+H); pg.wait_for_timeout(1500)
    data=pg.evaluate("""() => {
      const out={};
      for (let n=1;n<=8;n++){
        const svg=document.querySelector('#page-'+n+' svg');
        const uses=[...svg.querySelectorAll('use')].map(u=>{const b=u.getBBox(); const m=u.transform.baseVal.consolidate().matrix;
          const x0=m.a*b.x+m.e, x1=m.a*(b.x+b.width)+m.e, y0=m.d*(b.y+b.height)+m.f, y1=m.d*b.y+m.f;
          return {g:u.getAttribute('href'), s:Math.abs(m.a), x0, x1, top:Math.min(y0,y1), bot:Math.max(y0,y1), fill:u.getAttribute('fill')}});
        const texts=[...svg.querySelectorAll('text')].map(t=>{const b=t.getBBox(); const cs=getComputedStyle(t);
          return {t:t.textContent, size:+t.getAttribute('font-size'), weight:t.getAttribute('font-weight'), style:t.getAttribute('font-style'), fill:t.getAttribute('fill'), fam:cs.fontFamily, top:b.y, bot:b.y+b.height, x0:b.x, x1:b.x+b.width}});
        out[n]={uses,texts,label:svg.getAttribute('aria-label')};
      }
      out.fontsLoaded=[...document.fonts].map(f=>f.family+' '+f.weight+' '+f.style+' '+f.status);
      out.sections=[...document.querySelectorAll('body > section')].map(s=>s.id);
      return out;}""")
    b.close()
json.dump(data,open('out/verify.json','w'))
print('sections:',data['sections']); print('fonts:',data['fontsLoaded'])
for n in range(1,9): print(n, data[str(n)]['label'][:160])
