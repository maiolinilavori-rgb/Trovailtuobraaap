from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('import_excel', __name__, url_prefix='/api/import')


"""
Route per import_excel.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

@bp.route('/anteprima', methods=['POST'])
@login_required
def api_import_anteprima():
    file_bracc = trova_file_excel(NOMI_FILE_BRACCIALETTI)
    file_cont = trova_file_excel(NOMI_FILE_CONTATTI)
    anteprima = {'braccialetti': None, 'contatti': None}
    if file_bracc:
        eventi, scuole = analizza_excel_braccialetti(file_bracc)
        anteprima['braccialetti'] = {
            'file': file_bracc, 'n_eventi': len(eventi), 'n_scuole': len(scuole),
            'anteprima_eventi': eventi[:5]
        }
    if file_cont:
        scuole, contatti = analizza_excel_contatti(file_cont)
        anteprima['contatti'] = {
            'file': file_cont, 'n_scuole': len(scuole), 'n_contatti': len(contatti),
            'anteprima_scuole': scuole[:5], 'anteprima_contatti': contatti[:5]
        }
    return jsonify({'success': True, 'anteprima': anteprima})


@bp.route('/applica', methods=['POST'])
@login_required
def api_import_applica():
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400
    riepilogo = applica_import_excel(
        applica_eventi=body.get('eventi', True),
        applica_contatti=body.get('contatti', True)
    )
    return jsonify({'success': True, 'riepilogo': riepilogo})

