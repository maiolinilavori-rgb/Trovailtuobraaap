from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('manutenzione', __name__, url_prefix='/api/manutenzione')


"""
Route per manutenzione.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('/azzera_eventi', methods=['POST'])
def api_azzera_eventi():
    """
    Azzera SOLO la lista eventi.
    - Backup automatico su file PRIMA di cancellare
    - Richiede conferma esplicita nel body: {"conferma": "AZZERA_SOLO_EVENTI"}
    - NON tocca scuole, stock, rubrica, task, entita, movimenti, note vocali,
      postit, liste, inventario, portafoglio, note calendario.
    """
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'JSON non valido'}), 400

    if body.get('conferma') != 'AZZERA_SOLO_EVENTI':
        return jsonify({
            'success': False,
            'error': 'Conferma mancante. Passa {"conferma": "AZZERA_SOLO_EVENTI"}'
        }), 400

    n_prima = len(dati.get('eventi', []))

    # Backup automatico su file (in DATA_DIR / backups se esiste, altrimenti accanto al file dati)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    try:
        backup_base = os.path.join(DATA_DIR, 'backups')
        if not os.path.isdir(backup_base):
            backup_base = DATA_DIR
    except Exception:
        backup_base = os.path.dirname(DATA_FILE) or '.'
    backup_path = os.path.join(backup_base, f'braaap_data_PRE_AZZERA_EVENTI_{ts}.json')

    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(dati, f, indent=2, default=str, ensure_ascii=False)
        log.info('Backup pre-azzeramento salvato: %s', backup_path)
    except Exception as e:
        log.error('Backup pre-azzeramento fallito: %s', e)
        return jsonify({
            'success': False,
            'error': f'Backup fallito, azzeramento annullato per sicurezza: {e}'
        }), 500

    # Azzera SOLO gli eventi
    storage.get_dati()['eventi'] = []
    storage.salva()

    log.info('Azzerati %d eventi. Backup: %s', n_prima, backup_path)
    return jsonify({
        'success': True,
        'eventi_cancellati': n_prima,
        'backup_salvato': backup_path,
        'stock_invariato': dati.get('stock', {}),
        'scuole_invariate': len(dati.get('scuole', [])),
        'rubrica_invariata': len(dati.get('rubrica', [])),
    })

