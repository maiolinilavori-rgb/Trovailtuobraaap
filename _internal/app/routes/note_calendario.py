from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('note_calendario', __name__, url_prefix='/api')


"""
Route per note_calendario.
ATTENZIONE: gli handler qui sotto usano `@app.route` direttamente.
Devi avvolgerli in `def register(app):` oppure importare `app` da `app/__init__.py`.
Vedi REPORT.md.
"""

from flask import request, jsonify, render_template_string
from datetime import datetime

# Alias di lettura per il dizionario globale
dati = storage.get_dati()

@bp.route('/note_calendario', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_note_calendario():
    if request.method == 'GET':
        return jsonify(dati.get('note_calendario', []))
    if request.method == 'POST':
        try:
            n = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        n['id'] = _nuovo_id()
        storage.get_dati()['note_calendario'].append(n)
        storage.salva()
        return jsonify({'success': True, 'id': n['id']})
    if request.method == 'PUT':
        try:
            n = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        for i, x in enumerate(storage.get_dati()['note_calendario']):
            if x.get('id') == n.get('id'):
                storage.get_dati()['note_calendario'][i] = n
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False}), 404
    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['note_calendario'] = [n for n in storage.get_dati()['note_calendario'] if n.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})


@bp.route('/note_personali', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_note_personali():
    dati.setdefault('note_personali', {})
    if request.method == 'GET':
        return jsonify(storage.get_dati()['note_personali'].get(request.args.get('contesto', ''), []))
    if request.method == 'POST':
        try:
            body = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        contesto = body.get('contesto')
        testo = (body.get('testo') or '').strip()
        if not contesto or not testo:
            return jsonify({'success': False}), 400
        nota = {'id': _nuovo_id(), 'testo': testo,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M')}
        storage.get_dati()['note_personali'].setdefault(contesto, []).append(nota)
        storage.salva()
        return jsonify({'success': True, 'nota': nota})
    if request.method == 'DELETE':
        contesto = request.args.get('contesto', '')
        nota_id = request.args.get('id', type=int)
        if contesto in storage.get_dati()['note_personali']:
            storage.get_dati()['note_personali'][contesto] = [
                n for n in storage.get_dati()['note_personali'][contesto] if n.get('id') != nota_id]
            storage.salva()
        return jsonify({'success': True})

