"""Assistente conversazionale basato su Groq con contesto dei dati Braaap."""
from __future__ import annotations
import json
from datetime import datetime
from groq import Groq
from app import storage
from app.config import GROQ_API_KEY, GROQ_MODELLO_LLM
from app.vocabolario import rileva_wake_word, traduci_testo, estrai_apprendimento, impara


SYSTEM_PROMPT = """Sei l'assistente di Braaap, un'app di gestione eventi, magazzino gadgets, scuole e task.
Rispondi in italiano, in modo conciso e diretto. Usa i dati forniti per rispondere con precisione.

REGOLE IMPORTANTI:
- Se la domanda riguarda numeri/quantita, cita il valore esatto.
- Se non hai il dato, di: "Non ho questa informazione nei tuoi dati attuali".
- Non inventare. Non supporre. Se sei incerto, chiedi chiarimenti.
- Massimo 3-4 righe per risposta, a meno che serva un elenco.
- Tono amichevole ma professionale. Dai del "tu" all'utente.
"""


def _calcola_stock_dai_movimenti():
    """Ricalcola lo stock dai movimenti (come fa l'app in calcolaStock)."""
    d = storage.get_dati()
    stock = {'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0}
    for cat, movs in d.get('movimenti', {}).items():
        for m in movs:
            q = int(m.get('quantita', 0) or 0)
            if m.get('tipo') == 'carico':
                stock[cat] = stock.get(cat, 0) + q
            else:
                stock[cat] = stock.get(cat, 0) - q
    return stock

def _riassunto_dati():
    """Prepara un riassunto compatto dei dati dell'utente."""
    from datetime import datetime as _dt
    d = storage.get_dati()
    oggi_str = _dt.now().strftime('%Y-%m-%d')

    # ========================================================
    # EVENTI - con totali per anno + prossimi 15 dal presente
    # ========================================================
    eventi = d.get('eventi', [])
    totale_eventi = len(eventi)

    # Distribuzione per anno
    eventi_per_anno = {}
    for e in eventi:
        anno = (e.get('data') or '')[:4]
        if anno:
            eventi_per_anno[anno] = eventi_per_anno.get(anno, 0) + 1
    anni_str = ', '.join(f"{k}: {v}" for k, v in sorted(eventi_per_anno.items()))

    # Prossimi 15 eventi da oggi in poi
    eventi_futuri = sorted(
        [e for e in eventi if (e.get('data') or '') >= oggi_str],
        key=lambda e: e.get('data', '')
    )[:15]

    # Conta eventi con/senza scuola
    totale_con_scuola = sum(1 for e in eventi if e.get('scuola_id'))
    totale_altro = totale_eventi - totale_con_scuola

    eventi_txt = []
    for e in eventi_futuri:
        scuola = ''
        if e.get('scuola_id'):
            for s in d.get('scuole', []):
                if s.get('id') == e['scuola_id']:
                    scuola = s.get('nome', '')
                    break
        # Etichetta [ALTRO] se non ha scuola
        etichetta = f"({scuola})" if scuola else "[ALTRO - senza scuola]"
        eventi_txt.append(
            f"- {e.get('data', '?')}: {e.get('iniziativa', '?')} {etichetta}"
            + (f" - {e.get('numero_partecipanti', 0)} partecipanti" if e.get('numero_partecipanti') else "")
        )
    eventi_str = '\n'.join(eventi_txt) if eventi_txt else 'Nessun evento futuro'

    # ========================================================
    # SCUOLE
    # ========================================================
    scuole = d.get('scuole', [])
    totale_scuole = len(scuole)
    scuole_txt = ', '.join(s.get('nome', '?') for s in scuole[:20])
    if totale_scuole > 20:
        scuole_txt += f' (+{totale_scuole - 20} altre)'

    # ========================================================
    # TASK
    # ========================================================
    task = d.get('task', [])
    totale_task = len(task)
    task_aperti = [t for t in task if t.get('stato') != 'completato']
    task_txt = '\n'.join(
        f"- {t.get('titolo', '?')}" + (f" (scad: {t.get('data_scadenza')})" if t.get('data_scadenza') else "")
        for t in task_aperti[:10]
    ) if task_aperti else 'Nessun task aperto'

    # ========================================================
    # INVENTARIO
    # ========================================================
    inv = d.get('inventario', [])
    inv_tot = 0
    for o in inv:
        q = float(o.get('quantita', 1) or 1)
        vu = float(o.get('valore_unitario', o.get('valore', 0)) or 0)
        inv_tot += q * vu
    inv_txt = f"{len(inv)} oggetti, valore totale {inv_tot:.2f} EUR"

    # ========================================================
    # MATERIALI
    # ========================================================
    entita = d.get('entita', [])
    ent_tot = 0
    for e in entita:
        q = int(e.get('quantita', 0) or 0)
        cu = float(e.get('costo_unitario', 0) or 0)
        ent_tot += q * cu
    ent_txt = f"{len(entita)} materiali, valore totale {ent_tot:.2f} EUR"

    # ========================================================
    # MOVIMENTI
    # ========================================================
    mov = d.get('movimenti', {})
    totale_movimenti = sum(len(v) for v in mov.values())
    mov_list = []
    for cat, items in mov.items():
        for m in items:
            mov_list.append({
                'data': m.get('data', ''),
                'cat': cat,
                'tipo': m.get('tipo', ''),
                'q': m.get('quantita', 0),
                'motivo': m.get('motivo', ''),
            })
    mov_list.sort(key=lambda x: x['data'], reverse=True)
    mov_txt = '\n'.join(
        f"- {m['data']}: {m['tipo']} {m['q']} {m['cat']}"
        + (f" ({m['motivo']})" if m['motivo'] else "")
        for m in mov_list[:8]
    ) if mov_list else 'Nessun movimento'

    # ========================================================
    # STOCK - calcolato dai movimenti come nell'app
    # ========================================================
    stock_calcolato = _calcola_stock_dai_movimenti()
    stock_salvato = d.get('stock', {})

    # Usa SEMPRE il calcolato (allineato con l'interfaccia Magazzino)
    stock_txt = ', '.join(f"{k}: {stock_calcolato.get(k, 0)}" for k in ['braccialetti', 'medaglie', 'adesivi', 'coppe'])

    # Avvisa se c'e' divergenza (utile per debug)
    divergenza = any(stock_calcolato.get(k, 0) != stock_salvato.get(k, 0) for k in ['braccialetti', 'medaglie', 'adesivi', 'coppe'])
    nota_stock = ''
    if divergenza:
        nota_stock = f"\nNOTA: lo stock salvato nel DB e' {stock_salvato}, ma quello mostrato nell'app (calcolato dai movimenti) e' il valore sopra."

    return f"""DATI ATTUALI DELL'UTENTE (aggiornati al {oggi_str}):

STOCK MAGAZZINO (calcolato dai movimenti): {stock_txt or 'vuoto'}{nota_stock}

EVENTI: {totale_eventi} in totale.
- Con scuola associata: {totale_con_scuola}
- ALTRO (senza scuola): {totale_altro}
Distribuzione per anno: {anni_str or 'nessun dato'}

NOTA sugli eventi ALTRO: gli eventi senza scuola sono iniziative generiche (sagre, feste di paese, eventi aziendali) e vanno contati separatamente. Se l'utente chiede "eventi ALTRO" o "eventi senza scuola", rispondi con il valore di ALTRO qui sopra.

PROSSIMI 15 EVENTI (dal {oggi_str} in poi):
{eventi_str}

IMPORTANTE sugli eventi: se l'utente chiede eventi di un anno specifico, rispondi con il TOTALE per quell'anno. Per i dettagli, invitalo ad aprire la sezione "Eventi" dell'app e filtrare per anno.

SCUOLE: {totale_scuole} in totale. Elenco: {scuole_txt or 'nessuna'}

TASK: {totale_task} totali, {len(task_aperti)} aperti:
{task_txt}

INVENTARIO: {inv_txt}

MATERIALI: {ent_txt}

MOVIMENTI MAGAZZINO: {totale_movimenti} totali. Ultimi 8:
{mov_txt}

DATA ODIERNA: {oggi_str}
"""

def chatta(messaggi: list) -> dict:
    """Elabora una conversazione con Groq e restituisce la risposta."""
    if not GROQ_API_KEY:
        return {
            'success': False,
            'error': 'GROQ_API_KEY non configurata nel .env',
        }

    if not messaggi:
        return {'success': False, 'error': 'Nessun messaggio'}

    # Prendi l'ultimo messaggio utente
    ultimo_utente = None
    for m in reversed(messaggi):
        if m.get('role') == 'user':
            ultimo_utente = m.get('content', '')
            break

    if not ultimo_utente:
        return {'success': False, 'error': 'Nessun messaggio utente'}

    # 1) Controlla se e' un comando di apprendimento
    apprendimento = estrai_apprendimento(ultimo_utente)
    if apprendimento:
        risultato = impara(apprendimento['parola'], apprendimento['significato'])
        if risultato.get('success'):
            return {
                'success': True,
                'risposta': f"Ho imparato! Ora so che \"{apprendimento['parola']}\" significa \"{apprendimento['significato']}\". Lo userò quando parli.",
                'wake_word': False,
            }

    # 2) Rileva wake-word
    wake_trovata, testo_pulito = rileva_wake_word(ultimo_utente)
    if wake_trovata and not testo_pulito:
        # Solo wake-word senza altro testo
        return {
            'success': True,
            'risposta': 'Ti ascolto! Cosa vuoi sapere?',
            'wake_word': True,
        }

    # 3) Traduci il testo con il vocabolario
    testo_tradotto = traduci_testo(testo_pulito) if wake_trovata else traduci_testo(ultimo_utente)

    # 4) Prepara i messaggi per Groq (sostituisci l'ultimo con il tradotto)
    msgs_groq = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + _riassunto_dati()},
    ]
    for i, m in enumerate(messaggi[-10:]):
        if m.get('role') in ('user', 'assistant') and m.get('content'):
            contenuto = m['content']
            # Sostituisci l'ultimo messaggio utente con la versione tradotta
            if i == len(messaggi[-10:]) - 1 and m.get('role') == 'user':
                contenuto = testo_tradotto
            msgs_groq.append({
                "role": m['role'],
                "content": contenuto,
            })

    try:
        client = Groq(api_key=GROQ_API_KEY)
        risposta = client.chat.completions.create(
            model=GROQ_MODELLO_LLM,
            messages=msgs_groq,
            temperature=0.3,
            max_tokens=500,
        )
        testo = risposta.choices[0].message.content.strip()
        return {
            'success': True,
            'risposta': testo,
            'wake_word': wake_trovata,
        }
    except Exception as e:
        return {'success': False, 'error': f'Errore Groq: {e}'}