from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
import time
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('postit', __name__, url_prefix='/api/postit')


"""
Route per postit.
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
def api_postit():
    dati.setdefault('postit', [])
    if request.method == 'GET':
        return jsonify(storage.get_dati()['postit'])
    if request.method == 'POST':
        try:
            p = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        p['id'] = _nuovo_id()
        p['creato_il'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        if 'colore' not in p:
            p['colore'] = 'giallo'
        if 'rotazione' not in p:
            p['rotazione'] = (time.time_ns() % 7) - 3  # -3..+3
        storage.get_dati()['postit'].append(p)
        storage.salva()
        return jsonify({'success': True, 'id': p['id'], 'postit': p})
    if request.method == 'PUT':
        try:
            p = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        for i, x in enumerate(storage.get_dati()['postit']):
            if x.get('id') == p.get('id'):
                storage.get_dati()['postit'][i] = p
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False}), 404
    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['postit'] = [p for p in storage.get_dati()['postit'] if p.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})

