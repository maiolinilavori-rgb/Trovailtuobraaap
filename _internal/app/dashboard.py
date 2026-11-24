"""Dashboard intelligente - genera riepiloghi dai dati locali (zero token)."""
from __future__ import annotations
from datetime import datetime, timedelta
from app import storage


def _f(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _fmt_euro(n):
    return f"{_f(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def _fmt_num(n):
    try:
        return f"{int(n):,}".replace(',', '.')
    except Exception:
        return str(n)


def dashboard_panoramica():
    """Dashboard completa."""
    d = storage.get_dati()
    eventi = d.get('eventi', [])
    scuole = d.get('scuole', [])
    task = d.get('task', [])
    stock = d.get('stock', {})
    inventario = d.get('inventario', [])
    entita = d.get('entita', [])
    movimenti = d.get('movimenti', {})

    oggi = datetime.now().date()
    oggi_str = oggi.strftime('%Y-%m-%d')
    fra_15 = (oggi + timedelta(days=15)).strftime('%Y-%m-%d')

    # --- EVENTI ---
    eventi_futuri = [e for e in eventi if (e.get('data') or '') >= oggi_str]
    prossimi_15 = [e for e in eventi_futuri if (e.get('data') or '') <= fra_15]

    eventi_per_anno = {}
    for e in eventi:
        anno = (e.get('data') or '')[:4]
        if anno:
            eventi_per_anno[anno] = eventi_per_anno.get(anno, 0) + 1

    # --- MAGAZZINO (calcolato dai movimenti come l'app) ---
    stock_calc = {'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0}
    for cat, movs in movimenti.items():
        for m in movs:
            q = int(m.get('quantita', 0) or 0)
            if m.get('tipo') == 'carico':
                stock_calc[cat] = stock_calc.get(cat, 0) + q
            else:
                stock_calc[cat] = stock_calc.get(cat, 0) - q

    # Valore magazzino (prezzo medio carico)
    tot_val_mag = 0
    for cat in ['braccialetti', 'medaglie', 'adesivi', 'coppe']:
        tq, tv = 0, 0
        for m in movimenti.get(cat, []):
            if m.get('tipo') == 'carico':
                q = int(m.get('quantita', 0) or 0)
                pu = _f(m.get('prezzo_unitario'), 0) or _f(m.get('valore_unitario'), 0)
                if pu > 0:
                    tq += q
                    tv += q * pu
        pm = (tv / tq) if tq else 0
        tot_val_mag += stock_calc.get(cat, 0) * pm

    # --- INVENTARIO ---
    tot_inv = 0
    for o in inventario:
        q = _f(o.get('quantita'), 1)
        vu = _f(o.get('valore_unitario'))
        if vu == 0 and o.get('valore') is not None:
            vu = _f(o.get('valore'))
        tot_inv += q * vu

    # --- MATERIALI ---
    tot_mat = 0
    for e in entita:
        q = int(e.get('quantita', 0) or 0)
        cu = _f(e.get('costo_unitario'), 0)
        tot_mat += q * cu

    # --- TASK ---
    task_aperti = [t for t in task if t.get('stato') != 'completato']
    task_oggi = [t for t in task_aperti if (t.get('data_scadenza') or '') == oggi_str]
    task_scaduti = [t for t in task_aperti if t.get('data_scadenza') and (t.get('data_scadenza') or '') < oggi_str]

    # --- SCUOLE ---
    scuole_con_eventi = len(set(e.get('scuola_id') for e in eventi if e.get('scuola_id')))

    # --- SUGGERIMENTI ---
    suggerimenti = []
    if len(prossimi_15) == 0:
        suggerimenti.append("Nessun evento nei prossimi 15 giorni")
    if len(task_aperti) == 0:
        suggerimenti.append("Nessun task aperto: creane uno di preparazione")
    if len(scuole) > 0 and scuole_con_eventi == 0:
        suggerimenti.append("Hai scuole ma nessun evento collegato")
    if tot_mat > 0 and tot_val_mag == 0:
        suggerimenti.append("Hai materiali ma nessun valore magazzino calcolato")
    if len(inventario) == 0:
        suggerimenti.append("Inventario vuoto: aggiungi almeno un oggetto")
    if not suggerimenti:
        suggerimenti.append("Tutto in ordine! Continua così")

    # --- FORMATTAZIONE ---
    righe = []
    righe.append("📊 **PANORAMICA BRAAAP**")
    righe.append("")
    righe.append("📅 **Eventi**")
    righe.append(f"• Totali: {_fmt_num(len(eventi))}")
    if eventi_per_anno:
        anni_txt = ", ".join(f"{a}: {n}" for a, n in sorted(eventi_per_anno.items()))
        righe.append(f"• Per anno: {anni_txt}")
    righe.append(f"• Prossimi 15 giorni: {len(prossimi_15)}")
    righe.append("")

    righe.append("📦 **Magazzino**")
    righe.append(f"• Braccialetti: {_fmt_num(stock_calc.get('braccialetti', 0))}")
    righe.append(f"• Medaglie: {_fmt_num(stock_calc.get('medaglie', 0))}")
    righe.append(f"• Adesivi: {_fmt_num(stock_calc.get('adesivi', 0))}")
    righe.append(f"• Coppe: {_fmt_num(stock_calc.get('coppe', 0))}")
    righe.append(f"• Valore magazzino: € {_fmt_euro(tot_val_mag)}")
    righe.append("")

    righe.append("🧰 **Inventario e Materiali**")
    righe.append(f"• Inventario: {len(inventario)} oggetti (€ {_fmt_euro(tot_inv)})")
    righe.append(f"• Materiali: {len(entita)} voci (€ {_fmt_euro(tot_mat)})")
    righe.append("")

    righe.append("✅ **Task**")
    righe.append(f"• Aperti: {len(task_aperti)}")
    if task_oggi:
        righe.append(f"• Per oggi: {len(task_oggi)}")
    if task_scaduti:
        righe.append(f"• ⚠️ Scaduti: {len(task_scaduti)}")
    righe.append("")

    righe.append("🏫 **Scuole**")
    righe.append(f"• Totali: {len(scuole)}")
    righe.append(f"• Con eventi: {scuole_con_eventi}")
    righe.append("")

    righe.append("💡 **Suggerimenti**")
    for s in suggerimenti[:5]:
        righe.append(f"• {s}")

    return "\n".join(righe)


def dashboard_magazzino():
    """Dettaglio magazzino."""
    d = storage.get_dati()
    movimenti = d.get('movimenti', {})

    stock_calc = {'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0}
    for cat, movs in movimenti.items():
        for m in movs:
            q = int(m.get('quantita', 0) or 0)
            if m.get('tipo') == 'carico':
                stock_calc[cat] = stock_calc.get(cat, 0) + q
            else:
                stock_calc[cat] = stock_calc.get(cat, 0) - q

    # Ultimi 5 movimenti
    mov_list = []
    for cat, movs in movimenti.items():
        for m in movs:
            mov_list.append({
                'data': m.get('data', ''),
                'cat': cat,
                'tipo': m.get('tipo', ''),
                'q': m.get('quantita', 0),
            })
    mov_list.sort(key=lambda x: x['data'], reverse=True)

    righe = []
    righe.append("📦 **MAGAZZINO**")
    righe.append("")
    righe.append("**Stock attuale**")
    for cat in ['braccialetti', 'medaglie', 'adesivi', 'coppe']:
        righe.append(f"• {cat.capitalize()}: {_fmt_num(stock_calc.get(cat, 0))}")
    righe.append("")

    if mov_list:
        righe.append("**Ultimi movimenti**")
        for m in mov_list[:8]:
            icona = "🟢" if m['tipo'] == 'carico' else "🔴"
            righe.append(f"• {icona} {m['data']} — {m['tipo']} {_fmt_num(m['q'])} {m['cat']}")

    return "\n".join(righe)


def dashboard_task():
    """Task aperti e in scadenza."""
    d = storage.get_dati()
    task = d.get('task', [])
    oggi = datetime.now().date().strftime('%Y-%m-%d')

    task_aperti = [t for t in task if t.get('stato') != 'completato']
    task_aperti.sort(key=lambda t: t.get('data_scadenza') or '9999-99-99')

    righe = []
    righe.append("✅ **TASK**")
    righe.append("")

    if not task_aperti:
        righe.append("Nessun task aperto. 🎉")
        righe.append("")
        righe.append("Suggerimento: aggiungi task di preparazione eventi.")
        return "\n".join(righe)

    righe.append(f"**{len(task_aperti)} task aperti**")
    righe.append("")

    for t in task_aperti[:15]:
        scad = t.get('data_scadenza') or '—'
        icona = "🔴" if (t.get('data_scadenza') and (t.get('data_scadenza') or '') < oggi) else "🟡"
        prio = t.get('priorita', 'media')
        righe.append(f"• {icona} **{t.get('titolo', '?')}** — scad. {scad} ({prio})")

    if len(task_aperti) > 15:
        righe.append(f"\n... e altri {len(task_aperti) - 15}")

    return "\n".join(righe)


def dashboard_eventi():
    """Eventi futuri e panoramica scuole."""
    d = storage.get_dati()
    eventi = d.get('eventi', [])
    scuole = d.get('scuole', [])

    oggi = datetime.now().date().strftime('%Y-%m-%d')
    eventi_futuri = sorted(
        [e for e in eventi if (e.get('data') or '') >= oggi],
        key=lambda e: e.get('data', '')
    )

    righe = []
    righe.append("📅 **EVENTI**")
    righe.append("")

    if not eventi_futuri:
        righe.append("Nessun evento futuro.")
        righe.append("")
        righe.append("Suggerimento: aggiungi i prossimi eventi dal pulsante ➕ in basso a destra.")
        return "\n".join(righe)

    righe.append(f"**{len(eventi_futuri)} eventi futuri**")
    righe.append("")

    for e in eventi_futuri[:10]:
        scuola_nome = ""
        if e.get('scuola_id'):
            for s in scuole:
                if s.get('id') == e['scuola_id']:
                    scuola_nome = s.get('nome', '')
                    break
        etichetta = scuola_nome or "ALTRO"
        righe.append(f"• **{e.get('data', '?')}** — {e.get('iniziativa', '?')} ({etichetta})")

    if len(eventi_futuri) > 10:
        righe.append(f"\n... e altri {len(eventi_futuri) - 10}")

    return "\n".join(righe)


def dashboard_bilancio():
    """Bilancio complessivo."""
    from app.bilancio import bilancio_magazzino, bilancio_materiali, bilancio_inventario
    m = bilancio_magazzino()
    mat = bilancio_materiali()
    inv = bilancio_inventario()
    tot = m['totale_valore'] + mat['totale_valore'] + inv['totale_valore']

    righe = []
    righe.append("💰 **BILANCIO**")
    righe.append("")
    righe.append(f"📦 Magazzino: **€ {_fmt_euro(m['totale_valore'])}** ({_fmt_num(m['totale_quantita'])} pezzi)")
    righe.append(f"🎁 Materiali: **€ {_fmt_euro(mat['totale_valore'])}** ({_fmt_num(mat['totale_quantita'])} pezzi)")
    righe.append(f"🧰 Inventario: **€ {_fmt_euro(inv['totale_valore'])}** ({_fmt_num(inv['totale_quantita'])} pezzi)")
    righe.append("")
    righe.append(f"💵 **Totale: € {_fmt_euro(tot)}**")
    return "\n".join(righe)