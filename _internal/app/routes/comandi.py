from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('comandi', __name__, url_prefix='/api/comandi')


"""
Route per comandi.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

@bp.route('', methods=['POST'])
@login_required
def api_comandi():
    """Comandi batch: ricalcola_stock, azzera_movimenti_precedenti_a_DATA,
    sposta_eventi_senza_scuola_in_ALTRO, unifica_scuola_X_in_Y, ..."""
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400
    testo = body.get('comandi', '') or ''
    log_esec = []
    righe = [r.strip() for r in testo.split('\n') if r.strip() and not r.strip().startswith('#')]

    for riga in righe:
        rl = riga.lower()
        try:
            if rl == 'ricalcola_stock':
                s = ricalcola_stock()
                log_esec.append('✅ Stock ricalcolato: ' + ', '.join(f'{k}={v}' for k, v in s.items()))
            elif rl.startswith('azzera_movimenti_precedenti_a_'):
                data_str = riga[len('azzera_movimenti_precedenti_a_'):]
                d = _parse_data(data_str)
                if not d:
                    log_esec.append(f'⚠️ Data non valida: {data_str}')
                    continue
                tot = 0
                for cat in storage.get_dati()['movimenti']:
                    prima = len(storage.get_dati()['movimenti'][cat])
                    storage.get_dati()['movimenti'][cat] = [
                        m for m in storage.get_dati()['movimenti'][cat]
                        if _parse_data(m.get('data')) and _parse_data(m['data']) >= d]
                    tot += prima - len(storage.get_dati()['movimenti'][cat])
                ricalcola_stock()
                log_esec.append(f'✅ Rimossi {tot} movimenti precedenti a {data_str}')
            elif rl == 'sposta_eventi_senza_scuola_in_altro':
                n = 0
                for e in storage.get_dati()['eventi']:
                    if e.get('scuola_id'):
                        continue
                    n += 1
                log_esec.append(f'✅ {n} eventi già in ALTRO')
            else:
                log_esec.append(f'❓ Comando non riconosciuto: {riga}')
        except Exception as ex:
            log_esec.append(f'❌ Errore su "{riga}": {ex}')
    if righe:
        storage.salva()
    return jsonify({'success': True, 'log': log_esec})

