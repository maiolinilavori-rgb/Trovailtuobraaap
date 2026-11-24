"""Modulo unificato per il calcolo del bilancio delle sezioni."""
from __future__ import annotations
from app import storage


def _f(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def bilancio_magazzino():
    """Valore del magazzino: per ogni categoria, stock * prezzo medio di carico."""
    dati = storage.get_dati()
    stock = dati.get('stock', {})
    movimenti = dati.get('movimenti', {})

    risultato = {
        'sezione': 'magazzino',
        'voci': [],
        'totale_quantita': 0,
        'totale_valore': 0.0,
    }

    for cat in ['braccialetti', 'medaglie', 'adesivi', 'coppe']:
        qta = int(stock.get(cat, 0) or 0)

        totale_carico_qta = 0
        totale_carico_val = 0.0
        for m in movimenti.get(cat, []):
            if m.get('tipo') == 'carico':
                q = int(m.get('quantita', 0) or 0)
                pu = _f(m.get('prezzo_unitario'), 0)
                if pu == 0:
                    pu = _f(m.get('valore_unitario'), 0)
                if pu > 0:
                    totale_carico_qta += q
                    totale_carico_val += q * pu

        prezzo_medio = (totale_carico_val / totale_carico_qta) if totale_carico_qta > 0 else 0.0
        valore = qta * prezzo_medio

        risultato['voci'].append({
            'nome': cat.capitalize(),
            'quantita': qta,
            'prezzo_unitario': round(prezzo_medio, 2),
            'valore': round(valore, 2),
        })
        risultato['totale_quantita'] += qta
        risultato['totale_valore'] += valore

    risultato['totale_valore'] = round(risultato['totale_valore'], 2)
    return risultato


def bilancio_materiali():
    """Valore dei materiali (entita): somma di quantita * costo_unitario."""
    dati = storage.get_dati()
    entita = dati.get('entita', [])

    risultato = {
        'sezione': 'materiali',
        'voci': [],
        'totale_quantita': 0,
        'totale_valore': 0.0,
    }

    for e in entita:
        q = int(e.get('quantita', 0) or 0)
        cu = _f(e.get('costo_unitario'), 0)
        valore = q * cu
        risultato['voci'].append({
            'nome': e.get('nome', '(senza nome)'),
            'categoria': e.get('categoria', ''),
            'quantita': q,
            'prezzo_unitario': round(cu, 2),
            'valore': round(valore, 2),
        })
        risultato['totale_quantita'] += q
        risultato['totale_valore'] += valore

    risultato['totale_valore'] = round(risultato['totale_valore'], 2)
    return risultato


def bilancio_inventario():
    """Valore dell'inventario: somma di quantita * valore_unitario."""
    dati = storage.get_dati()
    inventario = dati.get('inventario', [])

    risultato = {
        'sezione': 'inventario',
        'voci': [],
        'totale_quantita': 0,
        'totale_valore': 0.0,
    }

    for o in inventario:
        q = _f(o.get('quantita'), 1)
        vu = _f(o.get('valore_unitario'))
        if vu == 0 and o.get('valore') is not None:
            vu = _f(o.get('valore'))
        valore = q * vu
        risultato['voci'].append({
            'nome': o.get('nome', '(senza nome)'),
            'quantita': q,
            'prezzo_unitario': round(vu, 2),
            'valore': round(valore, 2),
        })
        risultato['totale_quantita'] += q
        risultato['totale_valore'] += valore

    risultato['totale_valore'] = round(risultato['totale_valore'], 2)
    return risultato


def bilancio_completo():
    """Bilancio aggregato di tutte le sezioni."""
    m = bilancio_magazzino()
    mat = bilancio_materiali()
    inv = bilancio_inventario()
    return {
        'magazzino': m,
        'materiali': mat,
        'inventario': inv,
        'totale_generale': round(m['totale_valore'] + mat['totale_valore'] + inv['totale_valore'], 2),
    }