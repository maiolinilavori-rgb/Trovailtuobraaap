from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('portafoglio', __name__, url_prefix='/api/portafoglio')


"""
Route per portafoglio.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_portafoglio():
    dati.setdefault('portafoglio', [])
    if request.method == 'GET':
        return jsonify(storage.get_dati()['portafoglio'])
    if request.method == 'POST':
        try:
            t = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        t['id'] = _nuovo_id()
        storage.get_dati()['portafoglio'].append(t)
        storage.salva()
        return jsonify({'success': True, 'id': t['id']})
    if request.method == 'PUT':
        try:
            t = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        for i, x in enumerate(storage.get_dati()['portafoglio']):
            if x.get('id') == t.get('id'):
                storage.get_dati()['portafoglio'][i] = t
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False}), 404
    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['portafoglio'] = [x for x in storage.get_dati()['portafoglio'] if x.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})

