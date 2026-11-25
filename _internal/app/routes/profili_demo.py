from __future__ import annotations
import copy
from flask import Blueprint, jsonify, request
from app import storage
from app.auth import login_required

bp = Blueprint('profili_demo', __name__, url_prefix='/api/profili')

PROFILI = {
    'motoclub': {
        'label': '🏁 Motoclub & Educazione Stradale',
        'dati': {
            'scuole': [
                {'id': 1, 'nome': 'I.C. Valle Camonica - Plesso Braone', 'tipo': 'Scuola Primaria', 'referente': 'Prof.ssa Bianchi', 'telefono': '0364 000001'},
                {'id': 2, 'nome': 'Motoclub Sebino Off-Road', 'tipo': 'Associazione Sportiva', 'referente': 'Marco Rossi', 'telefono': '333 000002'}
            ],
            'eventi': [
                {'id': 101, 'data': '2026-04-18', 'scuola_id': 1, 'iniziativa': 'Educazione Stradale & Mini-Cross', 'numero_partecipanti': 85, 'braccialetti': 85, 'medaglie': 85, 'adesivi': 120, 'coppe': 3, 'voci_ricavi': [{'descrizione': 'Contributo Comune e Pro Loco', 'importo': 1200}], 'voci_costi': [{'descrizione': 'Carburante e trasporto mezzi', 'importo': 180}, {'descrizione': 'Assicurazione FMI', 'importo': 140}]},
                {'id': 102, 'data': '2026-05-24', 'scuola_id': 2, 'iniziativa': 'Trova il tuo Braaap - Open Day Pista', 'numero_partecipanti': 110, 'braccialetti': 110, 'medaglie': 60, 'adesivi': 150, 'coppe': 6, 'voci_ricavi': [{'descrizione': 'Quote iscrizione partecipanti', 'importo': 1650}, {'descrizione': 'Sponsor officina', 'importo': 500}], 'voci_costi': [{'descrizione': 'Ambulanza e presidio medico', 'importo': 350}, {'descrizione': 'Allestimento tracciato', 'importo': 220}]}
            ],
            'stock': {'braccialetti': 305, 'medaglie': 155, 'adesivi': 530, 'coppe': 21},
            'movimenti': {
                'braccialetti': [{'id': 1, 'data': '2026-02-10', 'tipo': 'carico', 'quantita': 500, 'prezzo_unitario': 0.45, 'motivo': 'Fornitura stagione 2026'}],
                'medaglie': [{'id': 2, 'data': '2026-02-10', 'tipo': 'carico', 'quantita': 300, 'prezzo_unitario': 1.80, 'motivo': 'Medaglie finisher Braaap'}],
                'adesivi': [{'id': 3, 'data': '2026-02-10', 'tipo': 'carico', 'quantita': 800, 'prezzo_unitario': 0.15, 'motivo': 'Kit adesivi casco'}],
                'coppe': [{'id': 4, 'data': '2026-02-10', 'tipo': 'carico', 'quantita': 30, 'prezzo_unitario': 12.0, 'motivo': 'Trofei podi giovanili'}]
            },
            'inventario': [
                {'id': 1, 'nome': 'Minimoto Elettrica Training #1-#2', 'quantita': 2, 'valore_unitario': 1450.0, 'valore_totale': 2900.0, 'data_acquisto': '2026-01-15', 'stato': 'Operativo'},
                {'id': 2, 'nome': 'Gazebo Paddock 4x4 Impermeabile', 'quantita': 2, 'valore_unitario': 380.0, 'valore_totale': 760.0, 'data_acquisto': '2026-02-05', 'stato': 'Operativo'}
            ],
            'entita': [
                {'id': 1, 'nome': 'Caschi Cross Junior omologati ECE', 'categoria': 'Protezioni', 'quantita': 14, 'costo_unitario': 65.0, 'data_carico': '2026-02-20', 'condizione': 'Nuovo'}
            ],
            'entrate': [
                {'id': 1, 'data': '2026-04-18', 'tipo': 'evento', 'descrizione': 'Contributo Evento Scuola Braone', 'importo': 1200.0},
                {'id': 2, 'data': '2026-05-24', 'tipo': 'evento', 'descrizione': 'Quote e Sponsor Open Day Pista', 'importo': 2150.0}
            ],
            'uscite': [],
            'altro': [{'id': 1, 'data': '2026-03-10', 'descrizione': 'Tagliando furgone trasporto moto', 'importo': 290.0}],
            'task': [
                {'id': 1, 'titolo': 'Verificare carica batterie minimoto elettriche', 'categoria': 'Mezzi', 'data_scadenza': '2026-06-10', 'priorita': 'Alta', 'stato': 'Da fare'},
                {'id': 2, 'titolo': 'Inviare elenco telai per assicurazione FMI', 'categoria': 'Segreteria', 'data_scadenza': '2026-06-12', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 3, 'titolo': 'Preparare 120 kit braccialetto + adesivo per tappa estiva', 'categoria': 'Magazzino', 'data_scadenza': '2026-06-15', 'priorita': 'Media', 'stato': 'Da fare'},
                {'id': 4, 'titolo': 'Sopralluogo area erbosa e fettucciato sicurezza', 'categoria': 'Sicurezza', 'data_scadenza': '2026-06-16', 'priorita': 'Alta', 'stato': 'Completato'}
            ]
        }
    },
    'proloco': {
        'label': '🎪 Pro Loco & Feste di Paese',
        'dati': {
            'scuole': [
                {'id': 1, 'nome': 'Comune - Ufficio SUAP & Polizia Locale', 'tipo': 'Ente Pubblico', 'referente': 'Comm. Cattaneo', 'telefono': '0364 112233'},
                {'id': 2, 'nome': 'Consorzio Commercianti & Artigiani', 'tipo': 'Sponsor', 'referente': 'Elena Ferri', 'telefono': '347 889900'}
            ],
            'eventi': [
                {'id': 201, 'data': '2026-05-01', 'scuola_id': 1, 'iniziativa': 'Festa di Primavera & Mercatino Artigiano', 'numero_partecipanti': 450, 'braccialetti': 300, 'medaglie': 20, 'adesivi': 400, 'coppe': 5, 'voci_ricavi': [{'descrizione': 'Quote piazzole espositori (45 stand)', 'importo': 2250}, {'descrizione': 'Sponsor locali', 'importo': 1500}], 'voci_costi': [{'descrizione': 'Pratica SIAE e diritti musicali', 'importo': 380}, {'descrizione': 'Bagni chimici e transenne', 'importo': 620}]},
                {'id': 202, 'data': '2026-07-18', 'scuola_id': 2, 'iniziativa': 'Notte Bianca & Sagra dei Sapori', 'numero_partecipanti': 900, 'braccialetti': 600, 'medaglie': 0, 'adesivi': 500, 'coppe': 3, 'voci_ricavi': [{'descrizione': 'Incasso stand gastronomico', 'importo': 5400}, {'descrizione': 'Patrocinio Comune', 'importo': 2000}], 'voci_costi': [{'descrizione': 'Service audio-luci concerto', 'importo': 1400}, {'descrizione': 'Materie prime cucina', 'importo': 1950}]}
            ],
            'stock': {'braccialetti': 400, 'medaglie': 80, 'adesivi': 600, 'coppe': 12},
            'movimenti': {
                'braccialetti': [{'id': 1, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 1300, 'prezzo_unitario': 0.30, 'motivo': 'Pass ingresso area spettacoli'}],
                'medaglie': [{'id': 2, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 100, 'prezzo_unitario': 2.10, 'motivo': 'Premi gare popolari'}],
                'adesivi': [{'id': 3, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 1500, 'prezzo_unitario': 0.12, 'motivo': 'Gadget festa paese'}],
                'coppe': [{'id': 4, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 20, 'prezzo_unitario': 15.0, 'motivo': 'Trofei concorso vetrine'}]
            },
            'inventario': [
                {'id': 1, 'nome': 'Cucina mobile inox 6 fuochi + friggitrici', 'quantita': 1, 'valore_unitario': 4200.0, 'valore_totale': 4200.0, 'data_acquisto': '2025-04-10', 'stato': 'Operativo'},
                {'id': 2, 'nome': 'Set panche e tavoli birreria (25 set)', 'quantita': 25, 'valore_unitario': 140.0, 'valore_totale': 3500.0, 'data_acquisto': '2025-05-01', 'stato': 'Operativo'}
            ],
            'entita': [
                {'id': 1, 'nome': 'Estintori omologati 6kg + Gilet Staff', 'categoria': 'Sicurezza', 'quantita': 38, 'costo_unitario': 18.0, 'data_carico': '2026-03-15', 'condizione': 'Nuovo'}
            ],
            'entrate': [
                {'id': 1, 'data': '2026-05-01', 'tipo': 'evento', 'descrizione': 'Festa Primavera - Espositori e Sponsor', 'importo': 3750.0},
                {'id': 2, 'data': '2026-07-18', 'tipo': 'evento', 'descrizione': 'Notte Bianca - Stand e Patrocinio', 'importo': 7400.0}
            ],
            'uscite': [],
            'altro': [{'id': 1, 'data': '2026-04-02', 'descrizione': 'Polizza RC Terzi annuale manifestazioni', 'importo': 680.0}],
            'task': [
                {'id': 1, 'titolo': 'Depositare SCIA evento e Piano Emergenza in Comune', 'categoria': 'Permessi', 'data_scadenza': '2026-06-25', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 2, 'titolo': 'Aprire permesso musicale SIAE online', 'categoria': 'Amministrazione', 'data_scadenza': '2026-07-01', 'priorita': 'Alta', 'stato': 'Da fare'},
                {'id': 3, 'titolo': 'Confermare turni volontari cassa, griglia e bar', 'categoria': 'Staff', 'data_scadenza': '2026-07-10', 'priorita': 'Media', 'stato': 'Da fare'},
                {'id': 4, 'titolo': 'Verifica impianto elettrico e conformita quadri', 'categoria': 'Sicurezza', 'data_scadenza': '2026-07-16', 'priorita': 'Alta', 'stato': 'Da fare'}
            ]
        }
    },
    'asd': {
        'label': '⚽ ASD & Centro Estivo Multisport',
        'dati': {
            'scuole': [{'id': 1, 'nome': 'Centro Sportivo Valgrigna', 'tipo': 'Impianto', 'referente': 'Luca Fontana', 'telefono': '335 771122'}],
            'eventi': [{'id': 301, 'data': '2026-06-15', 'scuola_id': 1, 'iniziativa': 'Summer Sport Camp - Turno 1', 'numero_partecipanti': 65, 'braccialetti': 65, 'medaglie': 65, 'adesivi': 130, 'coppe': 4, 'voci_ricavi': [{'descrizione': 'Rette iscritti camp', 'importo': 5850}], 'voci_costi': [{'descrizione': 'Istruttori e mensa', 'importo': 3450}]}],
            'stock': {'braccialetti': 255, 'medaglie': 155, 'adesivi': 270, 'coppe': 14},
            'movimenti': {'braccialetti': [{'id': 1, 'data': '2026-05-01', 'tipo': 'carico', 'quantita': 320, 'prezzo_unitario': 0.50, 'motivo': 'Braccialetti camp'}], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Defibrillatore DAE + teca', 'quantita': 2, 'valore_unitario': 1150.0, 'valore_totale': 2300.0, 'data_acquisto': '2025-09-10', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Kit palloni e pettorine', 'categoria': 'Attrezzatura', 'quantita': 45, 'costo_unitario': 18.0, 'data_carico': '2026-04-10', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-06-15', 'tipo': 'evento', 'descrizione': 'Incasso Summer Sport Camp', 'importo': 5850.0}],
            'uscite': [], 'altro': [],
            'task': [
                {'id': 1, 'titolo': 'Controllare scadenza certificati medici atleti', 'categoria': 'Segreteria', 'data_scadenza': '2026-06-10', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 2, 'titolo': 'Raccogliere deleghe ritiro minori e allergie', 'categoria': 'Camp Estivo', 'data_scadenza': '2026-06-12', 'priorita': 'Alta', 'stato': 'Da fare'},
                {'id': 3, 'titolo': 'Testare batterie ed elettrodi Defibrillatore DAE', 'categoria': 'Sicurezza', 'data_scadenza': '2026-06-14', 'priorita': 'Alta', 'stato': 'Completato'}
            ]
        }
    },
    'scuola': {
        'label': '🏫 Scuola & Istituto Comprensivo',
        'dati': {
            'scuole': [{'id': 1, 'nome': 'Plesso Primaria Rodari', 'tipo': 'Scuola Primaria', 'referente': 'Ins. Colombo', 'telefono': '0364 221100'}],
            'eventi': [{'id': 401, 'data': '2026-05-19', 'scuola_id': 1, 'iniziativa': 'Olimpiadi Matematica & Sport', 'numero_partecipanti': 210, 'braccialetti': 210, 'medaglie': 90, 'adesivi': 210, 'coppe': 9, 'voci_ricavi': [{'descrizione': 'Bando Scuole Attive', 'importo': 2500}], 'voci_costi': [{'descrizione': 'Kit robotica e pullman', 'importo': 1500}]}],
            'stock': {'braccialetti': 150, 'medaglie': 110, 'adesivi': 310, 'coppe': 8},
            'movimenti': {'braccialetti': [], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Carrello ricarica + 24 Tablet', 'quantita': 1, 'valore_unitario': 5400.0, 'valore_totale': 5400.0, 'data_acquisto': '2025-11-10', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Pettorine alta visibilita gite', 'categoria': 'Sicurezza', 'quantita': 80, 'costo_unitario': 5.0, 'data_carico': '2026-01-25', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-05-19', 'tipo': 'evento', 'descrizione': 'Finanziamento Bando Scuole', 'importo': 2500.0}],
            'uscite': [], 'altro': [],
            'task': [
                {'id': 1, 'titolo': 'Raccogliere autorizzazioni famiglie per uscita didattica', 'categoria': 'Segreteria', 'data_scadenza': '2026-05-12', 'priorita': 'Alta', 'stato': 'In corso'},
                {'id': 2, 'titolo': 'Inviare elenco alunni per copertura assicurativa', 'categoria': 'Amministrazione', 'data_scadenza': '2026-05-14', 'priorita': 'Alta', 'stato': 'Da fare'}
            ]
        }
    }
}

@bp.route('/lista', methods=['GET'])
@login_required
def api_lista_profili():
    d = storage.get_dati()
    return jsonify({'success': True, 'attivo': d.get('profilo_demo_attivo', 'motoclub'), 'profili': [{'id': k, 'label': v['label']} for k, v in PROFILI.items()]})

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
    return jsonify({'success': True, 'profilo': pid, 'label': PROFILI[pid]['label']})