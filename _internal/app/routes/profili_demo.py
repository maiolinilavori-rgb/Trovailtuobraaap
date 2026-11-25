from __future__ import annotations
import copy, json
from pathlib import Path
from flask import Blueprint, jsonify, request
from app import storage
from app.auth import login_required

bp = Blueprint('profili_demo', __name__, url_prefix='/api/profili')

PROFILI = {
    'motoclub': {
        'label': '🏁 Motoclub & Educazione Stradale',
        'ui': {'eventi': '📅 Eventi', 'scuole': '🏫 Scuole', 'altro': '📦 Eventi ALTRO', 'bracc': '📦 Bracc.', 'med': '🏅 Med.', 'ades': '🔖 Ades.', 'coppe': '🏆 Coppe', 'mat': '📦 Materiali'},
        'dati': {
            'rubrica': [
                {'id': 1, 'nome': 'Prof.ssa Giulia Bianchi', 'ruolo': 'Referente Scuola Primaria', 'telefono': '333 0001101', 'email': 'g.bianchi@scuolademo.it', 'note': 'Plesso Braone'},
                {'id': 2, 'nome': 'Marco Rossi', 'ruolo': 'Direttore Gara FMI', 'telefono': '333 0001102', 'email': 'm.rossi@motodemo.it', 'note': 'Omologazione pista'},
                {'id': 3, 'nome': 'Dott. Andrea Riva', 'ruolo': 'Medico di Gara', 'telefono': '333 0001103', 'email': 'a.riva@soccorsodemo.it', 'note': 'Presidio ambulanza'}
            ],
            'scuole': [
                {'id': 1, 'nome': 'I.C. Valle Demo - Plesso Nord', 'tipo': 'Scuola Primaria', 'referente': 'Prof.ssa Giulia Bianchi', 'telefono': '0364 000101', 'email': 'plesso.nord@scuolademo.it'},
                {'id': 2, 'nome': 'Motoclub Circuito Verde', 'tipo': 'Associazione Sportiva', 'referente': 'Marco Rossi', 'telefono': '0364 000102', 'email': 'info@motodemo.it'}
            ],
            'eventi': [
                {'id': 101, 'data': '2026-04-18', 'scuola_id': 1, 'iniziativa': 'Educazione Stradale & Mini-Cross', 'numero_partecipanti': 85, 'braccialetti': 85, 'medaglie': 85, 'adesivi': 120, 'coppe': 3, 'voci_ricavi': [{'descrizione': 'Contributo Comune', 'importo': 1200}], 'voci_costi': [{'descrizione': 'Carburante e polizza FMI', 'importo': 320}]},
                {'id': 102, 'data': '2026-05-24', 'scuola_id': 2, 'iniziativa': 'Open Day Pista Giovanile', 'numero_partecipanti': 110, 'braccialetti': 110, 'medaglie': 60, 'adesivi': 150, 'coppe': 6, 'voci_ricavi': [{'descrizione': 'Quote iscrizione e sponsor', 'importo': 2150}], 'voci_costi': [{'descrizione': 'Ambulanza e fettucciato', 'importo': 570}]}
            ],
            'altro': [{'id': 1, 'data': '2026-06-05', 'titolo': 'Esposizione Moto Storiche in Piazza', 'luogo': 'Piazza Centrale', 'note': 'Stand promozionale domenica mattina'}],
            'stock': {'braccialetti': 305, 'medaglie': 155, 'adesivi': 530, 'coppe': 21},
            'movimenti': {
                'braccialetti': [{'id': 1, 'data': '2026-02-10', 'tipo': 'carico', 'quantita': 500, 'prezzo_unitario': 0.45, 'motivo': 'Fornitura stagione 2026'}],
                'medaglie': [{'id': 2, 'data': '2026-02-10', 'tipo': 'carico', 'quantita': 300, 'prezzo_unitario': 1.80, 'motivo': 'Medaglie finisher'}],
                'adesivi': [{'id': 3, 'data': '2026-02-10', 'tipo': 'carico', 'quantita': 800, 'prezzo_unitario': 0.15, 'motivo': 'Kit adesivi casco'}],
                'coppe': [{'id': 4, 'data': '2026-02-10', 'tipo': 'carico', 'quantita': 30, 'prezzo_unitario': 12.0, 'motivo': 'Trofei podi'}]
            },
            'inventario': [
                {'id': 1, 'nome': 'Minimoto Elettrica Training #1-#2', 'quantita': 2, 'valore_unitario': 1450.0, 'valore_totale': 2900.0, 'data_acquisto': '2026-01-15', 'stato': 'Operativo'},
                {'id': 2, 'nome': 'Gazebo Paddock 4x4 Impermeabile', 'quantita': 2, 'valore_unitario': 380.0, 'valore_totale': 760.0, 'data_acquisto': '2026-02-05', 'stato': 'Operativo'}
            ],
            'entita': [
                {'id': 1, 'nome': 'Caschi Cross Junior omologati ECE', 'categoria': 'Protezioni', 'quantita': 14, 'costo_unitario': 65.0, 'data_carico': '2026-02-20', 'condizione': 'Nuovo'},
                {'id': 2, 'nome': 'Pettorine e ginocchiere minicross', 'categoria': 'Protezioni', 'quantita': 14, 'costo_unitario': 38.0, 'data_carico': '2026-02-20', 'condizione': 'Ottimo'}
            ],
            'entrate': [{'id': 1, 'data': '2026-04-18', 'tipo': 'evento', 'descrizione': 'Contributo Scuola Nord', 'importo': 1200.0}, {'id': 2, 'data': '2026-05-24', 'tipo': 'evento', 'descrizione': 'Open Day Pista', 'importo': 2150.0}],
            'uscite': [{'id': 1, 'data': '2026-03-10', 'descrizione': 'Tagliando furgone trasporto moto', 'importo': 290.0}],
            'postit': [{'id': 1, 'testo': 'Controllare pressione gomme minimoto prima del carico', 'colore': '#fef08a'}],
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
            'rubrica': [
                {'id': 1, 'nome': 'Arch. Lorenzo Bresciani', 'ruolo': 'Cliente Studio Tecnico', 'telefono': '348 0002201', 'email': 'l.bresciani@studiodemo.it', 'note': 'Commessa ristrutturazione'},
                {'id': 2, 'nome': 'Geom. Paolo Ferrari', 'ruolo': 'Direttore Cantiere', 'telefono': '348 0002202', 'email': 'p.ferrari@edildemo.it', 'note': 'Referente forniture'},
                {'id': 3, 'nome': 'Sara Conti', 'ruolo': 'Fornitore Tipografia & Ferramenta', 'telefono': '348 0002203', 'email': 'ordini@fornituredemo.it', 'note': 'Consegne 24h'}
            ],
            'scuole': [
                {'id': 1, 'nome': 'Studio Tecnico Arch. Bresciani', 'tipo': 'Cliente Business', 'referente': 'Arch. Lorenzo Bresciani', 'telefono': '0364 000201', 'email': 'info@studiodemo.it'},
                {'id': 2, 'nome': 'EdilValcamonica S.r.l.', 'tipo': 'Cliente Cantiere', 'referente': 'Geom. Paolo Ferrari', 'telefono': '0364 000202', 'email': 'cantieri@edildemo.it'}
            ],
            'eventi': [
                {'id': 601, 'data': '2026-05-14', 'scuola_id': 1, 'iniziativa': 'Consegna Preventivo & Brochure Ristrutturazione', 'numero_partecipanti': 4, 'braccialetti': 25, 'medaglie': 5, 'adesivi': 40, 'coppe': 3, 'voci_ricavi': [{'descrizione': 'Acconto incarico e consulenza', 'importo': 2800}], 'voci_costi': [{'descrizione': 'Stampe tavole A0 e rilegatura', 'importo': 210}]},
                {'id': 602, 'data': '2026-05-28', 'scuola_id': 2, 'iniziativa': 'Appuntamento Collaudo & Chiusura Lavori', 'numero_partecipanti': 6, 'braccialetti': 50, 'medaglie': 10, 'adesivi': 80, 'coppe': 4, 'voci_ricavi': [{'descrizione': 'Saldo fornitura e posa in opera', 'importo': 4600}], 'voci_costi': [{'descrizione': 'Minuteria ferramenta e consumabili', 'importo': 340}]}
            ],
            'altro': [{'id': 1, 'data': '2026-06-09', 'titolo': 'Sopralluogo preventivo nuovo capannone zona industriale', 'luogo': 'Via Artigiani 12', 'note': 'Portare telemetro laser e campionario'}],
            'stock': {'braccialetti': 420, 'medaglie': 95, 'adesivi': 650, 'coppe': 8},
            'movimenti': {
                'braccialetti': [{'id': 1, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 495, 'prezzo_unitario': 0.35, 'motivo': 'Stampa volantini, brochure e cartellette preventivi'}],
                'medaglie': [{'id': 2, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 110, 'prezzo_unitario': 2.40, 'motivo': 'Gadget promozionali clienti'}],
                'adesivi': [{'id': 3, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 770, 'prezzo_unitario': 0.25, 'motivo': 'Stampe tecniche ed etichette brand'}],
                'coppe': [{'id': 4, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 15, 'prezzo_unitario': 45.0, 'motivo': 'Kit dotazione operatori Team'}]
            },
            'inventario': [
                {'id': 1, 'nome': 'Plotter CAD A0 + Stampante Laser Multifunzione', 'quantita': 2, 'valore_unitario': 1850.0, 'valore_totale': 3700.0, 'data_acquisto': '2025-11-20', 'stato': 'Operativo'},
                {'id': 2, 'nome': 'Trapano tassellatore + Livella laser rotante', 'quantita': 3, 'valore_unitario': 420.0, 'valore_totale': 1260.0, 'data_acquisto': '2026-01-18', 'stato': 'Operativo'}
            ],
            'entita': [
                {'id': 1, 'nome': 'Risme carta A4/A3, toner, raccoglitori (Cancelleria)', 'categoria': 'Cancelleria', 'quantita': 60, 'costo_unitario': 9.5, 'data_carico': '2026-03-10', 'condizione': 'Nuovo'},
                {'id': 2, 'nome': 'Viti, tasselli chimici, dischi taglio e siliconi (Ferramenta)', 'categoria': 'Ferramenta', 'quantita': 140, 'costo_unitario': 6.0, 'data_carico': '2026-03-12', 'condizione': 'Nuovo'},
                {'id': 3, 'nome': 'Riviste tecniche settore, moduli DDT e blocchi ricevute (Edicola)', 'categoria': 'Edicola', 'quantita': 25, 'costo_unitario': 4.5, 'data_carico': '2026-03-15', 'condizione': 'Nuovo'}
            ],
            'entrate': [{'id': 1, 'data': '2026-05-14', 'tipo': 'evento', 'descrizione': 'Fattura Studio Bresciani', 'importo': 2800.0}, {'id': 2, 'data': '2026-05-28', 'tipo': 'evento', 'descrizione': 'Saldo EdilValcamonica Srl', 'importo': 4600.0}],
            'uscite': [{'id': 1, 'data': '2026-04-05', 'descrizione': 'Fornitura toner, risme A3 e minuteria ferramenta', 'importo': 485.0}],
            'postit': [{'id': 1, 'testo': 'Richiamare Arch. Bresciani per conferma firma preventivo', 'colore': '#bfdbfe'}],
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
            'rubrica': [{'id': 1, 'nome': 'Comm. Roberto Cattaneo', 'ruolo': 'Ufficio SUAP Comune', 'telefono': '347 0003301', 'email': 'suap@comunedemo.it', 'note': 'Permessi occupazione suolo'}, {'id': 2, 'nome': 'Elena Ferri', 'ruolo': 'Coordinatrice Stand & Volontari', 'telefono': '347 0003302', 'email': 'elena@prolocodemo.it', 'note': 'Turni cucina e cassa'}],
            'scuole': [{'id': 1, 'nome': 'Comune - Ufficio SUAP & Polizia Locale', 'tipo': 'Ente Pubblico', 'referente': 'Comm. Roberto Cattaneo', 'telefono': '0364 000301', 'email': 'suap@comunedemo.it'}],
            'eventi': [{'id': 201, 'data': '2026-07-18', 'scuola_id': 1, 'iniziativa': 'Notte Bianca & Sagra dei Sapori', 'numero_partecipanti': 900, 'braccialetti': 600, 'medaglie': 20, 'adesivi': 500, 'coppe': 5, 'voci_ricavi': [{'descrizione': 'Stand gastronomico e patrocinio', 'importo': 7400}], 'voci_costi': [{'descrizione': 'Service concerto e forniture cucina', 'importo': 3350}]}],
            'altro': [{'id': 1, 'data': '2026-08-10', 'titolo': 'Mercatino Artigiani Sotto le Stelle', 'luogo': 'Centro Storico', 'note': '35 bancarelle confermate'}],
            'stock': {'braccialetti': 400, 'medaglie': 80, 'adesivi': 600, 'coppe': 12},
            'movimenti': {'braccialetti': [{'id': 1, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 1000, 'prezzo_unitario': 0.30, 'motivo': 'Pass ingresso area spettacoli'}], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Cucina mobile inox + 25 set panche legno', 'quantita': 1, 'valore_unitario': 7700.0, 'valore_totale': 7700.0, 'data_acquisto': '2025-05-01', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Estintori 6kg omologati + Gilet alta visibilita Staff', 'categoria': 'Sicurezza', 'quantita': 38, 'costo_unitario': 18.0, 'data_carico': '2026-03-15', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-07-18', 'tipo': 'evento', 'descrizione': 'Incasso Notte Bianca', 'importo': 7400.0}],
            'uscite': [{'id': 1, 'data': '2026-04-02', 'descrizione': 'Polizza RC Terzi manifestazioni + SIAE', 'importo': 980.0}],
            'postit': [{'id': 1, 'testo': 'Inviare planimetria vie di fuga alla Polizia Locale', 'colore': '#fde68a'}],
            'task': [
                {'id': 1, 'titolo': 'Depositare SCIA evento e Piano Emergenza in Comune', 'categoria': 'Permessi', 'data_scadenza': '2026-06-25', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 2, 'titolo': 'Aprire permesso musicale SIAE online', 'categoria': 'Amministrazione', 'data_scadenza': '2026-07-01', 'priorita': 'Alta', 'stato': 'Da fare'},
                {'id': 3, 'titolo': 'Confermare turni volontari cassa, griglia e bar', 'categoria': 'Staff', 'data_scadenza': '2026-07-10', 'priorita': 'Media', 'stato': 'Da fare'}
            ]
        }
    }
}

BACKUP_FILE = Path(__file__).resolve().parents[2] / 'dati_reali_backup.json'

@bp.route('/lista', methods=['GET'])
@login_required
def api_lista_profili():
    d = storage.get_dati()
    att = d.get('profilo_demo_attivo', 'motoclub')
    if att not in PROFILI:
        att = 'motoclub'
    opts = [{'id': k, 'label': v['label']} for k, v in PROFILI.items()]
    if BACKUP_FILE.exists():
        opts.append({'id': '__ripristina__', 'label': '🔒 Ripristina i miei dati reali Braaap'})
    return jsonify({'success': True, 'attivo': att, 'ui': PROFILI[att]['ui'], 'profili': opts})

@bp.route('/attiva', methods=['POST'])
@login_required
def api_attiva_profilo():
    body = request.get_json(silent=True) or {}
    pid = (body.get('profilo') or '').strip().lower()
    d = storage.get_dati()
    if pid == '__ripristina__' and BACKUP_FILE.exists():
        orig = json.loads(BACKUP_FILE.read_text(encoding='utf-8'))
        d.clear()
        d.update(orig)
        storage.salva_dati(d, crea_backup=False)
        return jsonify({'success': True, 'profilo': 'motoclub'})
    if pid not in PROFILI:
        return jsonify({'success': False, 'error': 'Profilo non valido'}), 400
    if not d.get('profilo_demo_attivo') and not BACKUP_FILE.exists():
        BACKUP_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    for k, v in copy.deepcopy(PROFILI[pid]['dati']).items():
        d[k] = v
    d['profilo_demo_attivo'] = pid
    d['giacenza_iniziale_impostata'] = True
    d['import_excel_fatto'] = True
    storage.salva_dati(d, crea_backup=False)
    return jsonify({'success': True, 'profilo': pid, 'ui': PROFILI[pid]['ui']})