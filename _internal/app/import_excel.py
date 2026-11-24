from __future__ import annotations
import os
import re
from datetime import datetime
from openpyxl import load_workbook
from app.utils import _parse_data, _intero, _nuovo_id
from app.config import NOMI_FILE_BRACCIALETTI, NOMI_FILE_CONTATTI
from app import storage


def trova_file_excel(candidati):
    for nome in candidati:
        if os.path.exists(nome):
            return nome
    return None

def _trova_o_crea_scuola(nome, tipo='Scuola'):
    if not nome:
        return None
    nome_up = nome.upper().strip()
    for s in storage.get_dati()['scuole']:
        if s['nome'].upper() == nome_up:
            return s['id']
    nuovo_id = _nuovo_id()
    storage.get_dati()['scuole'].append({
        'id': nuovo_id, 'nome': nome_up, 'tipo': tipo,
        'referente': '', 'telefono': '', 'email': ''
    })
    return nuovo_id

def analizza_excel_braccialetti(path):
    """Legge il file BRACCIALETTI e ritorna lista di eventi candidati (anteprima)."""
    eventi_trovati = []
    scuole_trovate = set()
    wb = load_workbook(path, data_only=True)
    if 'BRACCIALETTI' not in wb.sheetnames:
        return eventi_trovati, scuole_trovate
    ws = wb['BRACCIALETTI']
    # Header fissi: A=data, B=numero, C=iniziativa, D=luogo, E=note/coppe, F=braccialetti, G=medaglie, H=extra
    ultima_data = None
    for row in range(3, ws.max_row + 1):
        data_raw = ws.cell(row=row, column=1).value
        iniziativa = str(ws.cell(row=row, column=3).value or '').strip()
        if not iniziativa:
            continue
        # Salta righe di totale
        if 'SUM' in str(data_raw) or iniziativa.startswith('='):
            continue
        data_ev = _parse_data(data_raw)
        if data_ev:
            ultima_data = data_ev
        elif ultima_data:
            data_ev = ultima_data
        else:
            continue
        luogo = str(ws.cell(row=row, column=4).value or '').strip()
        col_e = str(ws.cell(row=row, column=5).value or '')
        col_h = str(ws.cell(row=row, column=8).value or '')
        num = _intero(ws.cell(row=row, column=2).value)
        bracc = _intero(ws.cell(row=row, column=6).value)
        med = _intero(ws.cell(row=row, column=7).value)
        coppe = 0
        m = re.search(r'(\d+)\s*copp', col_e.lower())
        if m:
            coppe = int(m.group(1))
        extra_note = []
        if col_e:
            extra_note.append(col_e)
        if col_h:
            extra_note.append(col_h)
        if luogo:
            scuole_trovate.add(luogo.upper())
        eventi_trovati.append({
            'data': data_ev.strftime('%Y-%m-%d'),
            'numero_partecipanti': num,
            'iniziativa': iniziativa,
            'luogo': luogo,
            'braccialetti': bracc,
            'medaglie': med,
            'adesivi': 0,
            'coppe': coppe,
            'note': ' | '.join(n for n in extra_note if n),
            'referente': '',
            'nota_carico': '',
        })
    return eventi_trovati, scuole_trovate

def analizza_excel_contatti(path):
    """Ritorna lista di scuole + contatti candidati (anteprima)."""
    scuole = []
    contatti = []
    wb = load_workbook(path, data_only=True)
    for sheet_name in wb.sheetnames:
        nome_norm = ' '.join(sheet_name.split()).upper()
        if nome_norm == 'RIEPILOGO GENERALE':
            continue
        ws = wb[sheet_name]
        # Cerca tipo (cella B4 circa) e direzione (A4)
        tipo = 'Scuola'
        for r in range(1, 8):
            for c in range(1, 5):
                v = ws.cell(row=r, column=c).value
                if v and str(v).strip().lower() in ('secondaria', 'primaria', 'media', 'superiore'):
                    tipo = str(v).strip().capitalize()
                    break
        scuole.append({'nome': sheet_name.upper(), 'tipo': tipo})

        # Trova PERSONA DI RIFERIMENTO
        riga_pdr = None
        for r in range(1, min(ws.max_row, 60)):
            for c in range(1, 6):
                v = ws.cell(row=r, column=c).value
                if v and 'PERSONA DI RIFERIMENTO' in str(v).upper():
                    riga_pdr = r
                    break
            if riga_pdr:
                break
        if riga_pdr:
            vuote = 0
            for r in range(riga_pdr + 1, min(riga_pdr + 12, ws.max_row + 1)):
                celle = []
                for c in range(1, 8):
                    v = ws.cell(row=r, column=c).value
                    if v and str(v).strip():
                        celle.append(str(v).strip())
                if not celle:
                    vuote += 1
                    if vuote >= 2:
                        break
                    continue
                vuote = 0
                nome_c, tel_c, email_c = None, None, None
                for v in celle:
                    if '@' in v and email_c is None:
                        email_c = v
                    elif re.fullmatch(r'[\d\s\+\-\(\)]{6,}', v) and tel_c is None:
                        tel_c = v
                    elif len(v) < 60 and not any(ch.isdigit() for ch in v) and nome_c is None:
                        nome_c = v
                upper = ' '.join(celle).upper()
                if 'PROGETT' in upper or 'DATA CONTATTO' in upper:
                    break
                if nome_c or tel_c or email_c:
                    contatti.append({
                        'nome': nome_c or '', 'telefono': tel_c or '',
                        'email': email_c or '', 'scuola': sheet_name.upper(),
                        'ruolo': '', 'note': '', 'fonte': 'import'
                    })
    return scuole, contatti

def applica_import_excel(applica_eventi=True, applica_contatti=True):
    """Esegue l'import vero dopo l'anteprima. Ritorna un riepilogo."""
    riepilogo = {'scuole_create': 0, 'eventi_importati': 0, 'contatti_importati': 0}
    file_bracc = trova_file_excel(NOMI_FILE_BRACCIALETTI)
    file_cont = trova_file_excel(NOMI_FILE_CONTATTI)

    if applica_contatti and file_cont:
        scuole, contatti = analizza_excel_contatti(file_cont)
        for sc in scuole:
            if not any(s['nome'].upper() == sc['nome'] for s in storage.get_dati()['scuole']):
                storage.get_dati()['scuole'].append({
                    'id': _nuovo_id(), 'nome': sc['nome'], 'tipo': sc['tipo'],
                    'referente': '', 'telefono': '', 'email': ''
                })
                riepilogo['scuole_create'] += 1
        for c in contatti:
            dup = any(e.get('nome') == c['nome'] and e.get('telefono') == c['telefono']
                      for e in storage.get_dati()['rubrica'])
            if not dup:
                c['id'] = _nuovo_id()
                storage.get_dati()['rubrica'].append(c)
                riepilogo['contatti_importati'] += 1

    if applica_eventi and file_bracc:
        eventi, scuole_nomi = analizza_excel_braccialetti(file_bracc)
        for nome in scuole_nomi:
            if not any(s['nome'].upper() == nome for s in storage.get_dati()['scuole']):
                storage.get_dati()['scuole'].append({
                    'id': _nuovo_id(), 'nome': nome, 'tipo': 'Altro',
                    'referente': '', 'telefono': '', 'email': ''
                })
                riepilogo['scuole_create'] += 1
        for ev in eventi:
            # dedup: stessa data + iniziativa + luogo
            dup = any(e.get('data') == ev['data'] and
                      e.get('iniziativa', '').upper() == ev['iniziativa'].upper() and
                      e.get('luogo', '').upper() == ev['luogo'].upper()
                      for e in storage.get_dati()['eventi'])
            if dup:
                continue
            scuola_id = None
            if ev['luogo']:
                for s in storage.get_dati()['scuole']:
                    if s['nome'].upper() == ev['luogo'].upper():
                        scuola_id = s['id']
                        break
            ev['id'] = _nuovo_id()
            ev['scuola_id'] = scuola_id
            storage.get_dati()['eventi'].append(ev)
            riepilogo['eventi_importati'] += 1

    storage.get_dati()['import_excel_fatto'] = True
    storage.salva()
    return riepilogo
