from __future__ import annotations
import re
from datetime import datetime, timedelta
from app.utils import _intero, _nuovo_id
from app import storage

# ============================================================
# COSTANTI PER IL PARSING DEL LINGUAGGIO NATURALE
# ============================================================

MESI_IT = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
           'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']

NUMERI_IT = {
    'zero': 0, 'uno': 1, 'due': 2, 'tre': 3, 'quattro': 4, 'cinque': 5,
    'sei': 6, 'sette': 7, 'otto': 8, 'nove': 9, 'dieci': 10,
    'undici': 11, 'dodici': 12, 'tredici': 13, 'quattordici': 14,
    'quindici': 15, 'sedici': 16, 'diciassette': 17, 'diciotto': 18,
    'diciannove': 19, 'venti': 20, 'trenta': 30, 'quaranta': 40,
    'cinquanta': 50, 'sessanta': 60, 'settanta': 70, 'ottanta': 80,
    'novanta': 90, 'cento': 100, 'mille': 1000
}

_DECINE = {
    'venti': 20, 'trenta': 30, 'quaranta': 40, 'cinquanta': 50,
    'sessanta': 60, 'settanta': 70, 'ottanta': 80, 'novanta': 90
}

_UNITA = {
    'uno': 1, 'due': 2, 'tre': 3, 'quattro': 4, 'cinque': 5,
    'sei': 6, 'sette': 7, 'otto': 8, 'nove': 9
}

CATEGORIE_MAGAZZINO_NOTE = ['braccialetti', 'medaglie', 'adesivi', 'coppe']

VERBI_CARICO = ['carica', 'carico', 'caricato', 'caricati', 'caricate',
                'aggiungi', 'aggiunto', 'aggiunti', 'aggiunte',
                'entrato', 'entrata', 'entrati', 'entrate',
                'ricevuto', 'ricevuta', 'ricevuti', 'ricevute',
                'comprato', 'acquistato', 'preso', 'arrivato', 'arrivata',
                'arrivati', 'arrivate', 'consegnato', 'consegnata',
                'consegnati', 'consegnate']

VERBI_SCARICO = ['scarica', 'scarico', 'scaricato', 'scaricati', 'scaricate',
                 'tolto', 'tolta', 'tolti', 'tolte',
                 'uscito', 'uscita', 'usciti', 'uscite',
                 'dato', 'data', 'dati', 'date',
                 'do', 'dò', 'daro', 'darò', 'dar', 'consegno', 'consegnato',
                 'portato', 'porto', 'faccio', 'fatto', 'uso', 'usato',
                 'utilizzo', 'utilizzato', 'spedito', 'inviato', 'regalato',
                 'regalo', 'distribuito', 'perso', 'persa', 'buttato']

# ============================================================
# FINE COSTANTI
# ============================================================


def _numero_da_parola_composta(parola):
    parola = parola.lower()
    if parola in NUMERI_IT:
        return NUMERI_IT[parola]
    for decina_txt, decina_val in _DECINE.items():
        base = decina_txt[:-1] if decina_txt[-1] == 'i' else decina_txt
        if parola.startswith(base):
            resto = parola[len(base):]
            if resto in _UNITA:
                return decina_val + _UNITA[resto]
            if resto == '':
                return decina_val
    return None

def estrai_numero_italiano(testo):
    m = re.search(r'\b(\d+)\b', testo)
    if m:
        return int(m.group(1))
    for parola in re.findall(r"[a-zàèéìòù']+", testo.lower()):
        n = _numero_da_parola_composta(parola)
        if n is not None and n > 0:
            return n
    return None

def estrai_data_da_testo(testo_lower, oggi=None):
    oggi = oggi or datetime.now()
    if 'dopodomani' in testo_lower:
        return (oggi + timedelta(days=2)).strftime('%Y-%m-%d')
    if 'domani' in testo_lower:
        return (oggi + timedelta(days=1)).strftime('%Y-%m-%d')
    if re.search(r'\boggi\b', testo_lower):
        return oggi.strftime('%Y-%m-%d')
    m = re.search(r'\b(\d{1,2})\s+(' + '|'.join(MESI_IT) + r')\s+(?:del\s+)?(\d{4})', testo_lower)
    if m:
        try:
            return datetime(int(m.group(3)), MESI_IT.index(m.group(2)) + 1, int(m.group(1))).strftime('%Y-%m-%d')
        except ValueError:
            pass
    m = re.search(r'\b(\d{1,2})\s+(' + '|'.join(MESI_IT) + r')\b', testo_lower)
    if m:
        try:
            g = int(m.group(1))
            mese_n = MESI_IT.index(m.group(2)) + 1
            anno = oggi.year
            data_ev = datetime(anno, mese_n, g)
            if data_ev.date() < oggi.date():
                data_ev = datetime(anno + 1, mese_n, g)
            return data_ev.strftime('%Y-%m-%d')
        except ValueError:
            pass
    m = re.search(r'\b(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?\b', testo_lower)
    if m:
        try:
            g, mm = int(m.group(1)), int(m.group(2))
            aa = int(m.group(3)) if m.group(3) else oggi.year
            if aa < 100: aa += 2000
            return datetime(aa, mm, g).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return ''

def estrai_priorita_da_testo(tl):
    if any(p in tl for p in ['urgente', 'importante', 'subito', 'il prima possibile', 'priorità alta']):
        return 'alta'
    if any(p in tl for p in ['con calma', 'non urgente', 'quando puoi', 'poca fretta', 'priorità bassa']):
        return 'bassa'
    return 'media'

def estrai_referente_da_testo(testo):
    m = re.search(r'\b(?:chiamare?|contattare?|sentire?)\s+([A-ZÀ-Ù][a-zà-ù]+(?:\s+[A-ZÀ-Ù][a-zà-ù]+)?)', testo)
    if m: return m.group(1).strip()
    m = re.search(r'\bper\s+([A-ZÀ-Ù][a-zà-ù]+(?:\s+[A-ZÀ-Ù][a-zà-ù]+)?)\b', testo)
    if m: return m.group(1).strip()
    return ''

def _estrai_ora_da_testo(testo_lower):
    """Estrae l'ora se presente (formato: ore 10, alle 15:30, h. 18)."""
    m = re.search(r'\b(?:ore|alle|h\.?)\s*(\d{1,2})(?:[:.,](\d{2}))?\b', testo_lower)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2) if m.group(2) else '00'}"
    return ''


def _estrai_partecipanti(testo_lower):
    """Estrae il numero di partecipanti. Es: '50 partecipanti', '30 bambini', '20 persone'."""
    m = re.search(r'\b(\d+)\s*(?:partecipanti|persone|bambini|ragazzi|alunni|studenti|iscritti)\b', testo_lower)
    if m:
        return int(m.group(1))
    m = re.search(r'\b(?:partecipanti|persone|bambini|ragazzi|alunni|studenti|iscritti)\s*[:\-]?\s*(\d+)\b', testo_lower)
    if m:
        return int(m.group(1))
    return 0


def _rimuovi_ore_dal_testo(testo_lower):
    """Rimuove le ore dal testo per evitare che vengano confuse con quantita."""
    return re.sub(r'\b(?:ore|alle|h\.?)\s*\d{1,2}(?:[:.,]\d{2})?\b', ' ', testo_lower)


def _estrai_scuola_da_riga(riga, testo_lower):
    """Estrae la scuola dalla riga, cercando nell'elenco esistente o dopo parole chiave."""
    scuole = storage.get_dati().get('scuole', [])
    # 1) Cerca scuole esistenti il cui nome appare nel testo
    for sc in scuole:
        nome = (sc.get('nome') or '').lower().strip()
        if nome and nome in testo_lower:
            return sc
    # 2) Cerca dopo parole chiave
    m = re.search(r'\b(?:scuola|istituto|presso|con|alla)\s+([A-Za-zàèéìòù][a-zA-Zàèéìòù\s]{2,40})', riga)
    if m:
        nome = m.group(1).strip()
        # Rimuovi parole chiave comuni in coda
        nome = re.sub(r'\b(il|del|della|dei|delle|a|al|alla|con|per|e|ore|alle)\b.*', '', nome, flags=re.IGNORECASE).strip()
        if nome and len(nome) > 2:
            return nome.title()
    return None


def analizza_testo_libero(testo):
    """Analizza un blocco di testo e ritorna:
    {eventi: [...], movimenti: [...], entita: [...], task: [...], scuole: [...], contatti: [...], liste: [...], righe_non_capite: [...]}"""
    risultato = {
        'eventi': [], 'movimenti': [], 'entita': [], 'task': [],
        'scuole': [], 'contatti': [], 'liste': [], 'righe_non_capite': []
    }
    righe = [r.strip() for r in testo.split('\n') if r.strip()]

    PAROLE_EVENTO = ['evento', 'festa', 'sagra', 'manifestazione', 'incontro',
                     'raduno', 'fiera', 'spettacolo', 'grest', 'concerto',
                     'animazione', 'laboratorio']

    for riga in righe:
        rl = riga.lower()
        capito = False

        # =========================================================
        # STEP 1: EVENTO
        # =========================================================
        ha_parola_evento = any(p in rl for p in PAROLE_EVENTO)
        if ha_parola_evento:
            data_ev = estrai_data_da_testo(rl)
            ora_ev = _estrai_ora_da_testo(rl)
            partecipanti = _estrai_partecipanti(rl)
            scuola = _estrai_scuola_da_riga(riga, rl)

            # Iniziativa: rimuovi parole chiave, ore, date, numeri, scuola
            iniziativa = riga
            for p in PAROLE_EVENTO:
                iniziativa = re.sub(r'\b' + p + r'\b', '', iniziativa, flags=re.IGNORECASE)
            iniziativa = _rimuovi_ore_dal_testo(iniziativa.lower())
            iniziativa = re.sub(r'\b\d{1,2}\s+(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)(?:\s+\d{4})?\b', '', iniziativa, flags=re.IGNORECASE)
            iniziativa = re.sub(r'\b\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?\b', '', iniziativa)
            iniziativa = re.sub(r'\b(oggi|domani|dopodomani)\b', '', iniziativa, flags=re.IGNORECASE)
            iniziativa = re.sub(r'\b\d+\s*(?:partecipanti|persone|bambini|ragazzi|alunni|studenti|iscritti)\b', '', iniziativa, flags=re.IGNORECASE)
            if scuola and isinstance(scuola, dict):
                iniziativa = re.sub(r'\b' + re.escape(scuola['nome']) + r'\b', '', iniziativa, flags=re.IGNORECASE)
            elif scuola and isinstance(scuola, str):
                iniziativa = re.sub(r'\b' + re.escape(scuola) + r'\b', '', iniziativa, flags=re.IGNORECASE)
            iniziativa = re.sub(r'\b(il|del|della|dei|delle|a|al|alla|con|presso|per|scuola|istituto|ore|alle)\b', ' ', iniziativa, flags=re.IGNORECASE)
            iniziativa = re.sub(r'\s+', ' ', iniziativa).strip(' ,-')

            # Fallback: se l'iniziativa e vuota, usa un titolo di default
            if not iniziativa or len(iniziativa) <= 2:
                if isinstance(scuola, dict):
                    iniziativa = "Evento " + scuola['nome']
                elif scuola and isinstance(scuola, str):
                    iniziativa = "Evento " + scuola
                else:
                    iniziativa = "Evento"

            if True:
                risultato['eventi'].append({
                    'data': data_ev or datetime.now().strftime('%Y-%m-%d'),
                    'ora': ora_ev,
                    'iniziativa': iniziativa.title(),
                    'luogo': '',
                    'scuola_id': scuola['id'] if isinstance(scuola, dict) else None,
                    'scuola_nome': scuola['nome'] if isinstance(scuola, dict) else (scuola or ''),
                    'numero_partecipanti': partecipanti,
                    'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0,
                    'referente': '',
                    'nota_carico': '', 'note': riga,
                    'fonte': 'Elabora'
                })
                capito = True

        # =========================================================
        # STEP 2: MOVIMENTO MAGAZZINO (solo se non è un evento)
        # =========================================================
        if not capito:
            categoria = None
            for cat in CATEGORIE_MAGAZZINO_NOTE:
                if cat in rl:
                    categoria = cat
                    break
            if categoria:
                # Rimuovi le ore PRIMA di cercare la quantita
                rl_senza_ore = _rimuovi_ore_dal_testo(rl)
                quantita = estrai_numero_italiano(rl_senza_ore)
                tipo = None
                if any(v in rl for v in VERBI_SCARICO):
                    tipo = 'scarico'
                elif any(v in rl for v in VERBI_CARICO):
                    tipo = 'carico'
                if quantita and tipo:
                    risultato['movimenti'].append({
                        'categoria': categoria, 'tipo': tipo, 'quantita': quantita,
                        'motivo': f'Elabora: "{riga}"',
                        'data': estrai_data_da_testo(rl) or datetime.now().strftime('%Y-%m-%d')
                    })
                    capito = True

        # =========================================================
        # STEP 3: NUOVA ENTITA
        # =========================================================
        if not capito:
            m = re.search(r'(?:acquistato|comprato|ho|abbiamo|preso)\s+(?:un|uno|una|due|tre|quattro|cinque|sei|sette|otto|nove|dieci)?\s*(\d+)?\s*([a-zA-Zàèéìòù]+(?:\s+[a-zA-Zàèéìòù]+){0,4})', riga, re.IGNORECASE)
            if m:
                q = estrai_numero_italiano(riga) or 1
                nome_ent = m.group(2).strip() if m.group(2) else ''
                nome_ent = re.sub(r'\b(per|con|il|del|della|dei|delle|a|al|alla|allo)\b.*', '', nome_ent, flags=re.IGNORECASE).strip()
                if nome_ent and len(nome_ent) > 2:
                    costo = None
                    mc = re.search(r'(?:costo|valore|prezzo)[^\d]{0,20}(\d+)\s*(?:euro|€)?', rl)
                    if mc:
                        costo = float(mc.group(1))
                    fornitore = ''
                    mf = re.search(r'(?:alla|da|presso|fornitore)\s+([A-Z][a-zA-Z]+)', riga)
                    if mf:
                        fornitore = mf.group(1)
                    varianti = []
                    for colore in ['rosso', 'blu', 'verde', 'giallo', 'nero', 'bianco', 'rosa', 'viola']:
                        if colore in rl:
                            varianti.append({'nome_campo': 'colore', 'valore': colore, 'qta': 1})
                    risultato['entita'].append({
                        'nome': nome_ent.title(),
                        'categoria': 'Mezzi',
                        'quantita': q,
                        'costo_unitario': costo,
                        'data_carico': estrai_data_da_testo(rl) or datetime.now().strftime('%Y-%m-%d'),
                        'fornitore': fornitore,
                        'condizione': 'nuovo',
                        'varianti': varianti,
                        'note': riga,
                        'fonte': 'Elabora'
                    })
                    capito = True

        # =========================================================
        # STEP 4: TASK (fallback)
        # =========================================================
        if not capito:
            testo_pulito = riga.strip()
            if len(testo_pulito) > 3 and not testo_pulito.startswith('#'):
                risultato['task'].append({
                    'titolo': testo_pulito[:100],
                    'descrizione': testo_pulito,
                    'data_scadenza': estrai_data_da_testo(rl),
                    'priorita': estrai_priorita_da_testo(rl),
                    'referente': estrai_referente_da_testo(riga),
                    'stato': 'da_fare',
                    'fonte': 'Elabora'
                })

    return risultato

def applica_elaborazione(risultato):
    """Applica un risultato di analizza_testo_libero al database."""
    applicati = {'eventi': 0, 'movimenti': 0, 'entita': 0, 'task': 0, 'scuole': 0, 'contatti': 0, 'liste': 0}
    # EVENTI
    for ev in risultato.get('eventi', []):
        ev['id'] = _nuovo_id()
        scuola_nome = ev.pop('scuola_nome', '') or ''
        if not ev.get('scuola_id') and scuola_nome:
            nome_pulito = scuola_nome.replace('Scuola ', '').replace('scuola ', '').strip()
            trovata = False
            for sc in storage.get_dati().get('scuole', []):
                if (sc.get('nome') or '').lower().strip() == nome_pulito.lower():
                    ev['scuola_id'] = sc['id']
                    trovata = True
                    break
            if not trovata:
                nuova_sc = {
                    'id': _nuovo_id(),
                    'nome': nome_pulito.title(),
                    'referente': '', 'telefono': '', 'email': '',
                    'note': 'Creata da Elabora',
                    'fonte': 'Elabora'
                }
                storage.get_dati().setdefault('scuole', []).append(nuova_sc)
                ev['scuola_id'] = nuova_sc['id']
                applicati['scuole'] += 1
        storage.get_dati().setdefault('eventi', []).append(ev)
        applicati['eventi'] += 1

    for m in risultato.get('movimenti', []):
        cat = m['categoria']
        storage.get_dati()['movimenti'].setdefault(cat, []).append({
            'id': _nuovo_id(), 'tipo': m['tipo'], 'quantita': m['quantita'],
            'motivo': m.get('motivo', ''), 'nota_carico': '',
            'data': m.get('data', datetime.now().strftime('%Y-%m-%d'))
        })
        segno = 1 if m['tipo'] == 'carico' else -1
        storage.get_dati()['stock'][cat] = storage.get_dati()['stock'].get(cat, 0) + segno * m['quantita']
        applicati['movimenti'] += 1
    for e in risultato.get('entita', []):
        e['id'] = _nuovo_id()
        e['creato_il'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        storage.get_dati()['entita'].append(e)
        applicati['entita'] += 1
    for t in risultato.get('task', []):
        t['id'] = _nuovo_id()
        storage.get_dati()['task'].append(t)
        applicati['task'] += 1
    storage.salva()
    return applicati


# ============================================================
# DIZIONARIO SEMANTICO ITALIANO - Dominio Organizer/Eventi
# ============================================================

PAROLE_CHIAVE_MAGAZZINO = {
    'braccialetti': 'braccialetti', 'braccialetto': 'braccialetti',
    'bracciali': 'braccialetti', 'bracciale': 'braccialetti',
    'medaglie': 'medaglie', 'medaglia': 'medaglie',
    'medagliette': 'medaglie', 'medaglietta': 'medaglie',
    'premi': 'medaglie', 'premio': 'medaglie',
    'adesivi': 'adesivi', 'adesivo': 'adesivi',
    'sticker': 'adesivi', 'stickers': 'adesivi',
    'figurine': 'adesivi', 'figurina': 'adesivi',
    'coppe': 'coppe', 'coppa': 'coppe',
    'trofei': 'coppe', 'trofeo': 'coppe',
    'targhe': 'coppe', 'targa': 'coppe',
}

PAROLE_CHIAVE_MULTIPLE = {
    'gadget': ['braccialetti', 'medaglie'],
    'gadgets': ['braccialetti', 'medaglie'],
    'gadget promozionali': ['braccialetti', 'medaglie', 'adesivi'],
    'gadgets promozionali': ['braccialetti', 'medaglie', 'adesivi'],
    'materiale promozionale': ['braccialetti', 'adesivi'],
    'materiali promozionali': ['braccialetti', 'adesivi'],
    'materiale gadgets': ['braccialetti', 'medaglie'],
    'souvenir': ['braccialetti', 'medaglie'],
    'ninnoli': ['braccialetti', 'medaglie'],
    'ninnolo': ['braccialetti', 'medaglie'],
    'omaggi': ['braccialetti', 'medaglie'],
    'omaggio': ['braccialetti', 'medaglie'],
    'kit': ['braccialetti', 'medaglie', 'adesivi'],
    'pacchetto': ['braccialetti', 'medaglie', 'adesivi'],
    'premi e gadgets': ['braccialetti', 'medaglie', 'coppe'],
}

VERBI_SCARICO_ESTESI = [
    'consegno', 'consegnare', 'consegnato', 'consegnati', 'consegnate',
    'do', 'dare', 'dato', 'dati', 'date',
    'distribuisco', 'distribuire', 'distribuito', 'distribuiti',
    'regalo', 'regalare', 'regalato', 'regalati',
    'fornisco', 'fornire', 'fornito', 'forniti',
    'spedisco', 'spedire', 'spedito', 'spediti',
    'porto', 'portare', 'portato', 'portati',
    'utilizzo', 'utilizzare', 'utilizzato',
    'impiego', 'impiegare', 'impiegato',
    'uso', 'usare', 'usato',
    'preparo', 'preparare', 'preparato',
    'messo', 'metto', 'mettere',
    'tolgo', 'togliere', 'tolto',
    'scarico', 'scaricare', 'scaricato',
]

VERBI_CARICO_ESTESI = [
    'carico', 'caricare', 'caricato', 'caricati', 'caricate',
    'ricevo', 'ricevere', 'ricevuto', 'ricevuti', 'ricevute',
    'arrivato', 'arrivati', 'arrivate', 'arriva',
    'acquistato', 'acquistare', 'comprato', 'comprare',
    'ordinato', 'ordinare', 'preso', 'prendere',
    'aggiungo', 'aggiungere', 'aggiunto', 'aggiunti',
]

PER_TUTTI = [
    'a tutti', 'per tutti', 'a tutte', 'per tutte',
    'a ogni', 'per ogni', 'a ciascun', 'per ciascun',
    'a ognuno', 'per ognuno', 'a testa',
]

# ============================================================