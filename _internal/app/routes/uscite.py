"""Route per gestione uscite generiche (categoria: altro)."""
from __future__ import annotations
from datetime import datetime
from flask import Blueprint, request, jsonify
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero

bp = Blueprint('uscite', __name__, url_prefix='/api/uscite')


@bp.route('', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_uscite():
    if request.method == 'GET':
        return jsonify(storage.get_dati().get('uscite', []))

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400

    uscite = storage.get_dati().setdefault('uscite', [])

    if request.method == 'POST':
        nuova = {
            'id': _nuovo_id(),
            'data': body.get('data', datetime.now().strftime('%Y-%m-%d')),
            'descrizione': (body.get('descrizione') or '').strip(),
            'importo': float(body.get('importo') or 0),
            'categoria': body.get('categoria', 'generale'),
            'fornitore': (body.get('fornitore') or '').strip(),
            'evento_id': _intero(body.get('evento_id')) if body.get('evento_id') else None,
            'note': (body.get('note') or '').strip(),
            'fonte': 'manuale',
        }
        if not nuova['descrizione']:
            return jsonify({'success': False, 'error': 'Descrizione richiesta'}), 400
        if nuova['importo'] <= 0:
            return jsonify({'success': False, 'error': 'Importo > 0 richiesto'}), 400
        uscite.append(nuova)
        storage.salva()
        return jsonify({'success': True, 'id': nuova['id']})

    if request.method == 'PUT':
        for i, u in enumerate(uscite):
            if u.get('id') == _intero(body.get('id')):
                u['data'] = body.get('data', u.get('data'))
                u['descrizione'] = (body.get('descrizione') or u.get('descrizione', '')).strip()
                u['importo'] = float(body.get('importo') or u.get('importo', 0))
                u['categoria'] = body.get('categoria', u.get('categoria', 'generale'))
                u['fornitore'] = (body.get('fornitore') or '').strip()
                u['evento_id'] = _intero(body.get('evento_id')) if body.get('evento_id') else None
                u['note'] = (body.get('note') or '').strip()
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Uscita non trovata'}), 404

    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        storage.get_dati()['uscite'] = [u for u in uscite if u.get('id') != id_del]
        storage.salva()
        return jsonify({'success': True})