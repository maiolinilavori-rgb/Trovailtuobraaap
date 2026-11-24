from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.import_excel import trova_file_excel
from app.config import NOMI_FILE_BRACCIALETTI, NOMI_FILE_CONTATTI
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('primo_avvio', __name__, url_prefix='/api/primo_avvio')


"""
Route per primo_avvio.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('/giacenza', methods=['POST'])
@login_required
def api_primo_avvio_giacenza():
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False, 'error': 'JSON non valido'}), 400
    bracc = _intero(body.get('braccialetti'))
    med = _intero(body.get('medaglie'))
    ades = _intero(body.get('adesivi'))
    coppe = _intero(body.get('coppe'))
    carichi_extra = body.get('carichi_extra', [])
    oggi = datetime.now().strftime('%Y-%m-%d')

    if bracc > 0:
        storage.get_dati()['movimenti']['braccialetti'] = [{
            'id': _nuovo_id(), 'tipo': 'carico', 'quantita': bracc,
            'motivo': 'Giacenza iniziale dichiarata', 'nota_carico': '', 'data': oggi
        }]
    if med > 0:
        storage.get_dati()['movimenti']['medaglie'] = [{
            'id': _nuovo_id(), 'tipo': 'carico', 'quantita': med,
            'motivo': 'Giacenza iniziale dichiarata', 'nota_carico': '', 'data': oggi
        }]
    if ades > 0:
        storage.get_dati()['movimenti']['adesivi'] = [{
            'id': _nuovo_id(), 'tipo': 'carico', 'quantita': ades,
            'motivo': 'Giacenza iniziale dichiarata', 'nota_carico': '', 'data': oggi
        }]
    if coppe > 0:
        storage.get_dati()['movimenti']['coppe'] = [{
            'id': _nuovo_id(), 'tipo': 'carico', 'quantita': coppe,
            'motivo': 'Giacenza iniziale dichiarata', 'nota_carico': '', 'data': oggi
        }]

    for ce in carichi_extra:
        cat = ce.get('categoria')
        q = _intero(ce.get('quantita'))
        if cat in CATEGORIE_MAGAZZINO_NOTE and q > 0:
            storage.get_dati()['movimenti'][cat].append({
                'id': _nuovo_id(), 'tipo': 'carico', 'quantita': q,
                'motivo': ce.get('descrizione', 'Carico storico'),
                'nota_carico': '', 'data': ce.get('data', oggi)
            })

    storage.get_dati()['giacenza_iniziale_impostata'] = True
    storage.get_dati()['giacenza_iniziale_data'] = oggi
    ricalcola_stock()
    storage.salva()

    auto_import = {'fatto': False}
    if not dati.get('import_excel_fatto', False):
        file_b = trova_file_excel(NOMI_FILE_BRACCIALETTI)
        file_c = trova_file_excel(NOMI_FILE_CONTATTI)
        if file_b or file_c:
            try:
                riepilogo = applica_import_excel(applica_eventi=True, applica_contatti=True)
                auto_import = {'fatto': True, 'riepilogo': riepilogo}
                log.info('Auto-import: %s', riepilogo)
            except Exception as e:
                log.exception('Errore auto-import')
                auto_import = {'fatto': False, 'errore': str(e)}

    return jsonify({'success': True, 'stock': storage.get_dati()['stock'], 'auto_import': auto_import})


@bp.route('/stato')
@login_required
def api_primo_avvio_stato():
    return jsonify({
        'giacenza_iniziale_impostata': dati.get('giacenza_iniziale_impostata', False),
        'import_excel_fatto': dati.get('import_excel_fatto', False),
        'file_braccialetti_trovato': bool(trova_file_excel(NOMI_FILE_BRACCIALETTI)),
        'file_contatti_trovato': bool(trova_file_excel(NOMI_FILE_CONTATTI)),
    })

