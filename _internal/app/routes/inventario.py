from __future__ import annotations
from datetime import datetime
from flask import Blueprint, request, jsonify
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero


def _num(v, default=0.0):
    try:
        return float(v) if v not in (None, '') else default
    except (TypeError, ValueError):
        return default


bp = Blueprint('inventario', __name__, url_prefix='/api/inventario')


def _normalizza_oggetto(o: dict) -> dict:
    q = _num(o.get('quantita'), 1.0)
    vu_raw = o.get('valore_unitario') if o.get('valore_unitario') not in (None, '') else o.get('valore')
    vu = _num(vu_raw, 0.0)
    data_acq = (o.get('data_acquisto') or o.get('data') or '').strip()
    if not data_acq:
        data_acq = datetime.now().strftime('%Y-%m-%d')
    o['quantita'] = q
    o['valore_unitario'] = vu
    o['valore'] = vu
    o['valore_totale'] = round(q * vu, 2)
    o['data_acquisto'] = data_acq
    o['data'] = data_acq
    return o


@bp.route('', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_inventario():
    dati = storage.get_dati()
    dati.setdefault('inventario', [])
    if request.method == 'GET':
        return jsonify(dati['inventario'])
    if request.method == 'POST':
        try:
            o = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False, 'error': 'JSON non valido'}), 400
        o['id'] = _nuovo_id()
        _normalizza_oggetto(o)
        dati['inventario'].append(o)
        storage.salva()
        return jsonify({'success': True, 'id': o['id'], 'oggetto': o})
    if request.method == 'PUT':
        try:
            o = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False, 'error': 'JSON non valido'}), 400
        id_target = _intero(o.get('id'))
        for i, x in enumerate(dati['inventario']):
            if _intero(x.get('id')) == id_target:
                x.update(o)
                x['id'] = id_target
                _normalizza_oggetto(x)
                storage.salva()
                return jsonify({'success': True, 'oggetto': x})
        return jsonify({'success': False, 'error': 'Oggetto non trovato'}), 404
    if request.method == 'DELETE':
        id_target = _intero(request.args.get('id'))
        prima = len(dati['inventario'])
        dati['inventario'] = [x for x in dati['inventario'] if _intero(x.get('id')) != id_target]
        if len(dati['inventario']) < prima:
            storage.salva()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Oggetto non trovato'}), 404
