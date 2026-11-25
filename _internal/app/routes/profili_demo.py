from __future__ import annotations
import copy, json, os, shutil
from app.config import DATA_DIR
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
                {'id': 101, 'data': '2026-04-18', 'scuola_id': 1, 'foto': [{'file': 'demo_moto_1.png', 'didascalia': 'Briefing sicurezza stradale con gli studenti', 'tag': ['scuole', 'sicurezza']}], 'iniziativa': 'Educazione Stradale & Mini-Cross', 'numero_partecipanti': 85, 'braccialetti': 85, 'medaglie': 85, 'adesivi': 120, 'coppe': 3, 'voci_ricavi': [{'descrizione': 'Contributo Comune', 'importo': 1200}], 'voci_costi': [{'descrizione': 'Carburante e polizza FMI', 'importo': 320}]},
                {'id': 102, 'data': '2026-05-24', 'scuola_id': 2, 'foto': [{'file': 'demo_moto_2.png', 'didascalia': 'Paddock e premiazioni giovani piloti', 'tag': ['pista', 'openday']}], 'iniziativa': 'Open Day Pista Giovanile', 'numero_partecipanti': 110, 'braccialetti': 110, 'medaglie': 60, 'adesivi': 150, 'coppe': 6, 'voci_ricavi': [{'descrizione': 'Quote iscrizione e sponsor', 'importo': 2150}], 'voci_costi': [{'descrizione': 'Ambulanza e fettucciato', 'importo': 570}]}
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
                {'id': 1, 'titolo': 'Verificare carica batterie minimoto elettriche #1 e #2', 'categoria': 'generale', 'scadenza': '2026-12-05', 'priorita': 'alta', 'stato': 'in_lavorazione', 'note': 'Controllo voltaggio e connettori prima della tappa', 'referente': 'Marco Rossi'},
                {'id': 2, 'titolo': 'Preparare 120 braccialetti numerati per tappa scolastica', 'categoria': 'braccialetti', 'scadenza': '2026-12-08', 'priorita': 'alta', 'stato': 'da_fare', 'note': 'Dividere in buste da 30 per classe', 'referente': 'Prof.ssa Giulia Bianchi'},
                {'id': 3, 'titolo': 'Confezionare 90 medaglie finisher con nastrino tricolore', 'categoria': 'medaglie', 'scadenza': '2026-12-10', 'priorita': 'media', 'stato': 'da_fare', 'note': 'Verificare scorta nastrini in magazzino', 'referente': 'Marco Rossi'},
                {'id': 4, 'titolo': 'Stampare 150 adesivi casco Trova il tuo Braaap', 'categoria': 'adesivi', 'scadenza': '2026-12-12', 'priorita': 'media', 'stato': 'in_lavorazione', 'note': 'Finitura lucida resistente acqua', 'referente': 'Dott. Andrea Riva'},
                {'id': 5, 'titolo': 'Lucidare e targhettare 6 coppe podi categorie giovanili', 'categoria': 'coppe', 'scadenza': '2026-12-15', 'priorita': 'bassa', 'stato': 'da_fare', 'note': 'Incisione data evento sul basamento', 'referente': 'Marco Rossi'},
                {'id': 6, 'titolo': 'Assembleare kit gadgets benvenuto e portachiavi pista', 'categoria': 'gadgets', 'scadenza': '2026-12-18', 'priorita': 'media', 'stato': 'completato', 'note': 'Pronti in scatola #3 furgone', 'referente': 'Prof.ssa Giulia Bianchi'}
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
                {'id': 601, 'data': '2026-05-14', 'scuola_id': 1, 'foto': [{'file': 'demo_az_1.png', 'didascalia': 'Rilievo tecnico e presentazione preventivo', 'tag': ['preventivi', 'clienti']}], 'iniziativa': 'Consegna Preventivo & Brochure Ristrutturazione', 'numero_partecipanti': 4, 'braccialetti': 25, 'medaglie': 5, 'adesivi': 40, 'coppe': 3, 'voci_ricavi': [{'descrizione': 'Acconto incarico e consulenza', 'importo': 2800}], 'voci_costi': [{'descrizione': 'Stampe tavole A0 e rilegatura', 'importo': 210}]},
                {'id': 602, 'data': '2026-05-28', 'scuola_id': 2, 'foto': [{'file': 'demo_az_2.png', 'didascalia': 'Collaudo finale e consegna commessa', 'tag': ['cantiere', 'collaudo']}], 'iniziativa': 'Appuntamento Collaudo & Chiusura Lavori', 'numero_partecipanti': 6, 'braccialetti': 50, 'medaglie': 10, 'adesivi': 80, 'coppe': 4, 'voci_ricavi': [{'descrizione': 'Saldo fornitura e posa in opera', 'importo': 4600}], 'voci_costi': [{'descrizione': 'Minuteria ferramenta e consumabili', 'importo': 340}]}
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
                {'id': 1, 'titolo': 'Inviare preventivo aggiornato ristrutturazione a Studio Bresciani', 'categoria': 'braccialetti', 'scadenza': '2026-12-04', 'priorita': 'alta', 'stato': 'in_lavorazione', 'note': 'Allegare capitolato e brochure pdf', 'referente': 'Arch. Lorenzo Bresciani'},
                {'id': 2, 'titolo': 'Confermare appuntamento sopralluogo capannone con il Team', 'categoria': 'coppe', 'scadenza': '2026-12-07', 'priorita': 'alta', 'stato': 'da_fare', 'note': 'Portare telemetro laser e campionario', 'referente': 'Geom. Paolo Ferrari'},
                {'id': 3, 'titolo': 'Riordinare toner plotter A0, risme A3 e tasselli in ferramenta', 'categoria': 'generale', 'scadenza': '2026-12-09', 'priorita': 'media', 'stato': 'da_fare', 'note': 'Verificare scorta minima cancelleria ed edicola', 'referente': 'Sara Conti'},
                {'id': 4, 'titolo': 'Ritirare stampe tavole tecniche e cartelline intestate', 'categoria': 'adesivi', 'scadenza': '2026-12-11', 'priorita': 'media', 'stato': 'in_lavorazione', 'note': 'Tipografia centrale ore 16:00', 'referente': 'Sara Conti'},
                {'id': 5, 'titolo': 'Preparare kit gadget promozionali e agende clienti VIP', 'categoria': 'medaglie', 'scadenza': '2026-12-14', 'priorita': 'bassa', 'stato': 'da_fare', 'note': 'Consegnare durante gli appuntamenti di dicembre', 'referente': 'Arch. Lorenzo Bresciani'},
                {'id': 6, 'titolo': 'Omaggi tecnici e chiavette USB brandizzate per nuovi clienti', 'categoria': 'gadgets', 'scadenza': '2026-12-19', 'priorita': 'media', 'stato': 'completato', 'note': 'Caricate brochure aziendali sulle chiavette', 'referente': 'Geom. Paolo Ferrari'}
            ]
        }
    },
    'proloco': {
        'label': '🎪 Pro Loco & Feste di Paese',
        'ui': {'eventi': '📅 Feste & Sagre', 'scuole': '🏛️ Enti & Partner', 'altro': '📦 Stand & Mercatini', 'bracc': '🎟️ Pass & Biglietti', 'med': '🏅 Premi & Lotteria', 'ades': '🏷️ Locandine & Flyer', 'coppe': '🏆 Trofei & Targhe', 'mat': '🎪 Attrezzature Stand'},
        'dati': {
            'rubrica': [{'id': 1, 'nome': 'Comm. Roberto Cattaneo', 'ruolo': 'Ufficio SUAP Comune', 'telefono': '347 0003301', 'email': 'suap@comunedemo.it', 'note': 'Permessi occupazione suolo'}, {'id': 2, 'nome': 'Elena Ferri', 'ruolo': 'Coordinatrice Stand & Volontari', 'telefono': '347 0003302', 'email': 'elena@prolocodemo.it', 'note': 'Turni cucina e cassa'}],
            'scuole': [{'id': 1, 'nome': 'Comune - Ufficio SUAP & Polizia Locale', 'tipo': 'Ente Pubblico', 'referente': 'Comm. Roberto Cattaneo', 'telefono': '0364 000301', 'email': 'suap@comunedemo.it'}],
            'eventi': [{'id': 201, 'data': '2026-07-18', 'scuola_id': 1, 'foto': [{'file': 'demo_pro_1.png', 'didascalia': 'Allestimento piazza e stand gastronomico', 'tag': ['sagra', 'piazza']}], 'iniziativa': 'Notte Bianca & Sagra dei Sapori', 'numero_partecipanti': 900, 'braccialetti': 600, 'medaglie': 20, 'adesivi': 500, 'coppe': 5, 'voci_ricavi': [{'descrizione': 'Stand gastronomico e patrocinio', 'importo': 7400}], 'voci_costi': [{'descrizione': 'Service concerto e forniture cucina', 'importo': 3350}]}],
            'altro': [{'id': 1, 'data': '2026-08-10', 'titolo': 'Mercatino Artigiani Sotto le Stelle', 'luogo': 'Centro Storico', 'note': '35 bancarelle confermate'}],
            'stock': {'braccialetti': 400, 'medaglie': 80, 'adesivi': 600, 'coppe': 12},
            'movimenti': {'braccialetti': [{'id': 1, 'data': '2026-03-01', 'tipo': 'carico', 'quantita': 1000, 'prezzo_unitario': 0.30, 'motivo': 'Pass ingresso area spettacoli'}], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Cucina mobile inox + 25 set panche legno', 'quantita': 1, 'valore_unitario': 7700.0, 'valore_totale': 7700.0, 'data_acquisto': '2025-05-01', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Estintori 6kg omologati + Gilet alta visibilita Staff', 'categoria': 'Sicurezza', 'quantita': 38, 'costo_unitario': 18.0, 'data_carico': '2026-03-15', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-07-18', 'tipo': 'evento', 'descrizione': 'Incasso Notte Bianca', 'importo': 7400.0}],
            'uscite': [{'id': 1, 'data': '2026-04-02', 'descrizione': 'Polizza RC Terzi manifestazioni + SIAE', 'importo': 980.0}],
            'postit': [{'id': 1, 'testo': 'Inviare planimetria vie di fuga alla Polizia Locale', 'colore': '#fde68a'}],
                        'task': [
                {'id': 1, 'titolo': 'Depositare SCIA evento e Piano Emergenza in Comune', 'categoria': 'generale', 'scadenza': '2026-12-06', 'priorita': 'alta', 'stato': 'in_lavorazione', 'note': 'Protocollo SUAP + planimetria vie di fuga', 'referente': 'Comm. Roberto Cattaneo'},
                {'id': 2, 'titolo': 'Preparare 600 pass ingresso e braccialetti area spettacoli', 'categoria': 'braccialetti', 'scadenza': '2026-12-09', 'priorita': 'alta', 'stato': 'da_fare', 'note': 'Numerazione progressiva per botteghino', 'referente': 'Elena Ferri'},
                {'id': 3, 'titolo': 'Ritirare premi lotteria e riconoscimenti espositori', 'categoria': 'medaglie', 'scadenza': '2026-12-12', 'priorita': 'media', 'stato': 'da_fare', 'note': 'Controllare cesti e buoni sponsor locali', 'referente': 'Elena Ferri'},
                {'id': 4, 'titolo': 'Affissione locandine e distribuzione flyer nei negozi', 'categoria': 'adesivi', 'scadenza': '2026-12-14', 'priorita': 'media', 'stato': 'in_lavorazione', 'note': 'Coprire anche i comuni limitrofi', 'referente': 'Elena Ferri'},
                {'id': 5, 'titolo': 'Incidere targhe ringraziamento e trofei gara gastronomica', 'categoria': 'coppe', 'scadenza': '2026-12-16', 'priorita': 'bassa', 'stato': 'da_fare', 'note': 'Premiazione sul palco centrale ore 21:30', 'referente': 'Comm. Roberto Cattaneo'},
                {'id': 6, 'titolo': 'Preparare gadget ricordo e grembiuli staff cucina', 'categoria': 'gadgets', 'scadenza': '2026-12-20', 'priorita': 'media', 'stato': 'completato', 'note': '35 grembiuli lavati e imbustati', 'referente': 'Elena Ferri'}
            ]
        }
    }
,
    'asd': {
        'label': '⚽ ASD & Centro Estivo Multisport',
        'ui': {'eventi': '📅 Tornei & Camp', 'scuole': '🏟️ Impianti & Società', 'altro': '📦 Stage & Amichevoli', 'bracc': '🎽 Kit & Braccialetti', 'med': '🏅 Medaglie & Trofei', 'ades': '🔖 Adesivi & Borracce', 'coppe': '🏆 Coppe FairPlay', 'mat': '⚽ Attrezzatura Sportiva'},
        'dati': {
            'rubrica': [{'id': 1, 'nome': 'Luca Fontana', 'ruolo': 'Direttore Centro Sportivo', 'telefono': '335 0004401', 'email': 'l.fontana@sportdemo.it', 'note': 'Campi calcio e palestra'}, {'id': 2, 'nome': 'Chiara Bellini', 'ruolo': 'Coordinatrice Istruttori', 'telefono': '335 0004402', 'email': 'c.bellini@sportdemo.it', 'note': 'Turni camp estivo'}],
            'scuole': [{'id': 1, 'nome': 'Centro Sportivo Comunale Valgrigna', 'tipo': 'Impianto Sportivo', 'referente': 'Luca Fontana', 'telefono': '0364 000401', 'email': 'impianto@sportdemo.it'}],
            'eventi': [{'id': 301, 'data': '2026-06-15', 'scuola_id': 1, 'foto': [{'file': 'demo_asd_1.png', 'didascalia': 'Attivita multisport al campo estivo', 'tag': ['camp', 'ragazzi']}, {'file': 'demo_asd_2.png', 'didascalia': 'Premiazione torneo giovanile', 'tag': ['torneo', 'premiazioni']}], 'iniziativa': 'Summer Sport Camp - Turno 1', 'numero_partecipanti': 65, 'braccialetti': 65, 'medaglie': 65, 'adesivi': 130, 'coppe': 4, 'voci_ricavi': [{'descrizione': 'Rette settimanali iscritti', 'importo': 5850}], 'voci_costi': [{'descrizione': 'Istruttori e servizio mensa', 'importo': 3450}]}],
            'altro': [{'id': 1, 'data': '2026-07-04', 'titolo': 'Amichevole Genitori vs Figli & Grigliata ASD', 'luogo': 'Campo Principale', 'note': 'Serata conclusiva turno 2'}],
            'stock': {'braccialetti': 255, 'medaglie': 155, 'adesivi': 270, 'coppe': 14},
            'movimenti': {'braccialetti': [{'id': 1, 'data': '2026-05-01', 'tipo': 'carico', 'quantita': 320, 'prezzo_unitario': 0.50, 'motivo': 'Braccialetti gruppi camp'}], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Defibrillatore DAE + teca riscaldata', 'quantita': 2, 'valore_unitario': 1150.0, 'valore_totale': 2300.0, 'data_acquisto': '2025-09-10', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Kit palloni calcio/volley, pettorine e conetti', 'categoria': 'Attrezzatura', 'quantita': 45, 'costo_unitario': 18.0, 'data_carico': '2026-04-10', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-06-15', 'tipo': 'evento', 'descrizione': 'Incasso Summer Sport Camp', 'importo': 5850.0}],
            'uscite': [{'id': 1, 'data': '2026-05-15', 'descrizione': 'Tesseramenti assicurativi atleti CSI', 'importo': 920.0}],
            'portafoglio': [{'id': 1, 'nome': 'Conto Corrente ASD', 'saldo': 6420.0}, {'id': 2, 'nome': 'Cassa Segreteria Campo', 'saldo': 540.0}],
            'liste': [{'id': 1, 'titolo': 'Checklist Apertura Camp Estivo', 'voci': [{'testo': 'Verifica kit primo soccorso e ghiaccio spray', 'fatto': True}, {'testo': 'Stampa elenchi allergie e deleghe ritiro', 'fatto': False}]}],
            'note_calendario': [{'id': 1, 'data': '2026-06-15', 'testo': 'Accoglienza famiglie ore 08:30 e consegna kit camp'}],
            'postit': [{'id': 1, 'testo': 'Controllare scadenza elettrodi DAE prima del torneo', 'colore': '#bbf7d0'}],
                        'task': [
                {'id': 1, 'titolo': 'Controllare scadenza certificati medici e batterie DAE', 'categoria': 'generale', 'scadenza': '2026-12-05', 'priorita': 'alta', 'stato': 'in_lavorazione', 'note': 'Verifica registro sanitario atleti CSI', 'referente': 'Luca Fontana'},
                {'id': 2, 'titolo': 'Assegnare braccialetti colore squadra gruppi camp', 'categoria': 'braccialetti', 'scadenza': '2026-12-08', 'priorita': 'alta', 'stato': 'da_fare', 'note': 'Rosso junior, blu senior', 'referente': 'Chiara Bellini'},
                {'id': 3, 'titolo': 'Preparare 65 medaglie partecipazione torneo multisport', 'categoria': 'medaglie', 'scadenza': '2026-12-11', 'priorita': 'media', 'stato': 'da_fare', 'note': 'Consegna a fine settimana camp', 'referente': 'Chiara Bellini'},
                {'id': 4, 'titolo': 'Applicare adesivi nominativi su borracce e zaini ragazzi', 'categoria': 'adesivi', 'scadenza': '2026-12-13', 'priorita': 'bassa', 'stato': 'in_lavorazione', 'note': 'Etichette resistenti al lavaggio', 'referente': 'Chiara Bellini'},
                {'id': 5, 'titolo': 'Allestire tavolo coppe Fair-Play e miglior portiere', 'categoria': 'coppe', 'scadenza': '2026-12-16', 'priorita': 'media', 'stato': 'da_fare', 'note': '4 trofei principali + targhe', 'referente': 'Luca Fontana'},
                {'id': 6, 'titolo': 'Distribuire sacche sportive e polsini gadget iscritti', 'categoria': 'gadgets', 'scadenza': '2026-12-19', 'priorita': 'media', 'stato': 'completato', 'note': 'Kit completi in segreteria campo', 'referente': 'Luca Fontana'}
            ]
        }
    },
    'scuola': {
        'label': '🏫 Scuola & Istituto Comprensivo',
        'ui': {'eventi': '📅 Progetti & Uscite', 'scuole': '🏫 Plessi & Classi', 'altro': '📦 Laboratori & PON', 'bracc': '🪪 Pass Uscite', 'med': '🏅 Attestati & Premi', 'ades': '🔖 Etichette & Stampe', 'coppe': '🏆 Targhe & Diplomi', 'mat': '📚 Dotazioni Didattiche'},
        'dati': {
            'rubrica': [{'id': 1, 'nome': 'Ins. Marta Colombo', 'ruolo': 'Referente Progetti PTOF', 'telefono': '339 0005501', 'email': 'm.colombo@istitutodemo.edu.it', 'note': 'Plesso Primaria'}, {'id': 2, 'nome': 'Prof. Davide Galli', 'ruolo': 'Coordinatore STEM & Sport', 'telefono': '339 0005502', 'email': 'd.galli@istitutodemo.edu.it', 'note': 'Secondaria I Grado'}],
            'scuole': [{'id': 1, 'nome': 'Plesso Primaria "G. Rodari"', 'tipo': 'Scuola Primaria', 'referente': 'Ins. Marta Colombo', 'telefono': '0364 000501', 'email': 'rodari@istitutodemo.edu.it'}, {'id': 2, 'nome': 'Scuola Secondaria "A. Manzoni"', 'tipo': 'Scuola Media', 'referente': 'Prof. Davide Galli', 'telefono': '0364 000502', 'email': 'manzoni@istitutodemo.edu.it'}],
            'eventi': [{'id': 401, 'data': '2026-05-19', 'scuola_id': 2, 'foto': [{'file': 'demo_scuola_1.png', 'didascalia': 'Olimpiadi di robotica e sport interclasse', 'tag': ['stem', 'olimpiadi']}, {'file': 'demo_scuola_2.png', 'didascalia': 'Laboratorio ambientale e giornata green', 'tag': ['ambiente', 'primaria']}], 'iniziativa': 'Olimpiadi Matematica, Robotica & Sport', 'numero_partecipanti': 210, 'braccialetti': 210, 'medaglie': 90, 'adesivi': 210, 'coppe': 9, 'voci_ricavi': [{'descrizione': 'Bando Regionale Scuole Attive', 'importo': 2500}], 'voci_costi': [{'descrizione': 'Kit robotica e pullman trasferimento', 'importo': 1500}]}],
            'altro': [{'id': 1, 'data': '2026-05-29', 'titolo': 'Mostra Finale Laboratori PON & Musica', 'luogo': 'Aula Magna Istituto', 'note': 'Aperta alle famiglie dalle 16:30'}],
            'stock': {'braccialetti': 150, 'medaglie': 110, 'adesivi': 310, 'coppe': 8},
            'movimenti': {'braccialetti': [{'id': 1, 'data': '2026-01-20', 'tipo': 'carico', 'quantita': 360, 'prezzo_unitario': 0.35, 'motivo': 'Pass identificativi uscite didattiche'}], 'medaglie': [], 'adesivi': [], 'coppe': []},
            'inventario': [{'id': 1, 'nome': 'Carrello ricarica + 24 Tablet didattici', 'quantita': 1, 'valore_unitario': 5400.0, 'valore_totale': 5400.0, 'data_acquisto': '2025-11-10', 'stato': 'Operativo'}],
            'entita': [{'id': 1, 'nome': 'Pettorine alta visibilita gite + Kit robotica educativa', 'categoria': 'Sicurezza & Didattica', 'quantita': 80, 'costo_unitario': 7.5, 'data_carico': '2026-01-25', 'condizione': 'Nuovo'}],
            'entrate': [{'id': 1, 'data': '2026-05-19', 'tipo': 'evento', 'descrizione': 'Finanziamento Bando Scuole Attive', 'importo': 2500.0}],
            'uscite': [{'id': 1, 'data': '2026-03-05', 'descrizione': 'Rinnovo licenze software didattici', 'importo': 340.0}],
            'portafoglio': [{'id': 1, 'nome': 'Fondo Progetti PTOF / Comitato Genitori', 'saldo': 3180.0}],
            'liste': [{'id': 1, 'titolo': 'Checklist Uscita Didattica', 'voci': [{'testo': 'Raccolta moduli consenso firmati dai genitori', 'fatto': True}, {'testo': 'Consegna elenco alunni a compagnia pullman', 'fatto': False}]}],
            'note_calendario': [{'id': 1, 'data': '2026-05-19', 'testo': 'Partenza pullman ore 08:45 dal piazzale del plesso'}],
            'postit': [{'id': 1, 'testo': 'Stampare attestati partecipazione per le classi 3A e 3B', 'colore': '#ddd6fe'}],
                        'task': [
                {'id': 1, 'titolo': 'Raccogliere autorizzazioni famiglie per uscita didattica', 'categoria': 'generale', 'scadenza': '2026-12-05', 'priorita': 'alta', 'stato': 'in_lavorazione', 'note': 'Mancano 3 moduli classe 3B', 'referente': 'Ins. Marta Colombo'},
                {'id': 2, 'titolo': 'Consegnare pass identificativi uscite ai docenti accompagnatori', 'categoria': 'braccialetti', 'scadenza': '2026-12-08', 'priorita': 'alta', 'stato': 'da_fare', 'note': 'Numeri emergenza scuola stampati sul retro', 'referente': 'Ins. Marta Colombo'},
                {'id': 3, 'titolo': 'Stampare attestati e medaglie Olimpiadi STEM & Sport', 'categoria': 'medaglie', 'scadenza': '2026-12-12', 'priorita': 'media', 'stato': 'da_fare', 'note': '90 finalisti tra primaria e media', 'referente': 'Prof. Davide Galli'},
                {'id': 4, 'titolo': 'Etichettare kit robotica educativa e cartelle progetti PON', 'categoria': 'adesivi', 'scadenza': '2026-12-14', 'priorita': 'bassa', 'stato': 'in_lavorazione', 'note': 'Inventario laboratorio informatica', 'referente': 'Prof. Davide Galli'},
                {'id': 5, 'titolo': 'Preparare targhe e diplomi per le classi vincitrici', 'categoria': 'coppe', 'scadenza': '2026-12-17', 'priorita': 'media', 'stato': 'da_fare', 'note': 'Cerimonia in Aula Magna con il Dirigente', 'referente': 'Prof. Davide Galli'},
                {'id': 6, 'titolo': 'Consegnare segnalibri ecologici e matite gadget giornata green', 'categoria': 'gadgets', 'scadenza': '2026-12-20', 'priorita': 'bassa', 'stato': 'completato', 'note': 'Distribuiti a tutte le classi del plesso', 'referente': 'Ins. Marta Colombo'}
            ]
        }
    }
}

@bp.before_app_request
def _ensure_demo_bootstrap():
    d = storage.get_dati()
    if os.environ.get('VERCEL') and not d.get('profilo_demo_attivo'):
        for k, v in _espandi_3x('motoclub', PROFILI['motoclub']['dati']).items():
            d[k] = v
        d['profilo_demo_attivo'] = 'motoclub'
        d['giacenza_iniziale_impostata'] = True
        d['import_excel_fatto'] = True
        src_g = Path(__file__).resolve().parents[2] / 'static' / 'demo_gallery'
        dst_g = DATA_DIR / 'uploads' / 'eventi'
        dst_g.mkdir(parents=True, exist_ok=True)
        if src_g.exists():
            for f in src_g.glob('*.png'):
                if not (dst_g / f.name).exists():
                    shutil.copy2(f, dst_g / f.name)
        storage.salva_dati(d, crea_backup=False)

def _espandi_3x(pid, dati):
    d = copy.deepcopy(dati)
    scadenze_imminenti = ['2026-11-26', '2026-11-27', '2026-11-28', '2026-11-29', '2026-11-30', '2026-12-01']
    for idx, t in enumerate(d.get('task', [])):
        t['scadenza'] = scadenze_imminenti[idx % len(scadenze_imminenti)]
        if idx < 4:
            t['priorita'] = 'alta'
            t['stato'] = 'da_fare' if idx % 2 == 0 else 'in_lavorazione'
    extra_tasks = [
        {'id': 101, 'titolo': 'Urgente: conferma fornitura e consegna materiali evento', 'categoria': 'generale', 'scadenza': '2026-11-26', 'priorita': 'alta', 'stato': 'da_fare', 'note': 'Scadenza domani mattina', 'referente': 'Coordinamento'},
        {'id': 102, 'titolo': 'Verifica lotti braccialetti / pass e buste nominali', 'categoria': 'braccialetti', 'scadenza': '2026-11-27', 'priorita': 'alta', 'stato': 'in_lavorazione', 'note': 'Controllo numerazione sequenziale', 'referente': 'Logistica'},
        {'id': 103, 'titolo': 'Controllo incisioni targhe, coppe e premi podi', 'categoria': 'coppe', 'scadenza': '2026-11-28', 'priorita': 'alta', 'stato': 'da_fare', 'note': 'Ritiro presso premiazioni', 'referente': 'Segreteria'},
        {'id': 104, 'titolo': 'Stampa urgente locandine, adesivi e kit informativi', 'categoria': 'adesivi', 'scadenza': '2026-11-29', 'priorita': 'media', 'stato': 'da_fare', 'note': 'Bozza approvata', 'referente': 'Grafica'},
        {'id': 105, 'titolo': 'Confezionamento medaglie / riconoscimenti partecipanti', 'categoria': 'medaglie', 'scadenza': '2026-11-30', 'priorita': 'media', 'stato': 'in_lavorazione', 'note': 'Pronti in scatole numerate', 'referente': 'Magazzino'},
        {'id': 106, 'titolo': 'Allestimento buste gadgets e omaggi benvenuto', 'categoria': 'gadgets', 'scadenza': '2026-12-01', 'priorita': 'media', 'stato': 'da_fare', 'note': '150 kit completi', 'referente': 'Accoglienza'}
    ]
    d['task'] = d.get('task', []) + extra_tasks
    base_ev = list(d.get('eventi', []))
    mesi = [('2026-02-14', 'Edizione Invernale'), ('2026-03-21', 'Tappa Primavera'), ('2026-05-10', 'Speciale Maggio'), ('2026-06-21', 'Evento Estate'), ('2026-09-19', 'Rientro Autunno'), ('2026-10-24', 'Trofeo d Autunno'), ('2026-11-28', 'Speciale Novembre'), ('2026-12-12', 'Gran Gala Dicembre')]
    for i, (dt, suff) in enumerate(mesi):
        src = copy.deepcopy(base_ev[i % len(base_ev)])
        src['id'] = 700 + i
        src['data'] = dt
        src['iniziativa'] = f"{src['iniziativa']} - {suff}"
        src['numero_partecipanti'] = int(src.get('numero_partecipanti', 50) * (1 + (i % 3) * 0.25))
        d['eventi'].append(src)
    for sec, suf in [('rubrica', ' (Resp. Area)'), ('scuole', ' - Sede Distaccata'), ('altro', ' - Sessione Extra'), ('inventario', ' (Unità B)'), ('entita', ' - Scorta Magazzino'), ('entrate', ' - Seconda Tranche'), ('uscite', ' - Fornitura Integrativa'), ('postit', ' [Promemoria]'), ('note_calendario', ' - Conferma Orari'), ('liste', ' (Aggiornata)'), ('portafoglio', ' - Riserva')]:
        orig = list(d.get(sec, []))
        for rep in (1, 2):
            for j, item in enumerate(orig):
                cp = copy.deepcopy(item)
                cp['id'] = 500 + rep * 50 + j
                for k in ('nome', 'titolo', 'descrizione', 'testo'):
                    if k in cp and isinstance(cp[k], str):
                        cp[k] = f"{cp[k]}{suf} #{rep+1}"
                if 'telefono' in cp:
                    cp['telefono'] = f"33{rep} 009{rep}{j:02d}"
                if 'email' in cp and '@' in cp['email']:
                    cp['email'] = cp['email'].replace('@', f"{rep+1}@")
                d.setdefault(sec, []).append(cp)
    return d

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
        pwd = (body.get('password') or '').strip()
        expected = os.environ.get('BRAAAP_PASSWORD') or d.get('password_accesso') or ''
        if not expected or pwd != expected:
            return jsonify({'success': False, 'error': 'Password errata: accesso ai dati reali negato'}), 403
        orig = json.loads(BACKUP_FILE.read_text(encoding='utf-8'))
        d.clear()
        d.update(orig)
        storage.salva_dati(d, crea_backup=False)
        return jsonify({'success': True, 'profilo': 'motoclub'})
    if pid not in PROFILI:
        return jsonify({'success': False, 'error': 'Profilo non valido'}), 400
    if not d.get('profilo_demo_attivo') and not BACKUP_FILE.exists():
        BACKUP_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    for k, v in _espandi_3x(pid, PROFILI[pid]['dati']).items():
        d[k] = v
    d['profilo_demo_attivo'] = pid
    d['giacenza_iniziale_impostata'] = True
    d['import_excel_fatto'] = True
    src_g = Path(__file__).resolve().parents[2] / 'static' / 'demo_gallery'
    dst_g = DATA_DIR / 'uploads' / 'eventi'
    dst_g.mkdir(parents=True, exist_ok=True)
    if src_g.exists():
        for f in src_g.glob('*.png'):
            if not (dst_g / f.name).exists():
                shutil.copy2(f, dst_g / f.name)
    storage.salva_dati(d, crea_backup=False)
    return jsonify({'success': True, 'profilo': pid, 'ui': PROFILI[pid]['ui']})

@bp.route('/popola', methods=['POST'])
@login_required
def api_popola_profilo():
    import random
    d = storage.get_dati()
    pid = d.get('profilo_demo_attivo', 'motoclub')
    if pid not in PROFILI:
        pid = 'motoclub'
    base = PROFILI[pid]['dati']
    n = len(d.get('eventi', [])) + 1
    ev = copy.deepcopy(random.choice(base['eventi']))
    ev['id'] = 1000 + n
    ev['data'] = f"2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    ev['iniziativa'] = f"{ev['iniziativa']} (Extra #{n})"
    ev['numero_partecipanti'] = ev.get('numero_partecipanti', 40) + random.randint(10, 45)
    d.setdefault('eventi', []).append(ev)
    cont = copy.deepcopy(random.choice(base['rubrica']))
    cont['id'] = 1000 + len(d.get('rubrica', [])) + 1
    cont['nome'] = f"{cont['nome']} #{cont['id'] - 1000}"
    cont['telefono'] = f"339 70{random.randint(10000,99999)}"
    d.setdefault('rubrica', []).append(cont)
    cat_scelta = random.choice(['generale', 'braccialetti', 'medaglie', 'adesivi', 'coppe', 'gadgets'])
    tk = copy.deepcopy(random.choice(base['task']))
    tk['id'] = 1000 + len(d.get('task', [])) + 1
    tk['categoria'] = cat_scelta
    tk['titolo'] = f"[{cat_scelta.upper()}] {tk['titolo']} #{tk['id'] - 1000}"
    tk['scadenza'] = f"2026-11-{random.randint(26,30):02d}"
    tk['priorita'] = random.choice(['alta', 'media'])
    tk['stato'] = 'da_fare'
    d.setdefault('task', []).append(tk)
    mat = copy.deepcopy(random.choice(base['entita']))
    mat['id'] = 1000 + len(d.get('entita', [])) + 1
    mat['nome'] = f"{mat['nome']} (Lotto #{mat['id'] - 1000})"
    mat['quantita'] = mat.get('quantita', 10) + random.randint(5, 25)
    d.setdefault('entita', []).append(mat)
    imp = random.choice([450.0, 780.0, 1150.0, 1600.0])
    d.setdefault('entrate', []).append({'id': 1000 + len(d.get('entrate', [])) + 1, 'data': ev['data'], 'tipo': 'evento', 'descrizione': f"Incasso {ev['iniziativa']}", 'importo': imp})
    for k in ('braccialetti', 'medaglie', 'adesivi', 'coppe'):
        d.setdefault('stock', {})[k] = d.get('stock', {}).get(k, 0) + random.randint(10, 40)
    storage.salva_dati(d, crea_backup=False)
    return jsonify({'success': True, 'profilo': pid, 'tot_eventi': len(d['eventi']), 'tot_task': len(d['task']), 'tot_rubrica': len(d['rubrica'])})