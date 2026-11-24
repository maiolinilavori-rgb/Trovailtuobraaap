"""Gestione filtro anno + statistiche storiche."""
from __future__ import annotations
from collections import Counter
from datetime import datetime
from app import storage


def _f(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def anni_disponibili():
    """Ritorna la lista degli anni per cui esistono dati."""
    d = storage.get_dati()
    anni = set()

    for e in d.get('eventi', []):
        a = (e.get('data') or '')[:4]
        if a and a.isdigit():
            anni.add(int(a))

    for cat, movs in d.get('movimenti', {}).items():
        for m in movs:
            a = (m.get('data') or '')[:4]
            if a and a.isdigit():
                anni.add(int(a))

    return sorted(anni, reverse=True)


def eventi_per_anno(anno=None):
    """Ritorna gli eventi filtrati per anno (o tutti se None)."""
    d = storage.get_dati()
    eventi = d.get('eventi', [])
    if anno is None:
        return eventi
    prefisso = f"{anno}-"
    return [e for e in eventi if (e.get('data') or '').startswith(prefisso)]


def movimenti_per_anno(anno=None):
    """Ritorna movimenti filtrati per anno."""
    d = storage.get_dati()
    movimenti = d.get('movimenti', {})
    if anno is None:
        return movimenti
    prefisso = f"{anno}-"
    filtrati = {}
    for cat, movs in movimenti.items():
        sub = [m for m in movs if (m.get('data') or '').startswith(prefisso)]
        if sub:
            filtrati[cat] = sub
    return filtrati


def storico_anno(anno):
    """Statistiche complete di un anno."""
    d = storage.get_dati()
    eventi = eventi_per_anno(anno)
    movimenti = movimenti_per_anno(anno)

    scuole = d.get('scuole', [])
    task = d.get('task', [])
    inventario = d.get('inventario', [])
    entita = d.get('entita', [])

    # Eventi per mese
    eventi_per_mese = [0] * 12
    for e in eventi:
        mese = (e.get('data') or '')[5:7]
        if mese.isdigit():
            m = int(mese) - 1
            if 0 <= m < 12:
                eventi_per_mese[m] += 1

    # Eventi per scuola
    scuole_count = Counter()
    for e in eventi:
        sid = e.get('scuola_id')
        if sid:
            sc = next((s for s in scuole if s.get('id') == sid), None)
            nome = sc.get('nome') if sc else 'Sconosciuta'
            scuole_count[nome] += 1

    # Movimenti per mese (per tipo)
    carichi_per_mese = [0] * 12
    scarichi_per_mese = [0] * 12
    for cat, movs in movimenti.items():
        for m in movs:
            mese = (m.get('data') or '')[5:7]
            if mese.isdigit():
                mi = int(mese) - 1
                if 0 <= mi < 12:
                    q = int(m.get('quantita', 0) or 0)
                    if m.get('tipo') == 'carico':
                        carichi_per_mese[mi] += q
                    else:
                        scarichi_per_mese[mi] += q

    # Movimenti per categoria
    mov_per_cat = {}
    for cat in ['braccialetti', 'medaglie', 'adesivi', 'coppe']:
        movs = movimenti.get(cat, [])
        c = sum(int(m.get('quantita', 0) or 0) for m in movs if m.get('tipo') == 'carico')
        s = sum(int(m.get('quantita', 0) or 0) for m in movs if m.get('tipo') == 'scarico')
        mov_per_cat[cat] = {'carichi': c, 'scarichi': s, 'netto': c - s}

    # Task completati nell'anno (per data_scadenza)
    task_anno = [t for t in task if (t.get('data_scadenza') or '').startswith(f"{anno}-")]
    task_completati = [t for t in task_anno if t.get('stato') == 'completato']
    task_aperti = [t for t in task_anno if t.get('stato') != 'completato']

    # Statistiche generali
    tot_partecipanti = sum(int(e.get('numero_partecipanti', 0) or 0) for e in eventi)
    eventi_multi = [e for e in eventi if (e.get('durata_giorni', 1) or 1) > 1]

    # Top 5 eventi per partecipanti
    top_eventi = sorted(eventi, key=lambda e: int(e.get('numero_partecipanti', 0) or 0), reverse=True)[:5]

    return {
        'anno': anno,
        'eventi': {
            'totale': len(eventi),
            'per_mese': eventi_per_mese,
            'per_scuola': dict(scuole_count.most_common(10)),
            'multi_giorno': len(eventi_multi),
            'partecipanti_totali': tot_partecipanti,
            'top_5': [
                {
                    'data': e.get('data'),
                    'iniziativa': e.get('iniziativa'),
                    'partecipanti': int(e.get('numero_partecipanti', 0) or 0),
                    'scuola': next((s.get('nome') for s in scuole if s.get('id') == e.get('scuola_id')), 'ALTRO')
                }
                for e in top_eventi
            ]
        },
        'movimenti': {
            'per_categoria': mov_per_cat,
            'carichi_per_mese': carichi_per_mese,
            'scarichi_per_mese': scarichi_per_mese,
        },
        'task': {
            'totale': len(task_anno),
            'completati': len(task_completati),
            'aperti': len(task_aperti),
        },
        'inventario_attuale': len(inventario),
        'materiali_attuale': len(entita),
    }


def totali_globali():
    """Totali globali senza filtro anno."""
    d = storage.get_dati()
    return {
        'anni': anni_disponibili(),
        'eventi_totali': len(d.get('eventi', [])),
        'scuole_totali': len(d.get('scuole', [])),
        'task_totali': len(d.get('task', [])),
        'contatti_totali': len(d.get('rubrica', [])),
    }