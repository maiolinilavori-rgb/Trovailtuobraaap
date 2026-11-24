"""Route per il bilancio unificato."""
from __future__ import annotations
from flask import Blueprint, jsonify
from app.auth import login_required
from app.bilancio import bilancio_magazzino, bilancio_materiali, bilancio_inventario, bilancio_completo
from flask import request
from app.contabilita import bilancio_anno, bilancio_tutti_anni, bilancio_progressivo

bp = Blueprint('bilancio', __name__, url_prefix='/api/bilancio')


@bp.route('', methods=['GET'])
@login_required
def api_bilancio_completo():
    return jsonify(bilancio_completo())


@bp.route('/magazzino', methods=['GET'])
@login_required
def api_bilancio_magazzino():
    return jsonify(bilancio_magazzino())


@bp.route('/materiali', methods=['GET'])
@login_required
def api_bilancio_materiali():
    return jsonify(bilancio_materiali())


@bp.route('/inventario', methods=['GET'])
@login_required
def api_bilancio_inventario():
    return jsonify(bilancio_inventario())

@bp.route('/anno/<int:anno>', methods=['GET'])
@login_required
def api_bilancio_anno(anno):
    """Bilancio completo di un anno: entrate + uscite divise per categoria."""
    try:
        return jsonify({'success': True, 'dati': bilancio_anno(anno)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/anni', methods=['GET'])
@login_required
def api_bilancio_anni():
    """Riepilogo tutti gli anni."""
    return jsonify({'success': True, 'dati': bilancio_tutti_anni()})

@bp.route('/progressivo', methods=['GET'])
@login_required
def api_bilancio_progressivo():
    try:
        return jsonify({'success': True, 'dati': bilancio_progressivo(request.args.get('da'), request.args.get('a'))})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/voce', methods=['PUT', 'DELETE'])
@login_required
def api_bilancio_voce():
    from app.contabilita import modifica_voce_bilancio, elimina_voce_bilancio
    b = request.get_json(silent=True) or {}
    try:
        if request.method == 'PUT': modifica_voce_bilancio(b.get('ref') or {}, b.get('dati') or {})
        else: elimina_voce_bilancio(b.get('ref') or {})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/rettifica', methods=['POST'])
@login_required
def api_bilancio_rettifica():
    from app import storage
    import uuid
    b = request.get_json(silent=True) or {}
    d = storage.get_dati()
    chiave = 'entrate' if b.get('tipo') == 'entrata' else 'uscite'
    rec = {'id': str(uuid.uuid4())[:8], 'data': b.get('data') or '', 'descrizione': b.get('descrizione') or 'Rettifica bilancino', 'importo': round(float(b.get('importo') or 0), 2)}
    if chiave == 'entrate': rec['tipo'] = 'rettifica'
    else: rec['categoria'] = 'rettifica'
    d.setdefault(chiave, []).append(rec)
    storage.salva()
    return jsonify({'success': True})


@bp.route('/cerca', methods=['GET'])
@login_required
def api_bilancio_cerca():
    from app import storage
    q = (request.args.get('q') or '').strip().lower()
    if not q:
        return jsonify({'success': True, 'risultati': {}, 'totale_voci': 0})
    d = storage.get_dati()
    res = {'scuole': [], 'eventi': [], 'magazzino': [], 'materiali': [], 'inventario': [], 'entrate': [], 'uscite': []}

    def _match(*vals):
        blob = ' '.join(str(v) for v in vals if v is not None).lower()
        return all(tok in blob for tok in q.split())

    for s in d.get('scuole', []):
        if _match(s.get('nome'), s.get('citta'), s.get('comune'), s.get('indirizzo'), s.get('note'), s.get('referente')):
            res['scuole'].append({'id': s.get('id'), 'titolo': s.get('nome', '?'), 'dettaglio': s.get('citta') or s.get('comune') or s.get('indirizzo') or '', 'importo': None})

    for ev in d.get('eventi', []):
        imp = float(ev.get('importo') or ev.get('contributo') or 0)
        if _match(ev.get('iniziativa'), ev.get('scuola'), ev.get('luogo'), ev.get('data'), ev.get('note'), ev.get('referente'), imp):
            res['eventi'].append({'id': ev.get('id'), 'data': ev.get('data', ''), 'titolo': ev.get('iniziativa') or 'Evento', 'dettaglio': ev.get('scuola') or ev.get('luogo') or '', 'importo': round(imp, 2)})

    for cat, movs in d.get('movimenti', {}).items():
        for idx_m, m in enumerate(movs):
            qv = int(m.get('quantita') or 0)
            pu = float(m.get('prezzo_unitario') or 0)
            imp = float(m.get('importo_forzato')) if m.get('importo_forzato') is not None else round(qv * pu, 2)
            if _match(cat, m.get('tipo'), m.get('data'), m.get('motivo'), qv, pu, imp):
                res['magazzino'].append({'_ref': {'fonte': 'magazzino', 'cat': cat, 'id': m.get('id'), 'idx': idx_m} if m.get('tipo') == 'carico' else None, 'data': m.get('data', ''), 'titolo': f"{(m.get('tipo') or '').capitalize()} {cat} ({qv} pz)", 'dettaglio': m.get('motivo') or '', 'importo': round(imp, 2), 'quantita': qv, 'prezzo_unitario': pu})

    for idx_e, e in enumerate(d.get('entita', [])):
        qv = int(e.get('quantita') or 0)
        cu = float(e.get('costo_unitario') or 0)
        imp = float(e.get('importo_forzato')) if e.get('importo_forzato') is not None else round(qv * cu, 2)
        if _match(e.get('nome'), e.get('categoria'), e.get('data_carico'), e.get('data'), e.get('note'), qv, cu, imp):
            res['materiali'].append({'_ref': {'fonte': 'materiali', 'id': e.get('id'), 'idx': idx_e}, 'data': e.get('data_carico') or e.get('data') or '', 'titolo': e.get('nome', '?'), 'dettaglio': f"{qv} pz ? ? {cu:.2f}", 'importo': round(imp, 2), 'quantita': qv, 'prezzo_unitario': cu})

    for idx_o, o in enumerate(d.get('inventario', [])):
        qv = float(o.get('quantita') or 1)
        vu = float(o.get('valore_unitario') or o.get('valore') or 0)
        imp = float(o.get('importo_forzato')) if o.get('importo_forzato') is not None else round(qv * vu, 2)
        if _match(o.get('nome'), o.get('categoria'), o.get('stato'), o.get('data_acquisto'), o.get('data'), o.get('note'), qv, vu, imp):
            res['inventario'].append({'_ref': {'fonte': 'inventario', 'id': o.get('id'), 'idx': idx_o}, 'data': o.get('data_acquisto') or o.get('data') or '', 'titolo': o.get('nome', '?'), 'dettaglio': f"{qv:g} pz ? ? {vu:.2f}", 'importo': round(imp, 2), 'quantita': qv, 'prezzo_unitario': vu})

    for idx_en, en in enumerate(d.get('entrate', [])):
        imp = float(en.get('importo') or 0)
        if _match(en.get('descrizione'), en.get('tipo'), en.get('data'), imp):
            res['entrate'].append({'_ref': {'fonte': 'entrata', 'id': en.get('id'), 'idx': idx_en}, 'data': en.get('data', ''), 'titolo': en.get('descrizione', '?'), 'dettaglio': en.get('tipo') or 'entrata', 'importo': round(imp, 2)})

    for idx_u, u in enumerate(d.get('uscite', [])):
        imp = float(u.get('importo') or 0)
        if _match(u.get('descrizione'), u.get('categoria'), u.get('data'), imp):
            res['uscite'].append({'_ref': {'fonte': 'altro', 'id': u.get('id'), 'idx': idx_u}, 'data': u.get('data', ''), 'titolo': u.get('descrizione', '?'), 'dettaglio': u.get('categoria') or 'uscita', 'importo': round(imp, 2)})

    tot = sum(len(v) for v in res.values())
    return jsonify({'success': True, 'risultati': res, 'totale_voci': tot})
