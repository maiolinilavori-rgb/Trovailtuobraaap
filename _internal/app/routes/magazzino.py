"""Route per la gestione del magazzino."""
from __future__ import annotations
from flask import Blueprint, request, jsonify
from datetime import datetime
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero

bp = Blueprint('magazzino', __name__, url_prefix='/api')

CATEGORIE = ('braccialetti', 'medaglie', 'adesivi', 'coppe')


def _ricalcola_stock(categoria):
    movimenti = storage.get_dati().get('movimenti', {}).get(categoria, [])
    stock = 0
    for m in movimenti:
        q = _intero(m.get('quantita'))
        if m.get('tipo') == 'carico': stock += q
        else: stock -= q
    storage.get_dati().setdefault('stock', {})[categoria] = stock


@bp.route('/movimenti', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_movimenti():
    if request.method == 'GET':
        movs = storage.get_dati().get('movimenti', {})
        ordinati = {k: sorted(v, key=lambda x: (x.get('data') or '', x.get('id') or 0), reverse=True) for k, v in movs.items()}
        return jsonify(ordinati)

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400

    movimenti = storage.get_dati().setdefault('movimenti', {})

    if request.method == 'POST':
        cat = body.get('categoria'); tipo = body.get('tipo'); q = _intero(body.get('quantita'))
        if cat not in CATEGORIE: return jsonify({'success': False, 'error': 'Categoria non valida'}), 400
        if tipo not in ('carico', 'scarico') or q <= 0: return jsonify({'success': False, 'error': 'Tipo o quantita non validi'}), 400
        movimenti.setdefault(cat, []).append({
            'id': _nuovo_id(), 'data': body.get('data', datetime.now().strftime('%Y-%m-%d')),
            'tipo': tipo, 'quantita': q, 'prezzo_unitario': body.get('prezzo_unitario', 0),
            'motivo': body.get('motivo', ''), 'nota_carico': body.get('nota_carico', ''),
            'evento_id': _intero(body.get('evento_id')) if body.get('evento_id') else None,
            'scuola_id': _intero(body.get('scuola_id')) if body.get('scuola_id') else None,
            'destinatario': (body.get('destinatario') or '').strip()
        })
        _ricalcola_stock(cat); storage.salva()
        return jsonify({'success': True})

    if request.method == 'PUT':
        mov_id = _intero(body.get('id')); cat_old = body.get('categoria_old')
        cat_new = body.get('categoria', cat_old); tipo_new = body.get('tipo'); q_new = _intero(body.get('quantita'))
        if cat_old not in CATEGORIE or cat_new not in CATEGORIE: return jsonify({'success': False}), 400
        mov_old = None
        for i, m in enumerate(movimenti.get(cat_old, [])):
            if m.get('id') == mov_id:
                mov_old = movimenti[cat_old].pop(i); break
        if not mov_old: return jsonify({'success': False, 'error': 'Movimento non trovato'}), 404
        ev_id = _intero(body.get('evento_id')) if body.get('evento_id') else mov_old.get('evento_id')
        sc_id = _intero(body.get('scuola_id')) if body.get('scuola_id') else mov_old.get('scuola_id')
        dest = (body.get('destinatario') or '').strip() or mov_old.get('destinatario', '')
        pu_new = float(body.get('prezzo_unitario')) if body.get('prezzo_unitario') is not None else float(mov_old.get('prezzo_unitario') or 0)
        mov_agg = {
            'id': mov_id, 'tipo': tipo_new, 'quantita': q_new,
            'data': body.get('data') or mov_old.get('data'), 'prezzo_unitario': pu_new,
            'motivo': body.get('motivo', ''), 'nota_carico': body.get('nota_carico', ''),
            'evento_id': ev_id, 'scuola_id': sc_id, 'destinatario': dest
        }
        movimenti.setdefault(cat_new, []).append(mov_agg)
        _ricalcola_stock(cat_old)
        if cat_old != cat_new: _ricalcola_stock(cat_new)
        # Sincronizza la quantita sull'eventuale evento collegato
        if ev_id and tipo_new == 'scarico':
            for ev in storage.get_dati().get('eventi', []):
                if _intero(ev.get('id')) == ev_id:
                    if cat_old != cat_new and cat_old in ev: ev[cat_old] = 0
                    ev[cat_new] = q_new
                    break
        storage.salva()
        return jsonify({'success': True})

    if request.method == 'DELETE':
        mov_id = _intero(request.args.get('id'))
        cat = (request.args.get('categoria') or '').strip().lower()
        if cat not in CATEGORIE:
            return jsonify({'success': False, 'error': 'Categoria non valida'}), 400
        mov_rimosso = None
        for i, m in enumerate(movimenti.get(cat, [])):
            if _intero(m.get('id')) == mov_id:
                mov_rimosso = movimenti[cat].pop(i)
                break
        if not mov_rimosso:
            return jsonify({'success': False, 'error': 'Movimento non trovato'}), 404
        _ricalcola_stock(cat)
        ev_id = _intero(mov_rimosso.get('evento_id'))
        if ev_id and mov_rimosso.get('tipo') == 'scarico':
            for ev in storage.get_dati().get('eventi', []):
                if _intero(ev.get('id')) == ev_id:
                    ev[cat] = 0
                    break
        storage.salva()
        return jsonify({'success': True, 'stock': storage.get_dati().get('stock', {})})


@bp.route('/movimenti/storico', methods=['GET'])
@login_required
def api_movimenti_storico():
    movimenti = storage.get_dati().get('movimenti', {})
    risultato = {}
    for cat in CATEGORIE:
        movs_ordinati = sorted(movimenti.get(cat, []), key=lambda m: (m.get('data', ''), m.get('id', 0)))
        progressivo = 0
        storico = []
        for m in movs_ordinati:
            q = _intero(m.get('quantita'))
            if m.get('tipo') == 'carico': progressivo += q
            else: progressivo -= q
            storico.append({**m, 'progressivo': progressivo})
        storico.reverse()
        risultato[cat] = storico
    return jsonify(risultato)