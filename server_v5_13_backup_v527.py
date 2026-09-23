import json, os, random, time, urllib.parse, threading, mimetypes, shutil
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
ROOT=os.path.dirname(os.path.abspath(__file__))
REPLAY=json.load(open(os.path.join(ROOT,'replay_v5.json'),encoding='utf-8'))
POOL_FILE=os.path.join(ROOT,'prize_pools_v2.json')
POOLS=json.load(open(POOL_FILE,encoding='utf-8')) if os.path.exists(POOL_FILE) else {}
CARD_DETAIL_FILE=os.path.join(ROOT,'card_details_v511.json')
CARD_DETAILS=json.load(open(CARD_DETAIL_FILE,encoding='utf-8')) if os.path.exists(CARD_DETAIL_FILE) else {}
CARD_POOL_FILE=os.path.join(ROOT,'card_pool_v511.json')
CARD_POOLS=json.load(open(CARD_POOL_FILE,encoding='utf-8')) if os.path.exists(CARD_POOL_FILE) else {}
CARD_EXACT_FILE=os.path.join(ROOT,'card_exact_prices_v510.json')
CARD_EXACT=json.load(open(CARD_EXACT_FILE,encoding='utf-8')) if os.path.exists(CARD_EXACT_FILE) else {}
BAG_FILE=os.path.join(ROOT,'local_bag.json')
CARD_RATES_FILE=os.path.join(ROOT,'card_rates.json')
CARD_RATES_DEFAULT_FILE=os.path.join(ROOT,'card_rates_defaults_v511.json')
CARD_RATES_DEFAULT=json.load(open(CARD_RATES_DEFAULT_FILE,encoding='utf-8')) if os.path.exists(CARD_RATES_DEFAULT_FILE) else {}
CARD_ALBUM_FILE=os.path.join(ROOT,'card_album_v514.json')
CARD_ALBUM=json.load(open(CARD_ALBUM_FILE,encoding='utf-8')) if os.path.exists(CARD_ALBUM_FILE) else {}
LOCAL_PROFILE_FILE=os.path.join(ROOT,'local_profile.json')
CARD_ITEM_DETAILS_FILE=os.path.join(ROOT,'card_item_details_v524.json')
CARD_ITEM_DETAILS=json.load(open(CARD_ITEM_DETAILS_FILE,encoding='utf-8')) if os.path.exists(CARD_ITEM_DETAILS_FILE) else {}
LOCAL_STATS_FILE=os.path.join(ROOT,'local_stats.json')

def default_stats():
    return {'SP':{'current':0,'runs':[]},'A':{'current':0,'runs':[]},'history':[]}

def load_stats():
    try:
        x=json.load(open(LOCAL_STATS_FILE,encoding='utf-8'))
        d=default_stats()
        for lvl in ('SP','A'):
            q=x.get(lvl,{}) if isinstance(x,dict) else {}
            d[lvl]={'current':max(0,int(q.get('current',0) or 0)),'runs':[max(0,int(v)) for v in (q.get('runs') or [])][-100:]}
        d['history']=(x.get('history') or [])[-500:] if isinstance(x,dict) else []
        return d
    except: return default_stats()

def save_stats(x):
    tmp=LOCAL_STATS_FILE+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)
    os.replace(tmp,LOCAL_STATS_FILE)

def stats_summary():
    s=load_stats(); outx={}
    for lvl in ('SP','A'):
        runs=s[lvl]['runs']; cur=s[lvl]['current']
        outx[lvl]={'current':cur,'runs':runs,'average':round(sum(runs)/len(runs),2) if runs else 0,'max':max(runs) if runs else 0,'hits':len(runs)}
    outx['history']=list(reversed(s['history']))
    return outx

def record_pack_stats(gid, pack_rows):
    s=load_stats(); now=time.strftime('%Y-%m-%d %H:%M:%S')
    for pack_no,rows in enumerate(pack_rows,1):
        lvls={str(x.get('shang_title') or '').upper() for x in rows}
        for target in ('SP','A'):
            s[target]['current']+=1
            if target in lvls:
                s[target]['runs'].append(s[target]['current'])
                s[target]['runs']=s[target]['runs'][-100:]
                s[target]['current']=0
        # History UI is only for winning SP/A packs. B/C/D packs still count
        # toward the SP/A distance counters above, but are not shown in History.
        has_sp='SP' in lvls
        has_a='A' in lvls
        if has_sp or has_a:
            best='SP' if has_sp else 'A'
            s['history'].append({'time':now,'goods_id':gid,'pack_no':pack_no,'order_interval_num':rows[0].get('order_interval_num') if rows else None,'tier':best,'has_sp':has_sp,'has_a':has_a,'cards':[{'title':x.get('goodslist_title') or x.get('title'),'tier':x.get('shang_title'),'image':x.get('goodslist_imgurl'),'price':x.get('goodslist_price')} for x in rows]})
    s['history']=s['history'][-500:]; save_stats(s)



def local_card_shang_logs(p):
    """History tab: one row per local SP/A card. B/C/D never appear here."""
    gid=str(p.get('goods_id') or '0')
    try: shang_id=int(p.get('shang_id') or 0)
    except: shang_id=0
    try: page=max(1,int(p.get('page') or 1)); limit=max(1,int(p.get('limit') or 10))
    except: page,limit=1,10
    wanted={100:'SP',101:'A'}.get(shang_id)
    prof=load_profile()
    hist=list(reversed(load_stats().get('history',[])))
    hist=[h for h in hist if str(h.get('goods_id'))==gid]

    rows=[]
    seq=0
    for h in hist:
        ts=h.get('time') or ''
        try: addunix=int(time.mktime(time.strptime(ts,'%Y-%m-%d %H:%M:%S')))
        except: addunix=int(time.time())
        pack_id=int(h.get('order_interval_num') or 0)

        # IMPORTANT: history is card-level, not pack-level.
        # Only SP/A cards are emitted. B/C/D cards in the same pack are ignored.
        for c in (h.get('cards') or []):
            tier=str(c.get('tier') or '').strip().upper()
            if tier not in ('SP','A'):
                continue
            if wanted and tier != wanted:
                continue
            seq += 1
            sid=100 if tier=='SP' else 101
            title=c.get('title') or ''
            img=c.get('image') or ''
            price=str(c.get('price') or '0')
            row_id=pack_id*10 + seq if pack_id else int(time.time()*1000)+seq
            one_goods={
              'id':row_id,'sale_num':pack_id,'order_interval_num':pack_id,
              'goodslist_imgurl':img,'shang_id':sid,'num':1,
              'goodslist_money':price,'goodslist_price':price,'prize_type':1,
              'goodslist_id':0,'real_goods_list_id':0,
              'goodslist_title':title,'short_title':title,
              'shang_title':tier,'shang_image':LEVEL_BADGES.get(tier,'')
            }
            rows.append({
              'id':row_id,'user_id':999999,'shang_id':sid,
              'goodslist_id':0,'real_goods_list_id':0,
              'goodslist_imgurl':img,'sale_num':pack_id,
              'order_interval_num':pack_id,'order_id':pack_id,'addtime':addunix,
              'goodslist_price':price,'interval_num':1,
              'goodslist_title':title,'short_title':title,
              'price':price,'goodslist_money':price,
              'shang_title':tier,'shang_image':LEVEL_BADGES.get(tier,''),
              'straddtime':0,'nickname':prof['name'],'headimg':'','head_border':'',
              'sum_price':float(price or 0),'goods_imgurl':'','goodslist':[one_goods]
            })

    total=len(rows); start_i=(page-1)*limit; rows=rows[start_i:start_i+limit]
    rr=effective_rates(gid,CARD_DETAILS.get(gid,{}).get('data',{}))
    cats=[{'shang_id':0,'shang_title':'ทั้งหมด'}]
    for lvl,sid in [('SP',100),('A',101)]:
        if lvl in rr:
            cats.append({'shang_id':sid,'sum_real_pro':f"{float(rr[lvl]):.8f}",'max_sort':0,
              'shanginfo':{'id':sid,'title':lvl,'shang_level':4 if lvl=='SP' else 3,'image':LEVEL_BADGES.get(lvl,'')},
              'lilun':round(100/float(rr[lvl])) if float(rr[lvl]) else 0,'shang_title':lvl})
    return {'status':1,'msg':'Request successful','data':{'interval_num_average':1,'sh_no':0,'category':cats,'data':rows,
      'total':total,'current_page':page,'last_page':max(1,(total+limit-1)//limit)}}

def local_card_shang_count(p):
    """Statistics graph: blue=completed local runs, red=current local run."""
    gid=str(p.get('goods_id') or '0'); s=load_stats(); prof=load_profile(); rr=effective_rates(gid,CARD_DETAILS.get(gid,{}).get('data',{}))
    data={'type':'card_shang_count','now_sp_num':int(time.time())}
    for lvl,sid,prefix in [('SP',100,'SP'),('A',101,'A')]:
        q=s[lvl]; runs=list(q.get('runs') or []); cur=int(q.get('current') or 0)
        arr=[]
        # First item is the current red bar used by the captured UI.
        arr.append({'id':-sid,'user_id':999999,'goodslist_id':0,'interval_num':cur,'order_interval_num':int(time.time()),'goodslist_price':'0.000','shang_id':sid,'sale_num':0,'addtime':int(time.time()),
          'userinfo':{'id':999999,'nickname':lvl,'headimg':'','headimg_frame_id':'','headimg_brand_id':''},'shanginfo':{'id':sid,'title':lvl,'image':LEVEL_BADGES.get(lvl,''),'detail_image':LEVEL_BADGES.get(lvl,'')},
          'userinfo_id':999999,'nickname':lvl,'headimg':'','head_border':'','is_current':1})
        for i,v in enumerate(reversed(runs[-20:])):
            arr.append({'id':-(sid*100+i+1),'user_id':999999,'goodslist_id':0,'interval_num':int(v),'order_interval_num':0,'goodslist_price':'0.000','shang_id':sid,'sale_num':0,'addtime':int(time.time()),
              'userinfo':{'id':999999,'nickname':prof['name'],'headimg':'','headimg_frame_id':'','headimg_brand_id':''},'shanginfo':{'id':sid,'title':lvl,'image':LEVEL_BADGES.get(lvl,''),'detail_image':LEVEL_BADGES.get(lvl,'')},
              'userinfo_id':999999,'nickname':prof['name'],'headimg':'','head_border':'','is_current':0})
        avg=round(sum(runs)/len(runs)) if runs else 0; mx=max(runs) if runs else 0; rate=float(rr.get(lvl,0) or 0)
        data[prefix]=arr; data[prefix+'not_yet_released']=cur; data[prefix+'_probability']=rate; data[prefix+'_all_probability']=avg; data[prefix+'_gailv']=rate; data[prefix+'_average']=mx
    return {'status':1,'msg':'Request successful','data':data}

def load_profile():
    try:
        x=json.load(open(LOCAL_PROFILE_FILE,encoding='utf-8'))
        return {'name':str(x.get('name') or 'Local User'),'money':max(0.0,float(x.get('money',99999)))}
    except: return {'name':'Local User','money':99999.0}

def save_profile(x):
    tmp=LOCAL_PROFILE_FILE+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)
    os.replace(tmp,LOCAL_PROFILE_FILE)

LOCAL_ADMIN_HTML='<!doctype html><html lang="th"><head><meta charset="utf-8"><title>JOYPOP Local Settings</title><style>body{font-family:Arial;background:#111;color:#eee;padding:24px}.w{max-width:650px;margin:auto}.c{background:#1c1c1c;border:1px solid #333;border-radius:16px;padding:20px}input,button{font-size:17px;padding:11px;margin:8px 0;border-radius:9px}input{background:#111;color:#fff;width:90%}</style></head><body><div class="w"><h1>JOYPOP Local Settings</h1><div class="c">ชื่อตัวละคร<br><input id="nm"><br>เงิน Local<br><input id="mo" type="number" min="0" step="0.01"><br><button onclick="sv()">บันทึก</button><p>ยอดปัจจุบัน ฿<b id="bal"></b></p></div></div><script>async function ld(){let j=await (await fetch(\'/api/local/profile\')).json();nm.value=j.data.name;mo.value=j.data.money;bal.textContent=(+j.data.money).toFixed(2)}async function sv(){let j=await (await fetch(\'/api/local/profile\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({name:nm.value,money:+mo.value})})).json();if(!j.status)return alert(j.msg);await ld();alert(\'บันทึกแล้ว\')}ld()</script></body></html>'

def load_card_rates():
    try:
        x=json.load(open(CARD_RATES_FILE,encoding='utf-8'))
        return x if isinstance(x,dict) else {}
    except: return {}

def save_card_rates(x):
    tmp=CARD_RATES_FILE+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)
    os.replace(tmp,CARD_RATES_FILE)

def effective_rates(gid, detail):
    gid=str(gid); custom=load_card_rates().get(gid)
    if isinstance(custom,dict) and custom: return {str(k).upper():float(v) for k,v in custom.items()}
    return dict(CARD_RATES_DEFAULT.get(gid,{}) or {})

RATE_ADMIN_HTML='''<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>JOYPOP Local Rate Admin</title><style>body{font-family:Arial,sans-serif;background:#111;color:#eee;margin:0;padding:24px}.wrap{max-width:850px;margin:auto}.card{background:#1c1c1c;border:1px solid #333;border-radius:16px;padding:20px;margin:14px 0}select,input,button{font-size:16px;padding:10px;border-radius:8px;border:1px solid #444}select,input{background:#111;color:#fff}input{width:120px}.row{display:grid;grid-template-columns:80px 150px 1fr;gap:12px;align-items:center;margin:10px 0}.ok{color:#50d890}.bad{color:#ff6262}button{cursor:pointer;margin-right:8px}.note{color:#aaa;font-size:13px}</style></head><body><div class="wrap"><h1>JOYPOP Local — ปรับเรท Card</h1><div class="card"><label>เลือกตู้ </label><select id="cab"></select><div id="title" style="margin-top:12px;font-weight:bold"></div></div><div class="card" id="rates"></div><div class="card"><b>รวม: <span id="total"></span>%</b><div style="margin-top:16px"><button onclick="save()">บันทึกเรท</button><button onclick="resetRate()">คืนค่าจาก HAR</button></div><p class="note">มีผลเฉพาะระบบสุ่ม Local เท่านั้น ไม่แก้หรือส่งค่าไป JOYPOP</p></div></div><script>
let data={}; async function load(){data=await (await fetch('/api/local/card_rates')).json(); let s=document.getElementById('cab'); s.innerHTML=''; Object.keys(data.cabinets).forEach(id=>{let o=document.createElement('option');o.value=id;o.textContent=id+' — '+data.cabinets[id].title;s.appendChild(o)}); s.onchange=render; render()}
function render(){let id=cab.value,c=data.cabinets[id]; title.textContent=c.title; rates.innerHTML=''; ['SP','A','B','C','D'].forEach(k=>{if(c.available.includes(k)||c.rates[k]!=null){let d=document.createElement('div');d.className='row';d.innerHTML='<b>'+k+'</b><input type="number" min="0" step="0.01" data-k="'+k+'" value="'+(c.rates[k]??0)+'"><span>%</span>';rates.appendChild(d)}}); rates.querySelectorAll('input').forEach(x=>x.oninput=sum);sum()}
function sum(){let n=[...rates.querySelectorAll('input')].reduce((a,x)=>a+(+x.value||0),0);total.textContent=n.toFixed(2);total.className=Math.abs(n-100)<.001?'ok':'bad'}
async function save(){let id=cab.value,r={};rates.querySelectorAll('input').forEach(x=>r[x.dataset.k]=+x.value||0);let t=Object.values(r).reduce((a,b)=>a+b,0);if(Math.abs(t-100)>.001){alert('ผลรวมต้องเท่ากับ 100%');return} await fetch('/api/local/card_rates',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goods_id:id,rates:r})}); await load();cab.value=id;render();alert('บันทึกแล้ว')}
async function resetRate(){let id=cab.value;await fetch('/api/local/card_rates/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goods_id:id})});await load();cab.value=id;render()}
load();</script></body></html>'''
LOCK=threading.Lock()
FORCE_LEVEL=None
LEVEL_WEIGHTS={"SP":2,"A":8,"B":20,"C":70} # LOCAL DEMO ONLY

# Local tier presentation assets.
# shang_image = small SP/A/B/C badge.
# B and C use the same blue/ice card background, matching the captured UI.
LEVEL_BADGES={
    "SP":"/local-img/upload/20260817/91bfc32d5b257d01216aef3bbc4cff13de6f3f6d.webp",
    "A":"/local-img/upload/20260817/42b480e3af1884bd2ddc3c5c1789a4d0b86992c6.webp",
    "B":"/local-img/upload/20260817/6b140c0b707528013e3d079e637740e5ee0f1b6b.webp",
    "C":"/local-img/upload/20260817/f86d7dd169a497e17dc330c44627f98071761775.webp",
}
BC_BACKGROUND="/h5/assets/local-tier-bc-ice.png"

def apply_level_background(x):
    lvl=str(x.get('shang_title') or '').strip().upper()

    # Keep the actual tier badge separate from the card background.
    badge=LEVEL_BADGES.get(lvl)
    if badge:
        x['shang_image']=badge

    # JOYPOP B/C presentation uses the blue/ice background.
    # Force both fields because different frontend views read different fields.
    if lvl in ('B','C'):
        x['back_image']=BC_BACKGROUND
        x['color_t']=BC_BACKGROUND

    return x

def load_bag():
    try:
        x=json.load(open(BAG_FILE,encoding='utf-8'))
        return x if isinstance(x,list) else []
    except: return []
def save_bag(x):
    tmp=BAG_FILE+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)
    os.replace(tmp,BAG_FILE)

def parse_params(handler, body):
    p=dict(urllib.parse.parse_qsl(urllib.parse.urlparse(handler.path).query,keep_blank_values=True))
    if body:
      text=body.decode('utf-8','ignore'); ct=(handler.headers.get('Content-Type') or '').lower()
      try:
        if 'json' in ct or text.lstrip().startswith(('{','[')):
          x=json.loads(text)
          if isinstance(x,dict):
            for k,v in x.items(): p[str(k)]=str(v) if not isinstance(v,(dict,list)) else json.dumps(v,sort_keys=True,separators=(',',':'))
        else: p.update(dict(urllib.parse.parse_qsl(text,keep_blank_values=True)))
      except: pass
    return p

def rkey(path,p): return path+'|'+(urllib.parse.urlencode(sorted(p.items())) if p else '')
def out(h,obj,status=200):
    b=json.dumps(obj,ensure_ascii=False).encode(); h.send_response(status); h.send_header('Content-Type','application/json; charset=utf-8'); h.send_header('Access-Control-Allow-Origin','*'); h.send_header('Cache-Control','no-store'); h.send_header('Content-Length',str(len(b))); h.end_headers(); h.wfile.write(b)
def user():
 x=load_profile(); m=f"{float(x['money']):.2f}"; n=x['name']
 return {"status":1,"msg":"Request successful","data":{"userinfo":{"id":999999,"pid":999999,"username":n,"nickname":n,"name":n,"avatar":"","money":m,"balance":m,"credit":m,"language":"en-US","vip":0,"level":0,"is_login":1,"login":1}}}

def choose(gid):
    pool=POOLS.get(str(gid),{})
    if not pool:return None
    levels=[x for x in pool if pool.get(x)]
    if not levels:return None
    lvl=FORCE_LEVEL if FORCE_LEVEL in levels else random.choices(levels,weights=[LEVEL_WEIGHTS.get(x,1) for x in levels],k=1)[0]
    x=dict(random.choice(pool[lvl])); x['shang_title']=lvl
    title=x.get('goodslist_title') or x.get('title') or x.get('short_title') or 'Local Prize'
    image=x.get('goodslist_imgurl') or x.get('imgurl') or x.get('imgurltwo') or x.get('content_image') or ''
    price=x.get('goodslist_price') or x.get('price') or x.get('show_price') or '0.00'
    try: price=f'{float(price):.2f}'
    except: price=str(price)
    x.update(goodslist_title=title,title=title,goodslist_imgurl=image,imgurl=image,goodslist_price=price,price=price)
    x.setdefault('shang_id',{'SP':100,'A':101,'B':102,'C':103}.get(lvl,102))

    # Force the correct captured presentation background for SP/A/B/C.
    apply_level_background(x)

    return x

def add_to_bag(items,gid):
    with LOCK:
      bag=load_bag()
      for x in items:
        now=int(time.time()*1000)
        code='LOCAL-'+str(gid)+'-'+str(x.get('goods_list_id') or x.get('real_goods_list_id') or x.get('goodslist_id') or now)+'-'+str(now)+'-'+str(random.randint(1000,9999))
        b=dict(x)
        b.update({'prize_code':code,'prize_num':1,'num':1,'goods_id':gid,'status':1,'created_at':int(time.time())})
        bag.insert(0,b)
      save_bag(bag)

def prize_key(x):
    # Same physical prize/card = same stack. Use one shared ID namespace.
    v=x.get('goods_list_id') or x.get('real_goods_list_id') or x.get('goodslist_id')
    if v not in (None,'',0,'0'):
        return 'id:'+str(v)
    title=str(x.get('goodslist_title') or x.get('title') or x.get('short_title') or '')
    image=str(x.get('goodslist_imgurl') or x.get('imgurl') or x.get('imgurltwo') or '')
    return 'fallback:'+title+'|'+image

def grouped_bag(bag):
    groups={}
    order=[]
    for x in bag:
        k=prize_key(x)
        if k not in groups:
            y=dict(x)
            y['_stack_codes']=[]
            y['prize_num']=0
            y['num']=0
            groups[k]=y; order.append(k)
        y=groups[k]
        qty=max(1,int(x.get('prize_num',1) or 1))
        y['prize_num']+=qty
        y['num']+=qty
        if x.get('prize_code'): y['_stack_codes'].append(str(x['prize_code']))
    rows=[groups[k] for k in order]
    # Repair/normalize backgrounds for existing local_bag.json rows as well.
    for y in rows:
        apply_level_background(y)
    # Price high -> low only. Quantity does not affect sorting.
    def get_price(x):
        try:
            return float(x.get('goodslist_price') or x.get('price') or x.get('show_price') or 0)
        except (TypeError, ValueError):
            return 0.0
    rows.sort(key=get_price, reverse=True)
    for y in rows:
        y['stack_key']=prize_key(y)
        y['stack_codes']=list(y.pop('_stack_codes',[]))
    return rows

def card_album_response(p):
    gid=str(p.get('goods_id') or '0')
    src=CARD_ALBUM.get(gid,{})
    base=[dict(x) for x in (src.get('rows') or [])]

    # HAR ownership + cards obtained from local draws.
    owned=set(str(x.get('id')) for x in base if x.get('whether_to_have'))
    try:
      for b in load_bag():
        if str(b.get('goods_id'))==gid:
          cid=(b.get('album_card_id')
               or b.get('goodslist_id')
               or b.get('goods_list_id')
               or b.get('real_goods_list_id'))
          if cid: owned.add(str(cid))
    except: pass

    for x in base:
      x['whether_to_have']=1 if str(x.get('id')) in owned else None
      for k in ('imgurl','goodslist_imgurl','shang_imgurl'):
          v=x.get(k)
          if isinstance(v,str) and 'img.joypop.gg/' in v:
              rel=v.split('img.joypop.gg/',1)[1]
              x[k]='/local-img/'+rel

    shang=int(p.get('shang_id') or 0)
    typ=int(p.get('type') or 0)
    filtered=base
    if shang:
      filtered=[x for x in filtered if int(x.get('shang_id') or 0)==shang]
    if typ==1:
      filtered=[x for x in filtered if x.get('whether_to_have')]

    total_all=len(base)
    owned_all=sum(1 for x in base if x.get('whether_to_have'))
    level_total=sum(1 for x in base if shang and int(x.get('shang_id') or 0)==shang) if shang else 0
    level_owned=sum(1 for x in base if shang and int(x.get('shang_id') or 0)==shang and x.get('whether_to_have')) if shang else 0

    page=max(1,int(p.get('page') or 1))
    limit=max(1,int(p.get('limit') or 15))
    start=(page-1)*limit
    page_rows=filtered[start:start+limit]
    last=(len(filtered)+limit-1)//limit if filtered else 0

    return {'status':1,'msg':'ดำเนินการสำเร็จ','data':{
      'data':page_rows,
      'sum_count':total_all,
      'my_sum_count':owned_all,
      'level_sum_count':level_total,
      'level_my_sum_count':level_owned,
      'last_page':last,
      'currency_info':src.get('currency_info')
    }}

def bag_response(p):
    typ=str(p.get('type','1')); page=max(1,int(p.get('page','1') or 1)); per=20
    with LOCK: bag=load_bag()
    stacks=grouped_bag(bag)
    start=(page-1)*per; rows=stacks[start:start+per]
    last=(len(stacks)+per-1)//per if stacks else 0
    # prize_num = visible stacks on this page; total_prize_num = total physical cards/items.
    total_items=sum(int(x.get('prize_num',1) or 1) for x in stacks)
    return {'status':1,'msg':'Request successful','data':{'data':rows,'last_page':last,'prize_num':len(rows),'total_prize_num':total_items}}

def bag_sell(p):
    raw=p.get('choice_info','[]')
    try: choices=json.loads(raw) if isinstance(raw,str) else raw
    except: choices=[]
    sold=0.0

    with LOCK:
      bag=load_bag()

      # The UI sends the representative prize_code of each checked stack.
      # Resolve that code back to its stack key, then sell EVERY physical item
      # in that checked stack, regardless of the quantity sent by the UI.
      selected_keys=set()
      selected_codes=set()
      for c in choices if isinstance(choices,list) else []:
        code=str(c.get('prize_code',''))
        if code:
          selected_codes.add(code)

      for x in bag:
        if str(x.get('prize_code','')) in selected_codes:
          selected_keys.add(prize_key(x))

      kept=[]
      sold_count=0
      for x in bag:
        if prize_key(x) in selected_keys:
          sold_count+=max(1,int(x.get('prize_num',1) or 1))
          try: sold+=float(x.get('goodslist_price') or x.get('price') or 0) * max(1,int(x.get('prize_num',1) or 1))
          except: pass
        else:
          kept.append(x)

      save_bag(kept)
      prof=load_profile(); prof['money']=round(float(prof['money'])+sold,2); save_profile(prof)

    return {'status':1,'msg':'Operation successful','data':{'goodslist_price':round(sold,2),'sold_count':sold_count,'money':load_profile()['money']}}

def order(gid,n):
    items=[]
    for i in range(n):
      x=choose(gid)
      if not x:return {"status":0,"msg":f"No local prize pool for goods_id {gid}","data":None}
      x.update({'id':int(time.time()*1000)+i,'user_id':999999,'key_str':f'LOCAL-DEMO-{gid}-{i}','seed':'LocalDemo','sale_num':i+1,'user_box_num':i+1,'use_money':'0','use_money_coin':'0'})
      items.append(x)
    add_to_bag(items,gid)
    return {'status':1,'msg':'Order placed successfully','data':{'pay_type':1,'get_score':0,'order_num':f'LOCAL-{int(time.time())}','sum_use_money':n*2,'sum_use_money_coin':0,'data':{'list':items,'shang_list':items}}}


def card_order(gid,n):
    detail=CARD_DETAILS.get(str(gid),{}).get('data',{})

    # จำนวน Pack × จำนวนการ์ดต่อ Pack
    packs=max(1,int(n or 1))
    try:
      cards_per_pack=max(1,int(detail.get('num') or 1))
    except:
      cards_per_pack=1

    n=packs*cards_per_pack
    try: pack_price=float(detail.get('price') or 0)
    except: pack_price=0.0
    cost=round(pack_price*packs,2)
    prof=load_profile()
    if cost>float(prof['money']): return {'status':0,'msg':f"เงินไม่พอ ต้องใช้ ฿{cost:.2f} แต่มี ฿{float(prof['money']):.2f}",'data':None}

    # V5.18:
    # ใช้การ์ดทั้งหมดจาก Album เป็น pool หลัก
    album=CARD_ALBUM.get(str(gid),{})
    album_rows=album.get('rows') or []

    if album_rows:
      pool=[dict(x) for x in album_rows]
    else:
      pool=[dict(x) for x in CARD_POOLS.get(str(gid),[])]

    if not pool:
      return {
        "status":0,
        "msg":f"No local card pool for goods_id {gid}",
        "data":None
      }

    # LOCAL SIMULATION: use the tier percentages captured from /api/card/detail.
    # This fixes V5.6, which picked directly from goodslist_all (mostly SP/A only).
    tier_rates=effective_rates(gid, detail)

    available={}
    for z in pool:
      lvl=str(z.get('shang_title') or '').strip().upper()
      if lvl: available.setdefault(lvl,[]).append(z)

    levels=[lvl for lvl in tier_rates if available.get(lvl)]
    if not levels:
      levels=list(available)
    if not levels:
      return {"status":0,"msg":f"No usable local card prizes for goods_id {gid}","data":None}

    weights=[tier_rates.get(lvl,1.0) for lvl in levels]
    # V5.21: real JOYPOP groups all cards from one pack with the same order_interval_num.
    pack_base=int(time.time()*1000)
    items=[]
    for i in range(n):
      lvl=random.choices(levels,weights=weights,k=1)[0]
      candidates=available[lvl]

      # If captured per-card probability exists, respect it; otherwise equal within tier.
      item_weights=[]
      for z in candidates:
        try: w=float(z.get('real_pro') or 0)
        except: w=0.0
        item_weights.append(w if w>0 else 1.0)
      src=dict(random.choices(candidates,weights=item_weights,k=1)[0])

      img=src.get('goodslist_imgurl') or src.get('imgurl') or ''
      # Card result images must be served by the local mirror, never the live image host.
      img=str(img).replace(
        'https://img.joypop.gg/',
        '/local-img/'
      ).replace(
        'http://img.joypop.gg/',
        '/local-img/'
      )
      if img.startswith('/local-img/'):
        img=''+img
      title=src.get('goodslist_title') or src.get('title') or src.get('short_title') or f"{detail.get('title','Card')} - {lvl}"
      short=src.get('short_title') or title
      raw_price=src.get('goodslist_price') or src.get('price') or src.get('goodslist_money') or '0.00'
      try: price=f"{float(raw_price):.2f}"
      except: price=str(raw_price)

      pid=src.get('goodslist_id') or src.get('goods_list_id') or src.get('id') or (int(time.time()*1000)+i)
      realid=src.get('real_goods_list_id') or src.get('goods_list_id') or pid
      # Keep all cards from the same pack on the same interval number.
      pack_index = i // cards_per_pack
      order_interval_num = pack_base + pack_index
      x=dict(src)
      x.update({
        'id':int(time.time()*1000)+i,
        # Keep the original Album row ID so Collection ownership can be updated.
        'album_card_id':src.get('id'),
        'order_interval_num':order_interval_num,
        'goodslist_id':pid,
        'real_goods_list_id':realid,
        'goods_list_id':realid,
        'shang_id':{'SP':100,'A':101,'B':102,'C':103,'D':104}.get(lvl,104),
        'goodslist_title':title,'short_title':short,'title':title,
        'goodslist_imgurl':img,'imgurl':img,
        'goodslist_price':price,'price':price,
        'shang_title':lvl,
        'shang_image':LEVEL_BADGES.get(lvl) or src.get('shang_imgurl') or src.get('shang_iamge') or src.get('shang_image') or '',
        'key_str':f'LOCAL-CARD-{gid}-{i}','seed':'LocalDemo',
        'score':'0.00','use_money':'0','use_money_coin':'0',
        'user_id':999999,'sale_num':i+1,'user_box_num':i+1
      })
      items.append(x)

    if cost>0:
      prof=load_profile(); prof['money']=round(max(0,float(prof['money'])-cost),2); save_profile(prof)
    pack_rows=[items[i:i+cards_per_pack] for i in range(0,len(items),cards_per_pack)]
    record_pack_stats(gid,pack_rows)
    add_to_bag(items,gid)
    return {'status':1,'msg':'Order placed successfully','data':{
      'pay_type':0,'get_score':'0.00','order_num':f'LOCAL-CARD-{int(time.time())}',
      'use_money':cost,'sum_use_money':cost,'sum_use_money_coin':0,'order_total':cost,
      'money':load_profile()['money'],'balance':load_profile()['money'],'credit':load_profile()['money'],'data':items
    }}

BLOCK=('login','register','logout','payment','deposit','withdraw','recharge','session_sync')
class H(SimpleHTTPRequestHandler):
 def end_headers(self): self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Cache-Control','no-store'); super().end_headers()
 def do_OPTIONS(self): self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Headers','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS'); self.end_headers()
 def do_GET(self): self.route(b'')
 def do_HEAD(self): self.route(b'')
 def do_POST(self):
    n=int(self.headers.get('Content-Length','0') or 0); self.route(self.rfile.read(n) if n else b'')
 def route(self,body):
    u=urllib.parse.urlparse(self.path); path=u.path; p=parse_params(self,body)
    if path=='/rate-admin':
      b=RATE_ADMIN_HTML.encode('utf-8'); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
    if path=='/local-admin':
      b=LOCAL_ADMIN_HTML.encode('utf-8'); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
    if path=='/api/local/profile':
      if not body: return out(self,{'status':1,'data':load_profile()})
      try:
        x=json.loads(body.decode('utf-8')); cur=load_profile(); cur['name']=str(x.get('name') or cur['name']).strip()[:60] or 'Local User'; cur['money']=max(0.0,float(x.get('money',cur['money']))); save_profile(cur); return out(self,{'status':1,'data':cur})
      except Exception as e: return out(self,{'status':0,'msg':str(e)},400)
    if path=='/api/local/stats':
      return out(self,{'status':1,'msg':'Request successful','data':stats_summary()})
    if path=='/api/local/stats/reset':
      save_stats(default_stats()); return out(self,{'status':1,'msg':'Reset','data':stats_summary()})
    if path=='/api/local/card_rates' and not body:
      custom=load_card_rates(); cabinets={}
      for gid,obj in CARD_DETAILS.items():
        data=obj.get('data',{}) if isinstance(obj,dict) else {}
        pool=CARD_POOLS.get(str(gid),[]) or data.get('goodslist_all',[]) or []
        av=sorted(set(str(x.get('shang_title') or '').upper() for x in pool if x.get('shang_title')),key=lambda x:['SP','A','B','C','D'].index(x) if x in ['SP','A','B','C','D'] else 99)
        cabinets[str(gid)]={'title':data.get('title') or ('Cabinet '+str(gid)),'rates':custom.get(str(gid)) or CARD_RATES_DEFAULT.get(str(gid),{}),'available':av}
      return out(self,{'status':1,'cabinets':cabinets})
    if path=='/api/local/card_rates' and body:
      try:
        x=json.loads(body.decode('utf-8')); gid=str(x.get('goods_id')); rr={str(k).upper():float(v) for k,v in (x.get('rates') or {}).items()}; total=sum(rr.values())
        if abs(total-100)>0.001:return out(self,{'status':0,'msg':'Total rate must be 100%'},400)
        allr=load_card_rates(); allr[gid]=rr; save_card_rates(allr); return out(self,{'status':1,'msg':'Saved','data':rr})
      except Exception as e:return out(self,{'status':0,'msg':str(e)},400)
    if path=='/api/local/card_rates/reset':
      try:
        x=json.loads(body.decode('utf-8')); gid=str(x.get('goods_id')); allr=load_card_rates(); allr.pop(gid,None); save_card_rates(allr); return out(self,{'status':1,'msg':'Reset'})
      except Exception as e:return out(self,{'status':0,'msg':str(e)},400)
    if path=='/api/user/user': return out(self,user())
    if path=='/api/card/card_shang_logs': return out(self,local_card_shang_logs(p))
    if path=='/api/card/card_shang_count': return out(self,local_card_shang_count(p))
    if path=='/api/card/cardgoodslist_detail':
      cid=str(p.get('id') or p.get('goodslist_id') or p.get('goods_list_id') or '0')
      d=CARD_ITEM_DETAILS.get(cid)
      if d:
        d=json.loads(json.dumps(d)); data=d.get('data',{})
        for k in ('imgurl','content_image','goodslist_imgurl'):
          if data.get(k):
            v=str(data[k]).replace('https://img.joypop.gg/','/local-img/').replace('http://img.joypop.gg/','/local-img/')
            if not v.startswith(('http://','https://','/')): v='/local-img/'+v.lstrip('/')
            data[k]=v
        return out(self,d)
      for gid,pool in CARD_POOLS.items():
        for z in pool:
          if str(z.get('id') or z.get('goodslist_id') or z.get('goods_list_id') or '')==cid:
            img=str(z.get('goodslist_imgurl') or z.get('imgurl') or '').replace('https://img.joypop.gg/','/local-img/')
            return out(self,{'status':1,'msg':'ดำเนินการสำเร็จ','data':{'id':z.get('id'),'goods_id':int(gid),'goods_list_id':z.get('goods_list_id') or z.get('real_goods_list_id'),'title':z.get('goodslist_title') or z.get('title') or z.get('short_title'),'short_title':z.get('short_title'),'imgurl':img,'content_image':img,'price':z.get('goodslist_price') or z.get('price'),'show_price':z.get('goodslist_price') or z.get('price'),'real_pro':z.get('real_pro'),'shang_id':z.get('shang_id')}})
      return out(self,{'status':0,'msg':f'No captured card detail for id {cid}','data':None})
    if path=='/api/card/detail':
      gid=str(p.get('id') or p.get('goods_id') or '0')
      obj=CARD_DETAILS.get(gid)
      if obj is not None:
        # Return only this cabinet's own detail/pool; never cross-fallback.
        obj=json.loads(json.dumps(obj))
        data=obj.get('data',{})
        pool=CARD_POOLS.get(gid)
        if isinstance(pool,list) and pool:
          data['goodslist_all']=pool
        rr=effective_rates(gid,data)
        if rr:
          data['goodslist']=[{'shang_id':{'SP':100,'A':101,'B':102,'C':103,'D':104}.get(k,104),'real_pro':f'{float(v):.8f}','shang_title':k} for k,v in rr.items()]
        return out(self,obj)
      return out(self,{"status":0,"msg":f"No captured card detail for goods_id {gid}","data":None})
    if path=='/api/infinite/order_buy': return out(self,order(int(p.get('goods_id','0') or 0),max(1,int(p.get('prize_num','1') or 1))))
    if path=='/api/card/order_buy': return out(self,card_order(int(p.get('goods_id','0') or 0),max(1,int(p.get('prize_num','1') or 1))))
    if path=='/api/card/order_money':
      n=max(1,int(p.get('prize_num','1') or 1)); gid=str(p.get('goods_id','0')); d=CARD_DETAILS.get(gid,{}).get('data',{}); price=float(d.get('price') or 0); cost=round(price*n,2); bal=round(float(load_profile()['money']),2); goods={'title':d.get('title') or '', 'price':f'{price:.4f}', 'prize_num':n, 'num':int(d.get('num') or 1), 'prize_count':int(d.get('prize_count') or 0), 'imgurl':d.get('imgurl') or ''}; return out(self,{"status":1,"msg":"Request successful","data":{"goods":goods,"coupon_id":0,"coupon_money":0,"order_total":cost,"price":0,"money":bal,"balance":bal,"credit":bal,"use_money":cost,"sum_use_money":cost,"sum_use_money_coin":0,"money_stone":0,"use_money_stone":0}})
    if path=='/api/infinite/order_money':
      n=max(1,int(p.get('prize_num','1') or 1)); return out(self,{"status":1,"msg":"Request successful","data":{"sum_use_money":n*2,"sum_use_money_coin":0}})
    if path=='/api/bag/cardbag_goodslist': return out(self,card_album_response(p))
    if path=='/api/bag/bag': return out(self,bag_response(p))
    if path=='/api/market/bag_sell': return out(self,bag_sell(p))
    if path=='/api/local/bag_clear':
      with LOCK: save_bag([])
      return out(self,{'status':1,'msg':'Local bag cleared','data':None})
    if path.startswith('/api/'):
      if any(x in path.lower() for x in BLOCK): return out(self,{"status":0,"msg":"Blocked in local demo","data":None},403)
      k=rkey(path,p); obj=REPLAY.get(k)
      if obj is None: obj=REPLAY.get(path+'|')
      if obj is not None: print('[HAR REPLAY]',k); return out(self,obj)
      print('[MISSING LOCAL API]',path,p); return out(self,{"status":0,"msg":"No local replay available","data":None})
    if path=='/h5/sw.js': self.send_response(204); self.end_headers(); return
    if path=='/': self.path='/joypop.gg/h5/'
    elif path.startswith('/h5/'): self.path='/joypop.gg'+path
    elif path.startswith('/cdn-cgi/'): self.path='/joypop.gg'+path
    elif path.startswith('/local-img/'):
      # V5.17: serve mirrored img.joypop.gg files directly from disk.
      # urlparse() above already removes ?x-oss-process=... from `path`.
      rel=urllib.parse.unquote(path[len('/local-img/'):]).lstrip('/').replace('\\','/')
      imgroot=os.path.abspath(os.path.join(ROOT,'img.joypop.gg'))
      candidate=os.path.abspath(os.path.join(imgroot,rel))

      # Block ../ traversal.
      if not (candidate == imgroot or candidate.startswith(imgroot+os.sep)):
        self.send_error(403,'Forbidden')
        return

      if not os.path.isfile(candidate):
        print('[MISSING LOCAL IMAGE]',rel,candidate)
        self.send_error(404,'File not found')
        return

      ext=os.path.splitext(candidate)[1].lower()
      mime_map={
        '.webp':'image/webp',
        '.png':'image/png',
        '.jpg':'image/jpeg',
        '.jpeg':'image/jpeg',
        '.gif':'image/gif',
        '.svg':'image/svg+xml',
        '.avif':'image/avif'
      }
      ctype=mime_map.get(ext) or mimetypes.guess_type(candidate)[0] or 'application/octet-stream'

      try:
        size=os.path.getsize(candidate)
        self.send_response(200)
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(size))
        self.end_headers()

        # HEAD sends headers only; GET sends the image bytes.
        if self.command != 'HEAD':
          with open(candidate,'rb') as f:
            shutil.copyfileobj(f,self.wfile)
        return
      except (BrokenPipeError,ConnectionResetError):
        return
      except Exception as e:
        print('[LOCAL IMAGE ERROR]',candidate,repr(e))
        return
    return SimpleHTTPRequestHandler.do_GET(self)

os.chdir(ROOT)
PORT=int(os.environ.get('PORT','8080'))
print(f'JOYPOP Local V5.28 -> 0.0.0.0:{PORT}')
print('Rate Admin -> /rate-admin')
print('Cabinet 18 album: 17 cards / 11 collected (matched to HAR)')
print('Local Bag V5.5: stack xN, sort price high -> low, checked stack sells all')
print('Real purchases/auth are blocked.')
ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()