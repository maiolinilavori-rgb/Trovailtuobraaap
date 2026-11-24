"""Helper per l'export Excel/CSV."""
from __future__ import annotations
import io as io_mod
import csv as csv_mod
import json
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from app import storage


def _scrivi_foglio_excel(ws, intestazioni, righe):
    """Scrive un foglio Excel con header formattati."""
    ws.append(intestazioni)
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='37474F', end_color='37474F', fill_type='solid')
    for r in righe:
        ws.append(r)
    for i, _ in enumerate(intestazioni, 1):
        col = get_column_letter(i)
        max_len = len(str(intestazioni[i - 1]))
        for cell in ws[col]:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col].width = min(max_len + 2, 50)


def _dati_per_sezione(sezione, filtro_anno=None):
    """Ritorna (intestazioni, righe) per la sezione richiesta."""
    d = storage.get_dati()

    if sezione == 'eventi':
        intest = ['Data', 'Scuola/Luogo', 'Iniziativa', 'Partecipanti',
                  'Braccialetti', 'Medaglie', 'Adesivi', 'Coppe', 'Referente', 'Note']
        righe = []
        for e in sorted(d.get('eventi', []), key=lambda x: x.get('data', ''), reverse=True):
            if filtro_anno and not (e.get('data', '') or '').startswith(str(filtro_anno)):
                continue
            scuola_id = e.get('scuola_id')
            scuola = next((s for s in d.get('scuole', []) if s.get('id') == scuola_id), None)
            nome = scuola['nome'] if scuola else (e.get('luogo') or 'ALTRO')
            righe.append([e.get('data', ''), nome, e.get('iniziativa', ''),
                          e.get('numero_partecipanti', 0), e.get('braccialetti', 0),
                          e.get('medaglie', 0), e.get('adesivi', 0), e.get('coppe', 0),
                          e.get('referente', ''), e.get('note', '')])
        return intest, righe

    if sezione == 'scuole':
        intest = ['Nome', 'Tipo', 'Referente', 'Telefono', 'Email', 'N. Eventi']
        righe = []
        for s in d.get('scuole', []):
            n = sum(1 for e in d.get('eventi', []) if e.get('scuola_id') == s.get('id'))
            righe.append([s.get('nome', ''), s.get('tipo', ''), s.get('referente', ''),
                          s.get('telefono', ''), s.get('email', ''), n])
        return intest, righe

    if sezione == 'rubrica':
        intest = ['Nome', 'Telefono', 'Email', 'Scuola', 'Ruolo', 'Note']
        righe = [[c.get('nome', ''), c.get('telefono', ''), c.get('email', ''),
                  c.get('scuola', ''), c.get('ruolo', ''), c.get('note', '')]
                 for c in d.get('rubrica', [])]
        return intest, righe

    if sezione == 'task':
        intest = ['Titolo', 'Categoria', 'Scadenza', 'Priorità', 'Stato', 'Referente', 'Note']
        righe = [[t.get('titolo', ''), t.get('categoria', ''), t.get('data_scadenza', ''),
                  t.get('priorita', ''), t.get('stato', ''), t.get('referente', ''),
                  t.get('note') or t.get('descrizione', '')]
                 for t in d.get('task', [])]
        return intest, righe

    if sezione == 'magazzino':
        intest = ['Categoria', 'Tipo', 'Quantità', 'Data', 'Motivo', 'Nota Carico']
        righe = []
        for cat, movs in d.get('movimenti', {}).items():
            for m in movs:
                if filtro_anno and not (m.get('data', '') or '').startswith(str(filtro_anno)):
                    continue
                righe.append([cat, m.get('tipo', ''), m.get('quantita', 0),
                              m.get('data', ''), m.get('motivo', ''), m.get('nota_carico', '')])
        righe.sort(key=lambda r: r[3], reverse=True)
        return intest, righe

    if sezione == 'inventario':
        intest = ['Nome', 'Valore', 'Stato', 'Nota Carico', 'Note']
        righe = [[o.get('nome', ''), o.get('valore', 0), o.get('stato', ''),
                  o.get('nota_carico', ''), o.get('note', '')]
                 for o in d.get('inventario', [])]
        return intest, righe

    if sezione == 'entita':
        intest = ['Nome', 'Categoria', 'Quantità', 'Data Carico', 'Costo Unitario',
                  'Fornitore', 'Condizione', 'Note']
        righe = [[e.get('nome', ''), e.get('categoria', ''), e.get('quantita', 1),
                  e.get('data_carico', ''), e.get('costo_unitario', 0),
                  e.get('fornitore', ''), e.get('condizione', ''), e.get('note', '')]
                 for e in d.get('entita', [])]
        return intest, righe

    if sezione == 'liste':
        intest = ['Lista', 'Prodotto', 'Comprato', 'Data Acquisto']
        righe = []
        for l in d.get('liste', []):
            for p in l.get('prodotti', []):
                righe.append([l.get('nome', ''), p.get('nome', ''),
                              'Sì' if p.get('comprato') else 'No',
                              p.get('data_acquisto', '')])
        return intest, righe

    if sezione == 'portafoglio':
        intest = ['Titolo', 'Quantità', 'Prezzo Acquisto', 'Prezzo Attuale', 'Variazione %']
        righe = []
        for t in d.get('portafoglio', []):
            q = t.get('quantita', 0)
            pa = t.get('prezzo_acquisto', 0)
            pt = t.get('prezzo_attuale', 0)
            var = ((pt - pa) / pa * 100) if pa else 0
            righe.append([t.get('nome', ''), q, pa, pt, round(var, 2)])
        return intest, righe

    return ['(vuoto)'], []