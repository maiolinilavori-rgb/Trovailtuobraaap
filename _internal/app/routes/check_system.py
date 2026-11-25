"""Modulo di Autoanalisi, Diagnostica e Autoriparazione (Check System)."""
from __future__ import annotations
import json
import py_compile
import shutil
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request
from groq import Groq
from app import storage, backup
from app.auth import login_required
from app.config import APP_DIR, DATA_FILE, LOG_FILE, GROQ_API_KEY, GROQ_MODELLO_LLM

bp = Blueprint('check_system', __name__, url_prefix='/api/check-system')


def _controlla_sintassi_py():
    errori = []
    tot_file = 0
    for pyf in sorted(APP_DIR.rglob('*.py')):
        tot_file += 1
        try:
            py_compile.compile(str(pyf), doraise=True)
        except Exception as e:
            errori.append(f"{pyf.name}: {e}")
    return tot_file, errori


def _autoripara_dati():
    d = storage.get_dati()
    riparazioni = []

    # 1. Backup preventivo prima di toccare i dati
    meta = backup._crea_backup(etichetta='pre_check_system', forza_cloud=False)
    if meta:
        riparazioni.append(f"Creato punto di ripristino preventivo: {meta['file']}")

    # 2. Ripara ID mancanti o duplicati in tutte le liste
    sezioni = ('eventi', 'scuole', 'altro', 'rubrica', 'task', 'postit',
               'note_calendario', 'liste', 'note_vocali', 'entrate', 'uscite',
               'portafoglio', 'inventario', 'entita')
    for sez in sezioni:
        lista = d.get(sez)
        if not isinstance(lista, list):
            d[sez] = []
            riparazioni.append(f"Ricreata lista mancante '{sez}'")
            continue
        visti = set()
        max_id = max((int(x.get('id') or 0) for x in lista if isinstance(x, dict)), default=0)
        for item in lista:
            if not isinstance(item, dict):
                continue
            iid = item.get('id')
            if iid is None or iid in visti:
                max_id += 1
                item['id'] = max_id
                riparazioni.append(f"Assegnato nuovo ID #{max_id} univoco in '{sez}'")
            visti.add(item['id'])

    # 3. Riallinea stock magazzino dai movimenti reali
    stock = d.setdefault('stock', {})
    movimenti = d.setdefault('movimenti', {})
    for cat in ('braccialetti', 'medaglie', 'adesivi', 'coppe'):
        movs = movimenti.setdefault(cat, [])
        tot = 0
        for m in movs:
            try:
                q = int(float(m.get('quantita') or 0))
            except Exception:
                q = 0
                m['quantita'] = 0
            tot += q if m.get('tipo') == 'carico' else -q
        vecchio = int(stock.get(cat) or 0)
        if vecchio != tot:
            stock[cat] = tot
            riparazioni.append(f"Riallineato stock '{cat}': {vecchio} -> {tot}")

    if len(riparazioni) > 1:
        storage.salva_dati(d, crea_backup=False)
    return riparazioni


def _leggi_ultimi_errori_log(max_righe=60):
    if not LOG_FILE.exists():
        return ''
    try:
        righe = LOG_FILE.read_text(encoding='utf-8', errors='replace').splitlines()
        blocchi = []
        in_err = False
        for r in righe[-250:]:
            if '| ERROR' in r or '| CRITICAL' in r or 'Traceback (most recent call last)' in r:
                in_err = True
            if in_err:
                blocchi.append(r)
                if '| INFO' in r and 'Traceback' not in r:
                    in_err = False
        return '\n'.join(blocchi[-max_righe:])
    except Exception:
        return ''


def _analisi_ai_log(estratto_log: str):
    if not estratto_log.strip():
        return 'Nessun errore recente rilevato nei log di sistema. Il motore funziona regolarmente.'
    if not GROQ_API_KEY:
        return 'Errore rilevato nel log, ma GROQ_API_KEY non configurata per l\'analisi AI automatica.'
    try:
        client = Groq(api_key=GROQ_API_KEY, timeout=20.0)
        prompt = (
            "Sei l'ingegnere di auto-riparazione del gestionale Python/Flask 'Braaap'. "
            "Analizza questo estratto del log errori e rispondi in italiano chiaro e sintetico (max 6 righe):\n"
            "1) Cosa ha causato l'errore;\n"
            "2) Se riguarda file e riga specifici;\n"
            "3) Cosa fare per risolverlo in sicurezza.\n\n"
            f"LOG:\n{estratto_log}"
        )
        res = client.chat.completions.create(
            model=GROQ_MODELLO_LLM,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1,
            max_tokens=450,
        )
        return (res.choices[0].message.content or '').strip()
    except Exception as e:
        return f'Analisi AI non disponibile al momento ({e}).'


@bp.route('/esegui', methods=['POST'])
@login_required
def api_esegui_check():
    tot_py, err_py = _controlla_sintassi_py()
    riparazioni = _autoripara_dati()
    estratto_log = _leggi_ultimi_errori_log()
    analisi_ai = _analisi_ai_log(estratto_log)
    free_gb = round(shutil.disk_usage(DATA_FILE.parent).free / (1024 ** 3), 2)
    backups = backup._lista_backup()

    stato_ok = (len(err_py) == 0)
    return jsonify({
        'success': True,
        'stato_ok': stato_ok,
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'file_python_controllati': tot_py,
        'errori_sintassi': err_py,
        'riparazioni_dati': riparazioni,
        'spazio_libero_gb': free_gb,
        'numero_backup': len(backups),
        'ultimo_backup': backups[0]['file'] if backups else None,
        'analisi_ai': analisi_ai,
        'log_grezzo': estratto_log,
    })


@bp.route('/ripristina-ultimo', methods=['POST'])
@login_required
def api_ripristina_ultimo():
    backups = backup._lista_backup()
    sani = [b for b in backups if b.get('etichetta') != 'pre_check_system'] or backups
    if not sani:
        return jsonify({'success': False, 'error': 'Nessun backup disponibile'}), 404
    ok, msg = backup._ripristina_backup(sani[0]['file'])
    return jsonify({'success': ok, 'messaggio': msg})
