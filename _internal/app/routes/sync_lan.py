from __future__ import annotations
import base64, json, shutil, socket, time, urllib.request, urllib.parse
from flask import Blueprint, jsonify, request
from app import storage
from app.auth import login_required
from app.config import DATA_DIR, DATA_FILE, BACKUP_DIR, PASSWORD_DEFAULT

bp = Blueprint('sync_lan', __name__, url_prefix='/api/sync-lan')
SYNC_TOKEN = f"BRAAAP_LAN_{PASSWORD_DEFAULT}"

def _mio_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return "127.0.0.1"

def _lista_media() -> dict:
    res = {}
    for sub in ("foto", "video", "logo"):
        d = DATA_DIR / sub
        if d.exists():
            for f in d.iterdir():
                if f.is_file(): res[f"{sub}/{f.name}"] = f.stat().st_size
    return res

def _merge(loc: dict, rem: dict) -> dict:
    if DATA_FILE.exists(): shutil.copy2(DATA_FILE, BACKUP_DIR / f"pre_sync_{time.strftime('%Y%m%d_%H%M%S')}.json")
    u = json.loads(json.dumps(loc))
    for k in ("eventi", "altro", "entrate", "uscite", "portafoglio", "scuole", "rubrica", "inventario", "entita", "task", "liste", "note_calendario", "note_vocali", "postit"):
        m = {str(x.get("id")) if x.get("id") is not None else json.dumps(x, sort_keys=True): x for x in u.get(k, [])}
        for x in rem.get(k, []):
            key = str(x.get("id")) if x.get("id") is not None else json.dumps(x, sort_keys=True)
            if key not in m or len(json.dumps(x)) >= len(json.dumps(m[key])): m[key] = x
        u[k] = list(m.values())
    ml, mr = u.setdefault("movimenti", {}), rem.get("movimenti", {})
    for c in ("braccialetti", "medaglie", "adesivi", "coppe"):
        mc = {str(x.get("id")): x for x in ml.get(c, []) if x.get("id") is not None}
        for x in mr.get(c, []):
            if x.get("id") is not None: mc[str(x.get("id"))] = x
        ml[c] = list(mc.values())
        u.setdefault("stock", {})[c] = sum(int(x.get("quantita") or 0) if x.get("tipo") == "carico" else -int(x.get("quantita") or 0) for x in ml[c])
    return u

@bp.route('/info', methods=['GET'])
def api_info(): return jsonify({"app": "BRAAAP", "hostname": socket.gethostname(), "ip": _mio_ip()})

@bp.route('/pacchetto', methods=['GET', 'POST'])
def api_pacchetto():
    if request.headers.get("X-Sync-Token") != SYNC_TOKEN: return jsonify({"success": False}), 403
    if request.method == "GET":
        storage.salva(); return jsonify({"success": True, "hostname": socket.gethostname(), "dati": storage.get_dati(), "media": _lista_media()})
    nd = (request.get_json(force=True) or {}).get("dati")
    if isinstance(nd, dict):
        if DATA_FILE.exists(): shutil.copy2(DATA_FILE, BACKUP_DIR / f"pre_sync_rem_{time.strftime('%Y%m%d_%H%M%S')}.json")
        dc = storage.get_dati(); dc.clear(); dc.update(nd); storage.salva()
    return jsonify({"success": True})

@bp.route('/media-file', methods=['GET', 'POST'])
def api_media():
    if request.headers.get("X-Sync-Token") != SYNC_TOKEN: return jsonify({"success": False}), 403
    if request.method == "GET":
        t = (DATA_DIR / request.args.get("path", "")).resolve()
        return jsonify({"success": True, "b64": base64.b64encode(t.read_bytes()).decode("ascii")}) if t.is_relative_to(DATA_DIR.resolve()) and t.is_file() else (jsonify({"success": False}), 404)
    b = request.get_json(force=True) or {}; t = (DATA_DIR / b.get("path", "")).resolve()
    if t.is_relative_to(DATA_DIR.resolve()) and b.get("b64"):
        t.parent.mkdir(parents=True, exist_ok=True); t.write_bytes(base64.b64decode(b["b64"])); return jsonify({"success": True})
    return jsonify({"success": False}), 400

@bp.route('/esegui', methods=['POST'])
@login_required
def api_esegui():
    h = ((request.get_json(force=True) or {}).get("host") or "").strip()
    if not h: return jsonify({"success": False, "error": "Inserisci IP o Nome PC Fisso"}), 400
    url = h if h.startswith("http") else f"http://{h}:5000"
    hdr = {"X-Sync-Token": SYNC_TOKEN, "Content-Type": "application/json"}
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{url}/api/sync-lan/pacchetto", headers=hdr), timeout=6) as r: rem = json.loads(r.read().decode("utf-8"))
        storage.salva(); uniti = _merge(storage.get_dati(), rem.get("dati", {}))
        ml, mr, tr = _lista_media(), rem.get("media", {}), 0
        for rel in mr:
            if rel not in ml:
                with urllib.request.urlopen(urllib.request.Request(f"{url}/api/sync-lan/media-file?path={urllib.parse.quote(rel)}", headers=hdr), timeout=15) as rm:
                    jm = json.loads(rm.read().decode("utf-8"))
                    if jm.get("success") and jm.get("b64"):
                        dst = DATA_DIR / rel; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(base64.b64decode(jm["b64"])); tr += 1
        for rel in ml:
            if rel not in mr:
                pl = json.dumps({"path": rel, "b64": base64.b64encode((DATA_DIR / rel).read_bytes()).decode("ascii")}).encode("utf-8")
                with urllib.request.urlopen(urllib.request.Request(f"{url}/api/sync-lan/media-file", data=pl, headers=hdr, method="POST"), timeout=15): tr += 1
        dc = storage.get_dati(); dc.clear(); dc.update(uniti); storage.salva()
        with urllib.request.urlopen(urllib.request.Request(f"{url}/api/sync-lan/pacchetto", data=json.dumps({"dati": uniti}, ensure_ascii=False).encode("utf-8"), headers=hdr, method="POST"), timeout=15): pass
        return jsonify({"success": True, "remoto": rem.get("hostname", h), "media_sincronizzati": tr})
    except Exception as e:
        return jsonify({"success": False, "error": f"PC Fisso non raggiungibile ({e})."})

