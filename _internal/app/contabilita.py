"""Logica del bilancio annuale - entrate/uscite senza doppioni."""
from __future__ import annotations
from datetime import datetime
from collections import defaultdict
from app import storage


def _f(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _anno_da_data(data):
    return (data or '')[:4]


def bilancio_anno(anno):
    """Bilancio completo per un anno.
    Principio: ogni spesa va in UNA SOLA categoria per evitare doppi conteggi.
    
    Categorie USCITE:
    - magazzino: carichi gadget (braccialetti, medaglie, adesivi, coppe)
    - inventario: beni durevoli acquistati nell'anno
    - materiali: materiali di consumo (entita) con data_carico nell'anno
    - altro: spese generiche (uscite) inserite manualmente
    
    Categorie ENTRATE:
    - contributi: pagamenti di scuole/enti per eventi
    - sponsor: sponsorizzazioni
    - altro: altre entrate
    """
    d = storage.get_dati()
    anno_str = str(anno)

    # ============================================================
    # USCITE
    # ============================================================

    # 1) MAGAZZINO - carichi dell'anno
    magazzino_voci = []
    magazzino_tot = 0
    for cat, movs in d.get('movimenti', {}).items():
        for idx_m, m in enumerate(movs):
            if m.get('tipo') != 'carico':
                continue
            if _anno_da_data(m.get('data')) != anno_str:
                continue
            q = int(m.get('quantita', 0) or 0)
            pu = _f(m.get('prezzo_unitario'), 0)
            val = _f(m.get('importo_forzato'), q * pu) if m.get('importo_forzato') is not None else (q * pu)
            if val != 0:
                magazzino_voci.append({
                    '_ref': {'fonte': 'magazzino', 'cat': cat, 'id': m.get('id'), 'idx': idx_m},
                    'data': m.get('data', ''),
                    'descrizione': m.get('motivo') or f"Carico {cat}",
                    'categoria': cat,
                    'quantita': q,
                    'prezzo_unitario': pu,
                    'importo': round(val, 2),
                    'motivo': m.get('motivo', ''),
                })
                magazzino_tot += val

    # 2) INVENTARIO - oggetti acquistati nell'anno
    inventario_voci = []
    inventario_tot = 0
    for idx_o, o in enumerate(d.get('inventario', [])):
        data = o.get('data_acquisto') or o.get('data') or ''
        if _anno_da_data(data) != anno_str:
            continue
        q = _f(o.get('quantita'), 1)
        vu = _f(o.get('valore_unitario'), 0)
        if vu == 0 and o.get('valore') is not None:
            vu = _f(o.get('valore'))
        val = _f(o.get('importo_forzato'), q * vu) if o.get('importo_forzato') is not None else (q * vu)
        if val != 0:
            inventario_voci.append({
                '_ref': {'fonte': 'inventario', 'id': o.get('id'), 'idx': idx_o},
                'data': data,
                'descrizione': o.get('nome', '?'),
                'quantita': q,
                'prezzo_unitario': vu,
                'importo': round(val, 2),
            })
            inventario_tot += val

    # 3) MATERIALI - entita con data_carico nell'anno
    materiali_voci = []
    materiali_tot = 0
    for idx_e, e in enumerate(d.get('entita', [])):
        data = e.get('data_carico') or e.get('data') or ''
        if _anno_da_data(data) != anno_str:
            continue
        q = int(e.get('quantita', 0) or 0)
        cu = _f(e.get('costo_unitario'), 0)
        val = _f(e.get('importo_forzato'), q * cu) if e.get('importo_forzato') is not None else (q * cu)
        if val != 0:
            materiali_voci.append({
                '_ref': {'fonte': 'materiali', 'id': e.get('id'), 'idx': idx_e},
                'data': data,
                'descrizione': e.get('nome', '?'),
                'categoria': e.get('categoria', ''),
                'quantita': q,
                'prezzo_unitario': cu,
                'importo': round(val, 2),
            })
            materiali_tot += val

    # 4) ALTRO - uscite generiche dell'anno
    altro_voci = []
    altro_tot = 0
    for o in d.get('inventario', []):
        a = _anno_da_data(o.get('data_acquisto') or o.get('data'))
        if a: anni.add(a)
    for e in d.get('entita', []):
        a = _anno_da_data(e.get('data_carico') or e.get('data'))
        if a: anni.add(a)
    for idx_u, u in enumerate(d.get('uscite', [])):
        if _anno_da_data(u.get('data')) != anno_str:
            continue
        importo = _f(u.get('importo'), 0)
        if importo != 0:
            altro_voci.append({
                '_ref': {'fonte': 'altro', 'id': u.get('id'), 'idx': idx_u},
                'data': u.get('data', ''),
                'descrizione': u.get('descrizione', '?'),
                'categoria': u.get('categoria', 'generale'),
                'importo': round(importo, 2),
            })
            altro_tot += importo

    # ============================================================
    # ENTRATE
    # ============================================================
    entrate_per_tipo = defaultdict(list)
    entrate_tot = 0
    for idx_en, e in enumerate(d.get('entrate', [])):
        if _anno_da_data(e.get('data')) != anno_str:
            continue
        importo = _f(e.get('importo'), 0)
        if importo != 0:
            tipo = e.get('tipo') or 'altro'
            entrate_per_tipo[tipo].append({
                '_ref': {'fonte': 'entrata', 'id': e.get('id'), 'idx': idx_en},
                'data': e.get('data', ''),
                'descrizione': e.get('descrizione', '?'),
                'importo': round(importo, 2),
                'evento_id': e.get('evento_id'),
            })
            entrate_tot += importo

    # ============================================================
    # TOTALI
    # ============================================================
    uscite_tot = magazzino_tot + inventario_tot + materiali_tot + altro_tot
    margine = entrate_tot - uscite_tot

    return {
        'anno': anno,
        'entrate': {
            'voci_per_tipo': {k: v for k, v in entrate_per_tipo.items()},
            'totale': round(entrate_tot, 2),
        },
        'uscite': {
            'magazzino': {'voci': magazzino_voci, 'totale': round(magazzino_tot, 2)},
            'inventario': {'voci': inventario_voci, 'totale': round(inventario_tot, 2)},
            'materiali': {'voci': materiali_voci, 'totale': round(materiali_tot, 2)},
            'altro': {'voci': altro_voci, 'totale': round(altro_tot, 2)},
            'totale': round(uscite_tot, 2),
        },
        'margine': round(margine, 2),
        'ok': margine >= 0,
    }


def bilancio_tutti_anni():
    """Ritorna i totali per ogni anno disponibile."""
    d = storage.get_dati()
    anni = set()

    for e in d.get('eventi', []):
        a = _anno_da_data(e.get('data'))
        if a: anni.add(a)

    for cat, movs in d.get('movimenti', {}).items():
        for idx_m, m in enumerate(movs):
            a = _anno_da_data(m.get('data'))
            if a: anni.add(a)

    for idx_en, e in enumerate(d.get('entrate', [])):
        a = _anno_da_data(e.get('data'))
        if a: anni.add(a)

    for o in d.get('inventario', []):
        a = _anno_da_data(o.get('data_acquisto') or o.get('data'))
        if a: anni.add(a)
    for e in d.get('entita', []):
        a = _anno_da_data(e.get('data_carico') or e.get('data'))
        if a: anni.add(a)
    for idx_u, u in enumerate(d.get('uscite', [])):
        a = _anno_da_data(u.get('data'))
        if a: anni.add(a)

    risultato = {}
    for anno in sorted(anni):
        b = bilancio_anno(anno)
        risultato[anno] = {
            'entrate': b['entrate']['totale'],
            'uscite': b['uscite']['totale'],
            'margine': b['margine'],
        }
    return risultato

def bilancio_progressivo(anno_da=None, anno_a=None):
    tutti = bilancio_tutti_anni()
    anni_disp = sorted(int(a) for a in tutti.keys() if str(a).isdigit())
    if not anni_disp:
        return {'anni_disponibili': [], 'anno_da': anno_da, 'anno_a': anno_a, 'righe': [],
                'entrate': {'totale': 0.0, 'voci_per_tipo': {}},
                'uscite': {'magazzino': {'voci': [], 'totale': 0.0}, 'inventario': {'voci': [], 'totale': 0.0},
                           'materiali': {'voci': [], 'totale': 0.0}, 'altro': {'voci': [], 'totale': 0.0}, 'totale': 0.0},
                'margine': 0.0, 'ok': True}
    da = int(anno_da) if anno_da not in (None, '', 'tutti') else anni_disp[0]
    a = int(anno_a) if anno_a not in (None, '', 'tutti') else max(anni_disp)
    if da > a:
        da, a = a, da
    anni_filtrati = [y for y in anni_disp if da <= y <= a]
    righe = []
    cum_entrate = cum_uscite = cum_margine = 0.0
    tot_mag = tot_inv = tot_mat = tot_alt = 0.0
    for y in anni_filtrati:
        b = bilancio_anno(y)
        ent, usc, mar = b['entrate']['totale'], b['uscite']['totale'], b['margine']
        cum_entrate = round(cum_entrate + ent, 2)
        cum_uscite = round(cum_uscite + usc, 2)
        cum_margine = round(cum_margine + mar, 2)
        tot_mag = round(tot_mag + b['uscite']['magazzino']['totale'], 2)
        tot_inv = round(tot_inv + b['uscite']['inventario']['totale'], 2)
        tot_mat = round(tot_mat + b['uscite']['materiali']['totale'], 2)
        tot_alt = round(tot_alt + b['uscite']['altro']['totale'], 2)
        righe.append({'anno': y, 'entrate': ent, 'uscite': usc, 'margine': mar,
                      'cum_entrate': cum_entrate, 'cum_uscite': cum_uscite, 'cum_margine': cum_margine})
    return {'anni_disponibili': anni_disp, 'anno_da': da, 'anno_a': a, 'righe': righe,
            'entrate': {'totale': cum_entrate, 'voci_per_tipo': {}},
            'uscite': {'magazzino': {'voci': [], 'totale': tot_mag}, 'inventario': {'voci': [], 'totale': tot_inv},
                       'materiali': {'voci': [], 'totale': tot_mat}, 'altro': {'voci': [], 'totale': tot_alt}, 'totale': cum_uscite},
            'margine': cum_margine, 'ok': cum_margine >= 0}


def _trova_rec(lista, rec_id, idx):
    if rec_id is not None:
        for i, item in enumerate(lista):
            if str(item.get('id')) == str(rec_id): return i, item
    if idx is not None and 0 <= int(idx) < len(lista):
        return int(idx), lista[int(idx)]
    return None, None

def _ricalcola_stock(d, cat):
    tot = sum(int(m.get('quantita', 0) or 0) * (1 if m.get('tipo') == 'carico' else -1) for m in d.get('movimenti', {}).get(cat, []))
    d.setdefault('stock', {})[cat] = max(0, tot)

def modifica_voce_bilancio(ref, p):
    d = storage.get_dati()
    f, rid, idx = ref.get('fonte'), ref.get('id'), ref.get('idx')
    if f == 'magazzino':
        cat = ref.get('cat')
        _, m = _trova_rec(d.get('movimenti', {}).get(cat, []), rid, idx)
        if not m: raise ValueError('Movimento non trovato')
        if p.get('data'): m['data'] = p['data']
        if 'descrizione' in p: m['motivo'] = p['descrizione']
        if p.get('quantita') != '': m['quantita'] = int(float(p['quantita']))
        if p.get('prezzo_unitario') != '': m['prezzo_unitario'] = round(float(p['prezzo_unitario']), 4)
        if p.get('importo') != '':
            imp, calc = round(float(p['importo']), 2), round(int(m.get('quantita', 0)) * _f(m.get('prezzo_unitario'), 0), 2)
            if abs(imp - calc) > 0.009: m['importo_forzato'] = imp
            else: m.pop('importo_forzato', None)
        _ricalcola_stock(d, cat)
    elif f == 'inventario':
        _, o = _trova_rec(d.get('inventario', []), rid, idx)
        if not o: raise ValueError('Oggetto non trovato')
        if p.get('data'): o['data_acquisto'] = p['data']
        if p.get('descrizione'): o['nome'] = p['descrizione']
        if p.get('quantita') != '': o['quantita'] = float(p['quantita'])
        if p.get('prezzo_unitario') != '': o['valore_unitario'] = round(float(p['prezzo_unitario']), 4)
        if p.get('importo') != '': o['importo_forzato'] = round(float(p['importo']), 2)
    elif f == 'materiali':
        _, e = _trova_rec(d.get('entita', []), rid, idx)
        if not e: raise ValueError('Materiale non trovato')
        if p.get('data'): e['data_carico'] = p['data']
        if p.get('descrizione'): e['nome'] = p['descrizione']
        if p.get('quantita') != '': e['quantita'] = int(float(p['quantita']))
        if p.get('prezzo_unitario') != '': e['costo_unitario'] = round(float(p['prezzo_unitario']), 4)
        if p.get('importo') != '': e['importo_forzato'] = round(float(p['importo']), 2)
    elif f == 'altro':
        _, u = _trova_rec(d.get('uscite', []), rid, idx)
        if not u: raise ValueError('Uscita non trovata')
        if p.get('data'): u['data'] = p['data']
        if p.get('descrizione'): u['descrizione'] = p['descrizione']
        if p.get('importo') != '': u['importo'] = round(float(p['importo']), 2)
    elif f == 'entrata':
        _, e = _trova_rec(d.get('entrate', []), rid, idx)
        if not e: raise ValueError('Entrata non trovata')
        if p.get('data'): e['data'] = p['data']
        if p.get('descrizione'): e['descrizione'] = p['descrizione']
        if p.get('importo') != '':
            e['importo'] = round(float(p['importo']), 2)
            for ev in d.get('eventi', []):
                if str(ev.get('id')) == str(e.get('evento_id')):
                    if 'importo' in ev: ev['importo'] = e['importo']
                    if 'contributo' in ev: ev['contributo'] = e['importo']
    storage.salva()

def elimina_voce_bilancio(ref):
    d = storage.get_dati()
    f, rid, idx = ref.get('fonte'), ref.get('id'), ref.get('idx')
    mapa = {'inventario': 'inventario', 'materiali': 'entita', 'altro': 'uscite', 'entrata': 'entrate'}
    if f == 'magazzino':
        cat = ref.get('cat')
        lst = d.get('movimenti', {}).get(cat, [])
        i, m = _trova_rec(lst, rid, idx)
        if m is None: raise ValueError('Non trovato')
        lst.pop(i)
        _ricalcola_stock(d, cat)
    elif f in mapa:
        lst = d.get(mapa[f], [])
        i, item = _trova_rec(lst, rid, idx)
        if item is None: raise ValueError('Non trovato')
        if f == 'entrata' and item.get('evento_id'):
            for ev in d.get('eventi', []):
                if str(ev.get('id')) == str(item.get('evento_id')): ev['pagato'] = False
        lst.pop(i)
    storage.salva()

