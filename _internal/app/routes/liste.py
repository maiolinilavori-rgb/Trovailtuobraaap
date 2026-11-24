from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('liste', __name__, url_prefix='/api/liste')


"""
Route per liste.
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
def api_liste():
    dati.setdefault('liste', [])
    if request.method == 'GET':
        return jsonify(storage.get_dati()['liste'])
    if request.method == 'POST':
        try:
            l = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        l['id'] = _nuovo_id()
        l['creato_il'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        l.setdefault('prodotti', [])
        for prod in l['prodotti']:
            if 'id' not in prod:
                prod['id'] = _nuovo_id()
        storage.get_dati()['liste'].append(l)
        storage.salva()
        return jsonify({'success': True, 'id': l['id']})
    if request.method == 'PUT':
        try:
            l = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        for i, x in enumerate(storage.get_dati()['liste']):
            if x.get('id') == l.get('id'):
                for prod in l.get('prodotti', []):
                    if 'id' not in prod:
                        prod['id'] = _nuovo_id()
                storage.get_dati()['liste'][i] = l
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False}), 404
    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['liste'] = [l for l in storage.get_dati()['liste'] if l.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})

