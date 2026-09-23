import json, os, random, time, urllib.parse, urllib.request, threading, mimetypes, shutil
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
INFINITE_RATES_FILE=os.path.join(ROOT,'infinite_rates.json')
CARD_RATES_DEFAULT_FILE=os.path.join(ROOT,'card_rates_defaults_v511.json')
CARD_RATES_DEFAULT=json.load(open(CARD_RATES_DEFAULT_FILE,encoding='utf-8')) if os.path.exists(CARD_RATES_DEFAULT_FILE) else {}

CARD_ALBUM_FILE=os.path.join(ROOT,'card_album_v514.json')
CARD_ALBUM=json.load(open(CARD_ALBUM_FILE,encoding='utf-8')) if os.path.exists(CARD_ALBUM_FILE) else {}
POOL_FILE=os.path.join(ROOT,'prize_pools_v2.json')
POOLS=json.load(open(POOL_FILE,encoding='utf-8')) if os.path.exists(POOL_FILE) else {}


# ============================================================
# COMBO / GUARANTEED REWARD DETAILS
# ============================================================

COMBO_DETAIL_FILE = os.path.join(
    ROOT,
    'combo_details.json'
)

COMBO_DETAILS = json.load(
    open(
        COMBO_DETAIL_FILE,
        encoding='utf-8'
    )
) if os.path.exists(
    COMBO_DETAIL_FILE
) else {}

CARD_DETAIL_FILE=os.path.join(ROOT,'card_details_v511.json')

# =========================
# HAR CARD POOL - FULL SP/A/B/C/D
# =========================
HAR_CARD_POOL_FILE=os.path.join(ROOT,'card_pool_har.json')
HAR_CARD_POOLS=json.load(
    open(HAR_CARD_POOL_FILE,encoding='utf-8')
) if os.path.exists(HAR_CARD_POOL_FILE) else {}

LOCAL_PROFILE_FILE=os.path.join(ROOT,'local_profile.json')

CARD_ITEM_DETAILS_FILE=os.path.join(ROOT,'card_item_details_v524.json')
CARD_ITEM_DETAILS=json.load(
    open(CARD_ITEM_DETAILS_FILE,encoding='utf-8')
) if os.path.exists(CARD_ITEM_DETAILS_FILE) else {}
# =========================
# LOCAL STATS
# =========================
LOCAL_STATS_FILE=os.path.join(ROOT,'local_stats.json')

# =========================
# PACK COUNTER
# =========================
PACK_COUNTER_FILE=os.path.join(ROOT,'pack_counter.json')


COMBO_STATE_FILE = os.path.join(
    ROOT,
    'combo_state.json'
)


def load_combo_state():

    if not os.path.exists(
        COMBO_STATE_FILE
    ):
        return {}

    try:

        with open(
            COMBO_STATE_FILE,
            'r',
            encoding='utf-8'
        ) as f:

            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception as e:

        print(
            '[COMBO STATE LOAD ERROR]',
            e
        )

    return {}


def save_combo_state(state):

    try:

        tmp = COMBO_STATE_FILE + '.tmp'

        with open(
            tmp,
            'w',
            encoding='utf-8'
        ) as f:

            json.dump(
                state,
                f,
                ensure_ascii=False,
                indent=2
            )

        os.replace(
            tmp,
            COMBO_STATE_FILE
        )

    except Exception as e:

        print(
            '[COMBO STATE SAVE ERROR]',
            e
        )


def get_combo_count(gid):

    state = load_combo_state()

    row = state.get(
        str(gid)
    )

    if not isinstance(row, dict):
        return 0

    try:
        return max(
            0,
            int(row.get('count') or 0)
        )
    except Exception:
        return 0


def set_combo_count(gid, count):

    state = load_combo_state()

    gid = str(gid)

    row = state.get(gid)

    if not isinstance(row, dict):
        row = {}

    row['count'] = max(
        0,
        int(count)
    )

    state[gid] = row

    save_combo_state(
        state
    )

def reserve_pack_numbers(count):
    """
    เลขซอง Local
    เริ่มครั้งแรกจาก 0
    จากนั้น 1, 2, 3, 4...
    ปิด/เปิด Server ใหม่เลขยังต่อ
    """
    count = max(1, int(count or 1))

    try:
        with open(PACK_COUNTER_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        last = int(data.get('last', -1))
    except:
        last = -1

    start = last + 1
    numbers = list(range(start, start + count))

    tmp = PACK_COUNTER_FILE + '.tmp'

    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(
            {'last': numbers[-1]},
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(tmp, PACK_COUNTER_FILE)

    return numbers


def default_stats():
    return {'goods': {}}


def load_stats():
    try:
        with open(LOCAL_STATS_FILE, 'r', encoding='utf-8') as f:
            x = json.load(f)

        # FORMAT ใหม่
        if isinstance(x, dict) and isinstance(x.get('goods'), dict):
            out = {'goods': {}}

            for gid, old in x['goods'].items():
                cabinet = {
                    'SP': {'current': 0, 'runs': []},
                    'A': {'current': 0, 'runs': []},
                    'history': []
                }

                if isinstance(old, dict):
                    for lvl in ('SP', 'A'):
                        q = old.get(lvl, {})

                        try:
                            cabinet[lvl]['current'] = max(
                                0,
                                int(q.get('current', 0) or 0)
                            )
                        except:
                            pass

                        runs = []

                        for v in (
                            q.get('runs', [])
                            if isinstance(q, dict)
                            else []
                        ):

                            # ========================================================
                            # FORMAT ใหม่
                            #
                            # {
                            #   "count": 9,
                            #   "name": "Nut",
                            #   "headimg": "...",
                            #   "time": "..."
                            # }
                            # ========================================================

                            if isinstance(v, dict):

                                try:
                                    count = max(
                                        0,
                                        int(
                                            v.get(
                                                'count',
                                                0
                                            )
                                            or 0
                                        )
                                    )
                                except:
                                    count = 0

                                if count > 0:

                                    item = dict(v)

                                    item['count'] = count

                                    item['name'] = str(
                                        item.get('name')
                                        or 'Local User'
                                    )

                                    item['headimg'] = str(
                                        item.get('headimg')
                                        or ''
                                    )

                                    runs.append(item)

                                continue

                            # ========================================================
                            # FORMAT เก่า
                            #
                            # runs = [9, 15, 6]
                            #
                            # รองรับไว้ จะได้ไม่ error
                            # ========================================================

                            try:

                                count = max(
                                    0,
                                    int(v)
                                )

                                if count > 0:

                                    runs.append({
                                        'count':
                                            count,

                                        'name':
                                            'Local User',

                                        'headimg':
                                            '',

                                        'time':
                                            ''
                                    })

                            except:
                                pass


                        cabinet[lvl]['runs'] = \
                            runs[-100:]

                    hist = old.get('history', [])

                    if isinstance(hist, list):
                        cabinet['history'] = hist[-500:]

                out['goods'][str(gid)] = cabinet

            return out

        # FORMAT เก่า
        # SP/A current และ runs เก่าเป็นข้อมูลรวมทุกตู้
        # จึงไม่ย้าย เพื่อไม่ให้ข้อมูลข้ามตู้
        out = {'goods': {}}

        if isinstance(x, dict):
            for row in x.get('history', []):
                if not isinstance(row, dict):
                    continue

                gid = str(row.get('goods_id') or '').strip()

                if not gid:
                    continue

                if gid not in out['goods']:
                    out['goods'][gid] = {
                        'SP': {'current': 0, 'runs': []},
                        'A': {'current': 0, 'runs': []},
                        'history': []
                    }

                out['goods'][gid]['history'].append(row)

        for gid in out['goods']:
            out['goods'][gid]['history'] = \
                out['goods'][gid]['history'][-500:]

        return out

    except Exception as e:
        print('[STATS LOAD ERROR]', e)
        return {'goods': {}}


def save_stats(x):
    tmp = LOCAL_STATS_FILE + '.tmp'

    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(
            x,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(tmp, LOCAL_STATS_FILE)


def stats_summary(gid=None):
    s = load_stats()

    def build(cabinet):
        out = {}

        for lvl in ('SP', 'A'):
            q = cabinet.get(
                lvl,
                {'current': 0, 'runs': []}
            )

            try:
                cur = max(
                    0,
                    int(q.get('current', 0) or 0)
                )
            except:
                cur = 0

            runs = list(q.get('runs') or [])

            counts = []

            for run in runs:
                if isinstance(run, dict):
                    try:
                        count = int(
                            run.get('count', 0) or 0
                        )
                    except:
                        count = 0
                else:
                    try:
                        count = int(run)
                    except:
                        count = 0

                if count > 0:
                    counts.append(count)

            out[lvl] = {
                'current': cur,
                'runs': runs,
                'average': (
                    round(sum(counts) / len(counts), 2)
                    if counts else 0
                ),
                'max': max(counts) if counts else 0,
                'hits': len(counts)
            }

        out['history'] = list(
            reversed(
                cabinet.get('history', [])
            )
        )

        return out

    # ทุกตู้
    if gid is None:
        result = {}

        for goods_id, cabinet in (
            s.get('goods', {}).items()
        ):
            result[str(goods_id)] = build(cabinet)

        return {
            'goods': result
        }

    # ตู้เดียว
    gid = str(gid)

    cabinet = (
        s.get('goods', {})
        .get(
            gid,
            {
                'SP': {'current': 0, 'runs': []},
                'A': {'current': 0, 'runs': []},
                'history': []
            }
        )
    )

    return build(cabinet)

def record_pack_stats(gid, pack_rows):
    gid = str(gid)

    s = load_stats()
    goods = s.setdefault('goods', {})

    # ============================================================
    # สร้าง Stats ของตู้ ถ้ายังไม่มี
    # ============================================================

    if gid not in goods:
        goods[gid] = {
            'SP': {
                'current': 0,
                'runs': []
            },
            'A': {
                'current': 0,
                'runs': []
            },
            'history': []
        }

    cabinet = goods[gid]

    # กันโครงสร้างเก่าหรือข้อมูลไม่ครบ
    for target in ('SP', 'A'):

        if (
            target not in cabinet
            or not isinstance(cabinet[target], dict)
        ):
            cabinet[target] = {
                'current': 0,
                'runs': []
            }

        try:
            cabinet[target]['current'] = max(
                0,
                int(
                    cabinet[target].get(
                        'current',
                        0
                    )
                    or 0
                )
            )
        except:
            cabinet[target]['current'] = 0

        if not isinstance(
            cabinet[target].get('runs'),
            list
        ):
            cabinet[target]['runs'] = []

    if not isinstance(
        cabinet.get('history'),
        list
    ):
        cabinet['history'] = []

    # ============================================================
    # ข้อมูลคนที่กำลังเปิด
    # ============================================================

    try:
        prof = load_profile()
    except:
        prof = {}

    player_name = str(
        prof.get('name')
        or 'Local User'
    )

    player_headimg = str(
        prof.get('headimg')
        or ''
    )

    now = time.strftime(
        '%Y-%m-%d %H:%M:%S'
    )

    # ============================================================
    # LOOP แต่ละ PACK
    # ============================================================

    for pack_no, rows in enumerate(
        pack_rows,
        1
    ):

        if not isinstance(rows, list):
            continue

        # ========================================================
        # ORDER NUMBER
        # ========================================================

        order_no = None

        if rows:

            try:
                order_no = rows[0].get(
                    'order_interval_num'
                )
            except:
                order_no = None

        # ========================================================
        # DUPLICATE GUARD
        #
        # ถ้า order นี้เคยถูกบันทึกใน history แล้ว
        # จะไม่:
        #
        # - เพิ่ม current
        # - เพิ่ม runs
        # - เพิ่ม history
        #
        # ทำให้ request เดิมยิงซ้ำแล้ว Stats ไม่วิ่งตามกัน
        # ========================================================

        already_recorded = False

        if order_no not in (
            None,
            '',
            0,
            '0'
        ):

            for old in cabinet.get(
                'history',
                []
            ):

                if not isinstance(
                    old,
                    dict
                ):
                    continue

                old_order = old.get(
                    'order_interval_num'
                )

                if (
                    old_order not in (
                        None,
                        '',
                        0,
                        '0'
                    )
                    and
                    str(old_order)
                    ==
                    str(order_no)
                ):
                    already_recorded = True
                    break

        # PACK นี้เคยบันทึกแล้ว
        if already_recorded:

            print(
                '[STATS DUPLICATE SKIP]',
                'gid=',
                gid,
                'order=',
                order_no
            )

            continue

        # ========================================================
        # หา Tier ทั้งหมดที่อยู่ใน PACK
        # ========================================================

        lvls = set()

        for x in rows:

            if not isinstance(
                x,
                dict
            ):
                continue

            level = str(
                x.get('shang_title')
                or ''
            ).strip().upper()

            if level:
                lvls.add(level)

        # ========================================================
        # SP / A COUNTER
        # ========================================================

        for target in (
            'SP',
            'A'
        ):

            # ทุก PACK ที่ไม่ซ้ำ
            # ต้องเพิ่ม counter
            cabinet[target]['current'] += 1

            # ====================================================
            # ถ้า PACK นี้เจอ SP/A
            # ====================================================

            if target in lvls:

                completed_count = int(
                    cabinet[target]['current']
                )

                # ================================================
                # RUN ที่จบแล้ว
                #
                # count = จำนวนซองที่ใช้จนออก
                # name  = คนที่เปิดได้
                # ================================================

                new_run = {

                    'count':
                        completed_count,

                    'name':
                        player_name,

                    'headimg':
                        player_headimg,

                    'time':
                        now,

                    'goods_id':
                        gid,

                    'pack_no':
                        pack_no,

                    'order_interval_num':
                        order_no
                }

                # ================================================
                # GUARD ซ้ำอีกรอบสำหรับ RUN
                # ================================================

                duplicate_run = False

                if order_no not in (
                    None,
                    '',
                    0,
                    '0'
                ):

                    for old_run in cabinet[
                        target
                    ].get(
                        'runs',
                        []
                    ):

                        if not isinstance(
                            old_run,
                            dict
                        ):
                            continue

                        old_order = old_run.get(
                            'order_interval_num'
                        )

                        if (
                            old_order not in (
                                None,
                                '',
                                0,
                                '0'
                            )
                            and
                            str(old_order)
                            ==
                            str(order_no)
                        ):
                            duplicate_run = True
                            break

                # ================================================
                # บันทึก Completed Run
                # ================================================

                if not duplicate_run:

                    cabinet[target][
                        'runs'
                    ].append(
                        new_run
                    )

                    cabinet[target][
                        'runs'
                    ] = (
                        cabinet[target][
                            'runs'
                        ][-100:]
                    )

                    print(
                        '[STATS HIT]',
                        'gid=',
                        gid,
                        'tier=',
                        target,
                        'count=',
                        completed_count,
                        'player=',
                        player_name,
                        'order=',
                        order_no
                    )

                # ================================================
                # เจอแล้ว
                # เริ่มนับรอบใหม่จาก 0
                # ================================================

                cabinet[target][
                    'current'
                ] = 0

        # ========================================================
        # HISTORY
        # ========================================================

        has_sp = (
            'SP'
            in lvls
        )

        has_a = (
            'A'
            in lvls
        )

        if has_sp:
            best = 'SP'

        elif has_a:
            best = 'A'

        else:
            best = ''

        # ========================================================
        # CARD LIST
        # ========================================================

        history_cards = []

        for x in rows:

            if not isinstance(
                x,
                dict
            ):
                continue

            history_cards.append({

                'title':
                    (
                        x.get(
                            'goodslist_title'
                        )
                        or
                        x.get(
                            'title'
                        )
                        or ''
                    ),

                'tier':
                    str(
                        x.get(
                            'shang_title'
                        )
                        or ''
                    ).strip().upper(),

                'image':
                    (
                        x.get(
                            'goodslist_imgurl'
                        )
                        or ''
                    ),

                'price':
                    x.get(
                        'goodslist_price'
                    )
            })

        # ========================================================
        # บันทึก HISTORY
        # ========================================================

        cabinet[
            'history'
        ].append({

            'time':
                now,

            'goods_id':
                gid,

            'pack_no':
                pack_no,

            'player_name':
                player_name,

            'player_headimg':
                player_headimg,

            'order_interval_num':
                order_no,

            'tier':
                best,

            'has_sp':
                has_sp,

            'has_a':
                has_a,

            'cards':
                history_cards
        })

        # ========================================================
        # จำกัด HISTORY 500 PACK
        # ========================================================

        cabinet[
            'history'
        ] = (
            cabinet[
                'history'
            ][-500:]
        )

        print(
            '[STATS PACK]',
            'gid=',
            gid,
            'order=',
            order_no,
            'SP current=',
            cabinet['SP']['current'],
            'A current=',
            cabinet['A']['current']
        )

    # ============================================================
    # SAVE
    # ============================================================

    save_stats(s)


def record_infinite_stats(gid, items):
    gid = str(gid)

    if not isinstance(items, list):
        return

    s = load_stats()
    goods = s.setdefault('goods', {})

    if gid not in goods:
        goods[gid] = {
            'SP': {
                'current': 0,
                'runs': []
            },
            'A': {
                'current': 0,
                'runs': []
            },
            'history': [],
            'draw_seq': 0
        }

    cabinet = goods[gid]

    # ============================================================
    # FIX OLD STRUCTURE
    # ============================================================

    for target in ('SP', 'A'):

        if (
            target not in cabinet
            or not isinstance(cabinet[target], dict)
        ):
            cabinet[target] = {
                'current': 0,
                'runs': []
            }

        try:
            cabinet[target]['current'] = max(
                0,
                int(
                    cabinet[target].get('current', 0)
                    or 0
                )
            )
        except:
            cabinet[target]['current'] = 0

        if not isinstance(
            cabinet[target].get('runs'),
            list
        ):
            cabinet[target]['runs'] = []

    if not isinstance(
        cabinet.get('history'),
        list
    ):
        cabinet['history'] = []

    # ============================================================
    # DRAW SEQUENCE
    # ============================================================

    try:
        draw_seq = int(
            cabinet.get('draw_seq', 0)
            or 0
        )
    except:
        draw_seq = 0

    # ถ้าเป็นข้อมูลเก่าและยังไม่มี draw_seq
    if draw_seq <= 0:

        for old in cabinet['history']:

            if not isinstance(old, dict):
                continue

            try:
                old_draw = int(
                    old.get('draw_no', 0)
                    or old.get('order_interval_num', 0)
                    or 0
                )
            except:
                old_draw = 0

            draw_seq = max(
                draw_seq,
                old_draw
            )

    # ============================================================
    # LOCAL PLAYER
    # ============================================================

    try:
        prof = load_profile()
    except:
        prof = {}

    player_name = str(
        prof.get('name')
        or 'Local User'
    )

    player_headimg = str(
        prof.get('headimg')
        or ''
    )

    # ============================================================
    # EACH INFINITE RESULT = 1 DRAW
    # ============================================================

    for item in items:

        if not isinstance(item, dict):
            continue

        draw_seq += 1

        now = time.strftime(
            '%Y-%m-%d %H:%M:%S'
        )

        tier = str(
            item.get('shang_title')
            or item.get('tier')
            or ''
        ).strip().upper()

        title = str(
            item.get('goodslist_title')
            or item.get('title')
            or ''
        )

        image = str(
            item.get('goodslist_imgurl')
            or item.get('image')
            or item.get('imgurl')
            or ''
        )

        price = str(
            item.get('goodslist_price')
            or item.get('goodslist_money')
            or item.get('price')
            or '0'
        )

        # ========================================================
        # SP / A COUNTERS
        # ========================================================

        for target in ('SP', 'A'):

            cabinet[target]['current'] += 1

            if tier == target:

                completed_count = int(
                    cabinet[target]['current']
                )

                cabinet[target]['runs'].append({
                    'count':
                        completed_count,

                    'name':
                        player_name,

                    'headimg':
                        player_headimg,

                    'time':
                        now,

                    'goods_id':
                        gid,

                    'draw_no':
                        draw_seq,

                    'order_interval_num':
                        draw_seq
                })

                cabinet[target]['runs'] = (
                    cabinet[target]['runs'][-100:]
                )

                print(
                    '[INFINITE STATS HIT]',
                    'gid=', gid,
                    'tier=', target,
                    'count=', completed_count,
                    'draw=', draw_seq,
                    'player=', player_name
                )

                # เจอแล้วเริ่ม streak ใหม่
                cabinet[target]['current'] = 0

        # ========================================================
        # HISTORY
        #
        # สำคัญ:
        # บันทึกทุก Tier
        # SP / A / B / C / D / ...
        # ========================================================

        history_card = {
            'title':
                title,

            'tier':
                tier,

            'image':
                image,

            'price':
                price,

            'goodslist_id':
                (
                    item.get('goodslist_id')
                    or item.get('real_goods_list_id')
                    or item.get('id')
                    or 0
                )
        }

        cabinet['history'].append({
            'time':
                now,

            'goods_id':
                gid,

            'draw_no':
                draw_seq,

            # frontend เดิมอ่าน field นี้
            'order_interval_num':
                draw_seq,

            'pack_no':
                draw_seq,

            'player_name':
                player_name,

            'player_headimg':
                player_headimg,

            'tier':
                tier,

            'has_sp':
                tier == 'SP',

            'has_a':
                tier == 'A',

            'cards': [
                history_card
            ]
        })

        cabinet['history'] = (
            cabinet['history'][-500:]
        )

        print(
            '[INFINITE DRAW]',
            'gid=', gid,
            'draw=', draw_seq,
            'tier=', tier,
            'title=', title,
            'price=', price,
            'SP current=',
            cabinet['SP']['current'],
            'A current=',
            cabinet['A']['current']
        )

    cabinet['draw_seq'] = draw_seq

    save_stats(s)

    print(
        '[INFINITE STATS SAVED]',
        'gid=', gid,
        'total_draw=', draw_seq,
        'SP current=',
        cabinet['SP']['current'],
        'SP runs=',
        len(cabinet['SP']['runs']),
        'A current=',
        cabinet['A']['current'],
        'A runs=',
        len(cabinet['A']['runs'])
    )

def local_card_shang_logs(p):
    gid=str(p.get('goods_id') or '0')
    try: shang_id=int(p.get('shang_id') or 0)
    except: shang_id=0
    try:
        page=max(1,int(p.get('page') or 1))
        limit=max(1,int(p.get('limit') or 10))
    except:
        page,limit=1,10

    wanted={100:'SP',101:'A'}.get(shang_id)
    prof=load_profile()
    stats = load_stats()

    cabinet = (
        stats
        .get('goods', {})
        .get(gid, {})
    )

    hist = cabinet.get(
        'history',
        []
    )

    if not isinstance(hist, list):
        hist = []

    # ใหม่สุดอยู่ด้านบน
    hist = list(
        reversed(hist)
    )

    rows = []
    seq = 0

    for h in hist:
        ts=h.get('time') or ''
        try: addunix=int(time.mktime(time.strptime(ts,'%Y-%m-%d %H:%M:%S')))
        except: addunix=int(time.time())
        pack_id=int(h.get('order_interval_num') or 0)
        cards=list(h.get('cards') or [])

        # ALL = one row per pack.
        if shang_id == 0:
            if not cards: continue
            special=None
            for target in ('SP','A'):
                special=next((c for c in cards if str(c.get('tier') or '').strip().upper()==target),None)
                if special: break

            tier=str(special.get('tier') or '').strip().upper() if special else ''
            sid=100 if tier=='SP' else (101 if tier=='A' else 0)
            title=special.get('title') or '' if special else ''
            img=special.get('image') or '' if special else ''
            price=str(special.get('price') or '0') if special else '0'

            goodslist=[]
            for j,c in enumerate(cards,1):
                ctier=str(c.get('tier') or '').strip().upper()
                csid={'SP':100,'A':101,'B':102,'C':103,'D':104}.get(ctier,0)
                cprice=str(c.get('price') or '0')
                ctitle=c.get('title') or ''
                cimg=c.get('image') or ''
                goodslist.append({
                    'id':pack_id*10+j if pack_id else int(time.time()*1000)+j,
                    'sale_num':pack_id,'order_interval_num':pack_id,
                    'goodslist_imgurl':cimg,'shang_id':csid,'num':1,
                    'goodslist_money':cprice,'goodslist_price':cprice,'prize_type':1,
                    'goodslist_id':0,'real_goods_list_id':0,
                    'goodslist_title':ctitle,'short_title':ctitle,
                    'shang_title':ctier,'shang_image':LEVEL_BADGES.get(ctier,'')
                })

            seq+=1
            row_id=pack_id if pack_id else int(time.time()*1000)+seq
            try: sum_price=float(price or 0) if special else 0.0
            except: sum_price=0.0
            rows.append({
                'id':row_id,'user_id':999999,'shang_id':sid,
                'goodslist_id':0,'real_goods_list_id':0,'goodslist_imgurl':img,
                'sale_num':pack_id,'order_interval_num':pack_id,'order_id':pack_id,
                'addtime':addunix,'goodslist_price':price,'interval_num':1,
                'goodslist_title':title,'short_title':title,'price':price,
                'goodslist_money':price,'shang_title':tier,
                'shang_image':LEVEL_BADGES.get(tier,''),'straddtime':0,
                'nickname':prof['name'],'headimg':'','head_border':'',
                'sum_price':sum_price,'goods_imgurl':'','goodslist':goodslist
            })
            continue

        # SP/A = one row per matching card (V5.28 behavior).
        for c in cards:
            tier=str(c.get('tier') or '').strip().upper()
            if tier not in ('SP','A') or (wanted and tier != wanted):
                continue
            seq+=1
            sid=100 if tier=='SP' else 101
            title=c.get('title') or ''
            img=c.get('image') or ''
            price=str(c.get('price') or '0')
            row_id=pack_id*10+seq if pack_id else int(time.time()*1000)+seq
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
                'goodslist_id':0,'real_goods_list_id':0,'goodslist_imgurl':img,
                'sale_num':pack_id,'order_interval_num':pack_id,'order_id':pack_id,
                'addtime':addunix,'goodslist_price':price,'interval_num':1,
                'goodslist_title':title,'short_title':title,'price':price,
                'goodslist_money':price,'shang_title':tier,
                'shang_image':LEVEL_BADGES.get(tier,''),'straddtime':0,
                'nickname':prof['name'],'headimg':'','head_border':'',
                'sum_price':float(price or 0),'goods_imgurl':'','goodslist':[one_goods]
            })

    total=len(rows)
    start_i=(page-1)*limit
    rows=rows[start_i:start_i+limit]
    rr=effective_rates(gid,CARD_DETAILS.get(gid,{}).get('data',{}))
    cats=[{'shang_id':0,'shang_title':'ทั้งหมด'}]
    for lvl,sid in [('SP',100),('A',101)]:
        if lvl in rr:
            cats.append({
                'shang_id':sid,'sum_real_pro':f"{float(rr[lvl]):.8f}",'max_sort':0,
                'shanginfo':{'id':sid,'title':lvl,'shang_level':4 if lvl=='SP' else 3,
                             'image':LEVEL_BADGES.get(lvl,'')},
                'lilun':round(100/float(rr[lvl])) if float(rr[lvl]) else 0,
                'shang_title':lvl
            })
    return {'status':1,'msg':'Request successful','data':{
        'interval_num_average':1,'sh_no':0,'category':cats,'data':rows,
        'total':total,'current_page':page,
        'last_page':max(1,(total+limit-1)//limit)
    }}

def local_card_shang_count(p):
    gid = str(p.get('goods_id') or '0')

    # ============================================================
    # LOAD LOCAL STATS ONLY
    # ============================================================

    stats = load_stats()

    cabinet = (
        stats
        .get('goods', {})
        .get(
            gid,
            {
                'SP': {
                    'current': 0,
                    'runs': []
                },
                'A': {
                    'current': 0,
                    'runs': []
                },
                'history': []
            }
        )
    )

    # ============================================================
    # LOCAL RATE
    # ============================================================

    rr = effective_rates(
        gid,
        CARD_DETAILS
        .get(gid, {})
        .get('data', {})
    )

    now = int(time.time())

    data = {
        'type': 'card_shang_count',
        'goods_id': gid,
        'now_sp_num': now
    }

    # ============================================================
    # SP / A
    # ============================================================

    for lvl, sid, prefix in (
        ('SP', 100, 'SP'),
        ('A', 101, 'A')
    ):

        q = cabinet.get(
            lvl,
            {
                'current': 0,
                'runs': []
            }
        )

        # ========================================================
        # CURRENT
        #
        # ตัวนี้หน้า JOYPOP จะเอาไปสร้างแท่งแดงเอง
        # ห้ามใส่ current ลง arr
        # ========================================================

        try:
            cur = max(
                0,
                int(
                    q.get('current', 0)
                    or 0
                )
            )
        except:
            cur = 0

        # ========================================================
        # LOCAL COMPLETED RUNS
        # ========================================================

        raw_runs = q.get('runs', [])

        runs = []

        if isinstance(raw_runs, list):

            for r in raw_runs:

                # =================================================
                # FORMAT ใหม่
                # =================================================

                if isinstance(r, dict):

                    try:
                        count = max(
                            0,
                            int(
                                r.get('count', 0)
                                or 0
                            )
                        )
                    except:
                        count = 0

                    if count <= 0:
                        continue

                    runs.append({
                        'count': count,

                        'name': str(
                            r.get('name')
                            or 'Local User'
                        ),

                        'headimg': str(
                            r.get('headimg')
                            or ''
                        ),

                        'time': str(
                            r.get('time')
                            or ''
                        ),

                        'order_interval_num':
                            r.get('order_interval_num'),

                        'goods_id': gid
                    })

                    continue

                # =================================================
                # FORMAT เก่า
                # =================================================

                try:
                    count = int(r)

                    if count > 0:

                        runs.append({
                            'count': count,
                            'name': 'Local User',
                            'headimg': '',
                            'time': '',
                            'order_interval_num': None,
                            'goods_id': gid
                        })

                except:
                    pass

        # เก็บสูงสุด 100 completed runs
        runs = runs[-100:]

        # ========================================================
        # ARR
        #
        # สำคัญมาก:
        #
        # arr มีเฉพาะ LOCAL WINNERS
        #
        # ห้ามใส่ current
        # ห้ามอ่าน REPLAY
        # ห้ามอ่าน JOYPOP history
        # ========================================================

        arr = []

        # ========================================================
        # BLUE BARS = LOCAL COMPLETED RUNS
        #
        # ล่าสุดขึ้นก่อน
        # ========================================================

        visible_runs = list(
            reversed(
                runs[-20:]
            )
        )

        for index, run in enumerate(
            visible_runs,
            1
        ):

            count = int(
                run.get('count', 0)
                or 0
            )

            if count <= 0:
                continue

            name = str(
                run.get('name')
                or 'Local User'
            )

            headimg = str(
                run.get('headimg')
                or ''
            )

            order_no = (
                run.get('order_interval_num')
                or 0
            )

            # ====================================================
            # UNIQUE LOCAL ID
            # ====================================================

            row_id = (
                sid * 1000000
                +
                index
            )

            arr.append({

                'id':
                    row_id,

                'user_id':
                    999999,

                'goodslist_id':
                    0,

                # ================================================
                # จำนวน PACK ที่เปิดจน SP/A ออก
                # ================================================

                'interval_num':
                    count,

                'order_interval_num':
                    order_no,

                'goodslist_price':
                    '0.000',

                'shang_id':
                    sid,

                'sale_num':
                    order_no,

                'addtime':
                    now - index,

                # ================================================
                # LOCAL USER
                # ================================================

                'userinfo': {

                    'id':
                        999999,

                    'nickname':
                        name,

                    'headimg':
                        headimg,

                    'headimg_frame_id':
                        '',

                    'headimg_brand_id':
                        ''
                },

                # ================================================
                # SP / A INFO
                # ================================================

                'shanginfo': {

                    'id':
                        sid,

                    'title':
                        lvl,

                    'image':
                        LEVEL_BADGES.get(
                            lvl,
                            ''
                        ),

                    'detail_image':
                        LEVEL_BADGES.get(
                            lvl,
                            ''
                        )
                },

                # frontend บางส่วนอ่านค่าจาก root
                'userinfo_id':
                    999999,

                'nickname':
                    name,

                'headimg':
                    headimg,

                'head_border':
                    '',

                # completed only
                'is_current':
                    0,

                'completed':
                    1,

                'local':
                    1
            })

        # ========================================================
        # CALCULATE LOCAL AVG
        # ========================================================

        counts = []

        for run in runs:

            try:
                count = int(
                    run.get('count', 0)
                    or 0
                )
            except:
                count = 0

            if count > 0:
                counts.append(count)

        if counts:

            avg = round(
                sum(counts)
                /
                len(counts)
            )

            mx = max(counts)

        else:

            avg = 0
            mx = 0

        # ========================================================
        # LOCAL RATE
        # ========================================================

        try:
            rate = float(
                rr.get(lvl, 0)
                or 0
            )
        except:
            rate = 0.0

        # ========================================================
        # RESPONSE
        # ========================================================

        # เฉพาะ Local winners
        data[prefix] = arr

        # Current
        # Frontend ใช้สร้าง RED BAR
        data[
            prefix
            +
            'not_yet_released'
        ] = cur

        # Rate
        data[
            prefix
            +
            '_probability'
        ] = rate

        data[
            prefix
            +
            '_gailv'
        ] = rate

        # AVG ของ Local completed runs
        data[
            prefix
            +
            '_all_probability'
        ] = avg

        # MAX Local run
        data[
            prefix
            +
            '_average'
        ] = mx

        # ========================================================
        # EXTRA LOCAL DEBUG DATA
        # ========================================================

        data[
            prefix
            +
            '_current'
        ] = cur

        data[
            prefix
            +
            '_runs'
        ] = runs

        data[
            prefix
            +
            '_last_run'
        ] = (
            counts[-1]
            if counts
            else 0
        )

        data[
            prefix
            +
            '_hits'
        ] = len(counts)

    # ============================================================
    # LOCAL ONLY
    # ============================================================

    data['local_only'] = 1

    return {
        'status': 1,
        'msg': 'Request successful',
        'data': data
    }

def local_infinite_detail(p):

    # ============================================================
    # REQUEST PARAMS
    # ============================================================

    gid = str(
        p.get('goods_id')
        or p.get('id')
        or ''
    ).strip()

    request_play_type = str(
        p.get('play_type')
        or '0'
    ).strip()


    # ============================================================
    # หา Combo cabinet จาก combo_details.json
    # ============================================================

    combo_response = COMBO_DETAILS.get(
        gid
    )

    if not isinstance(
        combo_response,
        dict
    ):

        print(
            '[LOCAL COMBO DETAIL MISS]',
            'gid=', gid,
            'play_type=', request_play_type
        )

        return {
            'status': 0,
            'msg': 'No local Combo detail',
            'data': None
        }


    # ============================================================
    # combo_details.json เก็บ response เต็มจาก HAR
    #
    # {
    #     "status": 1,
    #     "msg": "...",
    #     "data": {
    #         "goods": {...},
    #         "goodslist": [...]
    #     }
    # }
    # ============================================================

    raw_data = combo_response.get(
        'data'
    )

    if not isinstance(
        raw_data,
        dict
    ):

        print(
            '[LOCAL COMBO DETAIL BAD DATA]',
            'gid=', gid
        )

        return {
            'status': 0,
            'msg': 'Invalid local Combo detail',
            'data': None
        }


    # copy ก่อน
    # ป้องกันการแก้ COMBO_DETAILS ต้นฉบับใน memory

    data = dict(
        raw_data
    )


    # ============================================================
    # GOODS
    # ============================================================

    raw_goods = data.get(
        'goods'
    )

    if isinstance(
        raw_goods,
        dict
    ):
        goods = dict(
            raw_goods
        )

    else:
        goods = {}


    # ถ้าไม่มี id ค่อยเติม

    if not goods.get('id'):

        if gid.isdigit():
            goods['id'] = int(gid)

        else:
            goods['id'] = gid


    # Combo cabinet ของ HAR ใช้ play_type = 7

    goods['play_type'] = 7


    # ใส่กลับ

    data['goods'] = goods


    # ============================================================
    # GOODSLIST
    #
    # HAR ของเรามี:
    #
    # 99  Combo
    # 100 SP
    # 101 A
    # 102 B
    # 103 C
    # ============================================================

    goodslist = data.get(
        'goodslist'
    )

    if not isinstance(
        goodslist,
        list
    ):
        goodslist = []

    data['goodslist'] = goodslist


    # ============================================================
    # COMBO TARGET
    #
    # HAR:
    #
    # goods.set_count = "16.0"
    # ============================================================

    try:

        combo_target = int(
            float(
                goods.get(
                    'set_count',
                    16
                )
            )
        )

    except Exception:

        combo_target = 16


    if combo_target <= 0:
        combo_target = 16


    # ============================================================
    # CURRENT COMBO
    #
    # ตอนนี้ให้ 0 ก่อน
    #
    # ขั้นถัดไปเราจะเปลี่ยนตรงนี้ให้ไปอ่าน state
    # ที่ order() บันทึกไว้
    # ============================================================

    combo_count = get_combo_count(
        gid
    )

    if combo_count > combo_target:
        combo_count = combo_target


    # ============================================================
    # CONTINUITY
    #
    # GuaranteedRewardView ต้องใช้:
    #
    # continuity.double_count
    # continuity.double_set_count
    # ============================================================

    raw_continuity = data.get(
        'continuity'
    )

    if isinstance(
        raw_continuity,
        dict
    ):

        continuity = dict(
            raw_continuity
        )

    else:

        continuity = {}


    continuity[
        'double_count'
    ] = combo_count

    continuity[
        'double_set_count'
    ] = combo_target


    data[
        'continuity'
    ] = continuity


    # ============================================================
    # DEBUG TIERS
    # ============================================================

    tiers = []

    for row in goodslist:

        if not isinstance(
            row,
            dict
        ):
            continue

        tiers.append(
            (
                row.get(
                    'shang_id'
                ),
                row.get(
                    'shang_title'
                ),
                row.get(
                    'real_pro'
                )
            )
        )


    print(
        '[LOCAL COMBO DETAIL]',
        'gid=', gid,
        'request_play_type=', request_play_type,
        'play_type=', goods.get(
            'play_type'
        ),
        'title=', goods.get(
            'title'
        ),
        'price=', goods.get(
            'price'
        ),
        'combo=',
        combo_count,
        '/',
        combo_target,
        'tiers=',
        tiers
    )


    # ============================================================
    # RESPONSE
    # ============================================================

    return {
        'status': 1,
        'msg': (
            combo_response.get(
                'msg'
            )
            or
            'Request successful'
        ),
        'data': data
    }

def local_infinite_shang_count(p):
    gid = str(p.get('goods_id') or '0')

    try:
        shang_id = int(p.get('shang_id') or 100)
    except:
        shang_id = 100

    stats = load_stats()

    cabinet = (
        stats
        .get('goods', {})
        .get(
            gid,
            {
                'SP': {
                    'current': 0,
                    'runs': []
                },
                'A': {
                    'current': 0,
                    'runs': []
                },
                'history': []
            }
        )
    )

    # ============================================================
    # LOCAL RATE
    # ============================================================

    try:
        rates = effective_infinite_rates(gid)
    except:
        rates = {}

    data = {
        'type': 'shang_count',

        'SP': [],
        'A': [],

        'SPnot_yet_released': 0,
        'Anot_yet_released': 0,

        'SP_all_probability': 0,
        'A_all_probability': 0,

        'SP_probability': 0,
        'A_probability': 0,

        'local_only': 1
    }

    # ============================================================
    # SP / A
    # ============================================================

    for lvl, sid, color in (
        ('SP', 100, '#FF0015'),
        ('A', 101, '#FF7A00')
    ):

        q = cabinet.get(
            lvl,
            {
                'current': 0,
                'runs': []
            }
        )

        # ========================================================
        # CURRENT
        # ========================================================

        try:
            current = max(
                0,
                int(
                    q.get(
                        'current',
                        0
                    )
                    or 0
                )
            )
        except:
            current = 0

        data[
            lvl + 'not_yet_released'
        ] = current

        # ========================================================
        # RATE
        # ========================================================

        try:
            probability = float(
                rates.get(
                    lvl,
                    0
                )
                or 0
            )
        except:
            probability = 0

        data[
            lvl + '_all_probability'
        ] = probability

        data[
            lvl + '_probability'
        ] = probability

        # ========================================================
        # COMPLETED RUNS
        # ========================================================

        raw_runs = q.get(
            'runs',
            []
        )

        if not isinstance(
            raw_runs,
            list
        ):
            raw_runs = []

        rows = []

        # ล่าสุดขึ้นก่อน
        for index, run in enumerate(
            reversed(raw_runs[-20:]),
            1
        ):

            # ----------------------------------------------------
            # NEW FORMAT
            # ----------------------------------------------------

            if isinstance(
                run,
                dict
            ):

                try:
                    count = int(
                        run.get(
                            'count',
                            0
                        )
                        or 0
                    )
                except:
                    count = 0

                nickname = str(
                    run.get('name')
                    or
                    'Local User'
                )

                headimg = str(
                    run.get('headimg')
                    or
                    ''
                )

                try:
                    sale_num = int(
                        run.get(
                            'order_interval_num',
                            0
                        )
                        or 0
                    )
                except:
                    sale_num = 0

            # ----------------------------------------------------
            # OLD FORMAT
            # ----------------------------------------------------

            else:

                try:
                    count = int(
                        run
                    )
                except:
                    count = 0

                nickname = (
                    'Local User'
                )

                headimg = ''

                sale_num = 0

            if count <= 0:
                continue

            # ====================================================
            # EXACT INFINITE SHANG_COUNT STYLE
            # ====================================================

            rows.append({

                'id':
                    900000000
                    +
                    sid * 1000
                    +
                    index,

                'user_id':
                    999999,

                'goodslist_id':
                    0,

                'goods_id':
                    int(gid)
                    if gid.isdigit()
                    else gid,

                # สำคัญที่สุด
                # จำนวน draw จนออก SP/A
                'interval_num':
                    count,

                'goodslist_price':
                    '0.00',

                'shang_id':
                    sid,

                'sale_num':
                    sale_num,

                # ของจริง Infinite เป็น null
                'userinfo':
                    None,

                'shanginfo':
                    None,

                'addtime':
                    15,

                'goodslist_money':
                    None,

                'head_imgurling':
                    '',

                'vip':
                    0,

                'vip_image':
                    '',

                # ชื่อ Local
                'nickname':
                    nickname,

                # รูป Local
                'headimg':
                    headimg,

                'head_border':
                    '',

                'shang_title':
                    lvl,

                'shang_color':
                    color,

                'detail_image':
                    '',

                'local':
                    1
            })

        data[lvl] = rows

    # ============================================================
    # DEBUG
    # ============================================================

    print(
        '[LOCAL INFINITE STATS]',
        'gid=', gid,
        'SP current=',
        data['SPnot_yet_released'],
        'SP runs=',
        len(data['SP']),
        'A current=',
        data['Anot_yet_released'],
        'A runs=',
        len(data['A'])
    )

    return {
        'status': 1,
        'msg': 'Request successful',
        'data': data
    }

def local_infinite_shang_logs(p):
    gid = str(
        p.get('goods_id')
        or '0'
    )

    try:
        shang_id = int(
            p.get('shang_id')
            or 0
        )
    except:
        shang_id = 0

    try:
        page = max(
            1,
            int(p.get('page') or 1)
        )

        limit = max(
            1,
            int(p.get('limit') or 10)
        )

    except:
        page = 1
        limit = 10

    # ============================================================
    # FILTER
    # ============================================================

    wanted = {
        100: 'SP',
        101: 'A',
        102: 'B',
        103: 'C',
        104: 'D'
    }.get(shang_id)

    # ============================================================
    # STATS
    # ============================================================

    stats = load_stats()

    cabinet = (
        stats
        .get('goods', {})
        .get(gid, {})
    )

    history = cabinet.get(
        'history',
        []
    )

    if not isinstance(history, list):
        history = []

    # ใหม่สุดก่อน
    history = list(
        reversed(history)
    )

    rows = []
    seq = 0

    # ============================================================
    # HISTORY
    # ============================================================

    for h in history:

        if not isinstance(h, dict):
            continue

        cards = h.get(
            'cards',
            []
        )

        if not isinstance(cards, list):
            continue

        try:
            draw_no = int(
                h.get('draw_no')
                or h.get('order_interval_num')
                or 0
            )
        except:
            draw_no = 0

        player_name = str(
            h.get('player_name')
            or 'Local User'
        )

        player_headimg = str(
            h.get('player_headimg')
            or ''
        )

        ts = str(
            h.get('time')
            or ''
        )

        try:
            addunix = int(
                time.mktime(
                    time.strptime(
                        ts,
                        '%Y-%m-%d %H:%M:%S'
                    )
                )
            )
        except:
            addunix = int(
                time.time()
            )

        # ========================================================
        # EVERY CARD / RESULT
        # ========================================================

        for card in cards:

            if not isinstance(card, dict):
                continue

            tier = str(
                card.get('tier')
                or ''
            ).strip().upper()

            if not tier:
                continue

            # ALL = ไม่กรองอะไร
            #
            # SP = เฉพาะ SP
            # A  = เฉพาะ A
            # B  = เฉพาะ B
            # ...
            if wanted and tier != wanted:
                continue

            seq += 1

            sid = {
                'SP': 100,
                'A': 101,
                'B': 102,
                'C': 103,
                'D': 104
            }.get(
                tier,
                0
            )

            color = {
                'SP': '#FF0015',
                'A': '#FF7A00'
            }.get(
                tier,
                ''
            )

            title = str(
                card.get('title')
                or ''
            )

            img = str(
                card.get('image')
                or ''
            )

            price = str(
                card.get('price')
                or '0'
            )

            try:
                goodslist_id = int(
                    card.get('goodslist_id')
                    or 0
                )
            except:
                goodslist_id = 0

            if draw_no > 0:
                row_id = (
                    draw_no * 100
                    +
                    seq
                )
            else:
                row_id = (
                    int(time.time() * 1000)
                    +
                    seq
                )

            # ====================================================
            # GOODS
            # ====================================================

            one_goods = {
                'id':
                    row_id,

                'sale_num':
                    draw_no,

                'order_interval_num':
                    draw_no,

                'goodslist_imgurl':
                    img,

                'shang_id':
                    sid,

                'num':
                    1,

                'goodslist_money':
                    price,

                'goodslist_price':
                    price,

                'prize_type':
                    1,

                'goodslist_id':
                    goodslist_id,

                'real_goods_list_id':
                    goodslist_id,

                'goodslist_title':
                    title,

                'short_title':
                    title,

                'shang_title':
                    tier,

                'shang_color':
                    color,

                'shang_image':
                    LEVEL_BADGES.get(
                        tier,
                        ''
                    )
            }

            # ====================================================
            # MAIN ROW
            # ====================================================

            try:
                sum_price = float(
                    price
                    or 0
                )
            except:
                sum_price = 0.0

            rows.append({
                'id':
                    row_id,

                'user_id':
                    999999,

                'goods_id':
                    (
                        int(gid)
                        if gid.isdigit()
                        else gid
                    ),

                'shang_id':
                    sid,

                'goodslist_id':
                    goodslist_id,

                'real_goods_list_id':
                    goodslist_id,

                'goodslist_imgurl':
                    img,

                'sale_num':
                    draw_no,

                'order_interval_num':
                    draw_no,

                'order_id':
                    draw_no,

                'draw_no':
                    draw_no,

                'addtime':
                    addunix,

                'goodslist_price':
                    price,

                'goodslist_money':
                    price,

                'goodslist_title':
                    title,

                'short_title':
                    title,

                'price':
                    price,

                'sum_price':
                    sum_price,

                'interval_num':
                    1,

                'shang_title':
                    tier,

                'shang_color':
                    color,

                'shang_image':
                    LEVEL_BADGES.get(
                        tier,
                        ''
                    ),

                'nickname':
                    player_name,

                'headimg':
                    player_headimg,

                'head_border':
                    '',

                'userinfo':
                    None,

                'shanginfo':
                    None,

                'goodslist': [
                    one_goods
                ],

                'straddtime':
                    0,

                'local':
                    1
            })

    # ============================================================
    # PAGINATION
    # ============================================================

    total = len(rows)

    start_i = (
        (page - 1)
        *
        limit
    )

    page_rows = rows[
        start_i:
        start_i + limit
    ]

    # ============================================================
    # CATEGORY
    # ============================================================

    categories = [
        {
            'shang_id': 0,
            'shang_title': 'All'
        },
        {
            'shang_id': 100,
            'shang_title': 'SP',
            'sum_real_pro': '0',
            'max_sort': 0,
            'lilun': 0,
            'shanginfo': {
                'id': 100,
                'title': 'SP',
                'shang_level': 4,
                'image':
                    LEVEL_BADGES.get('SP', '')
            }
        }
    ]

    # ============================================================
    # DEBUG
    # ============================================================

    print(
        '[LOCAL INFINITE HISTORY]',
        'gid=', gid,
        'filter=', wanted or 'ALL',
        'history=', len(history),
        'rows=', total
    )

    return {
        'status': 1,

        'msg':
            'Request successful',

        'data': {

            'interval_num_average':
                0,

            'sh_no':
                0,

            'category':
                categories,

            'data':
                page_rows,

            'total':
                total,

            'current_page':
                page,

            'last_page':
                max(
                    1,
                    (
                        total
                        +
                        limit
                        -
                        1
                    )
                    //
                    limit
                ),

            'local_only':
                1
        }
    }


def local_infinite_shang_log(p):
    result = local_infinite_shang_logs(
        p
    )

    data = result.get(
        'data',
        {}
    )

    rows = data.get(
        'data',
        []
    )

    if not isinstance(
        rows,
        list
    ):
        rows = []

    return {
        'status':
            1,

        'msg':
            'Request successful',

        'data': {

            'data':
                rows,

            'total':
                data.get(
                    'total',
                    len(rows)
                ),

            'current_page':
                data.get(
                    'current_page',
                    1
                ),

            'last_page':
                data.get(
                    'last_page',
                    1
                ),

            'local_only':
                1
        }
    }

def load_profile():
    try:
        x=json.load(open(LOCAL_PROFILE_FILE,encoding='utf-8'))
        return {'name':str(x.get('name') or 'Local User'),'money':max(0.0,float(x.get('money',99999)))}
    except: return {'name':'Local User','money':99999.0}

def save_profile(x):
    tmp=LOCAL_PROFILE_FILE+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)
    os.replace(tmp,LOCAL_PROFILE_FILE)

LOCAL_ADMIN_HTML=r'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>JOYPOP Local Credit Admin</title>

<style>
*{box-sizing:border-box}
body{
    margin:0;
    padding:30px 18px;
    font-family:Arial,sans-serif;
    background:#0d0d0f;
    color:#eee
}
.wrap{
    max-width:620px;
    margin:auto
}
h1{
    text-align:center;
    margin-bottom:25px
}
.card{
    background:#18181c;
    border:1px solid #303036;
    border-radius:18px;
    padding:24px;
    margin-bottom:18px
}
.balance{
    text-align:center;
    font-size:16px;
    color:#aaa
}
.balance strong{
    display:block;
    color:#fff;
    font-size:42px;
    margin-top:10px
}
label{
    display:block;
    margin:14px 0 7px;
    color:#bbb
}
input{
    width:100%;
    padding:14px;
    font-size:18px;
    border-radius:10px;
    border:1px solid #444;
    background:#0d0d0f;
    color:#fff;
    outline:none
}
.buttons{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-top:15px
}
button{
    border:0;
    border-radius:10px;
    padding:14px;
    font-size:17px;
    font-weight:bold;
    cursor:pointer
}
.add{background:#2cbd67;color:#fff}
.remove{background:#e84d4d;color:#fff}
.set{
    width:100%;
    margin-top:10px;
    background:#4776e6;
    color:#fff
}
.save{
    width:100%;
    margin-top:15px;
    background:#333;
    color:#fff
}
.msg{
    min-height:24px;
    text-align:center;
    margin-top:14px
}
.ok{color:#55d98b}
.bad{color:#ff6969}
.note{
    color:#777;
    font-size:13px;
    text-align:center
}
</style>
</head>

<body>
<div class="wrap">

<h1>JOYPOP Local Credit Admin</h1>

<div class="card">
    <div class="balance">
        เครดิตปัจจุบัน
        <strong>฿<span id="bal">0.00</span></strong>
    </div>
</div>

<div class="card">

    <label>จำนวนเครดิต</label>
    <input
        id="amount"
        type="number"
        min="0"
        step="0.01"
        value="1000"
    >

    <div class="buttons">
        <button class="add" onclick="changeCredit('add')">
            + เพิ่มเครดิต
        </button>

        <button class="remove" onclick="changeCredit('remove')">
            − ลบเครดิต
        </button>
    </div>

    <button class="set" onclick="changeCredit('set')">
        ตั้งยอดเครดิตเป็นจำนวนนี้
    </button>

    <div id="msg" class="msg"></div>

</div>

<div class="card">

    <label>ชื่อผู้เล่น Local</label>
    <input id="nm" type="text">

    <button class="save" onclick="saveName()">
        บันทึกชื่อ
    </button>

</div>

<p class="note">
ใช้กับ JOYPOP Local Simulator เท่านั้น
</p>

</div>

<script>
async function loadProfile(){
    const j=await(
        await fetch('/api/local/profile')
    ).json();

    if(!j.status)return;

    bal.textContent=
        Number(j.data.money||0).toLocaleString(
            'en-US',
            {
                minimumFractionDigits:2,
                maximumFractionDigits:2
            }
        );

    nm.value=j.data.name||'Local User';
}

async function changeCredit(action){

    const amount=Number(
        document.getElementById('amount').value
    );

    if(!Number.isFinite(amount)||amount<0){
        showMsg('กรุณาใส่จำนวนที่ถูกต้อง',false);
        return;
    }

    try{
        const r=await fetch(
            '/api/local/credit',
            {
                method:'POST',
                headers:{
                    'Content-Type':'application/json'
                },
                body:JSON.stringify({
                    action:action,
                    amount:amount
                })
            }
        );

        const j=await r.json();

        if(!j.status){
            showMsg(j.msg||'เกิดข้อผิดพลาด',false);
            return;
        }

        await loadProfile();

        if(action==='add'){
            showMsg(
                'เพิ่มเครดิต '+amount.toLocaleString()+
                ' สำเร็จ',
                true
            );
        }
        else if(action==='remove'){
            showMsg(
                'ลบเครดิต '+amount.toLocaleString()+
                ' สำเร็จ',
                true
            );
        }
        else{
            showMsg('ตั้งยอดเครดิตสำเร็จ',true);
        }

    }catch(e){
        showMsg(String(e),false);
    }
}

async function saveName(){

    const current=await(
        await fetch('/api/local/profile')
    ).json();

    const r=await fetch(
        '/api/local/profile',
        {
            method:'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body:JSON.stringify({
                name:nm.value,
                money:current.data.money
            })
        }
    );

    const j=await r.json();

    if(j.status){
        showMsg('บันทึกชื่อแล้ว',true);
        await loadProfile();
    }else{
        showMsg(j.msg||'บันทึกไม่สำเร็จ',false);
    }
}

function showMsg(text,ok){
    const e=document.getElementById('msg');
    e.textContent=text;
    e.className='msg '+(ok?'ok':'bad');
}

loadProfile();
</script>
</body>
</html>'''


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

# ============================================================
# V5.15 - INFINITE RATE SYSTEM
# ============================================================

def load_infinite_rates():

    try:

        with open(
            INFINITE_RATES_FILE,
            'r',
            encoding='utf-8'
        ) as f:

            data=json.load(f)

        if isinstance(data,dict):
            return data

    except:
        pass

    return {}


def save_infinite_rates(data):

    tmp=INFINITE_RATES_FILE+'.tmp'

    with open(
        tmp,
        'w',
        encoding='utf-8'
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        tmp,
        INFINITE_RATES_FILE
    )


def infinite_available_levels(gid):

    gid = str(gid)

    pool = POOLS.get(
        gid,
        {}
    )

    if not pool:
        return []

    result = []

    # ============================================================
    # FLAT POOL
    #
    # ตัวอย่าง:
    #
    # POOLS["98"] = [
    #     {
    #         "shang_title": "SP",
    #         ...
    #     },
    #     {
    #         "shang_title": "A",
    #         ...
    #     }
    # ]
    # ============================================================

    if isinstance(pool, list):

        found = set()

        for item in pool:

            if not isinstance(item, dict):
                continue

            level = str(
                item.get('shang_title')
                or item.get('tier')
                or item.get('level')
                or ''
            ).strip().upper()

            if level:
                found.add(level)

        # --------------------------------------------------------
        # รักษาลำดับ Tier
        # --------------------------------------------------------

        for level in (
            'COMBO',
            'SP',
            'A',
            'B',
            'C',
            'D'
        ):

            if level in found:

                result.append(
                    level
                )

        # --------------------------------------------------------
        # เผื่ออนาคตมี Tier อื่น
        # --------------------------------------------------------

        for level in found:

            if level not in result:

                result.append(
                    level
                )

        return result

    # ============================================================
    # DICT / TIER POOL
    #
    # ตัวอย่าง:
    #
    # POOLS["22"] = {
    #     "Combo": [...],
    #     "SP": [...],
    #     "A": [...],
    #     "B": [...],
    #     "C": [...]
    # }
    # ============================================================

    if isinstance(pool, dict):

        # --------------------------------------------------------
        # COMBO
        #
        # รองรับทั้ง:
        # Combo
        # COMBO
        # combo
        # --------------------------------------------------------

        combo_rows = (
            pool.get('Combo')
            or pool.get('COMBO')
            or pool.get('combo')
            or []
        )

        if combo_rows:

            result.append(
                'COMBO'
            )

        # --------------------------------------------------------
        # NORMAL LEVELS
        # --------------------------------------------------------

        for level in (
            'SP',
            'A',
            'B',
            'C',
            'D'
        ):

            rows = pool.get(
                level,
                []
            )

            if rows:

                result.append(
                    level
                )

        return result

    # ============================================================
    # UNKNOWN POOL FORMAT
    # ============================================================

    return []


def infinite_default_rates(gid):

    gid = str(gid)

    pool = POOLS.get(
        gid,
        {}
    )

    if not pool:
        return {}

    # ============================================================
    # AVAILABLE LEVELS
    # ============================================================

    levels = infinite_available_levels(
        gid
    )

    if not levels:
        return {}

    # ============================================================
    # COMBO ไม่ใช่ Tier สุ่มปกติ
    #
    # Combo ของตู้ play_type=7:
    #
    # C ติดต่อกันตาม set_count
    # -> ได้ Combo Reward
    #
    # เพราะฉะนั้นห้ามเอา COMBO มารวม normalize probability
    # ============================================================

    normal_levels = [
        level
        for level in levels
        if level != 'COMBO'
    ]

    if not normal_levels:
        return {}

    captured = {}

    captured_complete = True

    # ============================================================
    # FLAT POOL
    #
    # ตัวอย่างตู้ 98
    # ============================================================

    if isinstance(pool, list):

        # --------------------------------------------------------
        # รวม probability ตาม Tier
        # --------------------------------------------------------

        for level in normal_levels:

            total = 0.0

            found = False

            for item in pool:

                if not isinstance(item, dict):
                    continue

                item_level = str(
                    item.get('shang_title')
                    or item.get('tier')
                    or item.get('level')
                    or ''
                ).strip().upper()

                if item_level != level:
                    continue

                raw_probability = (
                    item.get('real_pro')
                    or item.get('probability')
                    or item.get('pro')
                    or 0
                )

                try:

                    probability = float(
                        raw_probability
                    )

                except:

                    probability = 0.0

                if probability > 0:

                    found = True

                    total += probability

            if found:

                captured[
                    level
                ] = total

            else:

                captured_complete = False

        # ========================================================
        # ถ้ามี captured probability ครบทุก Tier
        # ========================================================

        if (
            captured_complete
            and
            captured
            and
            sum(captured.values()) > 0
        ):

            total = sum(
                captured.values()
            )

            result = {}

            for level, value in captured.items():

                result[level] = round(
                    (
                        value
                        /
                        total
                    )
                    *
                    100.0,
                    8
                )

            print(
                '[INFINITE DEFAULT RATES]',
                'gid=',
                gid,
                'pool=FLAT',
                'source=CAPTURED',
                'rates=',
                result
            )

            return result

        # ========================================================
        # PARTIAL CAPTURE / FALLBACK
        # ========================================================

        raw = {}

        for level in normal_levels:

            # ถ้ามีค่าจริงของ Tier นี้
            if (
                level in captured
                and
                captured[level] > 0
            ):

                raw[level] = float(
                    captured[level]
                )

            else:

                try:

                    raw[level] = float(
                        LEVEL_WEIGHTS.get(
                            level,
                            1
                        )
                    )

                except:

                    raw[level] = 1.0

        total = sum(
            raw.values()
        )

        if total <= 0:

            raw = {
                level: 1.0
                for level in normal_levels
            }

            total = float(
                len(raw)
                or 1
            )

        result = {}

        for level, value in raw.items():

            result[level] = round(
                (
                    value
                    /
                    total
                )
                *
                100.0,
                8
            )

        print(
            '[INFINITE DEFAULT RATES]',
            'gid=',
            gid,
            'pool=FLAT',
            'source=FALLBACK',
            'rates=',
            result
        )

        return result

    # ============================================================
    # DICT / TIER POOL
    #
    # Combo / Demon / Infinite รุ่นเดิม
    # ============================================================

    if isinstance(pool, dict):

        # --------------------------------------------------------
        # อ่าน real_pro ของแต่ละ Tier
        # --------------------------------------------------------

        for level in normal_levels:

            total = 0.0

            found = False

            rows = pool.get(
                level,
                []
            )

            # เผื่อ key แปลก
            if rows is None:
                rows = []

            # ----------------------------------------------------
            # บาง pool อาจเป็น dict เดี่ยว
            # แปลงเป็น list
            # ----------------------------------------------------

            if isinstance(rows, dict):

                rows = [
                    rows
                ]

            if not isinstance(rows, list):

                rows = []

            for item in rows:

                if not isinstance(item, dict):
                    continue

                raw_probability = (
                    item.get('real_pro')
                    or item.get('probability')
                    or item.get('pro')
                    or 0
                )

                try:

                    probability = float(
                        raw_probability
                    )

                except:

                    probability = 0.0

                if probability > 0:

                    found = True

                    total += probability

            if found:

                captured[
                    level
                ] = total

            else:

                captured_complete = False

        # ========================================================
        # CAPTURED RATE ครบทุก Tier
        # ========================================================

        if (
            captured_complete
            and
            captured
            and
            sum(captured.values()) > 0
        ):

            total = sum(
                captured.values()
            )

            result = {}

            for level, value in captured.items():

                result[level] = round(
                    (
                        value
                        /
                        total
                    )
                    *
                    100.0,
                    8
                )

            print(
                '[INFINITE DEFAULT RATES]',
                'gid=',
                gid,
                'pool=DICT',
                'source=CAPTURED',
                'rates=',
                result
            )

            return result

        # ========================================================
        # FALLBACK
        #
        # ถ้า real_pro ไม่ครบ
        # ใช้ค่าที่ capture ได้ก่อน
        # Tier ที่ไม่มีค่อยใช้ LEVEL_WEIGHTS
        # ========================================================

        raw = {}

        for level in normal_levels:

            if (
                level in captured
                and
                captured[level] > 0
            ):

                raw[level] = float(
                    captured[level]
                )

            else:

                try:

                    raw[level] = float(
                        LEVEL_WEIGHTS.get(
                            level,
                            1
                        )
                    )

                except:

                    raw[level] = 1.0

        total = sum(
            raw.values()
        )

        if total <= 0:

            raw = {
                level: 1.0
                for level in normal_levels
            }

            total = float(
                len(raw)
                or 1
            )

        result = {}

        for level, value in raw.items():

            result[level] = round(
                (
                    value
                    /
                    total
                )
                *
                100.0,
                8
            )

        print(
            '[INFINITE DEFAULT RATES]',
            'gid=',
            gid,
            'pool=DICT',
            'source=FALLBACK',
            'rates=',
            result
        )

        return result

    # ============================================================
    # UNKNOWN FORMAT
    # ============================================================

    print(
        '[INFINITE DEFAULT RATES UNKNOWN POOL]',
        'gid=',
        gid,
        'type=',
        type(pool).__name__
    )

    return {}


def effective_infinite_rates(gid):

    """
    Rate ที่ใช้สุ่มจริง

    ถ้ามี infinite_rates.json
    จะใช้ค่าที่ Admin ตั้งไว้

    ถ้าไม่มี
    จะใช้ Default
    """

    gid=str(gid)

    custom=load_infinite_rates().get(
        gid
    )


    if (
        isinstance(
            custom,
            dict
        )
        and
        custom
    ):

        result={}


        for key,value in custom.items():

            try:

                result[
                    str(key).upper()
                ]=max(
                    0.0,
                    float(value)
                )

            except:

                pass


        if result:

            return result


    return infinite_default_rates(
        gid
    )


def infinite_cabinet_title(gid):

    gid=str(gid)

    pool=POOLS.get(
        gid,
        {}
    ) or {}


    # ถ้าใน Capture มีชื่อตู้
    # ให้เอามาใช้

    for level in (
        'SP',
        'A',
        'B',
        'C',
        'D'
    ):

        for item in (
            pool.get(
                level,
                []
            ) or []
        ):

            title=(
                item.get(
                    'cabinet_title'
                )
                or
                item.get(
                    'box_title'
                )
                or
                item.get(
                    'goods_title'
                )
            )


            if title:

                return str(
                    title
                )


    return (
        'Infinite Cabinet '
        +
        gid
    )

INFINITE_RATE_ADMIN_HTML=r'''
<!doctype html>

<html lang="th">

<head>

<meta charset="utf-8">

<meta
 name="viewport"
 content="width=device-width,initial-scale=1"
>

<title>
JOYPOP Infinite Rate Admin
</title>

<style>

body{
 font-family:Arial,sans-serif;
 background:#111;
 color:#eee;
 margin:0;
 padding:24px;
}

.wrap{
 max-width:850px;
 margin:auto;
}

.card{
 background:#1c1c1c;
 border:1px solid #333;
 border-radius:16px;
 padding:20px;
 margin:14px 0;
}

select,
input,
button{
 font-size:16px;
 padding:10px;
 border-radius:8px;
 border:1px solid #444;
}

select,
input{
 background:#111;
 color:#fff;
}

input{
 width:130px;
}

.row{
 display:grid;
 grid-template-columns:80px 160px 1fr;
 gap:12px;
 align-items:center;
 margin:10px 0;
}

.ok{
 color:#50d890;
}

.bad{
 color:#ff6262;
}

button{
 cursor:pointer;
 margin-right:8px;
}

.note{
 color:#aaa;
 font-size:13px;
}

a{
 color:#7db7ff;
}

</style>

</head>

<body>

<div class="wrap">

<h1>
JOYPOP Local — Infinite Rate
</h1>


<div class="card">

<label>
เลือกตู้
</label>

<select id="cab">
</select>

<div
 id="cabinetTitle"
 style="margin-top:15px;font-weight:bold"
>
</div>

</div>


<div
 class="card"
 id="rateBox"
>
</div>


<div class="card">

<b>
รวม:
<span id="total">
0
</span>%
</b>

<br><br>

<button onclick="saveRate()">
บันทึกเรท
</button>

<button onclick="resetRate()">
คืนค่าเริ่มต้น
</button>

<p class="note">
เรทนี้มีผลเฉพาะ Local Infinite Draw
</p>

<p class="note">
Card Draw ยังคงใช้ /rate-admin
</p>

<p>

<a href="/rate-admin">
เปิด Card Rate Admin
</a>

</p>

</div>

</div>


<script>

let DATA={};


async function loadData(){

 const response=
   await fetch(
     '/api/local/infinite_rates'
   );


 DATA=
   await response.json();


 cab.innerHTML='';


 const ids=
   Object.keys(
     DATA.cabinets || {}
   );


 ids.sort(
   (a,b)=>Number(a)-Number(b)
 );


 for(const id of ids){

   const option=
     document.createElement(
       'option'
     );


   option.value=id;


   option.textContent=
     id+
     ' — '+
     DATA.cabinets[id].title;


   cab.appendChild(
     option
   );

 }


 cab.onchange=
   renderRates;


 renderRates();
}


function renderRates(){

 const id=cab.value;


 const cabinet=
   DATA.cabinets[id];


 if(!cabinet){

   rateBox.innerHTML=
     'ไม่พบตู้';

   return;
 }


 cabinetTitle.textContent=
   cabinet.title;


 rateBox.innerHTML='';


 const levels=[
   'SP',
   'A',
   'B',
   'C',
   'D'
 ];


 for(const level of levels){


   if(
     !cabinet.available.includes(level)
     &&
     cabinet.rates[level]==null
   ){

     continue;
   }


   const row=
     document.createElement(
       'div'
     );


   row.className='row';


   row.innerHTML=

     '<b>'+
     level+
     '</b>'+

     '<input '+
     'type="number" '+
     'min="0" '+
     'step="0.0001" '+
     'data-level="'+
     level+
     '" '+
     'value="'+
     (
       cabinet.rates[level]
       ?? 0
     )+
     '">'+

     '<span>%</span>';


   rateBox.appendChild(
     row
   );

 }


 rateBox
 .querySelectorAll(
   'input'
 )
 .forEach(
   input=>{
     input.oninput=
       updateTotal;
   }
 );


 updateTotal();
}


function updateTotal(){

 const inputs=[
   ...rateBox.querySelectorAll(
     'input'
   )
 ];


 let value=0;


 for(const input of inputs){

   value+=
     Number(
       input.value
     ) || 0;

 }


 total.textContent=
   value.toFixed(4);


 if(
   Math.abs(
     value-100
   ) < 0.001
 ){

   total.className='ok';

 }else{

   total.className='bad';

 }
}


async function saveRate(){

 const id=cab.value;


 const rates={};


 rateBox
 .querySelectorAll(
   'input'
 )
 .forEach(
   input=>{

     rates[
       input.dataset.level
     ]=
       Number(
         input.value
       ) || 0;

   }
 );


 const sum=
   Object.values(
     rates
   )
   .reduce(
     (a,b)=>a+b,
     0
   );


 if(
   Math.abs(
     sum-100
   ) > 0.001
 ){

   alert(
     'ผลรวมต้องเท่ากับ 100%'
   );

   return;
 }


 const response=
   await fetch(

     '/api/local/infinite_rates',

     {
       method:'POST',

       headers:{
         'Content-Type':
         'application/json'
       },

       body:
         JSON.stringify({
           goods_id:id,
           rates:rates
         })
     }

   );


 const result=
   await response.json();


 if(!result.status){

   alert(
     result.msg
     ||
     'บันทึกไม่สำเร็จ'
   );

   return;
 }


 await loadData();


 cab.value=id;


 renderRates();


 alert(
   'บันทึกแล้ว'
 );
}


async function resetRate(){

 const id=cab.value;


 await fetch(

   '/api/local/infinite_rates/reset',

   {
     method:'POST',

     headers:{
       'Content-Type':
       'application/json'
     },

     body:
       JSON.stringify({
         goods_id:id
       })
   }

 );


 await loadData();


 cab.value=id;


 renderRates();
}


loadData();

</script>

</body>

</html>
'''

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

# ============================================================
# V5.15 - INFINITE PRESENTATION
# ============================================================

PUBLIC_BASE_URL = os.environ.get(
    'PUBLIC_BASE_URL',
    'http://localhost:8080'
).rstrip('/')


def rewrite_public_image_urls(obj):
    if isinstance(obj, dict):
        return {
            k: rewrite_public_image_urls(v)
            for k, v in obj.items()
        }

    if isinstance(obj, list):
        return [
            rewrite_public_image_urls(v)
            for v in obj
        ]

    if isinstance(obj, str):
        s = obj.strip()

        # Fix captured card cabinet image paths.
        # Cabinet 23 uses /uploads/images/card/23/...,
        # not /uploads/images/goods/23/...
        s = s.replace(
            '/local-img/uploads/images/goods/23/',
            '/local-img/uploads/images/card/23/'
        ).replace(
            '/uploads/images/goods/23/',
            '/uploads/images/card/23/'
        )

        prefixes = (
            'https://img.joypop.gg/',
            'http://img.joypop.gg/',
            'https://joypop.oss-accelerate.aliyuncs.com/',
            'http://joypop.oss-accelerate.aliyuncs.com/',
        )

        for prefix in prefixes:
            if s.startswith(prefix):
                path = urllib.parse.urlparse(s).path.lstrip('/')
                return PUBLIC_BASE_URL + '/local-img/' + path

        return s

    return obj


def infinite_local_url(value):
    """Normalize JOYPOP image URLs to an absolute URL on this local server.

    Absolute localhost is intentional: the captured frontend may resolve root-relative
    image paths against https://img.joypop.gg, which produced URLs such as
    /local-img/... .
    """
    if not value:
        return ''
    value=str(value).strip()
    if not value:
        return ''

    # Strip resize/query parameters before mapping to a local file.
    parsed=urllib.parse.urlparse(value)
    clean_path=parsed.path or value

    # IMPORTANT: handle an already rewritten /local-img/ path first, including
    # malformed captured URLs such as /local-img/uploads/...
    if '/local-img/' in clean_path:
        rel=clean_path.split('/local-img/',1)[1].lstrip('/')
        port=str(globals().get('PORT', os.environ.get('PORT','8080')))
        return PUBLIC_BASE_URL + '/local-img/' + rel

    for prefix in ('https://img.joypop.gg/','http://img.joypop.gg/'):
        if value.startswith(prefix):
            rel=urllib.parse.urlparse(value).path.lstrip('/')
            port=str(globals().get('PORT', os.environ.get('PORT','8080')))
            return PUBLIC_BASE_URL + '/local-img/' + rel

    local_prefixes=('uploads/','upload/','static/','newimage/','images/','webSite/','badge/','card/')
    rel=clean_path.lstrip('/')
    if rel.startswith(local_prefixes):
        port=str(globals().get('PORT', os.environ.get('PORT','8080')))
        return PUBLIC_BASE_URL + '/local-img/' + rel

    return value


def infinite_local_file_exists(url):
    if not url:
        return False
    url=str(url).strip()
    if '/local-img/' not in url:
        return url.startswith(('http://','https://'))
    try:
        relative=url.split('/local-img/',1)[1]
        relative=urllib.parse.unquote(urllib.parse.urlparse('/'+relative).path).lstrip('/')
        image_root=os.path.abspath(os.path.join(ROOT,'img.joypop.gg'))
        filename=os.path.abspath(os.path.join(image_root,relative))
        if not (filename == image_root or filename.startswith(image_root+os.sep)):
            return False
        return os.path.isfile(filename)
    except Exception:
        return False


def infinite_find_product_image(item):
    """
    หาเฉพาะรูปสินค้า Infinite

    ลำดับ:
    1. ใช้ local ถ้ามีไฟล์จริง
    2. ถ้า local ไม่มี ให้ใช้ URL img.joypop.gg ต้นฉบับ
    3. ไม่ใช้ content_image / imgurltwo / image
    """

    fields = (
        'goodslist_imgurl',
        'imgurl',
        'goods_imgurl',
        'goods_image',
        'prize_image',
        'prize_img',
        'product_image',
        'product_img',
        'cover',
        'cover_image',
        'thumb',
        'thumbnail',
    )

    candidates = []

    for key in fields:

        raw = item.get(key)

        if not raw:
            continue

        raw = str(raw).strip()

        if not raw:
            continue

        if raw not in candidates:
            candidates.append(raw)


    # ==================================================
    # 1. LOCAL FILE
    # ==================================================

    for raw in candidates:

        local_url = infinite_local_url(raw)

        if (
            local_url
            and
            '/local-img/' in local_url
            and
            infinite_local_file_exists(local_url)
        ):
            return local_url


    # ==================================================
    # 2. FALLBACK ไป JOYPOP URL จริง
    #
    # สำคัญ:
    # ต้องใช้ raw ต้นฉบับ
    # ห้ามใช้ค่าหลัง infinite_local_url()
    # ==================================================

    for raw in candidates:

        # URL เต็มอยู่แล้ว
        if raw.startswith(
            ('https://', 'http://')
        ):
            return raw


        # เช่น:
        # uploads/images/goods/66/goods1578.webp
        if raw.startswith('uploads/'):

            return (
                'https://img.joypop.gg/'
                + raw.lstrip('/')
            )


        # เช่น:
        # /uploads/images/goods/61/pro/goods6.webp
        if raw.startswith('/uploads/'):

            return (
                'https://img.joypop.gg'
                + raw
            )


    return ''

def infinite_find_background(gid, level, item):

    gid = str(gid)

    # ==================================================
    # 1. อ่าน Background จาก Infinite Detail โดยตรง
    #
    # REPLAY key:
    # /api/infinite/detail|goods_id=61&play_type=0
    #
    # Background จริง:
    # data.goods.imgurl_black
    # ==================================================

    possible_keys = (
        f'/api/infinite/detail|goods_id={gid}&play_type=0',
        f'/api/infinite/detail|play_type=0&goods_id={gid}',
    )

    detail = None

    for key in possible_keys:

        if key in REPLAY:
            detail = REPLAY[key]
            break


    # เผื่อ query order ใน replay ไม่เหมือนกัน
    if detail is None:

        prefix = '/api/infinite/detail|'

        for key, value in REPLAY.items():

            key_text = str(key)

            if not key_text.startswith(prefix):
                continue

            query = key_text.split('|', 1)[1]

            params = urllib.parse.parse_qs(query)

            replay_gid = str(
                (params.get('goods_id') or [''])[0]
            )

            if replay_gid == gid:
                detail = value
                break


    if isinstance(detail, dict):

        data = detail.get('data') or {}

        if isinstance(data, dict):

            goods = data.get('goods') or {}

            if isinstance(goods, dict):

                raw = goods.get('imgurl_black')

                if raw:

                    bg = infinite_local_url(raw)

                    print(
                        '[CABINET BG]',
                        gid,
                        '=>',
                        bg
                    )

                    return bg


    # ==================================================
    # 2. เผื่อ item มี imgurl_black ติดมาด้วย
    # ==================================================

    raw = item.get('imgurl_black')

    if raw:

        bg = infinite_local_url(raw)

        low = str(bg).lower()

        if not any(x in low for x in (
            '/static/phase-two/',
            'bottom-b',
            'bottom-c',
            '/images/draw/sp_bg',
            '/images/draw/a_bg',
            '/images/draw/guaranteed_bg',
        )):

            return bg


    # ==================================================
    # ไม่ใช้ color_t
    # ไม่ค้น /newimage/ แบบสุ่ม
    # ==================================================

    print(
        '[NO CABINET BG]',
        gid
    )

    return ''

# ============================================================
# LOCAL BAG + LOCAL SAFE
# ============================================================

def load_bag():
    try:
        with open(BAG_FILE, encoding='utf-8') as f:
            x = json.load(f)

        return x if isinstance(x, list) else []

    except:
        return []


def save_bag(x):
    tmp = BAG_FILE + '.tmp'

    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(
            x,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(tmp, BAG_FILE)


# ============================================================
# SAFE FILE
# ============================================================

SAFE_FILE = os.path.join(
    ROOT,
    'local_safe.json'
)


def load_safe():
    try:
        with open(SAFE_FILE, encoding='utf-8') as f:
            x = json.load(f)

        return x if isinstance(x, list) else []

    except:
        return []


def save_safe(x):
    tmp = SAFE_FILE + '.tmp'

    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(
            x,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(tmp, SAFE_FILE)


# ============================================================
# CHOICE INFO
# ============================================================

def parse_choice_info(p):
    raw = p.get(
        'choice_info',
        '[]'
    )

    try:

        if isinstance(raw, str):
            x = json.loads(raw)
        else:
            x = raw

        if isinstance(x, list):
            return x

    except Exception as e:

        print(
            '[CHOICE INFO ERROR]',
            e
        )

    return []


# ============================================================
# PRIZE KEY
#
# ใช้สำหรับรวมของชนิดเดียวกันเป็น stack
# ============================================================

def prize_key(x):

    v = (
        x.get('goods_list_id')
        or x.get('real_goods_list_id')
        or x.get('goodslist_id')
    )

    if v not in (
        None,
        '',
        0,
        '0'
    ):
        return 'id:' + str(v)

    title = str(
        x.get('goodslist_title')
        or x.get('title')
        or x.get('short_title')
        or ''
    )

    image = str(
        x.get('goodslist_imgurl')
        or x.get('imgurl')
        or x.get('imgurltwo')
        or ''
    )

    return (
        'fallback:'
        + title
        + '|'
        + image
    )


# ============================================================
# หา TYPE ของ item
# ============================================================

def get_local_bag_type(x):

    bag_type = str(
        x.get(
            'local_bag_type'
        )
        or 'toy'
    ).lower()

    if bag_type not in (
        'toy',
        'card'
    ):
        bag_type = 'toy'

    return bag_type


# ============================================================
# MOVE STACK
#
# source = ต้นทาง
# target = ปลายทาง
#
# frontend ส่ง representative prize_code ของ stack
# พร้อม prize_num ที่ต้องการย้าย
# ============================================================

def move_stack_items(
    source,
    target,
    choices,
    wanted_type
):

    moved = []

    wanted_type = str(
        wanted_type
        or 'toy'
    ).lower()

    for choice in choices:

        if not isinstance(
            choice,
            dict
        ):
            continue

        code = str(
            choice.get(
                'prize_code'
            )
            or ''
        )

        try:
            qty = max(
                1,
                int(
                    choice.get(
                        'prize_num',
                        1
                    )
                    or 1
                )
            )
        except:
            qty = 1

        if not code:
            continue

        # ----------------------------------------------------
        # หา representative item จาก prize_code
        # ----------------------------------------------------

        representative = None

        for x in source:

            if (
                str(
                    x.get(
                        'prize_code'
                    )
                    or ''
                )
                ==
                code
                and
                get_local_bag_type(x)
                ==
                wanted_type
            ):

                representative = x
                break

        if representative is None:

            print(
                '[SAFE ITEM NOT FOUND]',
                wanted_type,
                code
            )

            continue

        key = prize_key(
            representative
        )

        # ----------------------------------------------------
        # goods_id ช่วยป้องกันของชื่อเดียวกันจากคนละตู้
        # ถูกย้ายรวมกัน
        # ----------------------------------------------------

        ref_gid = str(
            representative.get(
                'goods_id'
            )
            or ''
        )

        remaining = qty

        keep = []

        for x in source:

            current_gid = str(
                x.get(
                    'goods_id'
                )
                or ''
            )

            same_item = (
                prize_key(x) == key
                and
                get_local_bag_type(x)
                == wanted_type
                and
                current_gid == ref_gid
            )

            if (
                remaining > 0
                and
                same_item
            ):

                moved.append(
                    x
                )

                target.append(
                    x
                )

                remaining -= 1

            else:

                keep.append(
                    x
                )

        source[:] = keep

    return moved


# ============================================================
# BAG -> SAFE
# ============================================================

def bag_movein(
    p,
    bag_type='toy'
):

    choices = parse_choice_info(
        p
    )

    if not choices:

        return {
            'status': 0,
            'msg': 'No item selected',
            'data': None
        }

    with LOCK:

        bag = load_bag()
        safe = load_safe()

        moved = move_stack_items(
            bag,
            safe,
            choices,
            bag_type
        )

        # mark หลังจากย้ายสำเร็จ
        now = int(
            time.time()
        )

        for x in moved:

            x['in_safe'] = 1
            x['safe_at'] = now

        save_bag(
            bag
        )

        save_safe(
            safe
        )

    print(
        '[SAFE MOVE IN]',
        bag_type,
        'count=',
        len(moved)
    )

    if not moved:

        return {
            'status': 0,
            'msg': 'No matching local prize',
            'data': None
        }

    return {
        'status': 1,
        'msg': 'Moved in successfully',
        'data': {
            'move_count':
                len(moved)
        }
    }


# ============================================================
# SAFE -> BAG
# ============================================================

def safe_remove(
    p,
    bag_type='toy'
):

    choices = parse_choice_info(
        p
    )

    if not choices:

        return {
            'status': 0,
            'msg': 'No item selected',
            'data': None
        }

    with LOCK:

        safe = load_safe()
        bag = load_bag()

        moved = move_stack_items(
            safe,
            bag,
            choices,
            bag_type
        )

        # ลบสถานะ Safe
        for x in moved:

            x.pop(
                'in_safe',
                None
            )

            x.pop(
                'safe_at',
                None
            )

        save_safe(
            safe
        )

        save_bag(
            bag
        )

    print(
        '[SAFE REMOVE]',
        bag_type,
        'count=',
        len(moved)
    )

    if not moved:

        return {
            'status': 0,
            'msg': 'No matching safe prize',
            'data': None
        }

    return {
        'status': 1,
        'msg': 'Removed successfully',
        'data': {
            'move_count':
                len(moved)
        }
    }


# ============================================================
# REQUEST PARAMS
# ============================================================

def parse_params(handler, body):

    p = dict(
        urllib.parse.parse_qsl(
            urllib.parse.urlparse(
                handler.path
            ).query,
            keep_blank_values=True
        )
    )

    if body:

        text = body.decode(
            'utf-8',
            'ignore'
        )

        ct = (
            handler.headers.get(
                'Content-Type'
            )
            or ''
        ).lower()

        try:

            if (
                'json' in ct
                or
                text.lstrip().startswith(
                    (
                        '{',
                        '['
                    )
                )
            ):

                x = json.loads(
                    text
                )

                if isinstance(
                    x,
                    dict
                ):

                    for k, v in x.items():

                        p[str(k)] = (
                            str(v)
                            if not isinstance(
                                v,
                                (
                                    dict,
                                    list
                                )
                            )
                            else json.dumps(
                                v,
                                sort_keys=True,
                                separators=(
                                    ',',
                                    ':'
                                )
                            )
                        )

            else:

                p.update(
                    dict(
                        urllib.parse.parse_qsl(
                            text,
                            keep_blank_values=True
                        )
                    )
                )

        except Exception as e:

            print(
                '[PARSE PARAM ERROR]',
                e
            )

    return p

def rkey(path,p): return path+'|'+(urllib.parse.urlencode(sorted(p.items())) if p else '')
def out(h,obj,status=200):
    obj = rewrite_public_image_urls(obj)
    b=json.dumps(obj,ensure_ascii=False).encode(); h.send_response(status); h.send_header('Content-Type','application/json; charset=utf-8'); h.send_header('Access-Control-Allow-Origin','*'); h.send_header('Cache-Control','no-store'); h.send_header('Content-Length',str(len(b))); h.end_headers(); h.wfile.write(b)
TURBO_STATE_FILE = os.path.join(ROOT, 'turbo_state.json')

def load_turbo_state():
    try:
        with open(TURBO_STATE_FILE, 'r', encoding='utf-8') as f:
            x = json.load(f)
        return 1 if int(x.get('is_turbo', 1)) == 1 else 2
    except Exception:
        return 1

def save_turbo_state(value):
    value = 1 if int(value) == 1 else 2
    with open(TURBO_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(
            {'is_turbo': value},
            f,
            ensure_ascii=False,
            indent=2
        )
    return value

def local_update_userinfo(p):
    if 'is_turbo' in p:
        try:
            turbo = int(p.get('is_turbo') or 2)
        except Exception:
            turbo = 2

        turbo = save_turbo_state(turbo)

        print(
            '[FAST MODE]',
            'ON' if turbo == 1 else 'OFF'
        )

    return {
        'status': 1,
        'msg': 'Request successful',
        'data': {
            'is_turbo': load_turbo_state()
        }
    }

def user():
 x=load_profile(); m=f"{float(x['money']):.2f}"; n=x['name']
 turbo=load_turbo_state()
 return {"status":1,"msg":"Request successful","data":{"userinfo":{"id":999999,"pid":999999,"username":n,"nickname":n,"name":n,"avatar":"","money":m,"balance":m,"credit":m,"language":"en-US","vip":0,"level":0,"is_login":1,"login":1,"is_turbo":turbo}}}

# ============================================================
# V5.15 - INFINITE DRAW
# ============================================================


def apply_infinite_presentation(gid, item):

    gid = str(gid)

    level = str(
        item.get('shang_title') or ''
    ).strip().upper()


    # ==================================================
    # PRODUCT IMAGE
    # ==================================================

    image = infinite_find_product_image(item)

    if image:
        item['goodslist_imgurl'] = image
        item['imgurl'] = image


    # ==================================================
    # CABINET BACKGROUND
    # ==================================================

    background = infinite_find_background(
        gid,
        level,
        item
    )

    if background:

        item['back_image'] = background
        item['background_image'] = background
        item['background'] = background
        item['goods_back_image'] = background
        item['goods_background'] = background

        # Result popup ใช้ field นี้สำหรับ B/C
        item['imgurl_black'] = background


    # ==================================================
    # COLOR_T
    #
    # เก็บไว้เป็น Tier asset เท่านั้น
    # ห้ามเอา background ของตู้มาทับ
    # ==================================================

    if item.get('color_t'):

        item['color_t'] = infinite_local_url(
            item['color_t']
        )


    # ==================================================
    # BADGE
    # ==================================================

    badge = (
        item.get('shang_image')
        or LEVEL_BADGES.get(level, '')
    )

    if badge:

        item['shang_image'] = infinite_local_url(
            badge
        )


    return item

def choose(gid):

    gid=str(gid)


    pool=POOLS.get(
        gid,
        {}
    )


    if not pool:

        return None

    # ============================================================
    # FLAT POOL SUPPORT
    # ตู้ใหม่ เช่น goods_id 98
    # POOLS["98"] เป็น list ของรางวัล
    # ============================================================

    if isinstance(pool, list):

        items = [
            x
            for x in pool
            if isinstance(x, dict)
        ]

        if not items:

            print(
                '[CHOOSE FLAT POOL EMPTY]',
                'gid=',
                gid
            )

            return None


        # ==========================================
        # อ่าน probability ของแต่ละรางวัล
        # ==========================================

        weights = []

        for item in items:

            raw_weight = (
                item.get('real_pro')
                or item.get('probability')
                or item.get('pro')
                or 0
            )

            try:

                weight = float(
                    raw_weight
                )

            except:

                weight = 0.0


            if weight < 0:

                weight = 0.0


            weights.append(
                weight
            )


        total_weight = sum(
            weights
        )


        # ==========================================
        # มี probability
        # ==========================================

        if total_weight > 0:

            selected = random.choices(
                items,
                weights=weights,
                k=1
            )[0]


        # ==========================================
        # ไม่มี probability
        # ==========================================

        else:

            selected = random.choice(
                items
            )


        result = dict(
            selected
        )


        # ========================================================
        # NORMALIZE FLAT POOL ITEM
        # ทำให้ตู้ 98 ใช้รูป / ราคา / Tier / Background
        # รูปแบบเดียวกับตู้เดิม
        # ========================================================

        # ----------------------------
        # TITLE
        # ----------------------------

        title = (
            result.get('goodslist_title')
            or result.get('title')
            or result.get('short_title')
            or ''
        )

        result['goodslist_title'] = title

        if not result.get('title'):
            result['title'] = title

        if not result.get('short_title'):
            result['short_title'] = title


        # ----------------------------
        # PRICE
        # ----------------------------

        raw_price = (
            result.get('goodslist_price')
            or result.get('price')
            or result.get('goodslist_money')
            or result.get('show_price')
            or 0
        )

        try:
            prize_price = float(
                raw_price
            )
        except:
            prize_price = 0.0

        result['goodslist_price'] = (
            f'{prize_price:.2f}'
        )

        result['price'] = (
            f'{prize_price:.2f}'
        )

        result['goodslist_money'] = (
            f'{prize_price:.2f}'
        )

        result['goodslist_money'] = (
            f'{prize_price:.2f}'
        )


        # ----------------------------
        # IMAGE
        # ----------------------------

        raw_img = (
            result.get('goodslist_imgurl')
            or result.get('imgurl')
            or result.get('imgurltwo')
            or ''
        )

        if raw_img:

            local_img = infinite_local_url(
                raw_img
            )

            result['goodslist_imgurl'] = (
                local_img
            )

            result['imgurl'] = (
                local_img
            )


        # ----------------------------
        # TIER / LEVEL
        # ----------------------------

        level = str(
            result.get('shang_title')
            or result.get('level')
            or result.get('grade')
            or ''
        ).upper().strip()


        # ถ้าไม่มีชื่อระดับ ให้หา shang_id
        if not level:

            try:
                sid = int(
                    result.get('shang_id')
                    or 0
                )
            except:
                sid = 0

            level = {
                98: 'DEMON',
                100: 'SP',
                101: 'A',
                102: 'B',
                103: 'C',
                104: 'D'
            }.get(
                sid,
                ''
            )

        result['shang_title'] = level
        result['level'] = level

               # ========================================================
        # SHANG ID
        # ========================================================

        result['shang_id'] = {
            'DEMON': 98,
            '魔王赏': 98,
            'SP': 100,
            'A': 101,
            'B': 102,
            'C': 103,
            'D': 104
        }.get(
            level,
            result.get('shang_id')
            or 104
        )


        # ========================================================
        # BADGE
        # ========================================================

        badge = (
            LEVEL_BADGES.get(level)
            or result.get('shang_imgurl')
            or result.get('shang_iamge')
            or result.get('shang_image')
            or ''
        )

        if badge:
            result['shang_image'] = (
                infinite_local_url(
                    badge
                )
            )


        # ========================================================
        # RESULT CARD BACKGROUND
        # ใช้ระบบเดียวกับ Infinite ตู้อื่น
        # ========================================================

        try:
            bg = infinite_find_background(
                gid,
                level,
                result
            )

        except Exception as e:
            print(
                '[FLAT BG ERROR]',
                'gid=', gid,
                'level=', level,
                'error=', e
            )
            bg = ''


        if bg:
            bg = infinite_local_url(bg)
            result['back_image'] = bg
            result['color_t'] = bg
            result['background'] = bg
            result['background_img'] = bg
            result['bg'] = bg
            result['bg_img'] = bg
            result['imgurl_black'] = bg
            result['imgurl_black'] = bg


        # ========================================================
        # DEMON BACKGROUND FALLBACK
        # ========================================================

        if (
            level in ('DEMON', '魔王赏')
            and not result.get('back_image')
        ):

            demon_bg = infinite_local_url(
                'static/newlevel/mowang.png'
            )

            result['back_image'] = demon_bg
            result['color_t'] = demon_bg
            result['background'] = demon_bg
            result['background_img'] = demon_bg
            result['bg'] = demon_bg
            result['bg_img'] = demon_bg
            result['imgurl_black'] = demon_bg


        # ========================================================
        # FALLBACK B/C
        # ใช้เหมือนกันทุกตู้
        # ========================================================

        if (
            level in ('B', 'C')
            and not result.get('back_image')
        ):

            result['back_image'] = (
                BC_BACKGROUND
            )

            result['color_t'] = (
                BC_BACKGROUND
            )


        # ========================================================
        # MARK AS INFINITE
        # สำคัญตอนเข้า My Bag
        # ========================================================

        result['_local_mode'] = (
            'infinite'
        )


        print(
            '[FLAT RESULT]',
            'gid=',
            gid,
            'level=',
            level,
            'price=',
            result.get('goodslist_price'),
            'image=',
            result.get('goodslist_imgurl')
        )


        print(
            '[CHOOSE FLAT POOL]',
            'gid=',
            gid,
            'items=',
            len(items),
            'total_weight=',
            total_weight,
            'selected=',
            result.get('goodslist_title')
            or result.get('title')
            or result.get('short_title')
            or result.get('goods_list_id')
            or result.get('id')
        )


        return result


    # ==================================
    # Tier ที่มีของจริง
    # ==================================

    levels=[]


    for level in (
        'SP',
        'A',
        'B',
        'C',
        'D'
    ):

        if pool.get(level):

            levels.append(
                level
            )

    # ==================================
    # Tier ที่มีของจริง
    # ==================================

    levels=[]


    for level in (
        'SP',
        'A',
        'B',
        'C',
        'D'
    ):

        if pool.get(level):

            levels.append(
                level
            )


    if not levels:

        return None


    # ==================================
    # Rate
    # ==================================

    rates=effective_infinite_rates(
        gid
    )


    # FORCE_LEVEL
    # ยังใช้ได้เหมือนเดิม

    if (
        FORCE_LEVEL
        and
        FORCE_LEVEL in levels
    ):

        level=FORCE_LEVEL


    else:

        weights=[]


        for name in levels:

            try:

                weight=float(
                    rates.get(
                        name,
                        0
                    )
                )

            except:

                weight=0.0


            weights.append(
                max(
                    0.0,
                    weight
                )
            )


        # ถ้า Rate ผิดจนเป็น 0 หมด
        # fallback

        if sum(weights)<=0:

            weights=[

                float(
                    LEVEL_WEIGHTS.get(
                        name,
                        1
                    )
                )

                for name in levels

            ]


        level=random.choices(
            levels,
            weights=weights,
            k=1
        )[0]


    # ==================================
    # รายการสินค้าใน Tier
    # ==================================

    candidates=(
        pool.get(
            level
        )
        or []
    )


    if not candidates:

        return None


    # ==================================
    # Weight ของสินค้าแต่ละชิ้น
    # ==================================

    item_weights=[]


    for source in candidates:

        try:

            weight=float(
                source.get(
                    'real_pro'
                ) or 0
            )

        except:

            weight=0.0


        # ไม่มี real_pro
        # ให้โอกาสเท่ากัน

        if weight<=0:

            weight=1.0


        item_weights.append(
            weight
        )


    source=random.choices(

        candidates,

        weights=item_weights,

        k=1

    )[0]


    item=dict(
        source
    )


    item[
        'shang_title'
    ]=level


    # ==================================
    # TITLE
    # ==================================

    title=(

        item.get(
            'goodslist_title'
        )

        or

        item.get(
            'title'
        )

        or

        item.get(
            'short_title'
        )

        or

        'Local Prize'

    )


    # ==================================
    # PRICE
    # ==================================

    raw_price=(

        item.get(
            'goodslist_price'
        )

        or

        item.get(
            'price'
        )

        or

        item.get(
            'show_price'
        )

        or

        '0.00'

    )


    try:

        price=f'{float(raw_price):.2f}'

    except:

        price=str(
            raw_price
        )


    item[
        'goodslist_title'
    ]=title


    item[
        'short_title'
    ]=(
        item.get(
            'short_title'
        )
        or
        title
    )


    item[
        'title'
    ]=title


    item[
        'goodslist_price'
    ]=price


    item[
        'price'
    ]=price


    # ==================================
    # SHANG ID
    # ==================================

    item.setdefault(

        'shang_id',

        {
            'SP':100,
            'A':101,
            'B':102,
            'C':103,
            'D':104

        }.get(
            level,
            102
        )

    )


    # ==================================
    # V5.15
    #
    # สำคัญมาก:
    #
    # ตรงนี้ห้ามเรียก
    #
    # apply_level_background(item)
    #
    # เพราะของเดิมจะเอา B/C
    # ไปเป็น local-tier-bc-ice.png
    # ==================================

    apply_infinite_presentation(
        gid,
        item
    )

    print(
        "\n[INFINITE RESULT DEBUG]",
        "gid=", gid,
        "level=", item.get("shang_title"),
        "\ntitle=", item.get("title") or item.get("short_title"),
        "\ngoodslist_imgurl=", item.get("goodslist_imgurl"),
        "\nimgurl=", item.get("imgurl"),
        "\nimgurl_black=", item.get("imgurl_black"),
        "\nback_image=", item.get("back_image"),
        "\ncolor_t=", item.get("color_t"),
        "\n"
    )


    return item

def add_to_bag(items, gid, bag_type='toy'):
    """
    bag_type:
      toy  = Hot / Combo / Demon / Infinite
      card = Card
    """

    bag_type = str(bag_type or 'toy').strip().lower()

    if bag_type not in ('toy', 'card'):
        bag_type = 'toy'

    with LOCK:
        bag = load_bag()

        for x in items:
            now = int(time.time() * 1000)

            code = (
                'LOCAL-'
                + str(gid)
                + '-'
                + str(
                    x.get('goods_list_id')
                    or x.get('real_goods_list_id')
                    or x.get('goodslist_id')
                    or now
                )
                + '-'
                + str(now)
                + '-'
                + str(random.randint(1000, 9999))
            )

            b = dict(x)

            b.update({
                'prize_code': code,
                'prize_num': 1,
                'num': 1,
                'goods_id': gid,
                'status': 1,

                # สำคัญ
                'local_bag_type': bag_type,

                'created_at': int(time.time())
            })

            bag.insert(0, b)

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

            groups[k]=y
            order.append(k)

        y=groups[k]

        qty=max(
            1,
            int(
                x.get(
                    'prize_num',
                    1
                ) or 1
            )
        )

        y['prize_num']+=qty
        y['num']+=qty

        if x.get('prize_code'):
            y['_stack_codes'].append(
                str(
                    x['prize_code']
                )
            )


    rows=[
        groups[k]
        for k in order
    ]


    # ==========================================
    # V5.15
    # แยก Card / Infinite Presentation
    # ==========================================

    for item in rows:

        gid=str(
            item.get(
                'goods_id'
            ) or ''
        )

        mode=str(
            item.get(
                '_local_mode'
            ) or ''
        )


        # Infinite ใหม่
        if mode=='infinite':

            apply_infinite_presentation(
                gid,
                item
            )


        # Card
        elif gid in CARD_DETAILS:

            apply_level_background(
                item
            )


        # Infinite เก่า
        elif gid in POOLS:

            apply_infinite_presentation(
                gid,
                item
            )


        # fallback
        else:

            apply_level_background(
                item
            )


    # ==========================================
    # เรียงราคาสูง -> ต่ำ
    # ==========================================

    def get_price(x):

        try:

            return float(
                x.get(
                    'goodslist_price'
                )
                or
                x.get(
                    'price'
                )
                or
                x.get(
                    'show_price'
                )
                or
                0
            )

        except (
            TypeError,
            ValueError
        ):

            return 0.0


    rows.sort(
        key=get_price,
        reverse=True
    )


    for y in rows:

        y['stack_key']=prize_key(
            y
        )

        y['stack_codes']=list(
            y.pop(
                '_stack_codes',
                []
            )
        )


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

    typ = str(
        p.get(
            'type',
            '1'
        )
    )

    try:
        page = max(
            1,
            int(
                p.get(
                    'page',
                    1
                )
                or 1
            )
        )
    except:
        page = 1

    try:
        per = max(
            1,
            int(
                p.get(
                    'limit',
                    20
                )
                or 20
            )
        )
    except:
        per = 20

    # ========================================================
    # FRONTEND MAPPING
    #
    # type 1 = My Bag / Toys
    # type 2 = My Bag / Cards
    #
    # type 3 = Safe / Toys
    # type 5 = Safe / Cards
    # ========================================================

    with LOCK:

        if typ in (
            '3',
            '5'
        ):

            source = load_safe()

        else:

            source = load_bag()

    # --------------------------------------------------------
    # MY BAG / TOYS
    # --------------------------------------------------------

    if typ == '1':

        source = [
            x
            for x in source
            if get_local_bag_type(x)
            == 'toy'
        ]

    # --------------------------------------------------------
    # MY BAG / CARDS
    # --------------------------------------------------------

    elif typ == '2':

        source = [
            x
            for x in source
            if get_local_bag_type(x)
            == 'card'
        ]

    # --------------------------------------------------------
    # SAFE / TOYS
    # --------------------------------------------------------

    elif typ == '3':

        source = [
            x
            for x in source
            if get_local_bag_type(x)
            == 'toy'
        ]

    # --------------------------------------------------------
    # SAFE / CARDS
    # --------------------------------------------------------

    elif typ == '5':

        source = [
            x
            for x in source
            if get_local_bag_type(x)
            == 'card'
        ]

    else:

        source = []

    stacks = grouped_bag(
        source
    )

    start = (
        page - 1
    ) * per

    rows = stacks[
        start:
        start + per
    ]

    if stacks:

        last = (
            len(stacks)
            + per
            - 1
        ) // per

    else:

        last = 0

    total_items = sum(
        int(
            x.get(
                'prize_num',
                1
            )
            or 1
        )
        for x in stacks
    )

    print(
        '[BAG LIST]',
        'type=',
        typ,
        'source=',
        (
            'SAFE'
            if typ in ('3', '5')
            else 'BAG'
        ),
        'stacks=',
        len(stacks),
        'items=',
        total_items
    )

    return {
        'status': 1,
        'msg': 'Request successful',

        'data': {

            'data':
                rows,

            'last_page':
                last,

            'prize_num':
                len(rows),

            'total_prize_num':
                total_items
        }
    }

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


def choose_combo(gid):

    gid = str(gid)

    response = COMBO_DETAILS.get(gid)

    if not isinstance(response, dict):
        print('[COMBO CHOOSE ERROR]', 'gid=', gid, 'reason=no detail')
        return None

    data = response.get('data') or {}

    if not isinstance(data, dict):
        return None

    goods = data.get('goods') or {}

    if not isinstance(goods, dict):
        goods = {}

    goodslist = data.get('goodslist') or []

    if not isinstance(goodslist, list):
        return None

    # ============================================================
    # NORMAL TIERS
    # ============================================================

    candidates = []
    weights = []

    for tier in goodslist:

        if not isinstance(tier, dict):
            continue

        try:
            shang_id = int(tier.get('shang_id') or 0)
        except Exception:
            shang_id = 0

        level = str(
            tier.get('shang_title') or ''
        ).strip().upper()

        if shang_id == 99 or level == 'COMBO':
            continue

        try:
            rate = float(tier.get('real_pro') or 0)
        except Exception:
            rate = 0.0

        if rate <= 0:
            continue

        tier_items = tier.get('goods_list') or []

        if not isinstance(tier_items, list):
            continue

        tier_items = [
            x for x in tier_items
            if isinstance(x, dict)
        ]

        if not tier_items:
            continue

        candidates.append((tier, tier_items))
        weights.append(rate)

    if not candidates:
        print(
            '[COMBO CHOOSE ERROR]',
            'gid=', gid,
            'reason=no normal tiers'
        )
        return None

    # ============================================================
    # RANDOM TIER
    # ============================================================

    selected_tier, tier_items = random.choices(
        candidates,
        weights=weights,
        k=1
    )[0]

    source = random.choice(tier_items)
    result = dict(source)

    level = str(
        selected_tier.get('shang_title') or ''
    ).strip().upper()

    try:
        shang_id = int(
            selected_tier.get('shang_id') or 0
        )
    except Exception:
        shang_id = 0

    result['shang_id'] = shang_id
    result['shang_title'] = level
    result['tier'] = level

    # ============================================================
    # TITLE
    # ============================================================

    title = (
        result.get('goodslist_title')
        or result.get('title')
        or result.get('goods_name')
        or result.get('short_title')
        or ''
    )

    result['goodslist_title'] = title
    result['title'] = title
    result['short_title'] = title

    # ============================================================
    # PRODUCT IMAGE
    # ============================================================

    image = (
        result.get('goodslist_imgurl')
        or result.get('imgurl')
        or result.get('image')
        or ''
    )

    if image:
        try:
            image = infinite_local_url(image)
        except Exception:
            pass

    result['goodslist_imgurl'] = image
    result['imgurl'] = image
    result['image'] = image

    # ============================================================
    # PRICE
    # ============================================================

    price = (
        result.get('goodslist_price')
        or result.get('goodslist_money')
        or result.get('price')
        or 0
    )

    result['goodslist_price'] = price
    result['goodslist_money'] = price
    result['price'] = price

    # ============================================================
    # QUANTITY
    # ============================================================

    try:
        num = int(
            result.get('num')
            or result.get('prize_num')
            or 1
        )
    except Exception:
        num = 1

    if num <= 0:
        num = 1

    result['num'] = num
    result['prize_num'] = num

    # ============================================================
    # BADGE
    # ============================================================

    badge = str(
        selected_tier.get('shang_image')
        or selected_tier.get('shang_imgurl')
        or ''
    ).strip()

    if badge:
        try:
            badge = infinite_local_url(badge)
        except Exception:
            pass

        result['shang_image'] = badge
        result['shang_imgurl'] = badge
        result['shang_iamge'] = badge

    # ============================================================
    # CABINET BACKGROUND
    #
    # ใช้ imgurl_black ของตู้ ไม่ใช้ color_t ของ tier
    # ============================================================

    raw_cabinet_background = str(
        goods.get('imgurl_black')
        or goods.get('imgurl')
        or ''
    ).strip()

    cabinet_background = ''

    if raw_cabinet_background:
        try:
            cabinet_background = infinite_local_url(
                raw_cabinet_background
            )
        except Exception:
            cabinet_background = raw_cabinet_background

    # ถ้าตู้นั้นไม่มี background จริง ๆ
    # ค่อย fallback กลับไปใช้ tier background
    if not cabinet_background:

        raw_tier_background = str(
            selected_tier.get('color_t')
            or ''
        ).strip()

        if raw_tier_background:

            if (
                raw_tier_background.startswith('http://')
                or raw_tier_background.startswith('https://')
            ):
                try:
                    cabinet_background = infinite_local_url(
                        raw_tier_background
                    )
                except Exception:
                    cabinet_background = raw_tier_background

            else:
                cabinet_background = (
                    '/local-img/'
                    + raw_tier_background.lstrip('/')
                )

    # ============================================================
    # ส่ง background ของตู้ไปกับผลรางวัล
    # ============================================================

    if cabinet_background:

        result['color_t'] = cabinet_background
        result['back_image'] = cabinet_background
        result['background_image'] = cabinet_background
        result['background'] = cabinet_background
        result['background_img'] = cabinet_background
        result['goods_back_image'] = cabinet_background
        result['goods_background'] = cabinet_background
        result['bg'] = cabinet_background
        result['bg_img'] = cabinet_background

        # สำคัญ:
        # ResultPopup เดิมอ่าน field นี้
        result['imgurl_black'] = cabinet_background

    result['shang_color'] = (
        selected_tier.get('shang_color')
        or result.get('shang_color')
        or ''
    )

    result['_local_mode'] = 'infinite'

    print(
        '[COMBO CHOOSE]',
        'gid=', gid,
        'tier=', level,
        'shang_id=', shang_id,
        'rate=', selected_tier.get('real_pro'),
        'item=', title,
        'cabinet_background=', cabinet_background
    )

    return result


def choose_combo_reward(gid):

    gid = str(gid)

    response = COMBO_DETAILS.get(gid)

    if not isinstance(response, dict):
        print(
            '[COMBO REWARD ERROR]',
            'gid=', gid,
            'reason=no detail'
        )
        return None

    data = response.get('data') or {}

    if not isinstance(data, dict):
        return None

    goodslist = data.get('goodslist') or []

    if not isinstance(goodslist, list):
        goodslist = []

    # ============================================================
    # COMBO TIER = 99
    # ============================================================

    combo_tier = None

    for tier in goodslist:

        if not isinstance(tier, dict):
            continue

        try:
            sid = int(
                tier.get('shang_id') or 0
            )
        except Exception:
            sid = 0

        level = str(
            tier.get('shang_title') or ''
        ).strip().upper()

        if sid == 99 or level == 'COMBO':
            combo_tier = tier
            break

    if not combo_tier:

        print(
            '[COMBO REWARD ERROR]',
            'gid=', gid,
            'reason=no tier 99'
        )
        return None

    reward_list = (
        combo_tier.get('goods_list')
        or []
    )

    if not isinstance(reward_list, list):
        reward_list = []

    reward_list = [
        x for x in reward_list
        if isinstance(x, dict)
    ]

    if not reward_list:

        print(
            '[COMBO REWARD ERROR]',
            'gid=', gid,
            'reason=no goods_list'
        )
        return None

    source = random.choice(reward_list)

    result = dict(source)

    # ============================================================
    # COMBO NORMALIZE
    # ============================================================

    result['shang_id'] = 99
    result['shang_title'] = 'Combo'
    result['tier'] = 'COMBO'

    title = (
        result.get('goodslist_title')
        or result.get('title')
        or result.get('goods_name')
        or result.get('short_title')
        or ''
    )

    result['goodslist_title'] = title
    result['title'] = title
    result['short_title'] = title

    # ============================================================
    # PRODUCT IMAGE
    # ============================================================

    image = (
        result.get('goodslist_imgurl')
        or result.get('imgurl')
        or result.get('image')
        or ''
    )

    if image:

        try:
            image = infinite_local_url(image)
        except Exception:
            pass

    result['goodslist_imgurl'] = image
    result['imgurl'] = image
    result['image'] = image

    # ============================================================
    # PRICE
    # ============================================================

    price = (
        result.get('goodslist_price')
        or result.get('goodslist_money')
        or result.get('price')
        or 0
    )

    result['goodslist_price'] = price
    result['goodslist_money'] = price
    result['price'] = price

    # ============================================================
    # QUANTITY
    # ============================================================

    try:
        num = int(
            result.get('num')
            or result.get('prize_num')
            or 1
        )
    except Exception:
        num = 1

    if num <= 0:
        num = 1

    result['num'] = num
    result['prize_num'] = num

    # ============================================================
    # COMBO BADGE
    # ============================================================

    badge = str(
        combo_tier.get('shang_image')
        or combo_tier.get('shang_imgurl')
        or ''
    ).strip()

    if badge:

        try:
            badge = infinite_local_url(badge)
        except Exception:
            pass

        result['shang_image'] = badge
        result['shang_imgurl'] = badge
        result['shang_iamge'] = badge

    # ============================================================
    # COMBO BACKGROUND
    # ============================================================

    raw_background = str(
        combo_tier.get('color_t')
        or 'static/newlevel/lianjie2.webp'
    ).strip()

    if (
        raw_background.startswith('http://')
        or raw_background.startswith('https://')
    ):

        try:
            combo_background = infinite_local_url(
                raw_background
            )
        except Exception:
            combo_background = raw_background

    else:

        combo_background = (
            '/local-img/'
            + raw_background.lstrip('/')
        )

    result['color_t'] = combo_background
    result['back_image'] = combo_background
    result['background_image'] = combo_background
    result['background'] = combo_background
    result['background_img'] = combo_background
    result['goods_back_image'] = combo_background
    result['goods_background'] = combo_background
    result['bg'] = combo_background
    result['bg_img'] = combo_background
    result['imgurl_black'] = combo_background

    result['shang_color'] = (
        combo_tier.get('shang_color')
        or '#FFE21F'
    )

    # frontend Combo animation
    result['prize_change'] = 3
    result['is_combo'] = 1
    result['combo_reward'] = 1

    result['_local_mode'] = 'infinite'
    result['_combo_reward'] = True

    print(
        '[COMBO REWARD]',
        'gid=', gid,
        'title=', title,
        'price=', price,
        'shang_id=99',
        'background=', combo_background
    )

    return result



# ============================================================
# LOCAL DEMON SYSTEM
# ============================================================

DEMON_STATE_FILE = os.path.join(ROOT, 'demon_state.json')
POINT_WALLET_FILE = os.path.join(ROOT, 'point_wallet.json')

DEMON_SHANG_ID = 98
DEMON_LIFETIME_SECONDS = 24 * 60 * 60

# ทุก 10 บาท = 1 คะแนน
POINTS_PER_MONEY = 10.0

# ตอนมีผู้ครอง Demon = x2
DEMON_POINT_MULTIPLIER = 2.0


def _load_json_file(path, default):

    try:
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, type(default)):
                return data

    except Exception as e:
        print('[DEMON JSON LOAD ERROR]', path, e)

    return default.copy()


def _save_json_file(path, data):

    tmp = path + '.tmp'

    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(tmp, path)


def load_demon_state():
    return _load_json_file(
        DEMON_STATE_FILE,
        {}
    )


def save_demon_state(data):
    _save_json_file(
        DEMON_STATE_FILE,
        data
    )


def load_point_wallet():
    return _load_json_file(
        POINT_WALLET_FILE,
        {}
    )


def save_point_wallet(data):
    _save_json_file(
        POINT_WALLET_FILE,
        data
    )


def demon_local_user():

    profile = {}

    try:
        profile = load_profile() or {}
    except Exception:
        profile = {}

    name = (
        profile.get('nickname')
        or profile.get('username')
        or profile.get('name')
        or 'LocalDemo'
    )

    avatar = (
        profile.get('avatar')
        or profile.get('avatar_url')
        or ''
    )

    return {
        'user_id': 999999,
        'username': str(name),
        'avatar': str(avatar)
    }


def demon_is_hit(item):

    if not isinstance(item, dict):
        return False

    try:
        sid = int(
            item.get('shang_id')
            or 0
        )
    except Exception:
        sid = 0

    title = str(
        item.get('shang_title')
        or item.get('tier')
        or ''
    ).strip().upper()

    return (
        sid == DEMON_SHANG_ID
        or title == 'DEMON'
        or title == '魔王赏'
    )


def demon_get_cabinet_price(gid):

    gid = str(gid)

    # --------------------------------------------------------
    # Combo detail
    # --------------------------------------------------------

    try:
        r = COMBO_DETAILS.get(gid) or {}
        d = r.get('data') or {}
        g = d.get('goods') or {}

        price = float(
            g.get('price')
            or 0
        )

        if price > 0:
            return price

    except Exception:
        pass

    # --------------------------------------------------------
    # REPLAY infinite detail
    # --------------------------------------------------------

    possible = [
        f'/api/infinite/detail|goods_id={gid}&play_type=0',
        f'/api/infinite/detail|play_type=0&goods_id={gid}',
        f'/api/infinite/detail|goods_id={gid}&play_type=1',
        f'/api/infinite/detail|play_type=1&goods_id={gid}'
    ]

    for key in possible:

        try:
            r = REPLAY.get(key)

            if not isinstance(r, dict):
                continue

            d = r.get('data') or {}
            g = d.get('goods') or {}

            price = float(
                g.get('price')
                or 0
            )

            if price > 0:
                return price

        except Exception:
            continue

    # --------------------------------------------------------
    # POOLS fallback
    # --------------------------------------------------------

    try:
        pool = POOLS.get(gid) or {}

        if isinstance(pool, dict):

            price = float(
                pool.get('price')
                or 0
            )

            if price > 0:
                return price

    except Exception:
        pass

    return 0.0


def demon_wallet_add(user_id, points):

    try:
        points = float(points)
    except Exception:
        points = 0.0

    if points <= 0:
        return

    uid = str(user_id)

    wallet = load_point_wallet()

    row = wallet.get(uid)

    if not isinstance(row, dict):
        row = {
            'points': 0.0
        }

    try:
        old_points = float(
            row.get('points')
            or 0
        )
    except Exception:
        old_points = 0.0

    row['points'] = round(
        old_points + points,
        4
    )

    row['updated_at'] = int(
        time.time()
    )

    wallet[uid] = row

    save_point_wallet(wallet)

    print(
        '[DEMON WALLET +]',
        'user=', uid,
        'points=', round(points, 4),
        'wallet=', row['points']
    )


def demon_close_owner(gid, reason='closed'):

    gid = str(gid)

    states = load_demon_state()

    state = states.get(gid)

    if not isinstance(state, dict):
        return None

    try:
        pending = float(
            state.get('pending_points')
            or 0
        )
    except Exception:
        pending = 0.0

    owner_id = state.get(
        'owner_user_id'
    )

    if owner_id is not None and pending > 0:

        demon_wallet_add(
            owner_id,
            pending
        )

    closed = dict(state)

    closed['closed_at'] = int(
        time.time()
    )

    closed['close_reason'] = reason

    print(
        '[DEMON CLOSED]',
        'gid=', gid,
        'owner=', owner_id,
        'pending_to_wallet=',
        round(pending, 4),
        'reason=', reason
    )

    states.pop(
        gid,
        None
    )

    save_demon_state(states)

    return closed


def demon_expire_if_needed(gid):

    gid = str(gid)

    states = load_demon_state()

    state = states.get(gid)

    if not isinstance(state, dict):
        return None

    now = int(
        time.time()
    )

    try:
        expires_at = int(
            state.get('expires_at')
            or 0
        )
    except Exception:
        expires_at = 0

    if (
        expires_at > 0
        and now >= expires_at
    ):

        demon_close_owner(
            gid,
            reason='24h_expired'
        )

        return None

    return state


def demon_get_state(gid):

    return demon_expire_if_needed(
        gid
    )


def demon_add_pending_points(gid, spend):
    gid = str(gid)

    # ตรวจ/ปิด Demon ที่หมดอายุก่อน
    demon_expire_if_needed(gid)

    state = load_demon_state()
    demon = state.get(gid)

    # ยังไม่มีคนถือ Demon
    if not isinstance(demon, dict):
        return 0.0

    try:
        spend = float(spend or 0)
    except Exception:
        spend = 0.0

    if spend <= 0:
        return 0.0

    # ==========================================
    # สูตรคะแนน Demon
    #
    # ปกติ:
    #   10 บาท = 1 คะแนน
    #
    # ถือ Demon:
    #   คะแนน x2
    #
    # ตัวอย่างตู้ 90:
    #   41 / 10 = 4.1
    #   4.1 * 2 = 8.2 คะแนน
    # ==========================================

    base_points = spend / 10.0
    multiplier = 2.0
    add_points = base_points * multiplier

    old_points = float(demon.get('pending_points') or 0)
    new_points = old_points + add_points

    # กัน floating point เช่น 24.599999999
    add_points = round(add_points, 4)
    new_points = round(new_points, 4)

    demon['pending_points'] = new_points
    demon['multiplier'] = multiplier
    demon['points_per_money'] = 10.0
    demon['last_score_at'] = int(time.time())

    state[gid] = demon
    save_demon_state(state)

    print(
        '[DEMON SCORE]',
        'gid=', gid,
        'spend=', spend,
        'base=', round(base_points, 4),
        'x=', multiplier,
        'add=', add_points,
        'total=', new_points
    )

    return add_points


def demon_set_new_owner(gid):

    gid = str(gid)

    # --------------------------------------------------------
    # ถ้ามีเจ้าของเดิม
    # ปิดรอบ + โอน pending เข้ากระเป๋าก่อน
    # --------------------------------------------------------

    old = demon_get_state(
        gid
    )

    if isinstance(old, dict):

        demon_close_owner(
            gid,
            reason='stolen'
        )

    # --------------------------------------------------------
    # ตั้งเจ้าของใหม่
    # --------------------------------------------------------

    user = demon_local_user()

    now = int(
        time.time()
    )

    state = {
        'cabinet_id': gid,

        'owner_user_id':
            user['user_id'],

        'owner_name':
            user['username'],

        'owner_avatar':
            user['avatar'],

        'started_at':
            now,

        'expires_at':
            now + DEMON_LIFETIME_SECONDS,

        # เจ้าของใหม่เริ่มจาก 0
        'pending_points':
            0.0,

        'multiplier':
            DEMON_POINT_MULTIPLIER,

        'points_per_money':
            POINTS_PER_MONEY
    }

    states = load_demon_state()

    states[gid] = state

    save_demon_state(states)

    print(
        '[DEMON NEW OWNER]',
        'gid=', gid,
        'user=', user['user_id'],
        'name=', user['username'],
        'pending=0',
        'expires_at=',
        state['expires_at']
    )

    return state


def demon_process_draw(gid, item, spend):

    """
    ลำดับสำคัญ:

    1. เงินของ draw นี้ให้คะแนนเจ้าของ Demon คนเก่าก่อน
    2. ถ้า draw นี้เปิดได้ Demon:
       - ปิดรอบคนเก่า
       - pending เข้ากระเป๋า
       - ตั้งคนที่เปิดได้เป็น Demon คนใหม่
       - คนใหม่เริ่ม pending = 0
    """

    gid = str(gid)

    # เช็ก 24 ชั่วโมงก่อน
    demon_expire_if_needed(
        gid
    )

    # draw นี้เกิดขึ้นตอนเจ้าของเก่ายังครอง
    # จึงคิดคะแนนให้เจ้าของเก่าก่อน
    demon_add_pending_points(
        gid,
        spend
    )

    # ถ้าเปิดโดน Demon -> เปลี่ยนเจ้าของ
    if demon_is_hit(item):

        print(
            '[DEMON HIT]',
            'gid=', gid,
            'title=',
            item.get('goodslist_title')
            or item.get('title')
            or '',
            'shang_id=',
            item.get('shang_id')
        )

        state = demon_set_new_owner(
            gid
        )

        item['is_demon'] = 1
        item['demon_hit'] = 1
        item['demon_owner'] = state

        return state

    return demon_get_state(
        gid
    )


def local_demon_king(p):

    gid = str(
        p.get('goods_id')
        or p.get('id')
        or ''
    ).strip()

    state = demon_get_state(gid)

    price = demon_get_cabinet_price(gid)

    user = demon_local_user()

    # ============================================================
    # POINT WALLET
    # ============================================================

    wallet = load_point_wallet()

    wallet_row = wallet.get(
        str(user.get('user_id') or 999999),
        {}
    )

    if not isinstance(wallet_row, dict):
        wallet_row = {}

    try:
        wallet_points = float(
            wallet_row.get('points')
            or 0
        )
    except Exception:
        wallet_points = 0.0


    # ============================================================
    # ไม่มีผู้ครอง Demon
    # ============================================================

    if not isinstance(state, dict):

        result = {
            'status': 1,
            'msg': 'Request successful',

            'data': {

                'title': price,

                'king': [],

                'log_data': [],

                'my_king': {

                    'username':
                        user.get('username')
                        or 'LocalDemo',

                    'headimg':
                        user.get('avatar')
                        or '',

                    'head_border':
                        '',

                    'rank':
                        0,

                    'capture_count':
                        0,

                    'pending_points':
                        0,

                    'points':
                        wallet_points,

                    'wallet_points':
                        wallet_points,

                    'multiplier':
                        DEMON_POINT_MULTIPLIER
                },

                'pending_points':
                    0,

                'wallet_points':
                    wallet_points,

                'multiplier':
                    DEMON_POINT_MULTIPLIER
            }
        }

        print(
            '[LOCAL DEMON KING]',
            'gid=', gid,
            'NO DEMON',
            'price=', price,
            'wallet=', wallet_points
        )

        return result


    # ============================================================
    # มีผู้ครอง Demon
    # ============================================================

    now = int(
        time.time()
    )

    started_at = int(
        state.get('started_at')
        or now
    )

    expires_at = int(
        state.get('expires_at')
        or (
            started_at
            + DEMON_LIFETIME_SECONDS
        )
    )


    try:

        pending_points = float(
            state.get('pending_points')
            or 0
        )

    except Exception:

        pending_points = 0.0


    pending_points = round(
        pending_points,
        4
    )


    # ============================================================
    # เงินที่ถูกใช้ระหว่างการครอง Demon
    #
    # point = money / 10 * 2
    # money = point * 10 / 2
    # ============================================================

    # หน้า Demon ให้แสดงคะแนนสะสมโดยตรง
    capture_money = round(
        pending_points,
        4
    )


    if price > 0:

        capture_count = int(
            round(
                capture_money
                / price
            )
        )

    else:

        capture_count = 0


    owner_id = int(
        state.get('owner_user_id')
        or 999999
    )

    owner_name = str(
        state.get('owner_name')
        or 'LocalDemo'
    )

    owner_avatar = str(
        state.get('owner_avatar')
        or ''
    )


    elapsed_seconds = max(
        0,
        now - started_at
    )

    elapsed_minutes = int(
        elapsed_seconds / 60
    )

    remaining_seconds = max(
        0,
        expires_at - now
    )


    # ============================================================
    # KING
    # รูปแบบหลักยังคงเหมือน HAR
    # ============================================================

    king = {

        'id':
            owner_id,

        'user_id':
            owner_id,

        'play_types':
            int(
                p.get('play_type')
                or 0
            ),

        'goods_id':
            int(gid)
            if gid.isdigit()
            else gid,

        'order_list_id':
            0,

        'luck_no':
            0,

        'sale_num':
            0,

        'capture_count':
            capture_count,

        'capture_money':
            str(capture_money),

        'addtime':
            started_at,

        'end_time':
            expires_at,

        'time':
            remaining_seconds,

        'nickname':
            owner_name,

        'username':
            owner_name,

        'headimg':
            owner_avatar,

        'avatar':
            owner_avatar,

        'head_border':
            '',

        'vip_icon':
            '',

        'vip_id':
            0,

        'head_imgurling':
            '',

        'now_time':
            str(elapsed_minutes),

        # --------------------------------------------
        # LOCAL DEMON DATA
        # --------------------------------------------

        'pending_points':
            pending_points,

        'score':
            pending_points,

        'points':
            pending_points,

        'wallet_points':
            wallet_points,

        'multiplier':
            DEMON_POINT_MULTIPLIER,

        'expires_at':
            expires_at,

        'remaining_seconds':
            remaining_seconds,

        'is_demon':
            1
    }


    # ============================================================
    # RESPONSE
    # ============================================================

    result = {

        'status':
            1,

        'msg':
            'Request successful',

        'data': {

            'title':
                price,

            'king':
                king,

            'log_data': [

                {

                    'user_id':
                        owner_id,

                    'userinfo': {
                        'id':
                            owner_id,

                        'username':
                            owner_name,

                        'nickname':
                            owner_name,

                        'headimg':
                            owner_avatar
                    },

                    'nickname':
                        owner_name,

                    'username':
                        owner_name,

                    'headimg':
                        owner_avatar,

                    'head_border':
                        '',

                    'vip_icon':
                        '',

                    'vip_id':
                        0,

                    'head_imgurling':
                        '',

                    'capture_count':
                        capture_count,

                    'capture_money':
                        str(capture_money),

                    'pending_points':
                        pending_points,

                    'score':
                        pending_points,

                    'points':
                        pending_points
                }
            ],

            'my_king': {

                'username':
                    user.get('username')
                    or 'LocalDemo',

                'nickname':
                    user.get('username')
                    or 'LocalDemo',

                'headimg':
                    user.get('avatar')
                    or '',

                'head_border':
                    '',

                'rank':
                    0,

                'capture_count':
                    capture_count
                    if owner_id == 999999
                    else 0,

                'capture_money':
                    str(capture_money)
                    if owner_id == 999999
                    else '0',

                'pending_points':
                    pending_points
                    if owner_id == 999999
                    else 0,

                'score':
                    pending_points
                    if owner_id == 999999
                    else 0,

                'points':
                    pending_points
                    if owner_id == 999999
                    else 0,

                'wallet_points':
                    wallet_points,

                'multiplier':
                    DEMON_POINT_MULTIPLIER
            },

            # ----------------------------------------
            # LOCAL EXTRA DATA
            # ----------------------------------------

            'pending_points':
                pending_points,

            'score':
                pending_points,

            'points':
                pending_points,

            'wallet_points':
                wallet_points,

            'multiplier':
                DEMON_POINT_MULTIPLIER,

            'started_at':
                started_at,

            'expires_at':
                expires_at,

            'remaining_seconds':
                remaining_seconds
        }
    }


    print(
        '[LOCAL DEMON KING]',
        'gid=', gid,
        'owner=', owner_name,
        'count=', capture_count,
        'money=', capture_money,
        'pending_points=', pending_points,
        'wallet=', wallet_points,
        'x=', DEMON_POINT_MULTIPLIER
    )

    return result

def order(gid, n):

    items = []

    gid_str = str(gid)

    # ============================================================
    # ตรวจว่าเป็น COMBO CABINET หรือ Infinite ปกติ
    # ============================================================

    is_combo = (
        gid_str in COMBO_DETAILS
    )

    print(
        '[ORDER START]',
        'gid=', gid,
        'n=', n,
        'mode=',
        'COMBO'
        if is_combo
        else 'INFINITE'
    )


    # ============================================================
    # DRAW
    # ============================================================

    # ถ้า batch นี้เปิดได้ Demon แล้ว
    # draw ที่เหลือใน batch เดียวกันจะไม่เพิ่มคะแนน
    # เจ้าของ Demon ใหม่จะเริ่มสะสมตั้งแต่ ORDER ครั้งถัดไป
    demon_hit_this_batch = False

    for i in range(n):

        # --------------------------------------------------------
        # COMBO
        # --------------------------------------------------------

        if is_combo:

            x = choose_combo(
                gid
            )

        # --------------------------------------------------------
        # INFINITE ปกติ
        # --------------------------------------------------------

        else:

            x = choose(
                gid
            )


        # ========================================================
        # ไม่มีรางวัล
        # ========================================================

        if not x:

            return {
                'status': 0,
                'msg':
                    f'No local prize pool for goods_id {gid}',
                'data': None
            }


        # ========================================================
        # LOCAL ORDER FIELDS
        # ========================================================

        x.update({

            'id':
                int(
                    time.time() * 1000
                ) + i,

            'user_id':
                999999,

            'key_str':
                f'LOCAL-DEMO-{gid}-{i}',

            'seed':
                'LocalDemo',

            'sale_num':
                i + 1,

            'user_box_num':
                i + 1,

            'use_money':
                '0',

            'use_money_coin':
                '0'
        })


        items.append(
            x
        )

        # ========================================================
        # DEMON SYSTEM
        # ========================================================
        #
        # ถ้ามีผู้ครอง Demon อยู่:
        # ทุกยอดเปิดตู้นี้ 10 บาท = 2 คะแนน
        #
        # ถ้า draw นี้ได้ shang_id 98:
        # เจ้าของเก่าถูกปิดรอบ -> pending เข้ากระเป๋า
        # คนใหม่ขึ้น Demon -> เริ่ม pending 0
        # ========================================================

        demon_draw_price = demon_get_cabinet_price(
            gid
        )

        # --------------------------------------------------------
        # ยังไม่เคยเจอ Demon ใน order/batch นี้
        # --------------------------------------------------------

        if not demon_hit_this_batch:

            # จำไว้ก่อนว่า draw นี้เป็น Demon หรือไม่
            is_demon_draw = demon_is_hit(
                x
            )

            demon_process_draw(
                gid,
                x,
                demon_draw_price
            )

            # ถ้า draw นี้ได้ Demon:
            # - เจ้าของเก่าปิดรอบแล้ว
            # - เจ้าของใหม่เริ่ม pending = 0
            # - draw ที่เหลือใน batch นี้ไม่คิดคะแนน
            if is_demon_draw:

                demon_hit_this_batch = True

                print(
                    '[DEMON BATCH HIT]',
                    'gid=', gid,
                    'draw=', i + 1,
                    'of=', n,
                    'remaining draws ignored for score=',
                    n - i - 1
                )


        # --------------------------------------------------------
        # เจอ Demon ไปแล้วใน batch นี้
        # --------------------------------------------------------

        else:

            # สำคัญ:
            # ไม่เรียก demon_add_pending_points()
            # เพื่อให้ Demon ใหม่ยังคงเริ่มที่ 0
            #
            # แต่ถ้าใน draw ที่เหลือเกิด Demon ซ้ำอีก
            # ให้ Demon ล่าสุดเป็นเจ้าของใหม่และ reset 0 อีกครั้ง

            if demon_is_hit(x):

                print(
                    '[DEMON AGAIN SAME BATCH]',
                    'gid=', gid,
                    'draw=', i + 1,
                    'of=', n
                )

                state = demon_set_new_owner(
                    gid
                )

                x['is_demon'] = 1
                x['demon_hit'] = 1
                x['demon_owner'] = state

                # ========================================================
        # COMBO COUNTER / GUARANTEED REWARD
        # ========================================================

        if is_combo:

            level_now = str(
                x.get('shang_title')
                or x.get('tier')
                or ''
            ).upper()


            current_combo = get_combo_count(
                gid
            )


            # ====================================================
            # อ่าน SET COUNT ของตู้นี้
            # ====================================================

            combo_target = 16

            try:

                combo_response = COMBO_DETAILS.get(
                    str(gid)
                ) or {}

                combo_data = combo_response.get(
                    'data'
                ) or {}

                combo_goods = combo_data.get(
                    'goods'
                ) or {}

                combo_target = int(
                    float(
                        combo_goods.get(
                            'set_count'
                        )
                        or 16
                    )
                )

            except Exception:

                combo_target = 16


            if combo_target <= 0:
                combo_target = 16


            # ====================================================
            # C = COMBO +1
            # ====================================================

            if level_now == 'C':

                current_combo += 1


                print(
                    '[COMBO +1]',
                    'gid=', gid,
                    'count=',
                    current_combo,
                    '/',
                    combo_target
                )


                # =================================================
                # ถึง Guaranteed Reward
                # =================================================

                if current_combo >= combo_target:

                    print(
                        '[COMBO TARGET HIT]',
                        'gid=', gid,
                        'count=', current_combo,
                        'target=', combo_target
                    )


                    combo_reward = choose_combo_reward(
                        gid
                    )


                    if combo_reward:

                        # -----------------------------------------
                        # ใส่ local order fields ให้ reward
                        # -----------------------------------------

                        combo_reward.update({

                            'id':
                                int(
                                    time.time() * 1000
                                ) + i + 100000,

                            'user_id':
                                999999,

                            'key_str':
                                f'LOCAL-COMBO-{gid}-{i}',

                            'seed':
                                'LocalComboReward',

                            'sale_num':
                                i + 1,

                            'user_box_num':
                                i + 1,

                            'use_money':
                                '0',

                            'use_money_coin':
                                '0',

                            'prize_change':
                                3
                        })


                        # =========================================
                        # สำคัญ:
                        # แทน C ตัวที่ทำให้ครบ ด้วย Combo Reward
                        # =========================================

                        items[-1] = combo_reward

                        x = combo_reward


                        # =========================================
                        # ครบแล้วเริ่ม streak ใหม่
                        # =========================================

                        set_combo_count(
                            gid,
                            0
                        )


                        print(
                            '[COMBO REWARD INSERTED]',
                            'gid=', gid,
                            'title=',
                            combo_reward.get(
                                'goodslist_title'
                            ),
                            'next_count=0'
                        )


                    else:

                        # หา reward ไม่เจอ
                        # เก็บ target ไว้ก่อน ไม่ให้เลขทะลุ

                        set_combo_count(
                            gid,
                            combo_target
                        )


                else:

                    set_combo_count(
                        gid,
                        current_combo
                    )


            # ====================================================
            # SP / A / B = RESET
            # ====================================================

            elif level_now in (
                'SP',
                'A',
                'B'
            ):

                if current_combo != 0:

                    print(
                        '[COMBO RESET]',
                        'gid=', gid,
                        'by=', level_now,
                        'old=', current_combo
                    )


                set_combo_count(
                    gid,
                    0
                )


            # ====================================================
            # D
            #
            # ตอนนี้ยัง KEEP ตามเดิม
            # ====================================================

            else:

                print(
                    '[COMBO KEEP]',
                    'gid=', gid,
                    'tier=', level_now,
                    'count=', current_combo
                )

        print(
            '[ORDER RESULT DEBUG]',
            'gid=', gid,
            'mode=',
            'COMBO'
            if is_combo
            else 'INFINITE',
            'level=',
            x.get(
                'shang_title'
            ),
            'shang_id=',
            x.get(
                'shang_id'
            ),
            'title=',
            x.get(
                'goodslist_title'
            )
            or x.get(
                'title'
            ),
            'back_image=',
            x.get(
                'back_image'
            ),
            'color_t=',
            x.get(
                'color_t'
            ),
            'background=',
            x.get(
                'background'
            ),
            'imgurl_black=',
            x.get(
                'imgurl_black'
            )
        )


    # ============================================================
    # INFINITE STATS
    # ============================================================

    record_infinite_stats(
        gid,
        items
    )


    # ============================================================
    # BAG
    # ============================================================

    add_to_bag(
        items,
        gid,
        'toy'
    )


    # ============================================================
    # RESPONSE
    # ============================================================

    return {
        'status': 1,

        'msg':
            'Order placed successfully',

        'data': {

            'pay_type':
                1,

            'get_score':
                0,

            'order_num':
                f'LOCAL-{int(time.time())}',

            'sum_use_money':
                n * 2,

            'sum_use_money_coin':
                0,

            'data': {

                'list':
                    items,

                'shang_list':
                    items
            }
        }
    }


def card_pool_for_gid(gid):
    gid = str(gid)

    HAR_COMPLETE_GIDS = {
        "11",
        "13",
        "17",
        "22",
        "23"
    }

    rows = []

    # ============================================================
    # 5 ตู้ใหม่
    # ใช้ FULL HAR โดยตรง
    # ============================================================

    if gid in HAR_COMPLETE_GIDS:

        har = HAR_CARD_POOLS.get(gid)

        if isinstance(har, list):
            rows = har

    # ============================================================
    # ตู้เก่าทั้งหมด
    #
    # สำคัญ:
    # CARD_ALBUM มีรูปแบบ:
    #
    # "18": {
    #     "rows": [...]
    # }
    #
    # ต้องเอา ["rows"] ออกมา
    # ห้ามใช้ CARD_POOLS ก่อน เพราะบางตู้มีแค่ SP/A
    # ============================================================

    else:

        album = CARD_ALBUM.get(gid)

        if isinstance(album, dict):

            album_rows = album.get(
                "rows",
                []
            )

            if isinstance(album_rows, list) and album_rows:
                rows = album_rows

        elif isinstance(album, list) and album:
            rows = album

        # --------------------------------------------------------
        # ถ้าไม่มี Album ค่อยใช้ CARD_POOLS
        # --------------------------------------------------------

        if not rows:

            old_pool = CARD_POOLS.get(gid)

            if isinstance(old_pool, list) and old_pool:
                rows = old_pool

    # ============================================================
    # FALLBACK -> CARD_DETAILS
    # ============================================================

    if not rows:

        detail = CARD_DETAILS.get(
            gid,
            {}
        ).get(
            "data",
            {}
        )

        detail_rows = detail.get(
            "goodslist_all",
            []
        )

        if isinstance(detail_rows, list):
            rows = detail_rows

    if not isinstance(rows, list):
        rows = []

    # ============================================================
    # NORMALIZE
    # ============================================================

    result = []

    sid_to_level = {
        100: "SP",
        101: "A",
        102: "B",
        103: "C",
        104: "D"
    }

    for index, item in enumerate(rows, 1):

        if not isinstance(item, dict):
            continue

        x = dict(item)

        # --------------------------------------------------------
        # Shang ID
        # --------------------------------------------------------

        try:
            sid = int(
                x.get("shang_id")
                or 0
            )
        except (TypeError, ValueError):
            sid = 0

        # --------------------------------------------------------
        # Tier
        # --------------------------------------------------------

        lvl = str(
            x.get("shang_title")
            or sid_to_level.get(
                sid,
                ""
            )
        ).strip().upper()

        if lvl not in {
            "SP",
            "A",
            "B",
            "C",
            "D"
        }:
            continue

        x["shang_id"] = sid
        x["shang_title"] = lvl

        # --------------------------------------------------------
        # Image
        # --------------------------------------------------------

        img = (
            x.get("goodslist_imgurl")
            or x.get("imgurl")
            or x.get("image")
            or ""
        )

        x["imgurl"] = img
        x["goodslist_imgurl"] = img

        # --------------------------------------------------------
        # Title
        # --------------------------------------------------------

        title = (
            x.get("goodslist_title")
            or x.get("title")
            or x.get("short_title")
            or f"{lvl} #{index}"
        )

        x["title"] = title
        x["goodslist_title"] = title

        if not x.get("short_title"):
            x["short_title"] = title

        # --------------------------------------------------------
        # Price
        # --------------------------------------------------------

        price = (
            x.get("goodslist_price")
            or x.get("goodslist_money")
            or x.get("price")
            or "0.00"
        )

        x["goodslist_price"] = price
        x["goodslist_money"] = price
        x["price"] = price

        # --------------------------------------------------------
        # Probability
        # --------------------------------------------------------

        try:
            x["real_pro"] = float(
                x.get("real_pro")
                or 0
            )
        except (TypeError, ValueError):
            x["real_pro"] = 0.0

        # --------------------------------------------------------
        # Badge
        # --------------------------------------------------------

        badge = (
            x.get("shang_imgurl")
            or x.get("shang_image")
            or x.get("shang_iamge")
            or LEVEL_BADGES.get(
                lvl,
                ""
            )
        )

        x["shang_imgurl"] = badge
        x["shang_image"] = badge
        x["shang_iamge"] = badge

        result.append(x)

    # ============================================================
    # DEBUG
    # ============================================================

    counts = {}

    for x in result:

        lvl = x.get(
            "shang_title",
            "?"
        )

        counts[lvl] = (
            counts.get(lvl, 0)
            + 1
        )

    print(
        "[CARD POOL SOURCE]",
        "goods_id=",
        gid,
        "mode=",
        (
            "HAR"
            if gid in HAR_COMPLETE_GIDS
            else "ALBUM/LEGACY"
        ),
        "total=",
        len(result),
        "tiers=",
        counts
    )

    return result


def card_order(gid,n):

    gid = str(gid)

    detail = CARD_DETAILS.get(
        gid,
        {}
    ).get(
        'data',
        {}
    )

    # ============================================================
    # PACK INFO
    # ============================================================

    try:
        packs = max(
            1,
            int(n or 1)
        )
    except:
        packs = 1

    try:
        cards_per_pack = max(
            1,
            int(
                detail.get('num')
                or 1
            )
        )
    except:
        cards_per_pack = 1

    # จำนวนการ์ดทั้งหมด
    total_cards = (
        packs
        *
        cards_per_pack
    )

    # ============================================================
    # PRICE
    # ============================================================

    try:
        pack_price = float(
            detail.get('price')
            or 0
        )
    except:
        pack_price = 0.0

    cost = round(
        pack_price * packs,
        2
    )

    # ============================================================
    # CHECK MONEY
    # ============================================================

    prof = load_profile()

    try:
        balance = float(
            prof.get(
                'money',
                0
            )
        )
    except:
        balance = 0.0

    if cost > balance:

        return {
            'status': 0,
            'msg': (
                f"เงินไม่พอ "
                f"ต้องใช้ ฿{cost:.2f} "
                f"แต่มี ฿{balance:.2f}"
            ),
            'data': None
        }

    # ============================================================
    # LOAD CARD POOL
    # ============================================================

    pool = card_pool_for_gid(
        gid
    )

    print(
        "[CARD POOL]",
        "goods_id=",
        gid,
        "items=",
        len(pool)
    )

    if not pool:

        return {
            "status": 0,
            "msg": (
                f"No local card pool "
                f"for goods_id {gid}"
            ),
            "data": None
        }

    # ============================================================
    # RATE
    # ============================================================

    tier_rates = effective_rates(
        gid,
        detail
    )

    # ============================================================
    # แยก Pool ตาม Tier
    # ============================================================

    available = {}

    for z in pool:

        if not isinstance(
            z,
            dict
        ):
            continue

        lvl = str(
            z.get(
                'shang_title'
            )
            or ''
        ).strip().upper()

        if lvl in (
            'SP',
            'A',
            'B',
            'C',
            'D'
        ):

            available.setdefault(
                lvl,
                []
            ).append(
                z
            )

    # ============================================================
    # HAR STRICT MODE
    #
    # 5 ตู้นี้เรามีข้อมูลครบทุก Tier จาก HAR แล้ว
    #
    # 11
    # 13
    # 17
    # 22
    # 23
    #
    # ตู้อื่นใช้ Legacy Mode
    # เพื่อไม่ทำให้ตู้เก่าที่ข้อมูลไม่ครบเปิดไม่ได้
    # ============================================================

        HAR_COMPLETE_GIDS = {
        "11",
        "13",
        "17",
        "22",
        "23"
    }

    strict_pool = gid in HAR_COMPLETE_GIDS

    # ============================================================
    # HAR MODE
    # เฉพาะ 11,13,17,22,23
    # ============================================================

    if strict_pool:

        tier_order = (
            "SP",
            "A",
            "B",
            "C",
            "D"
        )

        levels = []
        weights = []

        for lvl in tier_order:

            try:
                rate = float(
                    tier_rates.get(lvl, 0)
                    or 0
                )
            except:
                rate = 0.0

            if rate <= 0:
                continue

            if not available.get(lvl):

                return {
                    "status": 0,
                    "msg": (
                        f"Missing HAR cards: "
                        f"goods_id={gid}, "
                        f"tier={lvl}, "
                        f"rate={rate}"
                    ),
                    "data": None
                }

            levels.append(lvl)
            weights.append(rate)

    # ============================================================
    # LEGACY MODE
    # ตู้เก่าทั้งหมด
    #
    # ใช้ Logic เดิมก่อนที่เราจะแก้ HAR
    # ============================================================

    else:

        levels = [
            lvl
            for lvl
            in tier_rates
            if available.get(lvl)
        ]

        if not levels:
            levels = list(available)

        if not levels:

            return {
                "status": 0,
                "msg": (
                    f"No usable local card prizes "
                    f"for goods_id {gid}"
                ),
                "data": None
            }

        weights = [
            tier_rates.get(
                lvl,
                1.0
            )
            for lvl
            in levels
        ]

    print(
        "[CARD RATES]",
        "goods_id=",
        gid,
        "mode=",
        (
            "HAR-STRICT"
            if strict_pool
            else "LEGACY-ORIGINAL"
        ),
        "rates=",
        {
            lvl:
            tier_rates.get(
                lvl,
                0
            )
            for lvl
            in levels
        },
        "pool=",
        {
            lvl:
            len(
                available.get(
                    lvl,
                    []
                )
            )
            for lvl
            in levels
        }
    )

    pack_numbers = reserve_pack_numbers(
        packs
    )

    # ============================================================
    # DRAW
    # ============================================================

    items = []

    for i in range(
        total_cards
    ):

        # ========================================================
        # STEP 1
        # สุ่ม Tier ตาม Rate ของตู้
        # ========================================================

        lvl = random.choices(
            levels,
            weights=weights,
            k=1
        )[0]

        candidates = available[
            lvl
        ]

        # ========================================================
        # STEP 2
        # สุ่มการ์ดภายใน Tier
        #
        # ถ้ามี real_pro ใช้ real_pro
        # ถ้าไม่มีเลย ใช้ equal random
        # ========================================================

                # ========================================================
        # สุ่มการ์ดภายใน Tier
        # ========================================================

        item_weights = []

        for z in candidates:

            try:
                w = float(
                    z.get('real_pro')
                    or 0
                )
            except:
                w = 0.0

            # ----------------------------------------------------
            # HAR 5 ตู้ใหม่
            #
            # ถ้ามี real_pro = 0
            # ไม่ควรเพิ่มน้ำหนักปลอม
            # ----------------------------------------------------

            if strict_pool:
                item_weights.append(
                    max(0.0, w)
                )

            # ----------------------------------------------------
            # ตู้เก่า
            #
            # คืน Logic เดิม 100%
            # real_pro = 0 -> weight 1
            # ----------------------------------------------------

            else:
                item_weights.append(
                    w if w > 0 else 1.0
                )

        # ========================================================
        # HAR
        # ========================================================

        if strict_pool:

            if sum(item_weights) > 0:

                src = dict(
                    random.choices(
                        candidates,
                        weights=item_weights,
                        k=1
                    )[0]
                )

            else:

                src = dict(
                    random.choice(
                        candidates
                    )
                )

        # ========================================================
        # LEGACY
        # Logic เดิม
        # ========================================================

        else:

            src = dict(
                random.choices(
                    candidates,
                    weights=item_weights,
                    k=1
                )[0]
            )

        # ========================================================
        # IMAGE
        # ========================================================

        img = (
            src.get(
                'goodslist_imgurl'
            )
            or
            src.get(
                'imgurl'
            )
            or ''
        )

        # บังคับรูปผล Card
        # ให้วิ่งผ่าน Local Mirror
        img = str(
            img
        ).replace(
            'https://img.joypop.gg/',
            '/local-img/'
        ).replace(
            'http://img.joypop.gg/',
            '/local-img/'
        )

        if img.startswith(
            '/local-img/'
        ):

            img = (
                ''
                +
                img
            )

        # ========================================================
        # TITLE
        # ========================================================

        title = (
            src.get(
                'goodslist_title'
            )
            or
            src.get(
                'title'
            )
            or
            src.get(
                'short_title'
            )
            or
            f"{detail.get('title','Card')} - {lvl}"
        )

        short = (
            src.get(
                'short_title'
            )
            or
            title
        )

        # ========================================================
        # PRICE
        # ========================================================

        raw_price = (
            src.get(
                'goodslist_price'
            )
            or
            src.get(
                'price'
            )
            or
            src.get(
                'goodslist_money'
            )
            or
            '0.00'
        )

        try:

            price = (
                f"{float(raw_price):.2f}"
            )

        except:

            price = str(
                raw_price
            )

        # ========================================================
        # CARD ID
        # ========================================================

        pid = (
            src.get(
                'goodslist_id'
            )
            or
            src.get(
                'goods_list_id'
            )
            or
            src.get(
                'id'
            )
            or
            (
                int(
                    time.time()
                    *
                    1000
                )
                +
                i
            )
        )

        realid = (
            src.get(
                'real_goods_list_id'
            )
            or
            src.get(
                'goods_list_id'
            )
            or
            pid
        )

        # ========================================================
        # PACK INDEX
        # ========================================================

        pack_index = (
            i
            //
            cards_per_pack
        )

        order_interval_num = (
            pack_numbers[
                pack_index
            ]
        )

        # ========================================================
        # RESULT ITEM
        # ========================================================

        x = dict(
            src
        )

        x.update({

            'id':
                int(
                    time.time()
                    *
                    1000
                )
                +
                i,

            # ID จาก Album เดิม
            'album_card_id':
                src.get(
                    'id'
                ),

            # เลข Pack
            'order_interval_num':
                order_interval_num,

            'goodslist_id':
                pid,

            'real_goods_list_id':
                realid,

            'goods_list_id':
                realid,

            # Tier ID
            'shang_id': {
                'SP': 100,
                'A': 101,
                'B': 102,
                'C': 103,
                'D': 104
            }.get(
                lvl,
                104
            ),

            # Title
            'goodslist_title':
                title,

            'short_title':
                short,

            'title':
                title,

            # Image
            'goodslist_imgurl':
                img,

            'imgurl':
                img,

            # Price
            'goodslist_price':
                price,

            'goodslist_money':
                price,

            'price':
                price,

            # Tier
            'shang_title':
                lvl,

            # Badge
            'shang_image':
                (
                    LEVEL_BADGES.get(
                        lvl
                    )
                    or
                    src.get(
                        'shang_imgurl'
                    )
                    or
                    src.get(
                        'shang_iamge'
                    )
                    or
                    src.get(
                        'shang_image'
                    )
                    or
                    ''
                ),

            # Local
            'key_str':
                f'LOCAL-CARD-{gid}-{i}',

            'seed':
                'LocalDemo',

            'score':
                '0.00',

            'use_money':
                '0',

            'use_money_coin':
                '0',

            'user_id':
                999999,

            'sale_num':
                i + 1,

            'user_box_num':
                i + 1
        })

        items.append(
            x
        )

    # ============================================================
    # หักเงินหลังสุ่มสำเร็จเท่านั้น
    # ============================================================

    if cost > 0:

        prof = load_profile()

        try:
            current_money = float(
                prof.get(
                    'money',
                    0
                )
            )
        except:
            current_money = 0.0

        prof['money'] = round(
            max(
                0,
                current_money
                -
                cost
            ),
            2
        )

        save_profile(
            prof
        )

    # ============================================================
    # แบ่งกลับเป็น Pack
    # ============================================================

    pack_rows = [

        items[
            i:
            i + cards_per_pack
        ]

        for i
        in range(
            0,
            len(items),
            cards_per_pack
        )
    ]

    # ============================================================
    # UPDATE STATS
    # ============================================================

    record_pack_stats(
        gid,
        pack_rows
    )

    # ============================================================
    # ADD BAG
    # ============================================================

    add_to_bag(
        items,
        gid,
        'card'
    )

    # ============================================================
    # RESPONSE
    # ============================================================

    new_balance = load_profile()[
        'money'
    ]

    return {

        'status': 1,

        'msg':
            'Order placed successfully',

        'data': {

            'pay_type':
                0,

            'get_score':
                '0.00',

            'order_num':
                f'LOCAL-CARD-{int(time.time())}',

            'use_money':
                cost,

            'sum_use_money':
                cost,

            'sum_use_money_coin':
                0,

            'order_total':
                cost,

            'money':
                new_balance,

            'balance':
                new_balance,

            'credit':
                new_balance,

            'data':
                items
        }
    }

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
          # ==================================================
    # V5.15 - Infinite Rate Admin
    # ==================================================

      if path=='/infinite-rate-admin':

        b=INFINITE_RATE_ADMIN_HTML.encode(
          'utf-8'
      )

      self.send_response(
          200
      )

      self.send_header(
          'Content-Type',
          'text/html; charset=utf-8'
      )

      self.send_header(
          'Content-Length',
          str(len(b))
      )

      self.end_headers()

      self.wfile.write(
          b
      )

      return
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
        # ==================================================
    # V5.15 - Infinite Rates GET
    # ==================================================

    if (
        path==
        '/api/local/infinite_rates'
        and
        not body
    ):

      custom=load_infinite_rates()

      cabinets={}


      for gid,pool in POOLS.items():


        if not isinstance(
            pool,
            dict
        ):

            continue


        available=infinite_available_levels(
                gid
            )


        if not available:

            continue


        rates=(

            custom.get(
                str(gid)
            )

            or

            infinite_default_rates(
                gid
            )

        )


        cabinets[
            str(gid)
        ]={

            'title':
                infinite_cabinet_title(
                    gid
                ),

            'rates':
                rates,

            'available':
                available

        }


      return out(
          self,
          {
              'status':1,
              'msg':
                  'Request successful',
              'cabinets':
                  cabinets
          }
      )


    # ==================================================
    # V5.15 - Infinite Rates SAVE
    # ==================================================

    if (
        path==
        '/api/local/infinite_rates'
        and
        body
    ):

      try:

        data=json.loads(
            body.decode(
                'utf-8'
            )
        )


        gid=str(
            data.get(
                'goods_id'
            )
        )


        available=infinite_available_levels(
                gid
            )


        rates={}


        for key,value in (
            data.get(
                'rates'
            ) or {}
        ).items():


            level=str(
                key
            ).upper()


            if level not in available:

                continue


            rates[
                level
            ]=max(
                0.0,
                float(value)
            )


        if not rates:

            return out(
                self,
                {
                    'status':0,
                    'msg':
                        'No valid rates'
                },
                400
            )


        total=sum(
            rates.values()
        )


        if (
            abs(
                total-100
            )
            >
            0.001
        ):

            return out(
                self,
                {
                    'status':0,
                    'msg':
                        'Total rate must be 100%'
                },
                400
            )


        all_rates=load_infinite_rates()


        all_rates[
            gid
        ]=rates


        save_infinite_rates(
            all_rates
        )


        return out(
            self,
            {
                'status':1,
                'msg':'Saved',
                'data':rates
            }
        )


      except Exception as e:

        return out(
            self,
            {
                'status':0,
                'msg':str(e)
            },
            400
        )


    # ==================================================
    # V5.15 - Infinite Rates RESET
    # ==================================================

    if (
        path==
        '/api/local/infinite_rates/reset'
    ):

      try:

        data=json.loads(
            body.decode(
                'utf-8'
            )
        )


        gid=str(
            data.get(
                'goods_id'
            )
        )


        all_rates=load_infinite_rates()


        all_rates.pop(
            gid,
            None
        )


        save_infinite_rates(
            all_rates
        )


        return out(
            self,
            {
                'status':1,
                'msg':'Reset',

                'data':
                    infinite_default_rates(
                        gid
                    )
            }
        )


      except Exception as e:

        return out(
            self,
            {
                'status':0,
                'msg':str(e)
            },
            400
        )


    if path == '/api/infinite/king':

        print(
            '[DEMON KING ROUTE]',
            'gid=',
            p.get('goods_id')
        )

        return out(
            self,
            local_demon_king(p)
        )

    # ============================================================
    # LOCAL COMBO / GUARANTEED REWARD DETAIL
    # ============================================================

    if path == '/api/infinite/detail':

        detail_gid = str(
            p.get('goods_id')
            or p.get('id')
            or ''
        ).strip()

        # Combo / Guaranteed Reward เท่านั้น
        if detail_gid in COMBO_DETAILS:

            print(
                '[DETAIL ROUTE]',
                'gid=', detail_gid,
                'mode=COMBO'
            )

            return out(
                self,
                local_infinite_detail(p)
            )

        # HOT / High Drops / Infinite ปกติ
        # ไม่ return ตรงนี้
        # ปล่อยให้ REPLAY logic ด้านล่างจัดการ
        print(
            '[DETAIL ROUTE]',
            'gid=', detail_gid,
            'mode=REPLAY'
        )


    if path.startswith('/api/'):

        if any(
            x in path.lower()
            for x in BLOCK
        ):
            return out(
                self,
                {
                    "status": 0,
                    "msg": "Blocked in local demo",
                    "data": None
                },
                403
            )

        k = rkey(path, p)
        obj = REPLAY.get(k)

    if path.startswith('/api/'):

        if any(
            x in path.lower()
            for x in BLOCK
        ):
            return out(
                self,
                {
                    "status": 0,
                    "msg": "Blocked in local demo",
                    "data": None
                },
                403
            )

        k = rkey(path, p)
        obj = REPLAY.get(k)
    
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
    if path=='/api/user/update_userinfo':
        print('[USER UPDATE]', p)
        return out(self, local_update_userinfo(p))

    if path=='/api/user/user': 
        return out(self,user())
    if path=='/api/card/card_shang_logs': return out(self,local_card_shang_logs(p))
    if path=='/api/card/card_shang_count': return out(self,local_card_shang_count(p))
    if path=='/api/card/cardgoodslist_detail':
      cid=str(p.get('id') or p.get('goodslist_id') or p.get('goods_list_id') or '0')
      d=CARD_ITEM_DETAILS.get(cid)
      if d:
        d=json.loads(json.dumps(d)); data=d.get('data',{})
        for k in ('imgurl','content_image','goodslist_imgurl'):
          if data.get(k):
            v=str(data[k]).replace('https://img.joypop.gg/', PUBLIC_BASE_URL + '/local-img/').replace('http://img.joypop.gg/', PUBLIC_BASE_URL + '/local-img/')
            if not v.startswith(('http://','https://','/')): v=PUBLIC_BASE_URL + '/local-img/' + v.lstrip('/')
            data[k]=v
        return out(self,d)
      for gid,pool in CARD_POOLS.items():
        for z in pool:
          if str(z.get('id') or z.get('goodslist_id') or z.get('goods_list_id') or '')==cid:
            img=str(z.get('goodslist_imgurl') or z.get('imgurl') or '').replace('https://img.joypop.gg/', PUBLIC_BASE_URL + '/local-img/')
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
    # ============================================================
    # INFINITE LOCAL STATISTICS
    # Hot Combo / Demon / Infinite cabinets
    # ============================================================

    if path == '/api/infinite/shang_count':
        return out(
            self,
            local_infinite_shang_count(p)
        )

    if path == '/api/infinite/shang_logs':
        return out(
            self,
            local_infinite_shang_logs(p)
        )

    if path == '/api/infinite/shang_log':
        return out(
            self,
            local_infinite_shang_log(p)
        )
    if path=='/api/infinite/order_buy': return out(self,order(int(p.get('goods_id','0') or 0),max(1,int(p.get('prize_num','1') or 1))))
    if path=='/api/card/order_buy': return out(self,card_order(int(p.get('goods_id','0') or 0),max(1,int(p.get('prize_num','1') or 1))))
    if path=='/api/card/order_money':
      n=max(1,int(p.get('prize_num','1') or 1)); gid=str(p.get('goods_id','0')); d=CARD_DETAILS.get(gid,{}).get('data',{}); price=float(d.get('price') or 0); cost=round(price*n,2); bal=round(float(load_profile()['money']),2); goods={'title':d.get('title') or '', 'price':f'{price:.4f}', 'prize_num':n, 'num':int(d.get('num') or 1), 'prize_count':int(d.get('prize_count') or 0), 'imgurl':d.get('imgurl') or ''}; return out(self,{"status":1,"msg":"Request successful","data":{"goods":goods,"coupon_id":0,"coupon_money":0,"order_total":cost,"price":0,"money":bal,"balance":bal,"credit":bal,"use_money":cost,"sum_use_money":cost,"sum_use_money_coin":0,"money_stone":0,"use_money_stone":0}})
    if path == '/api/infinite/order_money':

      gid = str(
          p.get('goods_id', '0')
          or '0'
      )

      n = max(
          1,
          int(
              p.get('prize_num', '1')
              or 1
          )
      )

      # ==========================================
      # หา DETAIL ของตู้จาก REPLAY
      # ==========================================

      detail = None


      # ==========================================
      # COMBO DETAIL
      # ==========================================

      if gid in COMBO_DETAILS:

          combo_detail = COMBO_DETAILS.get(
              gid
          )

          if isinstance(
              combo_detail,
              dict
          ):
              detail = combo_detail


      # ==========================================
      # INFINITE DETAIL เดิมจาก REPLAY
      # ==========================================

      possible_keys = (
          f'/api/infinite/detail|goods_id={gid}&play_type=0',
          f'/api/infinite/detail|play_type=0&goods_id={gid}',
      )

      if detail is None:

          for key in possible_keys:

              if key in REPLAY:
                  detail = REPLAY[key]
                  break

      # เผื่อ query order ไม่ตรง
      if detail is None:

          for key, value in REPLAY.items():

              key_text = str(key)

              if not key_text.startswith(
                  '/api/infinite/detail|'
              ):
                  continue

              query = key_text.split(
                  '|',
                  1
              )[1]

              params = urllib.parse.parse_qs(
                  query
              )

              replay_gid = str(
                  (
                      params.get('goods_id')
                      or ['']
                  )[0]
              )

              if replay_gid == gid:
                  detail = value
                  break


      # ==========================================
      # อ่านข้อมูลตู้
      # ==========================================

      data = {}

      if isinstance(detail, dict):
          data = detail.get('data') or {}

      goods_data = {}

      if isinstance(data, dict):
          goods_data = (
              data.get('goods')
              or {}
          )


      # ==========================================
      # ราคา
      # ==========================================

      try:
          price = float(
              goods_data.get('price')
              or data.get('price')
              or 0
          )
      except:
          price = 0.0


      cost = round(
          price * n,
          2
      )


      # ==========================================
      # เงิน Local
      # ==========================================

      try:
          bal = round(
              float(
                  load_profile().get(
                      'money',
                      0
                  )
              ),
              2
          )
      except:
          bal = 0.0


      # ==========================================
      # ข้อมูลตู้สำหรับหน้า Confirm
      # ==========================================

      goods = {
          'id': int(gid) if gid.isdigit() else gid,

          'goods_id':
              int(gid)
              if gid.isdigit()
              else gid,

          'title':
              goods_data.get('title')
              or '',

          'price':
              f'{price:.2f}',

          'prize_num':
              n,

          'num':
              int(
                  goods_data.get('num')
                  or 1
              ),

          'prize_count':
              int(
                  goods_data.get(
                      'prize_count'
                  )
                  or 0
              ),

          'imgurl':
              goods_data.get('imgurl')
              or ''
      }


      print(
          '[INFINITE ORDER MONEY]',
          'gid=', gid,
          'n=', n,
          'price=', price,
          'cost=', cost,
          'balance=', bal
      )


      return out(
          self,
          {
              'status': 1,
              'msg': 'Request successful',

              'data': {

                  'goods': goods,

                  'coupon_id': 0,
                  'coupon_money': 0,

                  'order_total': cost,

                  'price': 0,

                  'money': bal,
                  'balance': bal,
                  'credit': bal,

                  'use_money': cost,
                  'sum_use_money': cost,

                  'sum_use_money_coin': 0,

                  'money_stone': 0,
                  'use_money_stone': 0
              }
          }
      )
    if path=='/api/bag/cardbag_goodslist':
        return out(self, card_album_response(p))

    if path=='/api/bag/bag':
        return out(self, bag_response(p))

    if path=='/api/market/bag_sell':
        return out(self, bag_sell(p))

    if path=='/api/local/bag_clear':
        with LOCK:
            save_bag([])
        return out(self, {
            'status': 1,
            'msg': 'Local bag cleared',
            'data': None
        })


    # ============================================================
    # TOYS -> SAFE
    # ============================================================

    if path == '/api/bag/bag_movein':
        return out(
            self,
            bag_movein(p, 'toy')
        )


    # ============================================================
    # CARDS -> SAFE
    # ============================================================

    if path == '/api/bag/cardbag_movein':
        return out(
            self,
            bag_movein(p, 'card')
        )


    # ============================================================
    # SAFE -> TOYS
    # ============================================================

    if path == '/api/bag/bag_remove':
        return out(
            self,
            safe_remove(p, 'toy')
        )


    # ============================================================
    # SAFE -> CARDS
    # ============================================================

    if path == '/api/bag/cardbag_remove':
        return out(
            self,
            safe_remove(p, 'card')
        )


    # ============================================================
    # GENERIC API FALLBACK
    # ต้องอยู่ท้ายสุด
    # ============================================================

    if path.startswith('/api/'):

        if any(
            x in path.lower()
            for x in BLOCK
        ):
            return out(
                self,
                {
                    "status": 0,
                    "msg": "Blocked in local demo",
                    "data": None
                },
                403
            )

        k = rkey(path, p)
        obj = REPLAY.get(k)

        if obj is None:
            obj = REPLAY.get(path + '|')

        if obj is not None:
            print('[HAR REPLAY]', k)
            obj = rewrite_public_image_urls(obj)
            return out(self, obj)

        print('[MISSING LOCAL API]', path, p)

        return out(
            self,
            {
                "status": 0,
                "msg": "No local replay available",
                "data": None
            }
        )


    # ============================================================
    # SERVICE WORKER
    # ============================================================

    if path == '/h5/sw.js':
        self.send_response(204)
        self.end_headers()
        return


    # ==================================================
    # V5.20 - Vue SPA Router fallback
    # ==================================================

    if path == '/':
        self.path = '/joypop.gg/h5/'

    elif path in ('/h5', '/h5/'):
        self.path = '/joypop.gg/h5/'

    elif path.startswith('/h5/'):

        local_path = os.path.join(
            ROOT,
            'joypop.gg',
            path.lstrip('/')
        )

        if os.path.isfile(local_path):

            self.path = (
                '/joypop.gg'
                + path
            )

        elif os.path.isdir(local_path):

            self.path = (
                '/joypop.gg'
                + path
            )

        else:

            print(
                '[SPA ROUTE]',
                path,
                '=> /joypop.gg/h5/'
            )

            self.path = (
                '/joypop.gg/h5/'
            )

    elif path.startswith('/cdn-cgi/'):

        self.path = (
            '/joypop.gg'
            + path
        )

    elif path.startswith('/local-img/'):

        # AUTO IMAGE MIRROR เดิมของคุณต่อจากตรงนี้

      # โค้ด AUTO IMAGE MIRROR เดิมต่อจากตรงนี้
      # ==================================================
      # V5.19 AUTO IMAGE MIRROR
      #
      # 1. ถ้ามีไฟล์ local -> ใช้ทันที
      # 2. ถ้าไม่มี -> ดาวน์โหลดจาก img.joypop.gg
      # 3. cache ลง img.joypop.gg/... ในเครื่อง
      # 4. request ครั้งต่อไปใช้ local
      # ==================================================

      rel = urllib.parse.unquote(
          path[len('/local-img/'):]
      ).lstrip('/').replace('\\', '/')

      imgroot = os.path.abspath(
          os.path.join(ROOT, 'img.joypop.gg')
      )

      candidate = os.path.abspath(
          os.path.join(imgroot, rel)
      )


      # ==================================================
      # SECURITY: ป้องกัน ../ traversal
      # ==================================================

      if not (
          candidate == imgroot
          or
          candidate.startswith(imgroot + os.sep)
      ):
          self.send_error(403, 'Forbidden')
          return


      # ==================================================
      # ถ้าไม่มีไฟล์ -> ดาวน์โหลดจาก JOYPOP
      # ==================================================

      if not os.path.isfile(candidate):

          remote_url = (
              'https://img.joypop.gg/'
              + urllib.parse.quote(
                  rel,
                  safe='/:%@-._~'
              )
          )

          print(
              '[AUTO IMAGE FETCH]',
              remote_url
          )

          try:

              req = urllib.request.Request(
                  remote_url,
                  headers={
                      'User-Agent':
                          'Mozilla/5.0 '
                          '(Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 '
                          '(KHTML, like Gecko) '
                          'Chrome/153.0.0.0 '
                          'Safari/537.36',

                      'Referer':
                          'https://joypop.gg/',

                      'Accept':
                          'image/avif,image/webp,'
                          'image/apng,image/svg+xml,'
                          'image/*,*/*;q=0.8',
                  }
              )


              with urllib.request.urlopen(
                  req,
                  timeout=15
              ) as response:

                  data = response.read()

                  content_type = str(
                      response.headers.get(
                          'Content-Type',
                          ''
                      )
                  ).lower()


              # ==========================================
              # ป้องกันหน้า error/html ถูกบันทึกเป็นรูป
              # ==========================================

              if not data:
                  raise RuntimeError(
                      'empty response'
                  )

              if (
                  'text/html' in content_type
                  or
                  'application/json' in content_type
              ):
                  raise RuntimeError(
                      'remote returned '
                      + content_type
                  )


              # ==========================================
              # สร้าง directory
              # ==========================================

              os.makedirs(
                  os.path.dirname(candidate),
                  exist_ok=True
              )


              # ==========================================
              # เขียน temp ก่อน
              # ป้องกัน Thread อื่นอ่านไฟล์ที่ยังโหลดไม่ครบ
              # ==========================================

              temp_file = (
                  candidate
                  + '.download'
                  + str(threading.get_ident())
              )

              with open(
                  temp_file,
                  'wb'
              ) as f:
                  f.write(data)


              os.replace(
                  temp_file,
                  candidate
              )


              print(
                  '[AUTO IMAGE SAVED]',
                  rel,
                  len(data),
                  'bytes'
              )


          except Exception as e:

              print(
                  '[AUTO IMAGE FAILED]',
                  remote_url,
                  repr(e)
              )

              # ลบไฟล์ temp ที่อาจค้าง
              try:
                  temp_prefix = candidate + '.download'

                  folder = os.path.dirname(
                      candidate
                  )

                  if os.path.isdir(folder):

                      for name in os.listdir(folder):

                          full = os.path.join(
                              folder,
                              name
                          )

                          if full.startswith(
                              temp_prefix
                          ):
                              try:
                                  os.remove(full)
                              except:
                                  pass

              except:
                  pass


      # ==================================================
      # หลัง download แล้วยังไม่มี = 404 จริง
      # ==================================================

      if not os.path.isfile(candidate):

          print(
              '[MISSING LOCAL IMAGE]',
              rel,
              candidate
          )

          self.send_error(
              404,
              'File not found'
          )

          return


      # ==================================================
      # MIME
      # ==================================================

      ext = os.path.splitext(
          candidate
      )[1].lower()

      mime_map = {
          '.webp': 'image/webp',
          '.png': 'image/png',
          '.jpg': 'image/jpeg',
          '.jpeg': 'image/jpeg',
          '.gif': 'image/gif',
          '.svg': 'image/svg+xml',
          '.avif': 'image/avif',
      }

      ctype = (
          mime_map.get(ext)
          or
          mimetypes.guess_type(candidate)[0]
          or
          'application/octet-stream'
      )


      # ==================================================
      # ส่งรูป
      # ==================================================

      try:

          size = os.path.getsize(
              candidate
          )

          self.send_response(200)

          self.send_header(
              'Content-Type',
              ctype
          )

          self.send_header(
              'Content-Length',
              str(size)
          )

          # cache browser สั้น ๆ
          self.send_header(
              'Cache-Control',
              'public, max-age=3600'
          )

          self.end_headers()


          if self.command != 'HEAD':

              with open(
                  candidate,
                  'rb'
              ) as f:

                  shutil.copyfileobj(
                      f,
                      self.wfile
                  )


          return


      except (
          BrokenPipeError,
          ConnectionResetError
      ):
          return


      except Exception as e:

          print(
              '[LOCAL IMAGE ERROR]',
              candidate,
              repr(e)
          )

          return
    return SimpleHTTPRequestHandler.do_GET(self)

os.chdir(ROOT)
PORT=int(os.environ.get('PORT','8080'))
print(
    f'JOYPOP Local V5.15 -> '
    f'0.0.0.0:{PORT}'
)

print(
    'Card Rate Admin -> '
    '/rate-admin'
)

print(
    'Infinite Rate Admin -> '
    '/infinite-rate-admin'
)
print('Cabinet 18 album: 17 cards / 11 collected (matched to HAR)')
print('Local Bag V5.5: stack xN, sort price high -> low, checked stack sells all')
print('Real purchases/auth are blocked.')
ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()
