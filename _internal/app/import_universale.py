# -*- coding: utf-8 -*-
"""Import universale BRAAAP.

Supporta 10 tipi di importazione da CSV o XLSX:
    eventi, scuole, rubrica, entita, inventario,
    movimenti, uscite, entrate, task, liste

Ogni tipo ha:
    - campo_chiave: per deduplicazione
    - campi: dict {nome_campo -> [alias_possibili]}
    - campi_obbligatori: lista di campi che devono esserci
    - template: esempio di riga per generare template CSV

Funzioni principali:
    - parse_file(file_stream, filename) -> (headers, rows)
    - mapping_automatico(tipo, headers) -> dict
    - valida(tipo, rows, mapping, strategy) -> dict
    - applica(tipo, righe_valide, strategy) -> dict
    - template_csv(tipo) -> str
"""
from __future__ import annotations
import csv
import io
import re
from datetime import datetime


# ============================================================================
# CONFIGURAZIONE TIPI
# ============================================================================

TIPI_SUPPORTATI = {
    'eventi': {
        'label': 'Eventi',
        'sezione_storage': 'eventi',
        'campo_chiave': ['data', 'iniziativa', 'luogo'],
        'campi': {
            'data': ['data', 'date', 'giorno'],
            'iniziativa': ['iniziativa', 'titolo', 'evento', 'nome'],
            'luogo': ['luogo', 'scuola', 'posto', 'location'],
            'numero_partecipanti': ['numero_partecipanti', 'partecipanti', 'num', 'n'],
            'braccialetti': ['braccialetti', 'bracc', 'bracelets'],
            'medaglie': ['medaglie', 'med', 'medals'],
            'adesivi': ['adesivi', 'ades', 'stickers'],
            'coppe': ['coppe', 'coppa', 'cups'],
            'referente': ['referente', 'contatto'],
            'note': ['note', 'notes', 'annotazioni'],
        },
        'campi_obbligatori': ['data', 'iniziativa'],
    },
    'scuole': {
        'label': 'Scuole',
        'sezione_storage': 'scuole',
        'campo_chiave': ['nome'],
        'campi': {
            'nome': ['nome', 'scuola', 'name', 'istituto', 'denominazione'],
            'tipo': ['tipo', 'type', 'categoria'],
            'referente': ['referente', 'contatto', 'persona_riferimento'],
            'telefono': ['telefono', 'tel', 'phone', 'cellulare'],
            'email': ['email', 'mail', 'e-mail', 'pec'],
            'note': ['note', 'notes', 'annotazioni'],
        },
        'campi_obbligatori': ['nome'],
    },
    'rubrica': {
        'label': 'Rubrica',
        'sezione_storage': 'rubrica',
        'campo_chiave': ['nome', 'telefono'],
        'campi': {
            'nome': ['nome', 'name', 'contatto', 'referente'],
            'telefono': ['telefono', 'tel', 'phone', 'cellulare'],
            'email': ['email', 'mail', 'e-mail'],
            'ruolo': ['ruolo', 'role', 'mansione'],
            'note': ['note', 'notes', 'annotazioni'],
            'scuola': ['scuola', 'azienda', 'ente'],
        },
        'campi_obbligatori': ['nome'],
    },
    'entita': {
        'label': 'Entità / Materiali',
        'sezione_storage': 'entita',
        'campo_chiave': ['nome'],
        'campi': {
            'nome': ['nome', 'name', 'materiale', 'oggetto'],
            'categoria': ['categoria', 'category', 'tipo'],
            'quantita': ['quantita', 'qta', 'qty', 'quantity'],
            'costo_unitario': ['costo_unitario', 'costo', 'prezzo', 'price'],
            'data_carico': ['data_carico', 'data', 'date'],
            'fornitore': ['fornitore', 'supplier', 'venditore'],
            'note': ['note', 'notes'],
        },
        'campi_obbligatori': ['nome'],
    },
    'inventario': {
        'label': 'Inventario',
        'sezione_storage': 'inventario',
        'campo_chiave': ['nome'],
        'campi': {
            'nome': ['nome', 'name', 'oggetto', 'bene'],
            'quantita': ['quantita', 'qta', 'qty', 'quantity'],
            'valore_unitario': ['valore_unitario', 'valore', 'prezzo', 'price'],
            'data_acquisto': ['data_acquisto', 'data', 'date'],
            'note': ['note', 'notes'],
        },
        'campi_obbligatori': ['nome'],
    },
    'movimenti': {
        'label': 'Movimenti Magazzino',
        'sezione_storage': 'movimenti',
        'campo_chiave': ['data', 'categoria', 'tipo', 'quantita'],
        'campi': {
            'data': ['data', 'date'],
            'tipo': ['tipo', 'type', 'carico_scarico'],
            'categoria': ['categoria', 'category', 'prodotto'],
            'quantita': ['quantita', 'qta', 'qty'],
            'prezzo_unitario': ['prezzo_unitario', 'prezzo', 'costo', 'price'],
            'motivo': ['motivo', 'note', 'reason'],
        },
        'campi_obbligatori': ['data', 'tipo', 'categoria', 'quantita'],
    },
    'uscite': {
        'label': 'Uscite',
        'sezione_storage': 'uscite',
        'campo_chiave': ['data', 'descrizione', 'importo'],
        'campi': {
            'data': ['data', 'date'],
            'descrizione': ['descrizione', 'description', 'causale'],
            'importo': ['importo', 'amount', 'totale', 'euro'],
            'categoria': ['categoria', 'category', 'tipo'],
            'fornitore': ['fornitore', 'supplier'],
            'note': ['note', 'notes'],
        },
        'campi_obbligatori': ['data', 'descrizione', 'importo'],
    },
    'entrate': {
        'label': 'Entrate',
        'sezione_storage': 'entrate',
        'campo_chiave': ['data', 'descrizione', 'importo'],
        'campi': {
            'data': ['data', 'date'],
            'descrizione': ['descrizione', 'description', 'causale'],
            'importo': ['importo', 'amount', 'totale', 'euro'],
            'tipo': ['tipo', 'type', 'categoria'],
            'note': ['note', 'notes'],
        },
        'campi_obbligatori': ['data', 'descrizione', 'importo'],
    },
    'task': {
        'label': 'Task',
        'sezione_storage': 'task',
        'campo_chiave': ['titolo'],
        'campi': {
            'titolo': ['titolo', 'title', 'task', 'nome'],
            'descrizione': ['descrizione', 'description', 'note'],
            'scadenza': ['scadenza', 'due', 'deadline', 'data'],
            'stato': ['stato', 'status', 'completato'],
        },
        'campi_obbligatori': ['titolo'],
    },
    'liste': {
        'label': 'Liste',
        'sezione_storage': 'liste',
        'campo_chiave': ['nome'],
        'campi': {
            'nome': ['nome', 'name', 'lista', 'titolo'],
            'elementi': ['elementi', 'items', 'contenuto'],
            'note': ['note', 'notes'],
        },
        'campi_obbligatori': ['nome'],
    },
}


# ============================================================================
# PARSING FILE
# ============================================================================

def parse_file(file_bytes, filename):
    """Legge un file CSV o XLSX e ritorna (headers, rows).

    Args:
        file_bytes: bytes del file
        filename: nome file (per capire estensione)

    Returns:
        (headers: list[str], rows: list[list]) con righe come liste di stringhe
    """
    fname_lower = (filename or '').lower()

    if fname_lower.endswith('.xlsx') or fname_lower.endswith('.xls'):
        return _parse_xlsx(file_bytes)
    elif fname_lower.endswith('.csv') or fname_lower.endswith('.txt'):
        return _parse_csv(file_bytes)
    else:
        raise ValueError(f'Formato non supportato: {filename}. Usa .csv o .xlsx')


def _parse_csv(file_bytes):
    """Parse CSV con auto-detect delimitatore."""
    # Prova a decodificare UTF-8, poi latin-1
    try:
        text = file_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = file_bytes.decode('latin-1')

    # Auto-detect delimitatore
    sample = text[:4096]
    delimiters = [',', ';', '\t', '|']
    delim = ','
    max_count = 0
    for d in delimiters:
        c = sample.count(d)
        if c > max_count:
            max_count = c
            delim = d

    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = [row for row in reader if any(cell.strip() for cell in row)]

    if not rows:
        return ([], [])

    headers = [str(h).strip() for h in rows[0]]
    data_rows = [[str(cell).strip() for cell in row] for row in rows[1:]]
    return (headers, data_rows)


def _parse_xlsx(file_bytes):
    """Parse XLSX con openpyxl."""
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise ValueError('openpyxl non installato. Installa con: pip install openpyxl')

    wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows = []
    for row in ws.iter_rows(values_only=True):
        if row and any(cell is not None for cell in row):
            rows.append(['' if cell is None else str(cell).strip() for cell in row])

    if not rows:
        return ([], [])

    headers = rows[0]
    data_rows = rows[1:]
    return (headers, data_rows)


# ============================================================================
# MAPPING AUTOMATICO
# ============================================================================

def _normalizza_header(h):
    """Normalizza header: minuscolo, senza accenti, spazi -> underscore."""
    if not h:
        return ''
    s = str(h).lower().strip()
    # Rimuovi accenti
    sostituzioni = {'à': 'a', 'è': 'e', 'é': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u'}
    for k, v in sostituzioni.items():
        s = s.replace(k, v)
    # Spazi/punti/trattini -> underscore
    s = re.sub(r'[\s\.\-/]+', '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    return s


def mapping_automatico(tipo, headers):
    """Indovina il mapping headers -> campi BRAAAP.

    Args:
        tipo: uno di TIPI_SUPPORTATI
        headers: list[str] intestazioni del file

    Returns:
        dict {campo_memorandia: indice_colonna_o_None}
    """
    if tipo not in TIPI_SUPPORTATI:
        raise ValueError(f'Tipo non supportato: {tipo}')

    config = TIPI_SUPPORTATI[tipo]
    headers_norm = [_normalizza_header(h) for h in headers]

    mapping = {}
    for campo, alias_list in config['campi'].items():
        mapping[campo] = None
        for alias in alias_list:
            alias_norm = _normalizza_header(alias)
            if alias_norm in headers_norm:
                mapping[campo] = headers_norm.index(alias_norm)
                break

    return mapping


# ============================================================================
# VALIDAZIONE
# ============================================================================

def _parse_float(val):
    """Converte stringa in float (gestisce virgola italiana)."""
    if val is None or val == '':
        return 0.0
    try:
        s = str(val).strip().replace('€', '').replace('$', '').replace(',', '.')
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_int(val):
    """Converte stringa in int."""
    if val is None or val == '':
        return 0
    try:
        s = str(val).strip()
        # Rimuovi decimali .0
        if '.' in s:
            s = s.split('.')[0]
        return int(s)
    except (ValueError, TypeError):
        return 0


def _riga_a_dict(row, mapping):
    """Trasforma una lista-row in dict {campo: valore}."""
    result = {}
    for campo, idx in mapping.items():
        if idx is None or idx >= len(row):
            result[campo] = ''
        else:
            result[campo] = row[idx]
    return result


def valida(tipo, rows, mapping, strategy='skip'):
    """Valida le righe e ritorna anteprima.

    Args:
        tipo: uno di TIPI_SUPPORTATI
        rows: list[list] righe del file
        mapping: dict {campo: idx}
        strategy: 'skip' | 'update' | 'ask'

    Returns:
        dict {
            'valide': list[dict],
            'errori': list[dict {riga, messaggio}],
            'duplicati': list[dict],
            'totale': int
        }
    """
    from app import storage

    if tipo not in TIPI_SUPPORTATI:
        raise ValueError(f'Tipo non supportato: {tipo}')

    config = TIPI_SUPPORTATI[tipo]
    sezione = config['sezione_storage']
    campi_obbligatori = config['campi_obbligatori']
    campo_chiave = config['campo_chiave']

    # Dati esistenti per dedup
    dati_esistenti = storage.get_dati().get(sezione, [])
    if isinstance(dati_esistenti, dict):
        # es. movimenti è dict {categoria: [lista]}
        dati_esistenti_flat = []
        for cat, movs in dati_esistenti.items():
            if isinstance(movs, list):
                dati_esistenti_flat.extend(movs)
        dati_esistenti = dati_esistenti_flat

    def _chiave(rec):
        return tuple(str(rec.get(k, '')).strip().lower() for k in campo_chiave)

    chiavi_esistenti = set(_chiave(d) for d in dati_esistenti if isinstance(d, dict))

    valide = []
    errori = []
    duplicati = []
    chiavi_viste = set()

    for i, row in enumerate(rows, start=2):  # start=2 perché riga 1 è header
        rec = _riga_a_dict(row, mapping)

        # Controlla campi obbligatori
        mancanti = [c for c in campi_obbligatori if not str(rec.get(c, '')).strip()]
        if mancanti:
            errori.append({'riga': i, 'messaggio': f'Campi obbligatori mancanti: {", ".join(mancanti)}'})
            continue

        # Normalizza tipi numerici
        for campo in ['quantita', 'numero_partecipanti', 'braccialetti', 'medaglie',
                      'adesivi', 'coppe']:
            if campo in rec:
                rec[campo] = _parse_int(rec[campo])
        for campo in ['importo', 'costo_unitario', 'valore_unitario', 'prezzo_unitario']:
            if campo in rec:
                rec[campo] = _parse_float(rec[campo])

        # Dedup
        chiave = _chiave(rec)
        if chiave in chiavi_esistenti:
            duplicati.append({'riga': i, 'record': rec})
            continue
        if chiave in chiavi_viste:
            duplicati.append({'riga': i, 'record': rec, 'motivo': 'duplicato nel file'})
            continue

        chiavi_viste.add(chiave)
        valide.append({'riga': i, 'record': rec})

    return {
        'valide': valide,
        'errori': errori,
        'duplicati': duplicati,
        'totale': len(rows),
    }


# ============================================================================
# APPLICAZIONE
# ============================================================================

def applica(tipo, righe_valide, strategy='skip'):
    """Applica l'import.

    Args:
        tipo: uno di TIPI_SUPPORTATI
        righe_valide: list[dict {riga, record}] da valida()
        strategy: 'skip' | 'update'

    Returns:
        dict {importati, saltati, aggiornati}
    """
    from app import storage
    from app.utils import _nuovo_id

    if tipo not in TIPI_SUPPORTATI:
        raise ValueError(f'Tipo non supportato: {tipo}')

    config = TIPI_SUPPORTATI[tipo]
    sezione = config['sezione_storage']
    campo_chiave = config['campo_chiave']

    dati = storage.get_dati()
    esistente = dati.get(sezione, [])

    if isinstance(esistente, dict):
        # es. movimenti: dict {categoria: [...]}
        # Per import, usiamo categoria come chiave
        contatore = {'importati': 0, 'saltati': 0, 'aggiornati': 0}
        for r in righe_valide:
            rec = r['record']
            categoria = rec.get('categoria', 'altro')
            if categoria not in esistente:
                esistente[categoria] = []
            rec['id'] = _nuovo_id()
            esistente[categoria].append(rec)
            contatore['importati'] += 1
        dati[sezione] = esistente
        storage.salva()
        return contatore

    # Lista semplice
    def _chiave(rec):
        return tuple(str(rec.get(k, '')).strip().lower() for k in campo_chiave)

    indici_esistenti = {_chiave(d): i for i, d in enumerate(esistente) if isinstance(d, dict)}

    importati = 0
    saltati = 0
    aggiornati = 0

    for r in righe_valide:
        rec = r['record']
        rec['id'] = _nuovo_id()
        chiave = _chiave(rec)

        if chiave in indici_esistenti:
            if strategy == 'update':
                idx = indici_esistenti[chiave]
                # Mantieni id vecchio, aggiorna altri campi
                vecchio_id = esistente[idx].get('id')
                esistente[idx] = rec
                esistente[idx]['id'] = vecchio_id
                aggiornati += 1
            else:
                saltati += 1
        else:
            esistente.append(rec)
            importati += 1
            indici_esistenti[chiave] = len(esistente) - 1

    dati[sezione] = esistente
    storage.salva()

    return {'importati': importati, 'saltati': saltati, 'aggiornati': aggiornati}


# ============================================================================
# TEMPLATE CSV
# ============================================================================

def template_csv(tipo):
    """Ritorna un CSV di esempio per il tipo richiesto."""
    if tipo not in TIPI_SUPPORTATI:
        raise ValueError(f'Tipo non supportato: {tipo}')

    config = TIPI_SUPPORTATI[tipo]
    campi = list(config['campi'].keys())

    # Riga di esempio
    esempi = {
        'eventi': ['2025-03-15', 'Festa di primavera', 'Scuola Primaria Roma', '100', '100', '30', '50', '3', 'Mario Rossi', 'Nota evento'],
        'scuole': ['Scuola Primaria Roma', 'Primaria', 'Mario Rossi', '3331234567', 'mario@scuola.it', 'Nota scuola'],
        'rubrica': ['Mario Rossi', '3331234567', 'mario@email.it', 'Referente', 'Nota contatto', 'Scuola Roma'],
        'entita': ['Carta A4', 'Cancelleria', '10', '5.50', '2025-01-15', 'Cartoleria XYZ', 'Nota'],
        'inventario': ['Computer portatile', '2', '800.00', '2024-09-01', 'Nota inventario'],
        'movimenti': ['2025-03-15', 'carico', 'braccialetti', '500', '0.50', 'Carico iniziale'],
        'uscite': ['2025-03-15', 'Acquisto materiale', '150.00', 'materiali', 'Fornitore ABC', 'Nota uscita'],
        'entrate': ['2025-03-15', 'Contributo scuola', '500.00', 'contributi', 'Nota entrata'],
        'task': ['Chiamare referente', 'Telefonare a Mario per conferma', '2025-03-20', 'aperto'],
        'liste': ['Spesa settimanale', 'latte,pane,uova', 'Nota lista'],
    }

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=';')
    writer.writerow(campi)
    if tipo in esempi:
        writer.writerow(esempi[tipo])

    return buf.getvalue()