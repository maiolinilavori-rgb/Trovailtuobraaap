from __future__ import annotations
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string
from datetime import datetime, timedelta
from app import storage
from app.auth import login_required
from app.utils import _nuovo_id, _intero, _parse_data

bp = Blueprint('eventi', __name__, url_prefix='/api/eventi')

CATEGORIE_MAG = ('braccialetti', 'medaglie', 'adesivi', 'coppe')

def _sincronizza_magazzino_evento(ev: dict, elimina: bool = False) -> None:
    """Crea, aggiorna o elimina i movimenti di scarico collegati all'evento."""
    d = storage.get_dati()
    movimenti = d.setdefault('movimenti', {})
    stock = d.setdefault('stock', {})
    ev_id = _intero(ev.get('id'))
    if not ev_id:
        return

    data_ev = (ev.get('data') or datetime.now().strftime('%Y-%m-%d')).strip()
    motivo = f"Evento: {(ev.get('iniziativa') or 'Senza titolo').strip()}"
    sc_id = _intero(ev.get('scuola_id')) if ev.get('scuola_id') not in (None, '', 0, '0') else None
    dest = (ev.get('luogo') or '').strip()

    for cat in CATEGORIE_MAG:
        lista_cat = movimenti.setdefault(cat, [])
        q_nuova = 0 if elimina else max(0, _intero(ev.get(cat)))
        idx_esistente = next((i for i, m in enumerate(lista_cat) if _intero(m.get('evento_id')) == ev_id and m.get('tipo') == 'scarico'), None)

        if q_nuova > 0:
            if idx_esistente is not None:
                lista_cat[idx_esistente]['quantita'] = q_nuova
                lista_cat[idx_esistente]['data'] = data_ev
                lista_cat[idx_esistente]['motivo'] = motivo
                lista_cat[idx_esistente]['scuola_id'] = sc_id
                if dest:
                    lista_cat[idx_esistente]['destinatario'] = dest
            else:
                lista_cat.append({
                    'id': _nuovo_id(),
                    'data': data_ev,
                    'tipo': 'scarico',
                    'quantita': q_nuova,
                    'prezzo_unitario': 0,
                    'motivo': motivo,
                    'nota_carico': ev.get('nota_carico', ''),
                    'evento_id': ev_id,
                    'scuola_id': sc_id,
                    'destinatario': dest,
                })
        elif idx_esistente is not None:
            lista_cat.pop(idx_esistente)

        # Ricalcola lo stock della categoria
        tot_cat = 0
        for m in lista_cat:
            qm = _intero(m.get('quantita'))
            tot_cat += qm if m.get('tipo') == 'carico' else -qm
        stock[cat] = tot_cat


def _collega_scuola_automatico(ev: dict) -> None:
    sid = ev.get('scuola_id')
    if sid not in (None, '', 0, '0'):
        ev['scuola_id'] = _intero(sid)
        return
    ev['scuola_id'] = None
    testo = f"{ev.get('iniziativa') or ''} {ev.get('luogo') or ''}".upper().strip()
    if not testo:
        return
    scuole = storage.get_dati().get('scuole', [])
    migliore = None
    for s in scuole:
        nome_s = (s.get('nome') or '').upper().strip()
        if len(nome_s) >= 4 and (nome_s in testo or (len(ev.get('iniziativa') or '') >= 6 and (ev.get('iniziativa') or '').upper().strip() in nome_s)):
            if migliore is None or len(nome_s) > len(migliore[0]):
                migliore = (nome_s, s.get('id'))
    if migliore:
        ev['scuola_id'] = _intero(migliore[1])



"""
Route per eventi.
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
def api_eventi():
    if request.method == 'GET':
        return jsonify(storage.get_dati()['eventi'])
    if request.method == 'POST':
        try:
            nuovo = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        if not nuovo.get('data'):
            return jsonify({'success': False, 'error': 'Data obbligatoria'}), 400
        nuovo['id'] = _nuovo_id()
        if 'scuola_id' not in nuovo:
            _collega_scuola_automatico(nuovo)
        elif nuovo.get('scuola_id') in (None, '', 0, '0'):
            nuovo['scuola_id'] = None
        else:
            nuovo['scuola_id'] = _intero(nuovo.get('scuola_id'))
        storage.get_dati()['eventi'].append(nuovo)
        _sincronizza_magazzino_evento(nuovo)
        storage.salva()
        return jsonify({'success': True, 'id': nuovo['id']})
    if request.method == 'PUT':
        try:
            modificato = request.get_json(force=True) or {}
        except Exception:
            return jsonify({'success': False}), 400
        for i, e in enumerate(storage.get_dati()['eventi']):
            if e.get('id') == modificato.get('id'):
                if 'foto' not in modificato and 'foto' in e:
                    modificato['foto'] = e['foto']
                if modificato.get('scuola_id') in (None, '', 0, '0'):
                    modificato['scuola_id'] = None
                else:
                    modificato['scuola_id'] = _intero(modificato.get('scuola_id'))
                storage.get_dati()['eventi'][i] = modificato
                _sincronizza_magazzino_evento(modificato)
                storage.salva()
                return jsonify({'success': True})
        return jsonify({'success': False}), 404
    if request.method == 'DELETE':
        id_del = request.args.get('id', type=int)
        ev_rimosso = next((e for e in storage.get_dati()['eventi'] if _intero(e.get('id')) == _intero(id_del)), None)
        storage.get_dati()['eventi'] = [e for e in storage.get_dati()['eventi'] if _intero(e.get('id')) != _intero(id_del)]
        if ev_rimosso:
            _sincronizza_magazzino_evento(ev_rimosso, elimina=True)
        storage.salva()
        return jsonify({'success': True})


@bp.route('/blocco', methods=['POST'])
@login_required
def api_eventi_blocco():
    """Sposta più eventi in blocco a una scuola o ad ALTRO (null)."""
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'success': False}), 400
    ids = body.get('ids', [])
    scuola_id = body.get('scuola_id')  # può essere None per ALTRO
    n = 0
    for e in storage.get_dati()['eventi']:
        if e.get('id') in ids:
            e['scuola_id'] = scuola_id
            n += 1
    storage.salva()
    return jsonify({'success': True, 'spostati': n})


@bp.route('/sospetti')
@login_required
def api_eventi_sospetti():
    """Eventi il cui luogo NON sembra un nome di scuola."""
    parole_sospette = ['assicurazioni', 'trattoria', 'cinema', 'concerto', 'festival',
                       'bar', 'ristorante', 'pizzeria', 'caffè', 'negozio', 'market',
                       'grest', 'estate', 'evento', 'sagra', 'festa']
    sospetti = []
    for e in dati.get('eventi', []):
        luogo = (e.get('luogo') or '').lower()
        iniz = (e.get('iniziativa') or '').lower()
        if any(p in luogo or p in iniz for p in parole_sospette):
            sospetti.append(e)
    return jsonify(sospetti)

