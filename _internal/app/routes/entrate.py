"""Route per gestione entrate."""
from __future__ import annotations
from datetime import datetime
from flask import Blueprint, request, jsonify
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero

bp = Blueprint('entrate', __name__, url_prefix='/api/entrate')


@bp.route('', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_entrate():
    if request.method == 'GET':
        return jsonify(storage.get_dati().get('entrate', []))

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400

    entrate = storage.get_dati().setdefault('entrate', [])

    if request.method == 'POST':
        nuova = {
            'id': _nuovo_id(),
            'data': body.get('data', datetime.now().strftime('%Y-%m-%d')),
            'descrizione': (body.get('descrizione') or '').strip(),
            'importo': float(body.get('importo') or 0),
            'tipo': body.get('tipo', 'contributo'),
            'evento_id': _intero(body.get('evento_id')) if body.get('evento_id') else None,
            'note': (body.get('note') or '').strip(),
            'fonte': 'manuale',
        }
        if not nuova['descrizione']:
            return jsonify({'success': False, 'error': 'Descrizione richiesta'}), 400
        if nuova['importo'] <= 0:
            return jsonify({'success': False, 'error': 'Importo > 0 richiesto'}), 400
        entrate.append(nuova)
        storage.salva()
        return jsonify({'success': True, 'id': nuova['id']})

    if request.method == 'PUT':
        for i, e in enumerate(entrate):
            if e.get('id') == _intero(body.get('id')):
                e['data'] = body.get('data', e.get('data'))
                e['descrizione'] = (body.get('descrizione') or e.get('descrizione', '')).strip()
                e['importo'] = float(body.get('importo') or e.get('importo', 0))
                e['tipo'] = body.get('tipo', e.get('tipo', 'contributo'))
                e['evento_id'] = _intero(body.get('evento_id')) if body.get('evento_id') else None
                e['note'] = (body.get('note') or '').strip()
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Entrata non trovata'}), 404

    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['entrate'] = [e for e in entrate if e.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})