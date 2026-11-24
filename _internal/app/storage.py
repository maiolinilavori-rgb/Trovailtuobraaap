from __future__ import annotations
import json
import os
import threading
from datetime import datetime
from app.config import DATA_FILE
from app.utils import _nuovo_id, _intero

_lock = threading.RLock()
_dati = None


def get_dati():
    """Ritorna il dizionario globale dei dati (caricandolo se serve)."""
    global _dati
    if _dati is None:
        _dati = carica_dati()
    return _dati


def set_dati(nuovi):
    global _dati
    _dati = nuovi


def salva():
    try:
        sync_scuole_rubrica(get_dati())
    except Exception:
        pass
    """Salva il dizionario globale su disco."""
    salva_dati(get_dati())


def _dati_default():
    return {
        'eventi': [],
        'scuole': [],  # solo scuole vere, ALTRO non è più qui
        'contatti': [],
        'rubrica': [],
        'task': [],
        'movimenti': {'braccialetti': [], 'medaglie': [], 'adesivi': [], 'coppe': []},
        'tipi_evento': ['INCONTRO', 'MEDIE', 'PRIMARIA', 'SECONDARIA', 'CAROVANA', 'CONCERTO', 'ALTRO'],
        'logo': None,
        'note_calendario': [],
        'note_personali': {},
        'inventario': [],
        'mezzi': [],
        'entita': [],           # entità dinamiche (GoKart, Tappetone...)
        'categorie_entita': ['Mezzi', 'Attrezzatura', 'Materiale informativo', 'Altro'],
        'liste': [],            # liste tipo "spesa"
        'postit': [],           # post-it della lavagna
        'portafoglio': [],
        'stock': {'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0},
        'soglie_scorta': {'braccialetti': 50, 'medaglie': 30, 'adesivi': 30, 'coppe': 3},
        'vocabolario': {'categorie': {}, 'tentativi': []},
        'meteo_preferiti': [],
        'comandi_log': [],
        'note_vocali': [],
        'wakeword_attiva': False,
        'testi_elaborati': [],  # hash testi elaborati per dedup
        'giacenza_iniziale_impostata': False,
        'giacenza_iniziale_data': None,
        'import_excel_fatto': False,
    }

def carica_dati():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            base = _dati_default()
            for k, v in base.items():
                d.setdefault(k, v)
            d['stock'].setdefault('coppe', 0)
            d['movimenti'].setdefault('coppe', [])
            # MIGRAZIONE: rimuovi pseudo-scuola ALTRO da scuole, sposta eventi a null
            scuole_da_rimuovere = [s for s in d['scuole'] if s.get('speciale') or s.get('nome', '').upper() == 'ALTRO']
            if scuole_da_rimuovere:
                ids_altro = {s['id'] for s in scuole_da_rimuovere}
                for e in d['eventi']:
                    if e.get('scuola_id') in ids_altro:
                        e['scuola_id'] = None
                d['scuole'] = [s for s in d['scuole'] if s.get('id') not in ids_altro]
                salva_dati(d)
            return d
        except Exception as e:
            log.error('Errore lettura %s: %s', DATA_FILE, e)
    return _dati_default()

def salva_dati(d):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, default=str, ensure_ascii=False)
        try:
            _backup_automatico()
        except Exception:
            pass
    except Exception as e:
        log.error('Errore scrittura %s: %s', DATA_FILE, e)

def ricalcola_stock():
    stock = {'braccialetti': 0, 'medaglie': 0, 'adesivi': 0, 'coppe': 0}
    for cat, movs in dati.get('movimenti', {}).items():
        for m in movs:
            q = _intero(m.get('quantita'))
            if m.get('tipo') == 'carico':
                stock[cat] = stock.get(cat, 0) + q
            else:
                stock[cat] = stock.get(cat, 0) - q
    storage.get_dati()['stock'] = stock
    storage.salva()
    return stock

def _trova_scuola(sid):
    for s in dati.get('scuole', []):
        if s.get('id') == sid:
            return s
    return None


def sync_scuole_rubrica(dati):
    scuole = dati.get('scuole', [])
    rubrica = dati.setdefault('rubrica', [])
    scuole_by_id = {s.get('id'): s for s in scuole if s.get('id') is not None}

    for s in scuole:
        sid = s.get('id')
        tel = (s.get('telefono') or '').strip()
        email = (s.get('email') or '').strip()
        ref = (s.get('referente') or '').strip()
        nome_s = (s.get('nome') or '').strip()
        if not (tel or email or ref or nome_s):
            continue
        nome_c = f"{ref} ({nome_s})" if ref else f"Segreteria - {nome_s}"
        trovato = next((r for r in rubrica if r.get('scuola_id') == sid), None)
        if not trovato:
            trovato = next((r for r in rubrica if (r.get('nome') or '').strip().lower() == nome_c.lower()), None)
        if trovato:
            trovato['scuola_id'] = sid
            if ref: trovato['nome'] = nome_c
            if tel: trovato['telefono'] = tel
            if email: trovato['email'] = email
            if s.get('tipo'): trovato['ruolo'] = s.get('tipo')
        elif tel or email or ref:
            rubrica.append({
                'id': int(sid) + 500000 if isinstance(sid, int) else len(rubrica) + 900000,
                'nome': nome_c,
                'ruolo': s.get('tipo') or 'Scuola / Segreteria',
                'telefono': tel,
                'email': email,
                'scuola_id': sid,
                'note': s.get('note') or f"Collegato a {nome_s}"
            })

    # Sincronizza anche eventuali modifiche fatte in Rubrica verso la Scuola collegata
    for r in rubrica:
        sid = r.get('scuola_id')
        if sid in scuole_by_id:
            s = scuole_by_id[sid]
            if r.get('telefono') and not s.get('telefono'): s['telefono'] = r['telefono']
            if r.get('email') and not s.get('email'): s['email'] = r['email']
