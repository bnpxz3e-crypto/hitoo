import json
import os
import shutil
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent

HAR_FILE = ROOT / 'joypop115.gg.har'
REPLAY_FILE = ROOT / 'replay_v5.json'

if not HAR_FILE.exists():
    raise SystemExit(
        f'ไม่พบไฟล์ {HAR_FILE.name}\n'
        f'ให้นำ joypop115.gg(1).har มาไว้ที่ {ROOT}'
    )

if not REPLAY_FILE.exists():
    raise SystemExit('ไม่พบ replay_v5.json')


# ============================================================
# LOAD
# ============================================================

print('Loading replay_v5.json ...')

replay = json.loads(
    REPLAY_FILE.read_text(
        encoding='utf-8'
    )
)

print(
    'Current replay entries:',
    len(replay)
)

print()
print('Loading HAR ...')

har = json.loads(
    HAR_FILE.read_text(
        encoding='utf-8'
    )
)

entries = (
    har
    .get('log', {})
    .get('entries', [])
)

print(
    'HAR entries:',
    len(entries)
)


# ============================================================
# HELPERS
# ============================================================

def decode_response(entry):

    content = (
        entry
        .get('response', {})
        .get('content', {})
    )

    text = content.get('text')

    if not text:
        return None

    encoding = str(
        content.get('encoding')
        or ''
    ).lower()

    if encoding == 'base64':

        try:
            import base64

            text = base64.b64decode(
                text
            ).decode(
                'utf-8',
                errors='replace'
            )

        except Exception:
            return None

    try:
        return json.loads(text)

    except Exception:
        return None


def request_params(entry):

    req = entry.get(
        'request',
        {}
    )

    result = {}

    # --------------------------------------------------------
    # QUERY STRING
    # --------------------------------------------------------

    for q in req.get(
        'queryString',
        []
    ):

        name = str(
            q.get('name')
            or ''
        )

        value = str(
            q.get('value')
            or ''
        )

        if name:
            result[name] = value


    # --------------------------------------------------------
    # POST DATA
    # --------------------------------------------------------

    post = req.get(
        'postData',
        {}
    )

    # HAR params
    for q in post.get(
        'params',
        []
    ):

        name = str(
            q.get('name')
            or ''
        )

        value = str(
            q.get('value')
            or ''
        )

        if name:
            result[name] = value


    text = post.get(
        'text'
    )

    if text:

        mime = str(
            post.get('mimeType')
            or ''
        ).lower()

        # JSON
        if (
            'json' in mime
            or text.lstrip().startswith('{')
        ):

            try:

                obj = json.loads(
                    text
                )

                if isinstance(
                    obj,
                    dict
                ):

                    for k, v in obj.items():

                        if v is None:
                            continue

                        if isinstance(
                            v,
                            (dict, list)
                        ):
                            continue

                        result[str(k)] = str(v)

            except Exception:
                pass

        # form-urlencoded
        try:

            form = urllib.parse.parse_qs(
                text,
                keep_blank_values=True
            )

            for k, values in form.items():

                if values:
                    result[str(k)] = str(
                        values[-1]
                    )

        except Exception:
            pass

    return result


def make_key(path, params):

    # ให้ key ตรงรูปแบบ replay_v5.json เดิม

    if not params:
        return path + '|'

    # endpoint ที่ order ของ parameter สำคัญกับ replay เดิม
    preferred = {

        '/api/infinite/detail': [
            'goods_id',
            'play_type'
        ],

        '/api/infinite/king': [
            'goods_id',
            'type',
            'play_type'
        ],

        '/api/infinite/ranking_list': [
            'goods_id',
            'play_type'
        ],

        '/api/infinite/shang_log': [
            'goods_id',
            'play_type',
            'show_type'
        ],

        '/api/infinite/shang_logs': [
            'goods_id',
            'limit',
            'page',
            'play_type',
            'shang_id'
        ],

        '/api/index/index_goods': [
            'category_id',
            'page',
            'type'
        ]
    }

    order = preferred.get(
        path
    )

    parts = []

    used = set()

    if order:

        for k in order:

            if k in params:

                parts.append(
                    (
                        k,
                        params[k]
                    )
                )

                used.add(k)

    for k in sorted(params):

        if k in used:
            continue

        parts.append(
            (
                k,
                params[k]
            )
        )

    query = urllib.parse.urlencode(
        parts
    )

    return path + '|' + query


# ============================================================
# IMPORT
# ============================================================

interesting = {

    '/api/infinite/detail',
    '/api/infinite/king',
    '/api/infinite/ranking_list',
    '/api/infinite/shang_log',
    '/api/infinite/shang_logs',

    '/api/index/index_goods',
    '/api/index/inigoods_category'
}


imported = 0

details = {}
kings = {}
demon_ids = set()

for i, entry in enumerate(
    entries
):

    req = entry.get(
        'request',
        {}
    )

    url = str(
        req.get('url')
        or ''
    )

    try:

        parsed = urllib.parse.urlparse(
            url
        )

        path = parsed.path

    except Exception:
        continue

    if path not in interesting:
        continue


    response = decode_response(
        entry
    )

    if not isinstance(
        response,
        dict
    ):
        continue


    params = request_params(
        entry
    )

    # query จาก URL เผื่อ HAR ไม่ได้ใส่ queryString
    try:

        qs = urllib.parse.parse_qs(
            parsed.query,
            keep_blank_values=True
        )

        for k, values in qs.items():

            if (
                k not in params
                and values
            ):
                params[k] = values[-1]

    except Exception:
        pass


    key = make_key(
        path,
        params
    )

    replay[key] = response

    imported += 1


    # ========================================================
    # DETAIL
    # ========================================================

    if path == '/api/infinite/detail':

        gid = str(
            params.get(
                'goods_id'
            )
            or ''
        )

        if gid:

            data = response.get(
                'data'
            ) or {}

            goods = data.get(
                'goods'
            ) or {}

            prizes = (
                data.get(
                    'goodslist_all'
                )
                or []
            )

            has_demon = False

            for item in prizes:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                try:
                    sid = int(
                        item.get(
                            'shang_id'
                        )
                        or 0
                    )
                except Exception:
                    sid = 0

                title = str(
                    item.get(
                        'shang_title'
                    )
                    or ''
                ).strip().upper()

                if (
                    sid == 98
                    or title == 'DEMON'
                    or title == '魔王赏'
                ):

                    has_demon = True
                    break


            details[gid] = {

                'title':
                    goods.get(
                        'title'
                    )
                    or '',

                'price':
                    goods.get(
                        'price'
                    )
                    or 0,

                'play_type':
                    goods.get(
                        'play_type'
                    ),

                'prizes':
                    len(prizes),

                'demon':
                    has_demon
            }

            if has_demon:

                demon_ids.add(
                    gid
                )


    # ========================================================
    # KING
    # ========================================================

    elif path == '/api/infinite/king':

        gid = str(
            params.get(
                'goods_id'
            )
            or ''
        )

        if gid:

            kings[gid] = response


# ============================================================
# BACKUP
# ============================================================

backup = ROOT / 'replay_v5.before_demon_all.json'

shutil.copy2(
    REPLAY_FILE,
    backup
)


# ============================================================
# SAVE
# ============================================================

tmp = ROOT / 'replay_v5.json.tmp'

tmp.write_text(
    json.dumps(
        replay,
        ensure_ascii=False,
        indent=2
    ),
    encoding='utf-8'
)

os.replace(
    tmp,
    REPLAY_FILE
)


# ============================================================
# REPORT
# ============================================================

print()
print('=' * 70)
print('IMPORT COMPLETE')
print('=' * 70)

print(
    'Imported API responses:',
    imported
)

print(
    'Replay entries now:',
    len(replay)
)

print(
    'Backup:',
    backup.name
)

print()

print(
    '===== ALL INFINITE DETAIL FROM HAR ====='
)

for gid in sorted(
    details,
    key=lambda x:
        int(x)
        if x.isdigit()
        else x
):

    d = details[gid]

    print(
        f'gid={gid:>4}',
        f'play={str(d["play_type"]):>3}',
        f'price={str(d["price"]):>8}',
        f'prizes={d["prizes"]:>3}',
        f'DEMON={"YES" if d["demon"] else "NO "}',
        '|',
        d['title']
    )


print()
print(
    '===== DEMON CABINETS ====='
)

if demon_ids:

    print(
        ', '.join(
            sorted(
                demon_ids,
                key=lambda x:
                    int(x)
                    if x.isdigit()
                    else x
            )
        )
    )

else:

    print(
        'ไม่พบ shang_id=98 '
        'ใน detail ของ HAR'
    )


print()
print(
    '===== KING API CABINETS ====='
)

if kings:

    print(
        ', '.join(
            sorted(
                kings,
                key=lambda x:
                    int(x)
                    if x.isdigit()
                    else x
            )
        )
    )

else:

    print(
        'HAR ไม่มี /api/infinite/king'
    )
