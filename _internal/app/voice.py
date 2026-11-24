from __future__ import annotations
import os
import re
import wave
import json as json_lib
import base64
from datetime import datetime
from app.config import BUNDLE_DIR, APP_DIR, DATA_DIR
from app.utils import _nuovo_id, _intero
from app import storage


def _trova_modello_vosk():
    candidati = [
        os.path.join(BUNDLE_DIR, 'vosk-model-it-0.22'),       # dentro _MEIPASS (exe)
        os.path.join(APP_DIR, 'vosk-model-it-0.22'),          # accanto all'exe
        os.path.join(DATA_DIR, 'vosk-model-it-0.22'),         # in APPDATA
        os.path.join(os.getcwd(), 'vosk-model-it-0.22'),      # cartella corrente
    ]
    for c in candidati:
        if os.path.isdir(c):
            return c
    return candidati[0]

def _get_vosk_model():
    """Ritorna il modello Vosk caricato, caricandolo alla prima chiamata.
    Il modello resta in memoria per tutte le trascrizioni successive."""
    global _vosk_model
    if _vosk_model is None:
        try:
            from vosk import Model
            if not os.path.exists(_vosk_model_path):
                return None
            log.info('📥 Caricamento modello Vosk (una volta sola)...')
            _vosk_model = Model(_vosk_model_path)
            log.info('✅ Modello Vosk pronto.')
        except ImportError:
            return None
    return _vosk_model

def interpreta_comando_vocale(testo):
    """Interpreta un comando vocale tipo 'BRAAAP carica 50 braccialetti'.
    Ritorna {'azione': str, 'parametri': dict, 'testo': str}."""
    if not testo:
        return {'azione': 'sconosciuto', 'parametri': {}, 'testo': ''}

    # Rimuovi wakeword (bra + a* + p+ con eventuale spazio/variazioni)
    t = re.sub(r'\bbra+a*p+\b', ' ', testo, flags=re.IGNORECASE)
    t = re.sub(r'\s+', ' ', t).strip()
    tl = t.lower()

    azione = 'sconosciuto'
    parametri = {}

    # Movimento: carica/scarica N categoria
    m = re.search(r'\b(carica|aggiungi|comprato|ricevuto|arrivato)\s+(?:n\s+)?(\d+)\s+([a-z]+)', tl)
    if m:
        cat = m.group(3).rstrip('i') + ('i' if m.group(3).endswith('i') else '')
        # normalizza al singolare/plurale accettato
        for c in CATEGORIE_MAGAZZINO_NOTE:
            if c.startswith(m.group(3)[:4]) or m.group(3).startswith(c[:4]):
                cat = c
                break
        return {'azione': 'movimento',
                'parametri': {'tipo': 'carico', 'quantita': int(m.group(2)), 'categoria': cat},
                'testo': testo}

    m = re.search(r'\b(scarica|togli|rimuovi|distribuisci|usato|usati|consegnato)\s+(?:n\s+)?(\d+)\s+([a-z]+)', tl)
    if m:
        cat = m.group(3)
        for c in CATEGORIE_MAGAZZINO_NOTE:
            if c.startswith(m.group(3)[:4]) or m.group(3).startswith(c[:4]):
                cat = c
                break
        return {'azione': 'movimento',
                'parametri': {'tipo': 'scarico', 'quantita': int(m.group(2)), 'categoria': cat},
                'testo': testo}

    # Quante X ho?
    m = re.search(r'\b(quante|quanti)\s+([a-z]+)\s+ho', tl)
    if m:
        cat = m.group(2)
        for c in CATEGORIE_MAGAZZINO_NOTE:
            if c.startswith(m.group(2)[:4]):
                cat = c
                break
        return {'azione': 'interroga_stock', 'parametri': {'categoria': cat}, 'testo': testo}

    # Ricordami di ...
    m = re.search(r'\bricordami\s+(?:di\s+)?(.+)', tl)
    if m:
        return {'azione': 'task',
                'parametri': {'titolo': m.group(1).strip()[:120],
                              'data_scadenza': estrai_data_da_testo(tl),
                              'priorita': estrai_priorita_da_testo(tl)},
                'testo': testo}

    # Crea evento / nuovo evento
    if re.search(r'\b(crea|nuovo|aggiungi)\s+(un\s+)?evento', tl):
        return {'azione': 'evento',
                'parametri': {'data': estrai_data_da_testo(tl) or datetime.now().strftime('%Y-%m-%d'),
                              'iniziativa': t[:100]},
                'testo': testo}

    return {'azione': 'sconosciuto', 'parametri': {}, 'testo': testo}

def _esegui_risultato_vocale(risultato, testo_originale):
    """Esegue l'azione interpretata e ritorna dict con success/message/tipo_azione."""
    azione = risultato.get('azione')
    p = risultato.get('parametri', {})

    if azione == 'movimento':
        cat = p.get('categoria')
        if cat not in CATEGORIE_MAGAZZINO_NOTE:
            return {'success': False, 'error': f'Categoria non valida: {cat}'}
        tipo = p.get('tipo')
        q = _intero(p.get('quantita'))
        if q <= 0:
            return {'success': False, 'error': 'Quantità non valida'}
        storage.get_dati()['movimenti'].setdefault(cat, []).append({
            'id': _nuovo_id(), 'tipo': tipo, 'quantita': q,
            'motivo': f'Voce: {testo_originale[:80]}',
            'nota_carico': '',
            'data': datetime.now().strftime('%Y-%m-%d')
        })
        segno = 1 if tipo == 'carico' else -1
        storage.get_dati()['stock'][cat] = storage.get_dati()['stock'].get(cat, 0) + segno * q
        storage.salva()
        return {'success': True, 'tipo_azione': 'movimento',
                'message': f"{tipo.title()} di {q} {cat} registrato. Stock ora: {storage.get_dati()['stock'][cat]}"}

    if azione == 'interroga_stock':
        cat = p.get('categoria')
        if cat not in CATEGORIE_MAGAZZINO_NOTE:
            return {'success': False, 'error': f'Categoria non valida: {cat}'}
        stock_attuale = storage.get_dati()['stock'].get(cat, 0)
        return {'success': True, 'tipo_azione': 'stock',
                'message': f'Ho {stock_attuale} {cat} in magazzino'}

    if azione == 'task':
        titolo = (p.get('titolo') or '').strip()
        if not titolo:
            return {'success': False, 'error': 'Titolo task vuoto'}
        dati.setdefault('task', []).append({
            'id': _nuovo_id(), 'titolo': titolo[:120],
            'descrizione': testo_originale,
            'data_scadenza': p.get('data_scadenza', ''),
            'priorita': p.get('priorita', 'media'),
            'stato': 'da_fare', 'fonte': 'voce'
        })
        storage.salva()
        return {'success': True, 'tipo_azione': 'task',
                'message': f"Task creato: {titolo[:60]}"}

    if azione == 'evento':
        dati.setdefault('eventi', []).append({
            'id': _nuovo_id(),
            'data': p.get('data') or datetime.now().strftime('%Y-%m-%d'),
            'iniziativa': (p.get('iniziativa') or '')[:120],
            'scuola_id': None, 'luogo': '',
            'numero_partecipanti': 0, 'braccialetti': 0, 'medaglie': 0,
            'adesivi': 0, 'coppe': 0,
            'note': testo_originale, 'fonte': 'voce'
        })
        storage.salva()
        return {'success': True, 'tipo_azione': 'evento',
                'message': 'Evento creato'}

    return {'success': True, 'tipo_azione': 'nessuna',
            'message': 'Comando non riconosciuto. Salvato come nota vocale.'}
