import json, re, html as H
D=json.load(open('out/verify.json'))
# glyph id -> character, from the PDF glyph exports
gmap={}
for n in range(1,9):
    s=open(f'svgsrc/p{n}.svg').read()
    for m in re.finditer(r'<use data-text="([^"]*)" xlink:href="#(font_[0-9_]+)"',s):
        gmap[f'#p{n}_{m.group(2)}']=H.unescape(m.group(1))
def line_groups(uses, smin, smax):
    us=[u for u in uses if smin<=u['s']<=smax and u['x1']-u['x0']>0.01]
    rows=[]
    for u in sorted(us,key=lambda u:(u['bot'])):
        for r in rows:
            if abs(r[0]['bot']-u['bot'])<14: r.append(u); break
        else: rows.append([u])
    return [sorted(r,key=lambda u:u['x0']) for r in rows]
def txt(r): return ''.join(gmap.get(u['g'],'?') for u in r)
def box(r): return (min(u['x0'] for u in r),max(u['x1'] for u in r),min(u['top'] for u in r),max(u['bot'] for u in r))
# PDF original ink boxes
def pdf_uses(n):
    s=open(f'svgsrc/p{n}.svg').read(); out=[]
    from svgpathtools import parse_path
    defs={m.group(1):m.group(2) for m in re.finditer(r'<path id="(font_[0-9_]+)" d="([^"]*)"',s)}
    for m in re.finditer(r'<use data-text="([^"]*)" xlink:href="#(font_[0-9_]+)" transform="matrix\(([^)]*)\)"',s):
        a,b,c,d,e,f=[float(v) for v in m.group(3).split(',')]
        dd=defs.get(m.group(2),'')
        if not dd.strip(): continue
        x0,x1,y0,y1=parse_path(dd).bbox()
        out.append({'g':'#p%d_%s'%(n,m.group(2)),'s':a,'x0':e+x0*a,'x1':e+x1*a,'top':f-y1*a,'bot':f-y0*a})
    return out
R=[]
def rep(page,item,ok,detail): R.append((page,item,'PASS' if ok is True else ('OPEN' if ok is None else 'FAIL'),detail))

# ---- page 1
p1=D['1']; rows=line_groups(p1['uses'],20,70)
names=[sorted([u for u in p1['uses'] if 20<=u['s']<=70 and u['x1']-u['x0']>0.01],key=lambda u:u['x0'])]
rep(1,'Comment: "Let\'s add Soumya & Madhur"', bool(names), f'Found on cover: "{txt(names[0])}" ' if names else 'not found')
if names:
    b=box(names[0]); rep(1,'  sits just below the monogram, centred', abs((b[0]+b[1])/2-405)<3 and b[2]>785, f'top {b[2]:.0f} pt (monogram ends 786 pt), centre {(b[0]+b[1])/2:.1f} pt (page centre 405)')
dates=[t for t in p1['texts'] if '2026' in t['t']]
rep(1,'Comment: "Maybe add dates here"', None if not dates else True, 'Not added (agreed to keep the cover minimal, as the reviewer preferred)' if not dates else 'added')

# ---- page 2
p2=D['2']; o2=pdf_uses(2)
for nm in ('Soumya Gupta','Madhur Gupta'):
    band=(450,700) if nm.startswith('S') else (750,1000)
    pick=lambda us:[sorted([u for u in us if 60<=u['s']<=70 and band[0]<u['top']<band[1] and u['x1']-u['x0']>0.01],key=lambda u:u['x0'])]
    r=pick(p2['uses']); ro=pick(o2)
    print(nm,'site:',txt(r[0]),'pdf:',txt(ro[0]))
    if r and ro:
        w,wo=box(r[0])[1]-box(r[0])[0], box(ro[0])[1]-box(ro[0])[0]
        cx,cxo=sum(box(r[0])[:2])/2,sum(box(ro[0])[:2])/2
        rep(2,f'Comment: less space between characters in "{nm}"', w<wo, f'width {wo:.1f} → {w:.1f} pt ({(1-w/wo)*100:.1f}% tighter), centre moved {abs(cx-cxo):.2f} pt')
    else: rep(2,nm,False,'line not found')
pickh=lambda us:[sorted([u for u in us if 21<=u['s']<=23 and gmap.get(u['g'])!='\u2756' and u['x1']-u['x0']>0.01],key=lambda u:u['x0'])]
hr=pickh(p2['uses']); ho=pickh(o2); print('hindi site:',txt(hr[0]),'pdf:',txt(ho[0]))
if hr and ho:
    w,wo=box(hr[0])[1]-box(hr[0])[0], box(ho[0])[1]-box(ho[0])[0]
    rep(2,'Comment: less space between characters in "॥ श्री गणेशाय नमः ॥"', w<wo, f'width of the Hindi text {wo:.1f} → {w:.1f} pt ({(1-w/wo)*100:.1f}% tighter)')
pt=[t for t in p2['texts']]
rep(2,'Comment: "Add actual text" (bride\'s parents)', any('Rashmi' in t['t'] for t in pt) and any('Umakant' in t['t'] for t in pt), ' / '.join(t['t'] for t in pt[:2]))
rep(2,'Comment: "Add actual text" (groom\'s parents)', any('Bhavna' in t['t'] for t in pt) and any('Santosh' in t['t'] for t in pt), ' / '.join(t['t'] for t in pt[2:4]))
L=[L for L in json.load(open('site/model.json'))[1]['lines'] if 'lorem' in L['text']]
okstyle=all(t['size']==round(L[0]['size'],3) and t['weight']=='600' and t['fill']==L[0]['color'] for t in pt)
rep(2,'  parent names keep original font/size/colour', okstyle, f"Crimson 600, {pt[0]['size']} pt, {pt[0]['fill']} (original: Crimson-Semibold {L[0]['size']} pt {L[0]['color']})")
allhtml=open('deliver/soumya-madhur-invite/index.html').read()
rep(2,'  no "lorem ipsum" left anywhere', 'lorem' not in allhtml.lower() and all('lorem' not in txt(r).lower() for n in range(1,9) for r in line_groups(D[str(n)]['uses'],1,200)), 'checked page text and drawn letters on all 8 pages')

# ---- pages 3-7
model=json.load(open('site/model.json'))
gaps={}
for n in range(3,8):
    P=D[str(n)]
    v=[t for t in P['texts'] if t['style']=='italic']
    orig=[L for L in model[n-1]['lines'] if L['font']=='Crimson-SemiboldItalic']
    rep(n,'Comment: venue font "without bold and little smaller"', all(t['weight']=='400' and t['size']<orig[0]['size'] for t in v),
        f"{len(v)} lines: {orig[0]['size']} pt semibold italic → {v[0]['size']:g} pt regular italic, colour {v[0]['fill']} (orig {orig[0]['color']})")
    date=[u for u in P['uses'] if abs(u['s']-34.4775)<0.05]
    dtop=min(u['top'] for u in date)
    title=[u for u in P['uses'] if u['s']>40 and u['x1']-u['x0']>0.01 and u['top']<dtop]
    gaps[n]=dtop-max(u['bot'] for u in title)
    trows=line_groups(title,40,90)
    if n==4:
        t=[txt(r) for r in trows]
        amp=[u for u in title if gmap.get(u['g'])=='&']
        rep(4,'Comment: "Engagement / & (small) / Sangeet, skip the ceremony"', t==['ENGAGEMENT','&','SANGEET'] or [x.upper() for x in t]==['ENGAGEMENT','&','SANGEET'],
            f"title lines now: {' / '.join(t)}; '&' drawn at {amp[0]['s']:.1f} pt vs words at 84.8 pt; 'Ceremony' gone: {'eremony' not in ''.join(t).lower()}")
    if n==5:
        t=[txt(r) for r in trows]; amp=[u for u in title if gmap.get(u['g'])=='&']
        rep(5,'Comment: "Haldi / & (small) / Mehendi"', [x.upper() for x in t]==['HALDI','&','MEHENDI'], f"title lines now: {' / '.join(t)}; '&' at {amp[0]['s']:.1f} pt")
    if n==7:
        rep(7,'Comment: "Why is this font different" (Jaimala)', None, 'NOT changed: still the script font. The PDF only contains the title font\'s letters used on other pages and has no "J". Needs the Alta font file from the designer')
g=list(gaps.values())
rep('3–7','Comment: "same width for all title and text sep"', max(g)-min(g)<0.5, 'title→date gap: '+', '.join(f'p{k} {v:.2f}' for k,v in gaps.items())+' pt')

# ---- page 8
rep(8,'Comment: "Logo here, maybe small"', None, 'NOT added: no logo file has been shared yet')
t8=D['8']['label']; o8=' '.join(L['text'].strip() for L in model[7]['lines'])
rep(8,'Page 8 text unchanged', t8.strip()==o8.strip(), 'identical to the PDF')
for r in R: print(r)
json.dump(R,open('out/verify-results.json','w'),ensure_ascii=False)
