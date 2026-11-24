from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('entita', __name__, url_prefix='/api')


"""
Route per entita.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('/entita', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_entita():
    dati.setdefault('entita', [])
    if request.method == 'GET':
        return jsonify(storage.get_dati()['entita'])
    if request.method == 'POST':
        try:
            e = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        e['id'] = _nuovo_id()
        e['creato_il'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        storage.get_dati()['entita'].append(e)
        storage.salva()
        return jsonify({'success': True, 'id': e['id']})
    if request.method == 'PUT':
        try:
            e = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        for i, x in enumerate(storage.get_dati()['entita']):
            if x.get('id') == e.get('id'):
                storage.get_dati()['entita'][i] = e
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False}), 404
    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['entita'] = [x for x in storage.get_dati()['entita'] if x.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})


@bp.route('/categorie_entita', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_categorie_entita():
    dati.setdefault('categorie_entita', ['Mezzi', 'Attrezzatura', 'Materiale informativo', 'Altro'])
    if request.method == 'GET':
        return jsonify(storage.get_dati()['categorie_entita'])
    if request.method == 'POST':
        try:
            body = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        nome = (body.get('nome') or '').strip()
        if nome and nome not in storage.get_dati()['categorie_entita']:
            storage.get_dati()['categorie_entita'].append(nome)
            storage.salva()
        return jsonify({'success': True, 'categorie': storage.get_dati()['categorie_entita']})
    if request.method == 'DELETE':
        nome = request.args.get('nome', '')
        if nome in storage.get_dati()['categorie_entita']:
            storage.get_dati()['categorie_entita'].remove(nome)
            storage.salva()
        return jsonify({'success': True})

