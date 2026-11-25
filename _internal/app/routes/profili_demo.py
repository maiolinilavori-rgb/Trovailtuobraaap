from __future__ import annotations
import copy
from flask import Blueprint, jsonify, request
from app import storage
from app.auth import login_required

bp = Blueprint('profili_demo', __name__, url_prefix='/api/profili')

PROFILI = {
    'motoclub': {
        'label': '🏁 Motoclub & Educazione Stradale',
        'ui': {'eventi': '📅 Eventi', 'scuole': '🏫 Scuole', 'altro': '📦 Eventi ALTRO', 'bracc': '📦 Bracc.', 'med': '🏅 Med.', 'ades': '🔖 Ades.', 'coppe': '🏆 Coppe', 'mat': '📦 Materiali'},
        'dati': {
            'scuole': [{'id': 1, 'nome': 'I.C. Valle Camonica - Plesso Braone', 'tipo': 'Scuola Primaria', 'referente': 'Prof.ssa Bianchi', 'telefono': '0364 000001'}, {'id': 2, 'nome': 'Motoclub Sebino Off-Road', 'tipo': 'Associazione', 'referente': 'Marco Rossi', 'telefono': '333 000002'}],
            'eventi': [{'id': 101, 'data': '2026-04-18', 'scuola_id': 1, 'iniziativa': 'Educazione Stradale & Mini-Cross', 'numero_partecipanti': 85, 'braccialetti': 85, 'medaglie': 85, 'adesivi': 120, 'coppe': 3, 'voci_ricavi': [{'descrizione': 'Contributo Comune', 'importo': 1200}], 'voci_costi': [{'descrizione': 'Carburante e assicurazione FMI', 'importo': 320}]}],
            'stock': {'braccialetti': 305, 'medaglie': 155, 'adesivi': 800, 'coppe': 30},
            'movimenti': {'braccialetti': [], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Minimoto Elettrica Training #1-#2', 'quantita': 2, 'valore_unitario': 1450.0, 'valore_totale': 2900.0, 'data_acquisto': '2026-01-15', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Caschi Cross Junior omologati', 'categoria': 'Protezioni', 'quantita': 14, 'costo_unitario': 65.0, 'data_carico': '2026-02-20', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-04-18', 'tipo': 'evento', 'descrizione': 'Contributo Scuola Braone', 'importo': 1200.0}],
            'uscite': [], 'altro': [],
            'task': [
                {'id': 1, 'titolo': 'Verificare carica batterie minimoto elettriche', 'categoria': 'Mezzi', 'data_scadenza': '2026-06-10', 'priorita': 'Alta', 'stato': 'Da fare'},
                {'id': 2, 'titolo': 'Inviare elenco telai per assicurazione FMI', 'categoria': 'Segreteria', 'data_scadenza': '2026-06-12', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 3, 'titolo': 'Sopralluogo area erbosa e fettucciato sicurezza', 'categoria': 'Sicurezza', 'data_scadenza': '2026-06-16', 'priorita': 'Alta', 'stato': 'Da fare'}
            ]
        }
    },
    'azienda': {
        'label': '🏢 Azienda, Studio & Artigiani',
        'ui': {'eventi': '📅 Appuntamenti', 'scuole': '🏢 Clienti & Aziende', 'altro': '📦 Sopralluoghi', 'bracc': '📄 Volantini / Preventivi', 'med': '🎁 Gadget & Promo', 'ades': '🖨️ Stampe', 'coppe': '👥 TEAM', 'mat': '🛠️ Cancelleria / Edicola / Ferramenta'},
        'dati': {
            'scuole': [{'id': 1, 'nome': 'Studio Tecnico Arch. Bresciani', 'tipo': 'Cliente Business', 'referente': 'Arch. Bresciani', 'telefono': '0364 551122'}, {'id': 2, 'nome': 'EdilValcamonica S.r.l.', 'tipo': 'Cliente Cantiere', 'referente': 'Geom. Ferrari', 'telefono': '348 990011'}],
            'eventi': [{'id': 601, 'data': '2026-05-14', 'scuola_id': 1, 'iniziativa': 'Sopralluogo e Consegna Preventivo Ristrutturazione', 'numero_partecipanti': 4, 'braccialetti': 25, 'medaglie': 5, 'adesivi': 40, 'coppe': 3, 'voci_ricavi': [{'descrizione': 'Acconto incarico e consulenza tecnica', 'importo': 2800}], 'voci_costi': [{'descrizione': 'Stampe tavole tecniche e materiali', 'importo': 210}]}, {'id': 602, 'data': '2026-05-28', 'scuola_id': 2, 'iniziativa': 'Appuntamento Chiusura Lavori & Consegna', 'numero_partecipanti': 6, 'braccialetti': 50, 'medaglie': 10, 'adesivi': 80, 'coppe': 4, 'voci_ricavi': [{'descrizione': 'Saldo fornitura e posa in opera', 'importo': 4600}], 'voci_costi': [{'descrizione': 'Minuteria ferramenta e consumabili', 'importo': 340}]}],
            'stock': {'braccialetti': 420, 'medaglie': 95, 'adesivi': 650, 'coppe': 8},
            'movimenti': {'braccialetti': [], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Plotter CAD A0 + Stampante Laser Multifunzione', 'quantita': 2, 'valore_unitario': 1850.0, 'valore_totale': 3700.0, 'data_acquisto': '2025-11-20', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Risme carta A4/A3, toner, cartelle e minuteria ferramenta', 'categoria': 'Cancelleria & Ferramenta', 'quantita': 95, 'costo_unitario': 12.0, 'data_carico': '2026-03-10', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-05-14', 'tipo': 'evento', 'descrizione': 'Fattura Studio Bresciani', 'importo': 2800.0}, {'id': 2, 'data': '2026-05-28', 'tipo': 'evento', 'descrizione': 'Saldo EdilValcamonica Srl', 'importo': 4600.0}],
            'uscite': [], 'altro': [],
            'task': [
                {'id': 1, 'titolo': 'Inviare preventivo aggiornato e brochure al cliente Bresciani', 'categoria': 'Commerciale', 'data_scadenza': '2026-06-08', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 2, 'titolo': 'Riordinare toner, risme A4/A3 e tasselli in ferramenta', 'categoria': 'Magazzino', 'data_scadenza': '2026-06-11', 'priorita': 'Media', 'stato': 'Da fare'},
                {'id': 3, 'titolo': 'Confermare appuntamento sopralluogo con il Team operativo', 'categoria': 'Appuntamenti', 'data_scadenza': '2026-06-14', 'priorita': 'Alta', 'stato': 'Da fare'}
            ]
        }
    },
    'proloco': {
        'label': '🎪 Pro Loco & Feste di Paese',
        'ui': {'eventi': '📅 Feste & Sagre', 'scuole': '🏛️ Enti & Partner', 'altro': '📦 Stand & Mercatini', 'bracc': '🎟️ Pass & Biglietti', 'med': '🏅 Premi & Lotteria', 'ades': '🏷️ Locandine & Flyer', 'coppe': '🏆 Trofei & Targhe', 'mat': '🎪 Attrezzature Stand'},
        'dati': {
            'scuole': [{'id': 1, 'nome': 'Comune - Ufficio SUAP & Polizia Locale', 'tipo': 'Ente Pubblico', 'referente': 'Comm. Cattaneo', 'telefono': '0364 112233'}],
            'eventi': [{'id': 201, 'data': '2026-07-18', 'scuola_id': 1, 'iniziativa': 'Notte Bianca & Sagra dei Sapori', 'numero_partecipanti': 900, 'braccialetti': 600, 'medaglie': 20, 'adesivi': 500, 'coppe': 5, 'voci_ricavi': [{'descrizione': 'Stand gastronomico e patrocinio', 'importo': 7400}], 'voci_costi': [{'descrizione': 'Service concerto e forniture cucina', 'importo': 3350}]}],
            'stock': {'braccialetti': 400, 'medaglie': 80, 'adesivi': 600, 'coppe': 12},
            'movimenti': {'braccialetti': [], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Cucina mobile inox + 25 set panche legno', 'quantita': 1, 'valore_unitario': 7700.0, 'valore_totale': 7700.0, 'data_acquisto': '2025-05-01', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Estintori 6kg omologati + Gilet Staff', 'categoria': 'Sicurezza', 'quantita': 38, 'costo_unitario': 18.0, 'data_carico': '2026-03-15', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-07-18', 'tipo': 'evento', 'descrizione': 'Incasso Notte Bianca', 'importo': 7400.0}],
            'uscite': [], 'altro': [],
            'task': [
                {'id': 1, 'titolo': 'Depositare SCIA evento e Piano Emergenza in Comune', 'categoria': 'Permessi', 'data_scadenza': '2026-06-25', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 2, 'titolo': 'Aprire permesso musicale SIAE online', 'categoria': 'Amministrazione', 'data_scadenza': '2026-07-01', 'priorita': 'Alta', 'stato': 'Da fare'},
                {'id': 3, 'titolo': 'Confermare turni volontari cassa, griglia e bar', 'categoria': 'Staff', 'data_scadenza': '2026-07-10', 'priorita': 'Media', 'stato': 'Da fare'}
            ]
        }
    },
    'asd': {
        'label': '⚽ ASD & Centro Estivo Multisport',
        'ui': {'eventi': '📅 Tornei & Camp', 'scuole': '🏟️ Impianti & Società', 'altro': '📦 Stage & Amichevoli', 'bracc': '🎽 Kit & Braccialetti', 'med': '🏅 Medaglie & Trofei', 'ades': '🔖 Adesivi & Borracce', 'coppe': '🏆 Coppe FairPlay', 'mat': '⚽ Attrezzatura Sportiva'},
        'dati': {
            'scuole': [{'id': 1, 'nome': 'Centro Sportivo Comunale Valgrigna', 'tipo': 'Impianto', 'referente': 'Luca Fontana', 'telefono': '335 771122'}],
            'eventi': [{'id': 301, 'data': '2026-06-15', 'scuola_id': 1, 'iniziativa': 'Summer Sport Camp - Turno 1', 'numero_partecipanti': 65, 'braccialetti': 65, 'medaglie': 65, 'adesivi': 130, 'coppe': 4, 'voci_ricavi': [{'descrizione': 'Rette iscritti camp', 'importo': 5850}], 'voci_costi': [{'descrizione': 'Istruttori e mensa', 'importo': 3450}]}],
            'stock': {'braccialetti': 255, 'medaglie': 155, 'adesivi': 270, 'coppe': 14},
            'movimenti': {'braccialetti': [], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Defibrillatore DAE + teca', 'quantita': 2, 'valore_unitario': 1150.0, 'valore_totale': 2300.0, 'data_acquisto': '2025-09-10', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Kit palloni, pettorine e conetti', 'categoria': 'Attrezzatura', 'quantita': 45, 'costo_unitario': 18.0, 'data_carico': '2026-04-10', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-06-15', 'tipo': 'evento', 'descrizione': 'Incasso Summer Sport Camp', 'importo': 5850.0}],
            'uscite': [], 'altro': [],
            'task': [
                {'id': 1, 'titolo': 'Controllare scadenza certificati medici atleti', 'categoria': 'Segreteria', 'data_scadenza': '2026-06-10', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 2, 'titolo': 'Raccogliere deleghe ritiro minori e allergie', 'categoria': 'Camp Estivo', 'data_scadenza': '2026-06-12', 'priorita': 'Alta', 'stato': 'Da fare'},
                {'id': 3, 'titolo': 'Testare batterie ed elettrodi Defibrillatore DAE', 'categoria': 'Sicurezza', 'data_scadenza': '2026-06-14', 'priorita': 'Alta', 'stato': 'Completato'}
            ]
        }
    }
}

@bp.route('/lista', methods=['GET'])
@login_required
def api_lista_profili():
    d = storage.get_dati()
    att = d.get('profilo_demo_attivo', 'motoclub')
    if att not in PROFILI:
        att = 'motoclub'
    return jsonify({'success': True, 'attivo': att, 'ui': PROFILI[att]['ui'], 'profili': [{'id': k, 'label': v['label']} for k, v in PROFILI.items()]})

@bp.route('/attiva', methods=['POST'])
@login_required
def api_attiva_profilo():
    body = request.get_json(silent=True) or {}
    pid = (body.get('profilo') or '').strip().lower()
    if pid not in PROFILI:
        return jsonify({'success': False, 'error': 'Profilo non valido'}), 400
    d = storage.get_dati()
    for k, v in copy.deepcopy(PROFILI[pid]['dati']).items():
        d[k] = v
    d['profilo_demo_attivo'] = pid
    d['giacenza_iniziale_impostata'] = True
    d['import_excel_fatto'] = True
    storage.salva_dati(d, crea_backup=False)
    return jsonify({'success': True, 'profilo': pid, 'ui': PROFILI[pid]['ui']})