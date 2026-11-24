"""Vocabolario dinamico + Wake-word di Braaap."""
from __future__ import annotations
import re
from app import storage


# ============================================================
# WAKE-WORDS (built-in, sempre attive)
# ============================================================
WAKE_WORDS = [
    'braap', 'braaap', 'braapp', 'braaaap', 'brap',
    'ehi braaap', 'ehi braap', 'ok braaap', 'ok braap',
    'forza braaap', 'ciao braaap', 'hey braaap', 'hey braap',
]


# ============================================================
# DIZIONARIO CONTESTUALE (organizer)
# ============================================================
# Parole tipiche del dominio organizer, con significato di default
DIZIONARIO_CONTESTUALE = {
    # Materiale magazzino
    'gadget': 'braccialetti e medaglie e adesivi (materiale promozionale)',
    'gadgets': 'braccialetti e medaglie e adesivi (materiale promozionale)',
    'gadget promozionali': 'braccialetti e medaglie e adesivi',
    'promo': 'materiale promozionale (braccialetti, adesivi)',
    'promozionale': 'materiale promozionale',
    'souvenir': 'braccialetti e medaglie',
    'ninnoli': 'braccialetti e medaglie',
    'omaggi': 'braccialetti e medaglie',
    'bracciali': 'braccialetti',
    'medagliette': 'medaglie',
    'sticker': 'adesivi',
    'stickers': 'adesivi',
    'trofei': 'coppe',

    # Eventi
    'festa': 'evento di tipo festa',
    'sagra': 'evento di tipo sagra',
    'raduno': 'evento di tipo raduno',
    'open day': 'evento di orientamento scolastico',
    'grest': 'evento estivo parrocchiale',

    # Operazioni
    'consegna': 'scarico dal magazzino',
    'distribuzione': 'scarico dal magazzino',
    'carico': 'carico al magazzino',
    'rifornimento': 'carico al magazzino',

    # Contesto scolastico
    'plesso': 'scuola',
    'istituto': 'scuola',
    'comprensivo': 'istituto comprensivo (scuola)',
}


# ============================================================
# FUNZIONI PRINCIPALI
# ============================================================
def _get_vocabolario():
    """Ritorna il vocabolario appreso (dict parola->dati)."""
    d = storage.get_dati()
    d.setdefault('vocabolario_appreso', {})
    return d['vocabolario_appreso']


def rileva_wake_word(testo):
    """Rileva se il testo contiene una wake-word e ritorna (trovata, testo_pulito)."""
    if not testo:
        return False, testo

    tl = testo.lower().strip()
    for wake in WAKE_WORDS:
        # Wake-word all'inizio
        if tl.startswith(wake):
            # Rimuovi la wake-word dall'inizio
            testo_pulito = testo[len(wake):].strip(' ,;:!?-')
            return True, testo_pulito

    return False, testo


def impara(parola, significato):
    """Impara una nuova parola nel vocabolario."""
    parola = parola.lower().strip()
    if not parola or len(parola) < 2:
        return {'success': False, 'error': 'Parola troppo corta'}

    d = storage.get_dati()
    d.setdefault('vocabolario_appreso', {})

    if parola in d['vocabolario_appreso']:
        # Aggiorna il significato esistente
        d['vocabolario_appreso'][parola]['significato'] = significato
        d['vocabolario_appreso'][parola]['usi'] = d['vocabolario_appreso'][parola].get('usi', 0) + 1
    else:
        d['vocabolario_appreso'][parola] = {
            'significato': significato,
            'usi': 1,
            'fonte': 'utente',
        }

    storage.salva()
    return {'success': True, 'parola': parola, 'significato': significato}


def cerca(parola):
    """Cerca una parola nel vocabolario (appreso + contestuale)."""
    parola = parola.lower().strip()

    # 1) Vocabolario appreso
    vocab = _get_vocabolario()
    if parola in vocab:
        return {
            'trovata': True,
            'significato': vocab[parola]['significato'],
            'fonte': 'appreso',
            'usi': vocab[parola].get('usi', 0),
        }

    # 2) Dizionario contestuale
    if parola in DIZIONARIO_CONTESTUALE:
        return {
            'trovata': True,
            'significato': DIZIONARIO_CONTESTUALE[parola],
            'fonte': 'contesto',
            'usi': 0,
        }

    return {'trovata': False}


def incrementa_uso(parola):
    """Incrementa il contatore d'uso di una parola."""
    parola = parola.lower().strip()
    d = storage.get_dati()
    vocab = d.get('vocabolario_appreso', {})
    if parola in vocab:
        vocab[parola]['usi'] = vocab[parola].get('usi', 0) + 1
        storage.salva()


def traduci_testo(testo):
    """Traduce un testo usando il vocabolario (per il prompt Groq)."""
    if not testo:
        return testo

    vocab = _get_vocabolario()
    risultato = testo

    # Sostituisci le parole lunghe prima (evita conflitti)
    parole_ordinate = sorted(vocab.keys(), key=len, reverse=True)

    for parola in parole_ordinate:
        # Regex case-insensitive con word boundary
        pattern = r'\b' + re.escape(parola) + r'\b'
        significato = vocab[parola].get('significato', '')
        if significato:
            # Sostituisci con significato tra parentesi solo se è diverso
            risultato = re.sub(
                pattern,
                f"{parola} ({significato})",
                risultato,
                flags=re.IGNORECASE
            )
            incrementa_uso(parola)

    return risultato


def lista_completa():
    """Ritorna tutto il vocabolario (appreso + contestuale)."""
    vocab = _get_vocabolario()
    appreso = [
        {'parola': k, 'significato': v.get('significato', ''), 'usi': v.get('usi', 0), 'fonte': 'appreso'}
        for k, v in sorted(vocab.items(), key=lambda x: -x[1].get('usi', 0))
    ]
    contestuale = [
        {'parola': k, 'significato': v, 'usi': 0, 'fonte': 'contesto'}
        for k, v in DIZIONARIO_CONTESTUALE.items()
    ]
    return {'appreso': appreso, 'contesto': contestuale}


def dimentica(parola):
    """Rimuove una parola dal vocabolario appreso."""
    parola = parola.lower().strip()
    d = storage.get_dati()
    vocab = d.get('vocabolario_appreso', {})
    if parola in vocab:
        del vocab[parola]
        storage.salva()
        return {'success': True}
    return {'success': False, 'error': 'Parola non trovata'}


def estrai_apprendimento(testo):
    """Estrae comandi di apprendimento dal testo.
    Esempi:
    - "chiama X Y"
    - "X si dice Y"
    - "X significa Y"
    - "impara X = Y"
    """
    tl = testo.lower().strip()

    pattern = [
        r'chiama\s+([a-zàèéìòù]+)\s+(.+)',
        r'impara\s+([a-zàèéìòù]+)\s*[=:]\s*(.+)',
        r'([a-zàèéìòù]+)\s+si\s+dice\s+(.+)',
        r'([a-zàèéìòù]+)\s+significa\s+(.+)',
    ]

    for p in pattern:
        m = re.search(p, tl)
        if m:
            return {'parola': m.group(1).strip(), 'significato': m.group(2).strip()}

    return None

# ============================================================
# CORRETTORE POST-WHISPER - Aggiusta errori fonetici
# ============================================================
import difflib

# Varianti fonetiche comuni di Whisper (voci italiane)
VARIANTI_FONETICHE = {
    # Wake-word Braaap
    'brap': 'braap',
    'braap': 'braap',
    'braapp': 'braaap',
    'braaap': 'braaap',
    'braaaap': 'braaap',
    'bra': 'braap',
    'brap brap': 'braap',
    'rap': 'braap',

    # Categorie magazzino
    'bracialetti': 'braccialetti',
    'braccialett': 'braccialetti',
    'braccialet': 'braccialetti',
    'bracciali': 'braccialetti',
    'braccia': 'braccialetti',
    'brccialetti': 'braccialetti',
    'braccialeti': 'braccialetti',
    'bracciali': 'braccialetti',

    'medagli': 'medaglie',
    'medaglia': 'medaglie',
    'medagliet': 'medaglie',
    'medagliett': 'medaglie',

    'adesiv': 'adesivi',
    'adesivo': 'adesivi',
    'adesivvi': 'adesivi',
    'adesii': 'adesivi',

    'coppa': 'coppe',
    'copp': 'coppe',
    'trofei': 'coppe',
    'trofeo': 'coppe',

    # Verbi operativi
    'consegni': 'consegno',
    'consegne': 'consegno',
    'distribuisc': 'distribuisco',
    'caric': 'carico',
    'scaric': 'scarico',

    # Domini
    'gadget': 'gadget',
    'gadgett': 'gadget',
    'gadgett': 'gadget',
    'gadgetz': 'gadget',
    'gadgetts': 'gadget',

    # Scuole
    'scuol': 'scuola',
    'scuole': 'scuola',

    # Eventi
    'event': 'evento',
    'eventi': 'evento',
    'eventto': 'evento',

    # Task
    'tasck': 'task',
    'tasc': 'task',
}


def correggi_trascrizione(testo):
    """Corregge errori fonetici comuni nella trascrizione di Whisper.
    Usa:
    1) Varianti fonetiche hardcoded
    2) Parole del vocabolario appreso (con similarita' > 0.8)
    Zero chiamate a Groq. Zero token.
    """
    if not testo:
        return testo

    import re

    # 1) Raccogli tutte le parole del vocabolario (apprese + contestuali)
    vocab = _get_vocabolario()
    parole_valide = list(vocab.keys()) + list(DIZIONARIO_CONTESTUALE.keys()) + WAKE_WORDS

    # 2) Aggiungi le parole hardcoded come "sorgenti" da correggere
    tutte_le_parole = set(parole_valide)
    for parola in tutte_le_parole:
        if parola not in VARIANTI_FONETICHE:
            VARIANTI_FONETICHE[parola] = parola

    # 3) Processa parola per parola
    def correggi_parola(match):
        p = match.group(0)
        pl = p.lower()

        # 3a) Match esatto nel dizionario varianti
        if pl in VARIANTI_FONETICHE:
            corretta = VARIANTI_FONETICHE[pl]
            # Mantieni la maiuscola iniziale se c'era
            if p[0].isupper():
                return corretta.capitalize()
            return corretta

        # 3b) Similarita' con le parole del vocabolario (>= 0.82)
        if len(pl) >= 4:
            matches = difflib.get_close_matches(pl, list(tutte_le_parole), n=1, cutoff=0.82)
            if matches:
                corretta = matches[0]
                # Se la parola non è gia' nel vocabolario appreso come variante, salvala
                if corretta in vocab and pl != corretta:
                    # Salva come variante per la prossima volta
                    try:
                        d = storage.get_dati()
                        d.setdefault('varianti_fonetiche', {})
                        d['varianti_fonetiche'][pl] = corretta
                        storage.salva()
                    except Exception:
                        pass
                if p[0].isupper():
                    return corretta.capitalize()
                return corretta

        return p

    # Sostituisci tutte le parole
    risultato = re.sub(r'\b[a-zA-Zàèéìòù]+\b', correggi_parola, testo)
    return risultato


def _get_varianti_salvate():
    """Ritorna le varianti fonetiche apprese automaticamente."""
    d = storage.get_dati()
    return d.get('varianti_fonetiche', {})


def lista_varianti():
    """Ritorna tutte le varianti fonetiche (hardcoded + apprese)."""
    hardcoded = [{'da': k, 'a': v, 'fonte': 'built-in'} for k, v in VARIANTI_FONETICHE.items() if k != v]
    apprese = [{'da': k, 'a': v, 'fonte': 'auto'} for k, v in _get_varianti_salvate().items()]
    return {'hardcoded': hardcoded, 'apprese': apprese}