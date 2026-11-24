"""Route per esportazione standard e Esportazione Intelligente."""
from __future__ import annotations
import csv as csv_mod
import io as io_mod
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from app import storage, contabilita, bilancio
from app.auth import login_required
from app.utils import _intero
from app.export_helpers import _scrivi_foglio_excel, _dati_per_sezione

bp = Blueprint('esporta', __name__, url_prefix='/api')


def _formatta_foglio(ws, intestazioni, righe, col_euro=()):
    ws.append(intestazioni)
    hdr_fill = PatternFill(start_color='0F172A', end_color='0F172A', fill_type='solid')
    tot_fill = PatternFill(start_color='E0F2FE', end_color='E0F2FE', fill_type='solid')
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = hdr_fill
        cell.alignment = Alignment(vertical='center')
    for idx_r, r in enumerate(righe, start=2):
        ws.append(r)
        is_tot = isinstance(r[0], str) and r[0].upper().startswith('TOTALE')
        for c_idx in range(1, len(intestazioni) + 1):
            c = ws.cell(row=idx_r, column=c_idx)
            if c_idx in col_euro and isinstance(c.value, (int, float)):
                c.number_format = '#,##0.00 €'
            if is_tot:
                c.font = Font(bold=True)
                c.fill = tot_fill
    for i, h in enumerate(intestazioni, 1):
        col = get_column_letter(i)
        max_len = max([len(str(h))] + [len(str(cell.value or '')) for cell in ws[col]])
        ws.column_dimensions[col].width = min(max_len + 4, 48)


@bp.route('/export/backup')
@login_required
def api_export_backup():
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    d = storage.get_dati()
    r = current_app.response_class(json.dumps(d, indent=2, default=str, ensure_ascii=False), mimetype='application/json')
    r.headers['Content-Disposition'] = f'attachment; filename="braaap_backup_{ts}.json"'
    return r


@bp.route('/esporta/intelligente.xlsx')
@login_required
def api_esporta_intelligente():
    d = storage.get_dati()
    anno = request.args.get('anno', type=int) or datetime.now().year
    profilo = (request.args.get('profilo') or 'completo').strip().lower()
    bil = contabilita.bilancio_anno(anno)
    pat = bilancio.bilancio_completo()

    ev_anno = [e for e in d.get('eventi', []) if (e.get('data') or '').startswith(str(anno))]
    ev_anno.sort(key=lambda x: x.get('data', ''))
    scuole_map = {s.get('id'): s.get('nome', '') for s in d.get('scuole', [])}
    tot_partecipanti = sum(_intero(e.get('numero_partecipanti')) for e in ev_anno)

    wb = Workbook()
    wb.remove(wb.active)

    # 1. RIEPILOGO EXECUTIVE
    ws1 = wb.create_sheet(title='Riepilogo Executive')
    righe_kpi = [
        ['Anno di riferimento', anno, ''],
        ['Profilo esportazione', profilo.upper(), datetime.now().strftime('%d/%m/%Y %H:%M')],
        ['Eventi svolti / programmati', len(ev_anno), 'Numero iniziative nell\'anno'],
        ['Partecipanti complessivi', tot_partecipanti, 'Somma partecipanti eventi'],
        ['Entrate totali anno', bil['entrate']['totale'], 'Contributi, sponsor e altre entrate'],
        ['Uscite totali anno', bil['uscite']['totale'], 'Magazzino + Inventario + Materiali + Altro'],
        ['TOTALE MARGINE NETTO ANNO', bil['margine'], 'Differenza Entrate - Uscite'],
        ['Valore Magazzino Gadget', pat['magazzino']['totale_valore'], 'Stock residuo valorizzato al prezzo medio'],
        ['Valore Beni Inventario', pat['inventario']['totale_valore'], 'Attrezzature e beni durevoli'],
        ['Valore Materiali Consumo', pat['materiali']['totale_valore'], 'Materiali disponibili'],
        ['TOTALE PATRIMONIO ATTUALE', pat['totale_generale'], 'Valore complessivo beni e scorte'],
    ]
    _formatta_foglio(ws1, ['Indicatore', 'Valore', 'Note'], righe_kpi, col_euro=(2,))

    # 2. BILANCIO ANNUALE
    ws2 = wb.create_sheet(title='Bilancio Annuale')
    righe_bil = []
    for tipo, voci in bil['entrate']['voci_per_tipo'].items():
        for v in voci:
            righe_bil.append(['ENTRATA', tipo.upper(), v.get('data', ''), v.get('descrizione', ''), v.get('importo', 0.0)])
    righe_bil.append(['TOTALE ENTRATE', '', '', f'Anno {anno}', bil['entrate']['totale']])
    for cat in ('magazzino', 'inventario', 'materiali', 'altro'):
        for v in bil['uscite'][cat]['voci']:
            righe_bil.append(['USCITA', cat.upper(), v.get('data', ''), v.get('descrizione', ''), v.get('importo', 0.0)])
    righe_bil.append(['TOTALE USCITE', '', '', f'Anno {anno}', bil['uscite']['totale']])
    righe_bil.append(['TOTALE MARGINE', '', '', 'Saldo netto annuale', bil['margine']])
    _formatta_foglio(ws2, ['Sezione', 'Categoria', 'Data', 'Descrizione', 'Importo'], righe_bil, col_euro=(5,))

    # 3. CONTO ECONOMICO EVENTI
    ws3 = wb.create_sheet(title='Eventi e Margini')
    righe_ev = []
    tot_ric_ev = tot_cos_ev = 0.0
    for e in ev_anno:
        luogo = scuole_map.get(e.get('scuola_id')) or e.get('luogo') or 'ALTRO'
        ric = sum(float(v.get('importo') or 0) for v in (e.get('voci_ricavi') or []))
        cos = sum(float(v.get('importo') or 0) for v in (e.get('voci_costi') or []))
        tot_ric_ev += ric
        tot_cos_ev += cos
        gadget = f"B:{_intero(e.get('braccialetti'))} M:{_intero(e.get('medaglie'))} A:{_intero(e.get('adesivi'))} C:{_intero(e.get('coppe'))}"
        righe_ev.append([e.get('data', ''), luogo, e.get('iniziativa', ''), _intero(e.get('numero_partecipanti')), gadget, round(ric, 2), round(cos, 2), round(ric - cos, 2)])
    righe_ev.append(['TOTALE EVENTI', f'{len(ev_anno)} eventi', '', tot_partecipanti, '', round(tot_ric_ev, 2), round(tot_cos_ev, 2), round(tot_ric_ev - tot_cos_ev, 2)])
    _formatta_foglio(ws3, ['Data', 'Scuola / Luogo', 'Iniziativa', 'Partecipanti', 'Gadget', 'Ricavi', 'Costi', 'Margine'], righe_ev, col_euro=(6, 7, 8))

    # 4. PATRIMONIO & SCORTE
    ws4 = wb.create_sheet(title='Patrimonio e Scorte')
    righe_pat = []
    for sez_k in ('magazzino', 'inventario', 'materiali'):
        for v in pat[sez_k]['voci']:
            righe_pat.append([sez_k.upper(), v.get('nome', ''), v.get('quantita', 0), v.get('prezzo_unitario', 0.0), v.get('valore', 0.0)])
    righe_pat.append(['TOTALE PATRIMONIO', '', '', '', pat['totale_generale']])
    _formatta_foglio(ws4, ['Sezione', 'Articolo', 'Quantita', 'Prezzo Unitario', 'Valore Totale'], righe_pat, col_euro=(4, 5))

    buf = io_mod.BytesIO()
    wb.save(buf)
    buf.seek(0)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    r = current_app.response_class(buf.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    r.headers['Content-Disposition'] = f'attachment; filename="Braaap_Report_Intelligente_{anno}_{ts}.xlsx"'
    return r


@bp.route('/esporta/<sezione>.<formato>')
@login_required
def api_esporta(sezione, formato):
    filtro_anno = request.args.get('anno', type=int)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome_file = f'braaap_{sezione}_{ts}'
    if sezione == 'tutto':
        wb = Workbook()
        wb.remove(wb.active)
        for sez in ['eventi', 'scuole', 'rubrica', 'task', 'magazzino', 'inventario', 'entita', 'liste', 'portafoglio']:
            intest, righe = _dati_per_sezione(sez, filtro_anno)
            ws = wb.create_sheet(title=sez.capitalize())
            _scrivi_foglio_excel(ws, intest, righe)
        buf = io_mod.BytesIO()
        wb.save(buf)
        buf.seek(0)
        r = current_app.response_class(buf.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        r.headers['Content-Disposition'] = f'attachment; filename="{nome_file}.xlsx"'
        return r
    intest, righe = _dati_per_sezione(sezione, filtro_anno)
    if formato == 'json':
        out = [dict(zip(intest, row)) for row in righe]
        r = current_app.response_class(json.dumps(out, indent=2, ensure_ascii=False), mimetype='application/json')
        r.headers['Content-Disposition'] = f'attachment; filename="{nome_file}.json"'
        return r
    if formato == 'csv':
        buf = io_mod.StringIO()
        w = csv_mod.writer(buf, delimiter=';')
        w.writerow(intest)
        w.writerows(righe)
        r = current_app.response_class(buf.getvalue().encode('utf-8-sig'), mimetype='text/csv')
        r.headers['Content-Disposition'] = f'attachment; filename="{nome_file}.csv"'
        return r
    wb = Workbook()
    _scrivi_foglio_excel(wb.active, intest, righe)
    buf = io_mod.BytesIO()
    wb.save(buf)
    buf.seek(0)
    r = current_app.response_class(buf.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    r.headers['Content-Disposition'] = f'attachment; filename="{nome_file}.xlsx"'
    return r

