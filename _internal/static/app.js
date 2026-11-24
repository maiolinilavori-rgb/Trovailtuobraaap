// ============================================================
// STATO
// ============================================================
var STATO = {
  eventi: [], scuole: [], task: [], rubrica: [],
  movimenti: {braccialetti:[], medaglie:[], adesivi:[], coppe:[]},
  note_calendario: [], inventario: [], entita: [], portafoglio: [],
  postit: [], liste: [], categorie_entita: [], soglie_scorta: {},
  giacenza_iniziale_impostata: false, import_excel_fatto: false
};
var annoCal = new Date().getFullYear();
var meseCal = new Date().getMonth() + 1;
var calAnno = new Date().getFullYear();
var calMese = new Date().getMonth() + 1;
var MESI_NOMI = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'];
var MESI_BREVI = ['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic'];
var GIORNI_NOMI = ['Domenica','Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato'];

function id(el) { return document.getElementById(el); }
function apriModale(mid) { id(mid).classList.add('open'); }
function chiudiModale(mid) { id(mid).classList.remove('open'); }

// ============================================================
// PRIMO AVVIO
// ============================================================
function paAggiungiCarico() {
  var c = id('pa-carichi-extra');
  var div = document.createElement('div');
  div.className = 'carico-extra-riga';
  div.innerHTML =
    '<input placeholder="Es. braccialetti fatti a luglio 2026">' +
    '<select><option value="braccialetti">Bracc.</option><option value="medaglie">Med.</option><option value="adesivi">Ades.</option><option value="coppe">Coppe</option></select>' +
    '<input type="number" placeholder="Qtà">' +
    '<input type="date">' +
    '<button class="btn btn-red" onclick="this.parentNode.remove()" style="padding:4px 8px">✕</button>';
  c.appendChild(div);
}

async function paConferma() {
  var carichi_extra = [];
  document.querySelectorAll('#pa-carichi-extra .carico-extra-riga').forEach(function(r) {
    var inputs = r.querySelectorAll('input, select');
    carichi_extra.push({
      descrizione: inputs[0].value,
      categoria: inputs[1].value,
      quantita: parseInt(inputs[2].value) || 0,
      data: inputs[3].value || new Date().toISOString().split('T')[0]
    });
  });
  var payload = {
    braccialetti: parseInt(id('pa-bracc').value) || 0,
    medaglie: parseInt(id('pa-med').value) || 0,
    adesivi: parseInt(id('pa-ades').value) || 0,
    coppe: parseInt(id('pa-coppe').value) || 0,
    carichi_extra: carichi_extra
  };
  var r = await fetch('/api/primo_avvio/giacenza', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  var res = await r.json();
  if (!res.success) {
    alert('Errore: ' + (res.error || '?'));
    return;
  }
  // Ricarica la pagina: al reload, verificaPrimoAvvio() carica i dati
  // e chiama proponiImportExcel() se i file Excel sono presenti.
  location.reload();
}

async function verificaPrimoAvvio() {
  var r = await fetch('/api/primo_avvio/stato');
  var res = await r.json();
  if (!res.giacenza_iniziale_impostata) {
    id('primoAvvio').classList.add('attivo');
    id('appContainer').style.display = 'none';
  } else {
    id('primoAvvio').classList.remove('attivo');
    id('appContainer').style.display = 'block';
    caricaDati();
    if (!res.import_excel_fatto && (res.file_braccialetti_trovato || res.file_contatti_trovato)) {
      setTimeout(proponiImportExcel, 500);
    }
  }
}

async function proponiImportExcel() {
  var r = await fetch('/api/import/anteprima', {method:'POST'});
  var res = await r.json();
  if (!res.success) return;
  var a = res.anteprima;
  var msg = '📥 Ho trovato i seguenti file nella cartella:\n\n';
  if (a.braccialetti) {
    msg += '• ' + a.braccialetti.file + '\n  → ' + a.braccialetti.n_eventi + ' eventi storici, ' + a.braccialetti.n_scuole + ' luoghi\n\n';
  }
  if (a.contatti) {
    msg += '• ' + a.contatti.file + '\n  → ' + a.contatti.n_scuole + ' scuole, ' + a.contatti.n_contatti + ' contatti\n\n';
  }
  msg += 'Vuoi importarli adesso?';
  if (confirm(msg)) {
    var r2 = await fetch('/api/import/applica', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({eventi: true, contatti: true})
    });
    var res2 = await r2.json();
    if (res2.success) {
      var rp = res2.riepilogo;
      alert('✅ Import completato!\n\n' +
            'Scuole create: ' + rp.scuole_create + '\n' +
            'Eventi importati: ' + rp.eventi_importati + '\n' +
            'Contatti importati: ' + rp.contatti_importati);
      caricaDati();
    }
  }
}

// ============================================================
// CARICAMENTO DATI
// ============================================================
function _fetchJSON(url) {
  return fetch(url).then(r => r.json()).catch(() => null);
}

async function caricaDati() {
  var res = await Promise.all([
    _fetchJSON('/api/eventi'), _fetchJSON('/api/scuole'), _fetchJSON('/api/task'),
    _fetchJSON('/api/movimenti'), _fetchJSON('/api/note_calendario'), _fetchJSON('/api/inventario'),
    _fetchJSON('/api/portafoglio'), _fetchJSON('/api/rubrica'), _fetchJSON('/api/entita'),
    _fetchJSON('/api/postit'), _fetchJSON('/api/liste'), _fetchJSON('/api/categorie_entita'),
    _fetchJSON('/api/soglie'), _fetchJSON('/api/stato')
  ]);
  STATO.eventi = res[0]||[]; STATO.scuole = res[1]||[]; STATO.task = res[2]||[];
  STATO.movimenti = res[3]||STATO.movimenti; STATO.note_calendario = res[4]||[];
  STATO.inventario = res[5]||[]; STATO.portafoglio = res[6]||[]; STATO.rubrica = res[7]||[];
  STATO.entita = res[8]||[]; STATO.postit = res[9]||[]; STATO.liste = res[10]||[];
  STATO.categorie_entita = res[11]||[]; STATO.soglie_scorta = res[12]||{};
  if (res[13]) {
    STATO.giacenza_iniziale_impostata = res[13].giacenza_iniziale_impostata;
    STATO.import_excel_fatto = res[13].import_excel_fatto;
  }
  aggiornaTutto();
}

function calcolaStock(cat) {
  var c = 0, s = 0;
  var mov = (STATO.movimenti && STATO.movimenti[cat]) || [];
  mov.forEach(m => { if (m.tipo === 'carico') c += m.quantita || 0; else s += m.quantita || 0; });
  return c - s;
}

// ============================================================
// OROLOGIO
// ============================================================
function aggiornaOrologio() {
  var o = new Date();
  id('orologio').textContent = String(o.getHours()).padStart(2,'0')+':'+String(o.getMinutes()).padStart(2,'0')+':'+String(o.getSeconds()).padStart(2,'0');
  id('dataCompleta').textContent = GIORNI_NOMI[o.getDay()]+' '+String(o.getDate()).padStart(2,'0')+' '+MESI_NOMI[o.getMonth()]+' '+o.getFullYear();
}
setInterval(aggiornaOrologio, 1000);

function mostra(pagina) {
  document.querySelectorAll('.pagina').forEach(el => el.classList.remove('active'));
  var p = id('page-'+pagina);
  if (p) p.classList.add('active');
  if (pagina === 'lavagna') renderLavagna();
  if (pagina === 'liste') renderListe();
  if (pagina === 'materiali') renderMateriali();
  if (pagina === 'altro') renderAltro();
  if (pagina === 'comandi') renderComandi();
}

function aggiornaTutto() {
  var steps = [
    aggiornaDashboard, aggiornaEventi, renderScuole, renderRubrica,
    aggiornaTaskCompleti, aggiornaMagazzino, aggiornaArchivio,
    aggiornaInventario, renderMateriali, disegnaPortafoglio,
    function(){ caricaCalendario(annoCal, meseCal); },
    function(){ caricaCalendarioCompleto(calAnno, calMese); },
    renderWidgetScadenze, renderWidgetStock, renderAltro,
    renderLavagna, renderListe
  ];
  steps.forEach(function(fn){
    try { fn(); } catch(e) { console.warn('aggiornaTutto step fallito:', fn.name || 'anon', e); }
  });
}

// ============================================================
// DASHBOARD
// ============================================================
function aggiornaDashboard() {
  id('sEventi').textContent = STATO.eventi.length;
  id('sScuole').textContent = STATO.scuole.length;
  id('sAltro').textContent = STATO.eventi.filter(e => !e.scuola_id).length;
  id('sRubrica').textContent = STATO.rubrica.length;
  id('sBraccialetti').textContent = calcolaStock('braccialetti');
  id('sMedaglie').textContent = calcolaStock('medaglie');
  id('sAdesivi').textContent = calcolaStock('adesivi');
  id('sCoppe').textContent = calcolaStock('coppe');
  id('sTask').textContent = STATO.task.filter(t => t.stato === 'da_fare').length;
  id('sEntita').textContent = STATO.entita.length;
  aggiornaTaskLista();
  aggiornaEventiRecenti();
  renderAvvisiDashboard();
}

function renderAvvisiDashboard() {
  var c = id('avvisiDashboard');
  c.innerHTML = '';
  var incomplete = STATO.entita.filter(e => !e.costo_unitario || !e.data_carico);
  if (incomplete.length > 0) {
    c.innerHTML += '<div class="card" style="background:#fef3c7;color:#92400e;border-left:4px solid #f59e0b">'+
      '⚠️ Hai <strong>'+incomplete.length+'</strong> materiali da completare. <a onclick="mostra(\'materiali\')" style="cursor:pointer;text-decoration:underline">Vai a completarli →</a></div>';
  }
}

function aggiornaEventiRecenti() {
  var recenti = STATO.eventi.slice().sort((a,b) => (b.data||'').localeCompare(a.data||'')).slice(0,5);
  var tbody = id('eventiRecenti');
  tbody.innerHTML = '';
  if (recenti.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted)">Nessun evento</td></tr>';
    return;
  }
  recenti.forEach(e => {
    var s = STATO.scuole.find(x => x.id === e.scuola_id);
    tbody.innerHTML += '<tr class="riga-cliccabile" onclick="apriModaleEvento('+e.id+')">'+
      '<td>'+e.data+'</td><td><strong>'+(s ? s.nome : (e.luogo||'ALTRO'))+'</strong></td>'+
      '<td>'+(e.iniziativa||'')+_getBadgeMedia(e)+'</td><td>'+(e.numero_partecipanti||0)+'</td>'+
      '<td>'+(e.braccialetti||0)+'</td><td>'+(e.medaglie||0)+'</td>'+
      '<td>'+(e.adesivi||0)+'</td><td>'+(e.coppe||0)+'</td></tr>';
  });
}

// ============================================================
// CALENDARIO (semplificato: solo mese per dashboard)
// ============================================================
var calMiniVista = 'mese';
function popolaSaltoAnno(sid, anno) {
  var sel = id(sid); if (!sel) return;
  var o = '';
  for (var a = anno-5; a <= anno+5; a++) o += '<option value="'+a+'"'+(a===anno?' selected':'')+'>'+a+'</option>';
  sel.innerHTML = o;
}
function saltaAnnoCalMini() { annoCal = parseInt(id('saltoAnnoMini').value); caricaCalendario(annoCal, meseCal); }
function cambiaVistaCalMini(v) {
  calMiniVista = v;
  ['mese','settimana','anno'].forEach(x => {
    var b = id('btnVista'+x.charAt(0).toUpperCase()+x.slice(1));
    if (b) { b.classList.remove('btn-red'); b.classList.add('btn-gray'); }
  });
  var att = id('btnVista'+v.charAt(0).toUpperCase()+v.slice(1));
  if (att) { att.classList.remove('btn-gray'); att.classList.add('btn-red'); }
  id('calendario').style.display = v==='mese'?'grid':'none';
  id('vistaSettimanaContainer').style.display = v==='settimana'?'flex':'none';
  id('vistaAnnoContainer').style.display = v==='anno'?'block':'none';
  caricaCalendario(annoCal, meseCal);
}
function caricaCalendario(anno, mese) {
  popolaSaltoAnno('saltoAnnoMini', anno);
  id('meseTitolo').textContent = MESI_NOMI[mese-1]+' '+anno;
  if (calMiniVista === 'mese') disegnaCalMiniMese(anno, mese);
  else if (calMiniVista === 'settimana') disegnaCalMiniSettimana(anno, mese);
  else disegnaCalMiniAnno(anno);
}
function eventiDelGiorno(g,m,a) { return STATO.eventi.filter(e => { var d = new Date(e.data+'T00:00:00'); return d.getDate()===g && d.getMonth()+1===m && d.getFullYear()===a; }); }
function tasksDelGiorno(g,m,a) { return STATO.task.filter(t => { if (!t.data_scadenza) return false; var d = new Date(t.data_scadenza+'T00:00:00'); return d.getDate()===g && d.getMonth()+1===m && d.getFullYear()===a; }); }
function disegnaCalMiniMese(anno, mese) {
  var grid = id('calendario');
  grid.innerHTML = '';
  ['Lun','Mar','Mer','Gio','Ven','Sab','Dom'].forEach(function(g) {
    var d = document.createElement('div');
    d.className = 'head';
    d.textContent = g;
    grid.appendChild(d);
  });
  var firstDay = new Date(anno, mese-1, 1).getDay();
  var daysInMonth = new Date(anno, mese, 0).getDate();
  var oggi = new Date();
  var off = firstDay === 0 ? 6 : firstDay - 1;
  for (var i=0; i<off; i++) {
    var v = document.createElement('div');
    v.className = 'day empty';
    grid.appendChild(v);
  }
  for (var d=1; d<=daysInMonth; d++) {
    var div = document.createElement('div');
    div.className = 'day';
    if (d === oggi.getDate() && mese === oggi.getMonth()+1 && anno === oggi.getFullYear()) {
      div.classList.add('today');
    }
    var evs = eventiDelGiorno(d, mese, anno);
    var tks = tasksDelGiorno(d, mese, anno);
    var html = '<div class="num-giorno">'+d+'</div>';
    var chips = [];
    evs.forEach(function(e) {
      var s = STATO.scuole.find(function(x){ return x.id === e.scuola_id; });
      chips.push({ tipo: 'evento', testo: s ? s.nome : (e.luogo || 'ALTRO') });
    });
    tks.forEach(function(t) {
      chips.push({ tipo: 'task', testo: t.titolo });
    });
    chips.slice(0, 3).forEach(function(c) {
      html += '<div class="chip chip-'+c.tipo+'" title="'+c.testo.replace(/"/g,'&quot;')+'">'+c.testo+'</div>';
    });
    if (chips.length > 3) {
      html += '<div class="chip-piu">+'+(chips.length-3)+'</div>';
    }
    div.innerHTML = html;
    div.onclick = (function(gg){ return function(){ apriModaleGiorno(gg, anno, mese); }; })(d);
    grid.appendChild(div);
  }
}
function disegnaCalMiniSettimana(anno, mese) {
  var c = id('vistaSettimanaContainer'); c.className='cal-settimana'; c.innerHTML='';
  var oggi = new Date();
  var rif = new Date(anno, mese-1, Math.min(oggi.getDate(), new Date(anno,mese,0).getDate()));
  var gs = rif.getDay()===0?6:rif.getDay()-1;
  var lun = new Date(rif); lun.setDate(rif.getDate()-gs);
  for (var i=0;i<7;i++) {
    var gd = new Date(lun); gd.setDate(lun.getDate()+i);
    var g=gd.getDate(), m=gd.getMonth()+1, a=gd.getFullYear();
    var isOggi = g===oggi.getDate() && m===oggi.getMonth()+1 && a===oggi.getFullYear();
    var riga = document.createElement('div');
    riga.style.cssText = 'padding:10px;background:var(--bg);border-radius:8px;cursor:pointer;margin-bottom:6px;border:1px solid var(--border)'+(isOggi?';border-color:var(--primary)':'');
    riga.innerHTML = '<strong>'+GIORNI_NOMI[gd.getDay()]+' '+g+'/'+m+'</strong> — '+
      eventiDelGiorno(g,m,a).length+' eventi, '+tasksDelGiorno(g,m,a).length+' task';
    riga.onclick = (function(gg,mm,aa){ return function(){ apriModaleGiorno(gg,aa,mm); }; })(g,m,a);
    c.appendChild(riga);
  }
}
function disegnaCalMiniAnno(anno) {
  var c = id('vistaAnnoContainer'); c.innerHTML = '';
  c.style.display = 'grid'; c.style.gridTemplateColumns = 'repeat(auto-fill,minmax(150px,1fr))'; c.style.gap = '10px';
  for (var mese=1; mese<=12; mese++) {
    var box = document.createElement('div');
    box.style.cssText = 'background:var(--bg);border-radius:8px;padding:8px;cursor:pointer;border:1px solid var(--border)';
    box.innerHTML = '<div style="text-align:center;font-weight:700;color:var(--primary);margin-bottom:4px">'+MESI_BREVI[mese-1]+'</div>';
    box.onclick = (function(m){ return function(){ meseCal = m; caricaCalendario(annoCal, meseCal); cambiaVistaCalMini('mese'); }; })(mese);
    c.appendChild(box);
  }
}
function cambiaMese(d) { var m = meseCal+d, a=annoCal; if (m>12){m=1;a++;} else if (m<1){m=12;a--;} annoCal=a; meseCal=m; caricaCalendario(a,m); }
function vaiOggi() { var o = new Date(); annoCal=o.getFullYear(); meseCal=o.getMonth()+1; caricaCalendario(annoCal, meseCal); }
function caricaCalendarioCompleto(anno, mese) {
  id('calMeseTitolo').textContent = MESI_NOMI[mese-1] + ' ' + anno;
  var grid = id('calendarioCompleto');
  grid.innerHTML = '';
  ['Lun','Mar','Mer','Gio','Ven','Sab','Dom'].forEach(function(g) {
    var d = document.createElement('div');
    d.className = 'head';
    d.textContent = g;
    grid.appendChild(d);
  });
  var firstDay = new Date(anno, mese-1, 1).getDay();
  var daysInMonth = new Date(anno, mese, 0).getDate();
  var oggi = new Date();
  var off = firstDay === 0 ? 6 : firstDay - 1;
  for (var i=0; i<off; i++) {
    var v = document.createElement('div');
    v.className = 'day empty';
    grid.appendChild(v);
  }
  for (var d=1; d<=daysInMonth; d++) {
    var div = document.createElement('div');
    div.className = 'day';
    if (d === oggi.getDate() && mese === oggi.getMonth()+1 && anno === oggi.getFullYear()) {
      div.classList.add('today');
    }
    var evs = eventiDelGiorno(d, mese, anno);
    var tks = tasksDelGiorno(d, mese, anno);
    var html = '<div class="num-giorno">'+d+'</div>';
    var chips = [];
    evs.forEach(function(e) {
      var s = STATO.scuole.find(function(x){ return x.id === e.scuola_id; });
      chips.push({ tipo: 'evento', testo: s ? s.nome : (e.luogo || 'ALTRO') });
    });
    tks.forEach(function(t) {
      chips.push({ tipo: 'task', testo: t.titolo });
    });
    chips.slice(0, 3).forEach(function(c) {
      html += '<div class="chip chip-'+c.tipo+'" title="'+c.testo.replace(/"/g,'&quot;')+'">'+c.testo+'</div>';
    });
    if (chips.length > 3) {
      html += '<div class="chip-piu">+'+(chips.length-3)+' altro</div>';
    }
    div.innerHTML = html;
    div.onclick = (function(gg){ return function(){ apriModaleGiorno(gg, anno, mese); }; })(d);
    grid.appendChild(div);
  }
}
function cambiaMeseCal(d) { var m=calMese+d, a=calAnno; if (m>12){m=1;a++;} else if(m<1){m=12;a--;} calAnno=a; calMese=m; caricaCalendarioCompleto(a,m); }
function vaiOggiCal() { var o=new Date(); calAnno=o.getFullYear(); calMese=o.getMonth()+1; caricaCalendarioCompleto(calAnno, calMese); }
function apriModaleGiorno(g, anno, mese) {
  // Assicura che il modale esista (lo crea al volo se manca)
  var m = id('modaleGiorno');
  if (!m) {
    m = document.createElement('div');
    m.id = 'modaleGiorno';
    m.className = 'modale';
    m.innerHTML = '<div class="content wide" id="modaleGiornoContent"></div>';
    document.body.appendChild(m);
  }

  // Data completa formattata
  var d = new Date(anno, mese-1, g);
  var giorni = ['Domenica','Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato'];
  var mesi = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio',
              'Agosto','Settembre','Ottobre','Novembre','Dicembre'];
  var titolo = giorni[d.getDay()] + ' ' + g + ' ' + mesi[mese-1] + ' ' + anno;

  var dataISO = anno + '-' + String(mese).padStart(2,'0') + '-' + String(g).padStart(2,'0');

  // Raccogli elementi del giorno
  var evs = eventiDelGiorno(g, mese, anno);
  var tks = tasksDelGiorno(g, mese, anno);
  var nts = (STATO.note_calendario || []).filter(function(n) {
    return n.data === dataISO;
  });

  // Costruisci HTML
  var html = '';
  html += '<button class="modale-chiudi" onclick="chiudiModale(\'modaleGiorno\')">✕</button>';
  html += '<h2 style="margin:0 0 4px 0">📅 ' + titolo + '</h2>';
  html += '<div style="font-size:12px;color:var(--text-muted);margin-bottom:16px">';
  html += evs.length + ' eventi · ' + nts.length + ' note · ' + tks.length + ' promemoria';
  html += '</div>';

  // Barra azioni rapide
  html += '<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">';
  html += '<button class="btn btn-red" onclick="apriFormRapido(\'evento\', \'' + dataISO + '\')" style="flex:1;min-width:140px;padding:12px">📅 + Evento</button>';
  html += '<button class="btn btn-blue" onclick="apriFormRapido(\'nota\', \'' + dataISO + '\')" style="flex:1;min-width:140px;padding:12px">📝 + Nota</button>';
  html += '<button class="btn btn-green" onclick="apriFormRapido(\'task\', \'' + dataISO + '\')" style="flex:1;min-width:140px;padding:12px">✅ + Promemoria</button>';
  html += '</div>';

  // Contenitore form rapido (nascosto di default)
  html += '<div id="formRapidoContainer"></div>';

  // SEZIONE EVENTI
  html += '<h3 style="margin-top:18px;color:var(--primary)">📅 Eventi</h3>';
  if (evs.length === 0) {
    html += '<div style="padding:14px;text-align:center;color:var(--text-muted);background:var(--bg);border-radius:8px;font-size:13px">';
    html += 'Nessun evento. Clicca <strong>📅 + Evento</strong> sopra per crearne uno.';
    html += '</div>';
  } else {
    evs.forEach(function(e) {
      var sc = STATO.scuole.find(function(x){ return x.id === e.scuola_id; });
      var nomeScuola = sc ? sc.nome : (e.luogo || 'ALTRO');
      html += '<div style="padding:10px 12px;background:rgba(220,38,38,0.06);border-left:3px solid #DC2626;border-radius:6px;margin-bottom:6px;cursor:pointer;display:flex;justify-content:space-between;gap:8px" ';
      html += 'onclick="chiudiModale(\'modaleGiorno\');apriModaleEvento(' + e.id + ')">';
      html += '<div style="flex:1">';
      html += '<div style="font-weight:600">' + (e.iniziativa || '(senza titolo)') + '</div>';
      html += '<div style="font-size:12px;color:var(--text-muted);margin-top:2px">';
      html += '🏫 ' + nomeScuola;
      if (e.numero_partecipanti) html += ' · 👥 ' + e.numero_partecipanti;
      if (e.braccialetti) html += ' · 📦 ' + e.braccialetti;
      html += '</div></div>';
      html += '<div style="font-size:11px;color:var(--text-muted);align-self:center">modifica →</div>';
      html += '</div>';
    });
  }

  // SEZIONE NOTE
  html += '<h3 style="margin-top:18px;color:#F59E0B">📝 Note</h3>';
  if (nts.length === 0) {
    html += '<div style="padding:14px;text-align:center;color:var(--text-muted);background:var(--bg);border-radius:8px;font-size:13px">';
    html += 'Nessuna nota. Clicca <strong>📝 + Nota</strong> sopra per crearne una.';
    html += '</div>';
  } else {
    nts.forEach(function(n) {
      html += '<div style="padding:10px 12px;background:rgba(245,158,11,0.08);border-left:3px solid #F59E0B;border-radius:6px;margin-bottom:6px;cursor:pointer;display:flex;justify-content:space-between;gap:8px" ';
      html += 'onclick="modificaNotaCalendario(' + n.id + ')">';
      html += '<div style="flex:1;white-space:pre-wrap">' + escapeHtmlJS(n.testo || '') + '</div>';
      html += '<button onclick="event.stopPropagation();eliminaNotaCalendario(' + n.id + ')" style="background:none;border:none;color:#DC2626;cursor:pointer;align-self:flex-start">🗑️</button>';
      html += '</div>';
    });
  }

  // SEZIONE TASK
  html += '<h3 style="margin-top:18px;color:var(--accent)">✅ Promemoria</h3>';
  if (tks.length === 0) {
    html += '<div style="padding:14px;text-align:center;color:var(--text-muted);background:var(--bg);border-radius:8px;font-size:13px">';
    html += 'Nessun promemoria. Clicca <strong>✅ + Promemoria</strong> sopra per crearne uno.';
    html += '</div>';
  } else {
    tks.forEach(function(t) {
      var prioColor = t.priorita === 'alta' ? '#DC2626' : t.priorita === 'media' ? '#F59E0B' : '#10B981';
      var done = t.stato === 'completato';
      html += '<div style="padding:10px 12px;background:rgba(37,99,235,0.06);border-left:3px solid ' + prioColor + ';border-radius:6px;margin-bottom:6px;display:flex;justify-content:space-between;gap:8px' + (done ? ';opacity:0.55' : '') + '">';
      html += '<div style="flex:1;cursor:pointer" onclick="chiudiModale(\'modaleGiorno\');apriModaleTask(' + t.id + ')">';
      html += '<div style="font-weight:600' + (done ? ';text-decoration:line-through' : '') + '">' + escapeHtmlJS(t.titolo || '') + '</div>';
      if (t.note || t.descrizione) {
        html += '<div style="font-size:12px;color:var(--text-muted);margin-top:2px">' + escapeHtmlJS((t.note || t.descrizione || '').substring(0, 80)) + '</div>';
      }
      html += '</div>';
      html += '<div style="display:flex;gap:4px;align-self:flex-start">';
      if (!done) {
        html += '<button onclick="event.stopPropagation();completaTaskRapido(' + t.id + ')" title="Segna come fatto" style="background:none;border:none;cursor:pointer;font-size:14px">☑️</button>';
      }
      html += '<button onclick="event.stopPropagation();eliminaTaskRapido(' + t.id + ')" title="Elimina" style="background:none;border:none;color:#DC2626;cursor:pointer;font-size:14px">🗑️</button>';
      html += '</div></div>';
    });
  }

  id('modaleGiornoContent').innerHTML = html;
  apriModale('modaleGiorno');
}

// ---------- UTILITY ----------
function escapeHtmlJS(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ---------- FORM RAPIDI ----------
function apriFormRapido(tipo, dataISO) {
  var c = id('formRapidoContainer');
  if (!c) return;
  var html = '';

  if (tipo === 'evento') {
    var selScuole = '<option value="">— Nessuna (ALTRO) —</option>';
    STATO.scuole.forEach(function(s){
      selScuole += '<option value="' + s.id + '">' + escapeHtmlJS(s.nome) + '</option>';
    });
    html += '<div style="background:rgba(220,38,38,0.08);border-radius:10px;padding:16px;margin-bottom:14px;border:1px solid rgba(220,38,38,0.3)">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">';
    html += '<strong style="color:#DC2626">📅 Nuovo evento del ' + dataISO + '</strong>';
    html += '<button onclick="id(\'formRapidoContainer\').innerHTML=\'\'" style="background:none;border:none;cursor:pointer;font-size:18px">✕</button>';
    html += '</div>';
    html += '<label style="font-size:12px">Iniziativa *</label>';
    html += '<input id="frEvIniziativa" placeholder="Es. Corso sicurezza" style="margin-bottom:8px" autofocus>';
    html += '<label style="font-size:12px">Scuola</label>';
    html += '<select id="frEvScuola" style="margin-bottom:8px">' + selScuole + '</select>';
    html += '<label style="font-size:12px">Luogo (se non è una scuola)</label>';
    html += '<input id="frEvLuogo" placeholder="Es. Trattoria da Mario" style="margin-bottom:8px">';
    html += '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-bottom:10px">';
    html += '<div><label style="font-size:11px">Part.</label><input type="number" id="frEvPart" value="0" min="0"></div>';
    html += '<div><label style="font-size:11px">Bracc.</label><input type="number" id="frEvBracc" value="0" min="0"></div>';
    html += '<div><label style="font-size:11px">Med.</label><input type="number" id="frEvMed" value="0" min="0"></div>';
    html += '<div><label style="font-size:11px">Ades.</label><input type="number" id="frEvAdes" value="0" min="0"></div>';
    html += '<div><label style="font-size:11px">Coppe</label><input type="number" id="frEvCoppe" value="0" min="0"></div>';
    html += '</div>';
    html += '<div style="display:flex;gap:8px">';
    html += '<button class="btn btn-green" onclick="salvaEventoRapido(\'' + dataISO + '\')" style="flex:1">💾 Salva evento</button>';
    html += '<button class="btn btn-gray" onclick="id(\'formRapidoContainer\').innerHTML=\'\'" style="flex:1">Annulla</button>';
    html += '</div></div>';
  }

  else if (tipo === 'nota') {
    html += '<div style="background:rgba(245,158,11,0.08);border-radius:10px;padding:16px;margin-bottom:14px;border:1px solid rgba(245,158,11,0.3)">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">';
    html += '<strong style="color:#F59E0B">📝 Nuova nota del ' + dataISO + '</strong>';
    html += '<button onclick="id(\'formRapidoContainer\').innerHTML=\'\'" style="background:none;border:none;cursor:pointer;font-size:18px">✕</button>';
    html += '</div>';
    html += '<label style="font-size:12px">Testo *</label>';
    html += '<textarea id="frNotaTesto" rows="4" placeholder="Scrivi qui la tua nota..." style="margin-bottom:8px" autofocus></textarea>';
    html += '<label style="font-size:12px">Titolo (opzionale)</label>';
    html += '<input id="frNotaTitolo" placeholder="Es. Riunione, Chiamare Mario..." style="margin-bottom:10px">';
    html += '<div style="display:flex;gap:8px">';
    html += '<button class="btn btn-green" onclick="salvaNotaRapida(\'' + dataISO + '\')" style="flex:1">💾 Salva nota</button>';
    html += '<button class="btn btn-gray" onclick="id(\'formRapidoContainer\').innerHTML=\'\'" style="flex:1">Annulla</button>';
    html += '</div></div>';
  }

  else if (tipo === 'task') {
    html += '<div style="background:rgba(37,99,235,0.08);border-radius:10px;padding:16px;margin-bottom:14px;border:1px solid rgba(37,99,235,0.3)">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">';
    html += '<strong style="color:var(--accent)">✅ Nuovo promemoria del ' + dataISO + '</strong>';
    html += '<button onclick="id(\'formRapidoContainer\').innerHTML=\'\'" style="background:none;border:none;cursor:pointer;font-size:18px">✕</button>';
    html += '</div>';
    html += '<label style="font-size:12px">Cosa devi fare? *</label>';
    html += '<input id="frTaskTitolo" placeholder="Es. Chiamare la segreteria" style="margin-bottom:8px" autofocus>';
    html += '<label style="font-size:12px">Priorità</label>';
    html += '<select id="frTaskPriorita" style="margin-bottom:8px">';
    html += '<option value="alta">🔴 Alta</option>';
    html += '<option value="media" selected>🟡 Media</option>';
    html += '<option value="bassa">🟢 Bassa</option>';
    html += '</select>';
    html += '<label style="font-size:12px">Note (opzionale)</label>';
    html += '<textarea id="frTaskNote" rows="2" style="margin-bottom:10px"></textarea>';
    html += '<div style="display:flex;gap:8px">';
    html += '<button class="btn btn-green" onclick="salvaTaskRapido(\'' + dataISO + '\')" style="flex:1">💾 Salva promemoria</button>';
    html += '<button class="btn btn-gray" onclick="id(\'formRapidoContainer\').innerHTML=\'\'" style="flex:1">Annulla</button>';
    html += '</div></div>';
  }

  c.innerHTML = html;
}

async function salvaEventoRapido(dataISO) {
  var iniziativa = (id('frEvIniziativa').value || '').trim();
  if (!iniziativa) { alert('Inserisci l\'iniziativa'); return; }
  var scuolaId = id('frEvScuola').value ? parseInt(id('frEvScuola').value) : null;
  var corpo = {
    data: dataISO,
    scuola_id: scuolaId,
    iniziativa: iniziativa,
    luogo: (id('frEvLuogo').value || '').trim(),
    numero_partecipanti: parseInt(id('frEvPart').value || 0),
    braccialetti: parseInt(id('frEvBracc').value || 0),
    medaglie: parseInt(id('frEvMed').value || 0),
    adesivi: parseInt(id('frEvAdes').value || 0),
    coppe: parseInt(id('frEvCoppe').value || 0),
    referente: '', nota_carico: '', note: '',
    fonte: 'calendario_rapido'
  };
  var r = await fetch('/api/eventi', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(corpo)
  });
  var res = await r.json();
  if (res.success) {
    // Ricarica lo stato e ridisegna il modale giorno
    await ricaricaStato();
    // Ricostruisci modale giorno sulla stessa data
    var parti = dataISO.split('-');
    apriModaleGiorno(parseInt(parti[2]), parseInt(parti[0]), parseInt(parti[1]));
  } else {
    alert('Errore: ' + (res.error || '?'));
  }
}

async function salvaNotaRapida(dataISO) {
  var testo = (id('frNotaTesto').value || '').trim();
  if (!testo) { alert('Scrivi qualcosa'); return; }
  var titolo = (id('frNotaTitolo').value || '').trim();
  var corpo = { data: dataISO, testo: testo, titolo: titolo, colore: 'giallo' };
  var r = await fetch('/api/note_calendario', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(corpo)
  });
  var res = await r.json();
  if (res.success) {
    await ricaricaStato();
    var parti = dataISO.split('-');
    apriModaleGiorno(parseInt(parti[2]), parseInt(parti[0]), parseInt(parti[1]));
  } else {
    alert('Errore: ' + (res.error || '?'));
  }
}

async function salvaTaskRapido(dataISO) {
  var titolo = (id('frTaskTitolo').value || '').trim();
  if (!titolo) { alert('Scrivi cosa devi fare'); return; }
  var corpo = {
    titolo: titolo,
    data_scadenza: dataISO,
    priorita: id('frTaskPriorita').value,
    stato: 'da_fare',
    note: (id('frTaskNote').value || ''),
    descrizione: (id('frTaskNote').value || ''),
    categoria: 'generale',
    fonte: 'calendario_rapido'
  };
  var r = await fetch('/api/task', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(corpo)
  });
  var res = await r.json();
  if (res.success) {
    await ricaricaStato();
    var parti = dataISO.split('-');
    apriModaleGiorno(parseInt(parti[2]), parseInt(parti[0]), parseInt(parti[1]));
  } else {
    alert('Errore: ' + (res.error || '?'));
  }
}

// ---------- AZIONI RAPIDE DAL MODALE GIORNO ----------
async function completaTaskRapido(tid) {
  var t = STATO.task.find(function(x){ return x.id === tid; });
  if (!t) return;
  t.stato = 'completato';
  await fetch('/api/task', {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(t)
  });
  await ricaricaStato();
  // Riprendi la data corrente dal titolo
  apriModaleGiornoDaTitolo();
}

async function eliminaTaskRapido(tid) {
  if (!confirm('Eliminare questo promemoria?')) return;
  await fetch('/api/task?id=' + tid, {method: 'DELETE'});
  await ricaricaStato();
  apriModaleGiornoDaTitolo();
}

async function eliminaNotaCalendario(nid) {
  if (!confirm('Eliminare questa nota?')) return;
  await fetch('/api/note_calendario?id=' + nid, {method: 'DELETE'});
  await ricaricaStato();
  apriModaleGiornoDaTitolo();
}

function modificaNotaCalendario(nid) {
  var n = (STATO.note_calendario || []).find(function(x){ return x.id === nid; });
  if (!n) return;
  var nuovo = prompt('Modifica nota:', n.testo || '');
  if (nuovo === null || nuovo === n.testo) return;
  n.testo = nuovo;
  fetch('/api/note_calendario', {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(n)
  }).then(function(){ ricaricaStato().then(apriModaleGiornoDaTitolo); });
}

// Utilità: recupera la data corrente dal titolo del modale giorno e ricarica
function apriModaleGiornoDaTitolo() {
  var h = document.querySelector('#modaleGiorno h2');
  if (!h) return;
  // Prova a estrarre "15 Ottobre 2026" dal titolo
  var txt = h.textContent || '';
  var m = txt.match(/(\d{1,2})\s+(\w+)\s+(\d{4})/);
  if (!m) return;
  var mesi = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio',
              'Agosto','Settembre','Ottobre','Novembre','Dicembre'];
  var g = parseInt(m[1]);
  var meseIdx = mesi.indexOf(m[2]);
  var a = parseInt(m[3]);
  if (meseIdx < 0) return;
  apriModaleGiorno(g, a, meseIdx + 1);
}

// ---------- RICARICA STATO LEGGERO ----------
async function ricaricaStato() {
  var res = await Promise.all([
    _fetchJSON('/api/eventi'),
    _fetchJSON('/api/task'),
    _fetchJSON('/api/note_calendario')
  ]);
  STATO.eventi = res[0] || [];
  STATO.task = res[1] || [];
  STATO.note_calendario = res[2] || [];

  // Ridisegna calendari
  try { caricaCalendario(annoCal, meseCal); } catch(e) {}
  try { caricaCalendarioCompleto(calAnno, calMese); } catch(e) {}
  try { aggiornaDashboard(); } catch(e) {}
  try { renderWidgetScadenze(); } catch(e) {}
}


// ============================================================
// EVENTI
// ============================================================

function _calcolaMargineEvento(e) {
  function tot(voci) {
    if (!Array.isArray(voci)) return 0;
    var t = 0;
    voci.forEach(function(v) {
      t += (parseFloat(v.quantita) || 0) * (parseFloat(v.prezzo_unitario) || 0);
    });
    return t;
  }
  var costi = tot(e.voci_costi);
  var ricavi = tot(e.voci_ricavi);
  return ricavi - costi;
}

function aggiornaEventi() {
  var search = (id('cercaEventi')?.value||'').toLowerCase();
  var tipo = id('filtroTipoEvento')?.value || '';
  var filtroMedia = id('filtroMediaEventi')?.value || '';
  var sid = id('filtroScuola')?.value;
  var anno = id('filtroAnno')?.value;
  var f = STATO.eventi.slice();
  if (search) f = f.filter(e => (e.iniziativa||'').toLowerCase().includes(search) || (e.luogo||'').toLowerCase().includes(search));
  if (tipo === 'con') f = f.filter(e => e.scuola_id);
    if (filtroMedia === 'con_media') f = f.filter(function(e) { return _contaMediaEvento(e).haMedia; });
    if (filtroMedia === 'senza_media') f = f.filter(function(e) { return !_contaMediaEvento(e).haMedia; });
  if (tipo === 'altro') f = f.filter(e => !e.scuola_id);
  if (sid) f = f.filter(e => e.scuola_id == sid);
  if (anno) f = f.filter(e => (e.data||'').startsWith(anno));
  f.sort((a,b) => (b.data||'').localeCompare(a.data||''));
  id('conteggioEventi').textContent = f.length;
  var tbody = id('listaEventi'); tbody.innerHTML = '';
  if (f.length === 0) tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:var(--text-muted)">Nessun evento</td></tr>';
  else f.forEach(e => {
    var s = STATO.scuole.find(x => x.id === e.scuola_id);
    tbody.innerHTML += '<tr class="riga-cliccabile" onclick="apriModaleEvento('+e.id+')">'+
      '<td>'+e.data+'</td><td><strong>'+(s?s.nome:(e.luogo||'<em>ALTRO</em>'))+'</strong></td>'+
      '<td>'+(e.iniziativa||'')+_getBadgeMedia(e)+'</td><td>'+(e.numero_partecipanti||0)+'</td>'+
      '<td>'+(e.braccialetti||0)+'</td><td>'+(e.medaglie||0)+'</td>'+
      '<td>'+(e.adesivi||0)+'</td><td>'+(e.coppe||0)+'</td>'+
      (function(){ var m = _calcolaMargineEvento(e); if (m === 0 && !(e.voci_costi && e.voci_costi.length) && !(e.voci_ricavi && e.voci_ricavi.length)) { return '<td style="color:var(--text-muted);text-align:right">—</td>'; } var col = m >= 0 ? '#16A34A' : '#DC2626'; var segno = m >= 0 ? '+' : ''; return '<td style="color:'+col+';font-weight:700;text-align:right">'+segno+m.toFixed(2).replace('.',',')+' €</td>'; })()+
      '<td><button onclick="event.stopPropagation();eliminaEvento('+e.id+')" style="background:none;border:none;color:#DC2626;cursor:pointer">🗑️</button></td></tr>';
  });
  var selS = id('filtroScuola');
  if (selS) {
    selS.innerHTML = '<option value="">Tutte le scuole</option>';
    STATO.scuole.forEach(s => selS.innerHTML += '<option value="'+s.id+'">'+s.nome+'</option>');
    selS.value = sid;
  }
  var selA = id('filtroAnno');
  if (selA) {
    var anni = [];
    STATO.eventi.forEach(e => { var a = (e.data||'').split('-')[0]; if (a && anni.indexOf(a)===-1) anni.push(a); });
    anni.sort();
    selA.innerHTML = '<option value="">Anno</option>';
    anni.forEach(a => selA.innerHTML += '<option value="'+a+'">'+a+'</option>');
    selA.value = anno;
  }
}
function filtraEventi() { aggiornaEventi(); }
function eliminaEvento(eid) { if (confirm('Eliminare questo evento?')) fetch('/api/eventi?id='+eid, {method:'DELETE'}).then(caricaDati); }
function renderAltro() {
  var f = STATO.eventi.filter(e => !e.scuola_id).sort((a,b) => (b.data||'').localeCompare(a.data||''));
  var tbody = id('altroBody'); if (!tbody) return;
  tbody.innerHTML = '';
  if (f.length === 0) tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--text-muted)">Nessun evento in ALTRO</td></tr>';
  else f.forEach(e => {
    tbody.innerHTML += '<tr class="riga-cliccabile" onclick="apriModaleEvento('+e.id+')">'+
      '<td>'+e.data+'</td><td>'+(e.luogo||'')+'</td><td>'+(e.iniziativa||'')+'</td>'+
      '<td>'+(e.numero_partecipanti||0)+'</td><td>'+(e.braccialetti||0)+'</td>'+
      '<td>'+(e.medaglie||0)+'</td><td>'+(e.adesivi||0)+'</td><td>'+(e.coppe||0)+'</td>'+
      '<td><button onclick="event.stopPropagation();eliminaEvento('+e.id+')" style="background:none;border:none;color:#DC2626;cursor:pointer">🗑️</button></td></tr>';
  });
}

// ============================================================
// MODALE EVENTO
// ============================================================
function apriModaleEvento(eid) {
  apriModale('modaleEvento');
  var sel = id('eScuola');
  sel.innerHTML = '<option value="">— Nessuna (ALTRO) —</option>';
  STATO.scuole.forEach(s => sel.innerHTML += '<option value="'+s.id+'">'+s.nome+'</option>');
  sel.onchange = function() {
    if (!sel.value) {
      if ((id('eLuogo').value || '').trim().toLowerCase() === 'altro') id('eLuogo').value = '';
      return;
    }
    var sc = STATO.scuole.find(x => String(x.id) === String(sel.value));
    if (!sc) return;
    if (!id('eReferente').value && sc.referente) id('eReferente').value = sc.referente;
    if (id('eReferenteTel') && !id('eReferenteTel').value && sc.telefono) id('eReferenteTel').value = sc.telefono;
    if (id('eReferenteEmail') && !id('eReferenteEmail').value && sc.email) id('eReferenteEmail').value = sc.email;
  };
  if (eid) {
    var e = STATO.eventi.find(x => x.id === eid);
    if (!e) return;
    id('modaleEventoTitolo').textContent = '📝 Modifica Evento';
    id('eId').value = e.id;
    id('eData').value = e.data || '';
    sel.value = e.scuola_id || '';
    id('eIniziativa').value = e.iniziativa || '';
    id('eLuogo').value = e.luogo || '';
    id('ePartecipanti').value = e.numero_partecipanti || 0;
    id('eBraccialetti').value = e.braccialetti || 0;
    id('eMedaglie').value = e.medaglie || 0;
    id('eAdesivi').value = e.adesivi || 0;
    id('eCoppe').value = e.coppe || 0;
    id('eReferente').value = e.referente || '';
    id('eReferenteTel').value = e.referente_telefono || '';
    id('eReferenteEmail').value = e.referente_email || '';
    id('eNotaCarico').value = e.nota_carico || '';
    id('eNote').value = e.note || '';
    renderFotoEvento(e.foto || [], e.id);
    id('eDurata').value = e.durata_giorni || 1;
    id('eDataFine').value = e.data_fine || e.data || '';
    _vociCostiEvento = Array.isArray(e.voci_costi) ? JSON.parse(JSON.stringify(e.voci_costi)) : [];
    _vociRicaviEvento = Array.isArray(e.voci_ricavi) ? JSON.parse(JSON.stringify(e.voci_ricavi)) : [];
    renderListaVociEvento('costi');
    renderListaVociEvento('ricavi');
    id('btnEliminaEventoModale').style.display = 'block';
  } else {
    id('modaleEventoTitolo').textContent = '📝 Nuovo Evento';
    id('eId').value = '';
    id('eData').value = new Date().toISOString().split('T')[0];
    id('eDurata').value = 1;
    id('eDataFine').value = id('eData').value;
    sel.value = '';
    ['eIniziativa','eLuogo','eReferente','eNotaCarico','eNote'].forEach(x => id(x).value = '');
    ['eReferenteTel','eReferenteEmail'].forEach(x => id(x).value = '');
    ['ePartecipanti','eBraccialetti','eMedaglie','eAdesivi','eCoppe'].forEach(x => id(x).value = 0);
    _vociCostiEvento = [];
    _vociRicaviEvento = [];
    renderListaVociEvento('costi');
    renderListaVociEvento('ricavi');
    id('btnEliminaEventoModale').style.display = 'none';
    var listaFoto = document.getElementById('listaFotoEvento');
    if (listaFoto) listaFoto.innerHTML = '';
  }
}
async function salvaEvento() {
  var data = id('eData').value;
  if (!data) { alert('Inserisci la data'); return; }
  var eid = id('eId').value ? parseInt(id('eId').value) : null;
  var durata = parseInt(id('eDurata').value) || 1;
  var dataFine = id('eDataFine').value || data;
  var corpo = {
    data: data,
    data_fine: dataFine,
    durata_giorni: durata,
    scuola_id: id('eScuola').value ? parseInt(id('eScuola').value) : null,
    iniziativa: (id('eIniziativa').value || '').trim(),
    luogo: (id('eLuogo').value || '').trim(),
    numero_partecipanti: parseInt(id('ePartecipanti').value || 0),
    braccialetti: parseInt(id('eBraccialetti').value || 0),
    medaglie: parseInt(id('eMedaglie').value || 0),
    adesivi: parseInt(id('eAdesivi').value || 0),
    coppe: parseInt(id('eCoppe').value || 0),
    referente: (id('eReferente').value || '').trim(),
    referente_telefono: (id('eReferenteTel')?.value || '').trim(),
    referente_email: (id('eReferenteEmail')?.value || '').trim(),
    nota_carico: (id('eNotaCarico').value || '').trim(),
    note: (id('eNote').value || '').trim(),
    voci_costi: _vociCostiEvento,
    voci_ricavi: _vociRicaviEvento
  };
  if (!corpo.iniziativa) { alert('Inserisci l\'iniziativa'); return; }
  if (eid) corpo.id = eid;
  await fetch('/api/eventi', { method: eid ? 'PUT' : 'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify(corpo) });
  chiudiModale('modaleEvento');
  caricaDati();
}
function eliminaEventoDaModale() {
  var eid = id('eId').value; if (!eid) return;
  if (confirm('Eliminare?')) fetch('/api/eventi?id='+eid, {method:'DELETE'}).then(function(){ chiudiModale('modaleEvento'); caricaDati(); });
}

// ============================================================
// SCUOLE
// ============================================================
function renderScuole() {
  var search = (id('cercaScuole')?.value||'').toLowerCase();
  var f = STATO.scuole.slice();
  if (search) f = f.filter(s => (s.nome||'').toLowerCase().includes(search) || (s.referente||'').toLowerCase().includes(search));
  var g = id('grigliaScuole'); g.innerHTML = '';
  if (f.length === 0) { g.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:30px">Nessuna scuola</div>'; return; }
  f.forEach(s => {
    var ne = STATO.eventi.filter(e => e.scuola_id != null && String(e.scuola_id) === String(s.id)).length;
    var d = document.createElement('div');
    d.className = 'card'; d.style.cursor='pointer';
    d.innerHTML = '<h3 style="margin:0;color:var(--accent)">'+s.nome+'</h3>'+
      (s.tipo ? '<span class="badge badge-blue" style="font-size:11px">'+s.tipo+'</span>' : '')+
      (s.referente?'<div style="font-size:14px;margin-top:6px">👤 '+s.referente+'</div>':'')+
      (s.telefono?'<div style="font-size:13px;color:var(--text-muted)">📞 '+s.telefono+'</div>':'')+
      (s.email?'<div style="font-size:13px;color:var(--text-muted)">✉️ '+s.email+'</div>':'')+
      '<div style="margin-top:8px"><span class="badge badge-blue">📅 '+ne+' eventi</span></div>';
    d.onclick = (function(sid){ return function(){ apriModaleScuola(sid); }; })(s.id);
    g.appendChild(d);
  });
}
function apriModaleScuola(sid) {
  apriModale('modaleScuola');
  if (sid) {
    var s = STATO.scuole.find(function(x) { return String(x.id) === String(sid); });
    if (!s) {
      console.warn('Scuola non trovata per id', sid);
      alert('Errore: scuola non trovata');
      return;
    }
    id('modaleScuolaTitolo').textContent = '🏫 '+s.nome;
    id('scuolaId').value = s.id;
    id('scuolaNome').value = s.nome || '';
    id('scuolaTipo').value = s.tipo || '';
    id('scuolaRef').value = s.referente || '';
    id('scuolaTel').value = s.telefono || '';
    id('scuolaEmail').value = s.email || '';
    id('btnEliminaScuolaModale').style.display = 'block';
    var noteEl = document.getElementById('scuolaNote'); if (noteEl) noteEl.value = s.note || '';
    var det = document.getElementById('scuolaDettaglioEventi');
    var listaEv = document.getElementById('scuolaEventiLista');
    if (det && listaEv) {
      var evCol = (STATO.eventi || []).filter(function(ev) {
        return ev.scuola_id != null && String(ev.scuola_id) === String(s.id);
      }).sort(function(a, b) { return (b.data || '').localeCompare(a.data || ''); });
      det.style.display = 'block';
      if (evCol.length === 0) {
        listaEv.innerHTML = '<div style="font-size:12px;color:#78909C">Nessun evento collegato a questa scuola.</div>';
      } else {
        listaEv.innerHTML = evCol.map(function(ev) {
          return '<div onclick="chiudiModale(\'modaleScuola\');apriModaleEvento(' + ev.id + ')" style="padding:6px 8px;margin-bottom:4px;background:#fff;border-radius:6px;border:1px solid #e0e7ef;cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-size:12px">' +
            '<span><strong>' + (ev.data || '') + '</strong> — ' + (ev.iniziativa || 'Evento') + (ev.luogo ? ' (' + ev.luogo + ')' : '') + '</span>' +
            '<span style="color:#0288D1;font-weight:700">Apri →</span></div>';
        }).join('');
      }
    }
  } else {
    id('modaleScuolaTitolo').textContent = '🏫 Nuova Scuola';
    id('scuolaId').value = '';
    ['scuolaNome','scuolaTipo','scuolaRef','scuolaTel','scuolaEmail'].forEach(x => id(x).value = '');
    id('btnEliminaScuolaModale').style.display = 'none';
  }
}
async function salvaScuola() {
  var nome = (id('scuolaNome').value||'').trim();
  if (!nome) { alert('Inserisci il nome'); return; }
  var sid = id('scuolaId').value;
  var corpo = {
    nome: nome,
    tipo: id('scuolaTipo').value,
    referente: id('scuolaRef').value,
    telefono: id('scuolaTel').value,
    email: id('scuolaEmail').value,
    note: (document.getElementById('scuolaNote') ? document.getElementById('scuolaNote').value : '')
  };
  if (sid) corpo.id = parseInt(sid);
  await fetch('/api/scuole', { method: sid?'PUT':'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(corpo) });
  chiudiModale('modaleScuola'); caricaDati();
}
function eliminaScuolaDaModale() {
  var sid = id('scuolaId').value; if (!sid) return;
  if (confirm('Eliminare? Gli eventi passeranno in ALTRO.')) fetch('/api/scuole?id='+sid, {method:'DELETE'}).then(function(){ chiudiModale('modaleScuola'); caricaDati(); });
}

// ============================================================
// TASK
// ============================================================
function apriModaleTask(tid) {
  apriModale('modaleTask');
  if (tid) {
    var t = STATO.task.find(x => x.id === tid); if (!t) return;
    id('modaleTaskTitolo').textContent = '✅ Modifica Task';
    id('taskId').value = t.id;
    id('taskTitolo').value = t.titolo || '';
    id('taskCategoria').value = t.categoria || 'generale';
    id('taskScadenza').value = t.data_scadenza || '';
    id('taskPriorita').value = t.priorita || 'media';
    id('taskStato').value = t.stato || 'da_fare';
    id('taskNote').value = t.note || t.descrizione || '';
    id('taskReferente').value = t.referente || '';
    id('btnEliminaTaskModale').style.display = 'block';
  } else {
    id('modaleTaskTitolo').textContent = '✅ Nuovo Task';
    id('taskId').value = '';
    id('taskTitolo').value = '';
    id('taskCategoria').value = 'generale';
    id('taskScadenza').value = '';
    id('taskPriorita').value = 'media';
    id('taskStato').value = 'da_fare';
    id('taskNote').value = '';
    id('taskReferente').value = '';
    id('btnEliminaTaskModale').style.display = 'none';
  }
}
async function salvaTask() {
  var titolo = (id('taskTitolo').value||'').trim(); if (!titolo) { alert('Titolo obbligatorio'); return; }
  var tid = id('taskId').value ? parseInt(id('taskId').value) : null;
  var corpo = { titolo: titolo, categoria: id('taskCategoria').value, data_scadenza: id('taskScadenza').value||'', priorita: id('taskPriorita').value, stato: id('taskStato').value, note: id('taskNote').value, descrizione: id('taskNote').value, referente: id('taskReferente').value };
  if (tid) corpo.id = tid;
  await fetch('/api/task', { method: tid?'PUT':'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(corpo) });
  chiudiModale('modaleTask'); caricaDati();
}
function eliminaTaskDaModale() {
  var tid = id('taskId').value; if (!tid) return;
  if (confirm('Eliminare?')) fetch('/api/task?id='+tid, {method:'DELETE'}).then(function(){ chiudiModale('modaleTask'); caricaDati(); });
}
function completaTask(tid) { var t = STATO.task.find(x=>x.id===tid); if (t) { t.stato='completato'; fetch('/api/task', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(t)}).then(caricaDati); } }
function eliminaTask(tid) { if (confirm('Eliminare?')) fetch('/api/task?id='+tid, {method:'DELETE'}).then(caricaDati); }
function renderTaskItemHTML(t) {
  var p = t.priorita === 'alta' ? '#DC2626' : t.priorita === 'media' ? '#F59E0B' : '#10B981';
  return '<div style="border-left:4px solid '+p+';padding:8px 12px;background:var(--bg);border-radius:0 8px 8px 0;margin-bottom:6px;display:flex;justify-content:space-between;gap:8px">'+
    '<div style="flex:1;cursor:pointer" onclick="apriModaleTask('+t.id+')">'+
    '<div style="font-weight:600">'+(t.titolo||'')+'</div>'+
    '<div style="font-size:12px;color:var(--text-muted);margin-top:3px">'+(t.data_scadenza?'📅 '+t.data_scadenza+' • ':'')+t.stato+'</div></div>'+
    '<button onclick="event.stopPropagation();eliminaTask('+t.id+')" style="background:none;border:none;color:#DC2626;cursor:pointer">🗑️</button></div>';
}
function aggiornaTaskLista() {
  var oggi = new Date(); var sette = new Date(); sette.setDate(sette.getDate()+7);
  var os = oggi.toISOString().split('T')[0], ss = sette.toISOString().split('T')[0];
  var ts = STATO.task.filter(t => t.stato!=='completato' && t.data_scadenza && t.data_scadenza>=os && t.data_scadenza<=ss).sort((a,b)=>a.data_scadenza.localeCompare(b.data_scadenza));
  var c = id('taskLista'); c.innerHTML = '';
  if (ts.length === 0) c.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px">🎉 Nessun task in scadenza</div>';
  else ts.forEach(t => c.innerHTML += renderTaskItemHTML(t));
}
function aggiornaTaskCompleti() {
  var c = id('taskCompleti'); if (!c) return;
  c.innerHTML = '';
  if (STATO.task.length === 0) c.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px">🎉 Nessun task</div>';
  else STATO.task.forEach(t => c.innerHTML += renderTaskItemHTML(t));
}

// ============================================================
// MAGAZZINO
// ============================================================
async function aggiornaMagazzino() {
  id('stockBracc').textContent = calcolaStock('braccialetti');
  id('stockMed').textContent = calcolaStock('medaglie');
  id('stockAdesivi').textContent = calcolaStock('adesivi');
  id('stockCoppe').textContent = calcolaStock('coppe');

  var tbody = id('movimentiLista');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:var(--text-muted)">Caricamento...</td></tr>';

  try {
    var r = await fetch('/api/movimenti/storico');
    var storico = await r.json();
    var all = [];
    ['braccialetti', 'medaglie', 'adesivi', 'coppe'].forEach(function(cat) {
      (storico[cat] || []).forEach(function(m) { all.push(Object.assign({}, m, { categoria: cat })); });
    });
    all.sort(function(a, b) { return (b.data || '').localeCompare(a.data || ''); });

    if (all.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:var(--text-muted)">Nessun movimento</td></tr>';
      return;
    }

    var html = '';
    all.forEach(function(m) {
      var col = m.tipo === 'carico' ? '#16A34A' : '#DC2626';
      var costoUnit = (m.prezzo_unitario && m.prezzo_unitario > 0) ? 'EUR ' + parseFloat(m.prezzo_unitario).toFixed(2).replace('.', ',') : '—';
      var progressivo = (m.progressivo !== undefined && m.progressivo !== null) ? m.progressivo : '—';
      html += '<tr>' +
        '<td>' + (m.data || '') + '</td>' +
        '<td style="color:' + col + ';font-weight:600">' + (m.tipo || '') + '</td>' +
        '<td>' + (m.categoria || '') + '</td>' +
        '<td style="color:' + col + '">' + (m.quantita || 0) + '</td>' +
        '<td>' + costoUnit + '</td>' +
        '<td style="font-weight:700">' + progressivo + '</td>' +
        '<td style="font-size:12px">' + (m.motivo || '—') + '</td>' + '<td style="font-size:12px">' + ([m.nota_carico, m.destinatario, m.evento_id ? _nomeEvento(m.evento_id) : (m.scuola_id ? _nomeScuola(m.scuola_id) : '')].filter(Boolean).join(' • ') || '—') + '</td>' +
        '<td>' +
          '<button onclick="modificaMovimento(' + m.id + ', &quot;' + m.categoria + '&quot;)" style="background:none;border:none;cursor:pointer" title="Modifica">&#9998;</button> ' +
          '<button onclick="eliminaMovimento(' + m.id + ', &quot;' + m.categoria + '&quot;)" style="background:none;border:none;cursor:pointer;color:#DC2626" title="Elimina">&#128465;</button>' +
        '</td>' +
      '</tr>';
    });
    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:#DC2626">Errore: ' + e.message + '</td></tr>';
  }
}
// ============================================================
// CARICO MAGAZZINO - con costo unitario
// ============================================================

function _parseFloatIt(v) {
  if (!v) return 0;
  return parseFloat(String(v).replace(',', '.')) || 0;
}

function aggiornaTotaleCarico() {
  var cats = ['Bracc', 'Med', 'Adesivi', 'Coppe'];
  var totale = 0;
  cats.forEach(function(c) {
    var q = _parseFloatIt(id('carico' + c) ? id('carico' + c).value : 0);
    var costo = _parseFloatIt(id('carico' + c + 'Costo') ? id('carico' + c + 'Costo').value : 0);
    totale += q * costo;
  });
  var el = id('caricoTotale');
  if (el) {
    el.textContent = totale.toFixed(2).replace('.', ',') + ' €';
    el.style.color = totale > 0 ? '#16A34A' : '#90A4AE';
  }
}

async function aggiungiCarico() {
  var br = parseInt(id('caricoBracc').value) || 0;
  var me = parseInt(id('caricoMed').value) || 0;
  var ad = parseInt(id('caricoAdesivi').value) || 0;
  var co = parseInt(id('caricoCoppe').value) || 0;

  var brCosto = _parseFloatIt(id('caricoBraccCosto') ? id('caricoBraccCosto').value : 0);
  var meCosto = _parseFloatIt(id('caricoMedCosto') ? id('caricoMedCosto').value : 0);
  var adCosto = _parseFloatIt(id('caricoAdesiviCosto') ? id('caricoAdesiviCosto').value : 0);
  var coCosto = _parseFloatIt(id('caricoCoppeCosto') ? id('caricoCoppeCosto').value : 0);

  var data = id('caricoData').value || new Date().toISOString().split('T')[0];
  var motivo = id('caricoMotivo').value || 'Carico manuale';
  var nota = id('caricoNota').value || '';

  var daCaricare = [
    ['braccialetti', br, brCosto],
    ['medaglie', me, meCosto],
    ['adesivi', ad, adCosto],
    ['coppe', co, coCosto]
  ].filter(function(x) { return x[1] > 0; });

  if (daCaricare.length === 0) {
    alert('Inserisci almeno una quantità');
    return;
  }

  // Validazione: se c'e' quantita' ma manca costo, chiedi conferma
  var mancanti = daCaricare.filter(function(x) { return x[2] <= 0; });
  if (mancanti.length > 0) {
    var nomi = mancanti.map(function(x) { return x[0]; }).join(', ');
    if (!confirm('⚠️ Stai caricando senza costo unitario: ' + nomi + '\n\nIl bilancio magazzino non sarà preciso.\n\nContinuare comunque?')) {
      return;
    }
  }

  var reqs = daCaricare.map(function(x) {
    return fetch('/api/movimenti', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        categoria: x[0],
        tipo: 'carico',
        quantita: x[1],
        prezzo_unitario: x[2],
        motivo: motivo,
        nota_carico: nota,
        data: data
      })
    });
  });

  await Promise.all(reqs);

  ['caricoBracc', 'caricoMed', 'caricoAdesivi', 'caricoCoppe',
   'caricoBraccCosto', 'caricoMedCosto', 'caricoAdesiviCosto', 'caricoCoppeCosto',
   'caricoMotivo', 'caricoNota']
    .forEach(function(x) { var el = id(x); if (el) el.value = ''; });

  aggiornaTotaleCarico();
  caricaDati();
}
// ============================================================
// INVENTARIO
// ============================================================
function aggiornaTotaleInventario() {
  var el = document.getElementById('invQuantita');
  if (!el) return;
  var q = parseFloat(id('invQuantita').value) || 0;
  var vu = parseFloat(id('invValoreUnit').value) || 0;
  var tot = q * vu;
  id('invValoreTot').value = tot.toFixed(2).replace('.', ',') + ' EUR';
}

function apriModaleInventario(iid) {
  apriModale('modaleInventario');
  if (iid) {
    var o = STATO.inventario.find(x => x.id === iid); if (!o) return;
    id('modaleInventarioTitolo').textContent = '🧰 '+o.nome;
    id('invId').value = o.id;
    id('invNome').value = o.nome||'';
    var q = o.quantita != null ? o.quantita : 1;
    var vu = o.valore_unitario != null ? o.valore_unitario : (o.valore || 0);
    id('invQuantita').value = q;
    id('invValoreUnit').value = vu;
    aggiornaTotaleInventario();
    id('invStato').value = o.stato||'funzionante';
    var elDataAcq1 = document.getElementById('invDataAcquisto');
    if (elDataAcq1) elDataAcq1.value = o.data_acquisto || o.data || '';
    id('invNotaCarico').value = o.nota_carico||'';
    id('invNote').value = o.note||'';
    id('btnEliminaInventarioModale').style.display = 'block';
  } else {
    id('modaleInventarioTitolo').textContent = '🧰 Nuovo Oggetto';
    id('invId').value = ''; id('invNome').value = '';
    id('invQuantita').value = 1;
    id('invValoreUnit').value = 0;
    aggiornaTotaleInventario();
    id('invStato').value = 'funzionante';
    var elDataAcq2 = document.getElementById('invDataAcquisto');
    if (elDataAcq2) elDataAcq2.value = new Date().toISOString().split('T')[0]; id('invNotaCarico').value = ''; id('invNote').value = '';
    id('btnEliminaInventarioModale').style.display = 'none';
  }
}
async function salvaInventario() {
  var nome = (id('invNome').value||'').trim(); if (!nome) { alert('Nome obbligatorio'); return; }
  var iid = id('invId').value ? parseInt(id('invId').value) : null;
  var q = parseFloat(id('invQuantita').value) || 0;
  var vu = parseFloat(id('invValoreUnit').value) || 0;
  var corpo = {
    nome: nome,
    quantita: q,
    valore_unitario: vu,
    valore_totale: q * vu,
    valore: vu,
    stato: id('invStato').value,
    data_acquisto: document.getElementById('invDataAcquisto') ? document.getElementById('invDataAcquisto').value : '',
    nota_carico: id('invNotaCarico').value,
    note: id('invNote').value
  };
  if (iid) corpo.id = iid;
  await fetch('/api/inventario', {method: iid?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(corpo)});
  chiudiModale('modaleInventario');
  await caricaDati();
  if (typeof renderBilancioInventario === 'function') renderBilancioInventario();
  if (typeof _annoCorrente !== 'undefined' && _annoCorrente !== 'tutti' && typeof caricaBilancioAnno === 'function') caricaBilancioAnno(_annoCorrente);
}
function eliminaInventarioDaModale() { var iid = id('invId').value; if (!iid) return; if (confirm('Eliminare?')) fetch('/api/inventario?id='+iid,{method:'DELETE'}).then(function(){chiudiModale('modaleInventario');caricaDati();}); }
function aggiornaInventario() {
  var g = id('grigliaInventario'); g.innerHTML = '';
  if (!STATO.inventario || STATO.inventario.length === 0) {
    g.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:30px">Nessun oggetto in inventario</div>';
    return;
  }
  
  var totaleGenerale = 0;
  
  STATO.inventario.forEach(o => {
    // Calcola valori
    var q = (o.quantita != null) ? parseFloat(o.quantita) : 1;
    var vu = (o.valore_unitario != null) ? parseFloat(o.valore_unitario) : (parseFloat(o.valore) || 0);
    var tot = q * vu;
    totaleGenerale += tot;
    
    // Data acquisto formattata
    var dataAcq = o.data_acquisto || o.data || '';
    var dataAcqTxt = '';
    if (dataAcq) {
      try {
        var dparts = dataAcq.split('-');
        dataAcqTxt = '<div style="font-size:11px;color:#90A4AE;margin-top:2px">&#128197; ' + dparts[2] + '/' + dparts[1] + '/' + dparts[0] + '</div>';
      } catch(e) {}
    }
    
    // Stato (badge)
    var statoBadge = '';
    if (o.stato && o.stato !== 'funzionante' && o.stato !== 'nuovo') {
      statoBadge = '<span class="badge badge-blue" style="font-size:10px">' + o.stato + '</span>';
    }
    
    var d = document.createElement('div');
    d.className = 'card';
    d.style.cursor = 'pointer';
    d.innerHTML =
      '<div style="display:flex;justify-content:space-between;align-items:start;gap:6px">' +
        '<h3 style="margin:0;color:var(--accent);font-size:16px">' + o.nome + '</h3>' +
        statoBadge +
      '</div>' +
      dataAcqTxt +
      '<div style="margin-top:10px;padding:8px;background:#f5f7fa;border-radius:8px">' +
        '<div style="display:flex;justify-content:space-between;font-size:12px;color:#607078;padding:2px 0">' +
          '<span>Quantità:</span><strong style="color:#1a232e">' + q + '</strong>' +
        '</div>' +
        '<div style="display:flex;justify-content:space-between;font-size:12px;color:#607078;padding:2px 0">' +
          '<span>Prezzo unit.:</span><strong style="color:#1a232e">€ ' + vu.toFixed(2).replace('.', ',') + '</strong>' +
        '</div>' +
        '<div style="display:flex;justify-content:space-between;font-size:13px;color:#16A34A;margin-top:6px;padding-top:6px;border-top:1px solid #e0e6eb">' +
          '<span style="font-weight:700">Totale:</span><strong>€ ' + tot.toFixed(2).replace('.', ',') + '</strong>' +
        '</div>' +
      '</div>' +
      (o.note ? '<div style="font-size:11px;color:var(--text-muted);margin-top:6px;font-style:italic">' + o.note + '</div>' : '');
    
    d.onclick = (function(iid){ return function(){ apriModaleInventario(iid); }; })(o.id);
    g.appendChild(d);
  });
  
  // Aggiungi totale generale in fondo
  var riepilogo = document.getElementById('inventarioTotaleGenerale');
  if (!riepilogo) {
    riepilogo = document.createElement('div');
    riepilogo.id = 'inventarioTotaleGenerale';
    riepilogo.style.cssText = 'grid-column:1/-1;text-align:right;padding:14px;background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-radius:10px;font-size:16px;font-weight:700;color:#16A34A;margin-top:10px;border-left:4px solid #16A34A';
    g.parentNode.insertBefore(riepilogo, g.nextSibling);
  }
  riepilogo.innerHTML = '&#128176; Valore totale inventario: € ' + totaleGenerale.toFixed(2).replace('.', ',');
}

// ============================================================
// MATERIALI (Entità)
// ============================================================
function renderMateriali() {
  var search = (id('cercaMateriali')?.value||'').toLowerCase();
  var catFiltro = id('filtroCategoriaMateriali')?.value || '';
  var sel = id('filtroCategoriaMateriali');
  if (sel && sel.options.length <= 1) {
    sel.innerHTML = '<option value="">Tutte le categorie</option>';
    STATO.categorie_entita.forEach(c => sel.innerHTML += '<option value="'+c+'">'+c+'</option>');
  }
  var f = STATO.entita.slice();
  if (search) f = f.filter(e => (e.nome||'').toLowerCase().includes(search));
  if (catFiltro) f = f.filter(e => e.categoria === catFiltro);
  var g = id('materialiContainer'); g.innerHTML = '';
  if (f.length === 0) { g.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:30px">Nessun materiale. Vai in "Elabora" e scrivi cosa hai acquistato.</div>'; return; }
  f.forEach(e => {
    var inc = !e.costo_unitario || !e.data_carico;
    var d = document.createElement('div'); d.className='card'; d.style.cursor='pointer';
    d.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:start">'+
      '<h3 style="margin:0;color:var(--accent)">'+e.nome+'</h3>'+
      (inc?'<span class="badge badge-yellow">🟡 da completare</span>':'<span class="badge badge-green">✅</span>')+'</div>'+
      '<div style="font-size:12px;color:var(--text-muted);margin-top:4px">'+e.categoria+'</div>'+
      '<div style="font-size:22px;font-weight:700;margin:8px 0">x'+e.quantita+'</div>'+
      (e.costo_unitario?'<div style="font-size:13px">€'+parseFloat(e.costo_unitario).toFixed(2)+' cad. → <strong>€'+(parseFloat(e.costo_unitario)*e.quantita).toFixed(2)+'</strong></div>':'')+
      (e.data_carico?'<div style="font-size:12px;color:var(--text-muted);margin-top:4px">📅 '+e.data_carico+'</div>':'')+
      (e.fornitore?'<div style="font-size:12px;color:var(--text-muted)">🏢 '+e.fornitore+'</div>':'')+
      (e.note?'<div style="font-size:12px;color:var(--text-muted);margin-top:6px;max-height:60px;overflow:hidden">'+e.note+'</div>':'');
    d.onclick = (function(eid){ return function(){ apriModaleEntita(eid); }; })(e.id);
    g.appendChild(d);
  });
}
function apriModaleEntita(eid) {
  apriModale('modaleEntita');
  var sel = id('entCategoria');
  sel.innerHTML = '';
  STATO.categorie_entita.forEach(c => sel.innerHTML += '<option value="'+c+'">'+c+'</option>');
  sel.innerHTML += '<option value="__nuova__">➕ Nuova categoria...</option>';
  if (eid) {
    var e = STATO.entita.find(x => x.id === eid); if (!e) return;
    id('modaleEntitaTitolo').textContent = '📦 '+e.nome;
    id('entitaId').value = e.id;
    id('entNome').value = e.nome||'';
    sel.value = e.categoria||'Altro';
    id('entQuantita').value = e.quantita||1;
    id('entDataCarico').value = e.data_carico||'';
    id('entCostoUnitario').value = e.costo_unitario||0;
    id('entFornitore').value = e.fornitore||'';
    id('entCondizione').value = e.condizione||'nuovo';
    id('entManutenzione').value = e.manutenzione||'';
    id('entNote').value = e.note||'';
    id('btnEliminaEntitaModale').style.display = 'block';
  } else {
    id('modaleEntitaTitolo').textContent = '📦 Nuovo Materiale';
    id('entitaId').value = '';
    id('entNome').value = '';
    sel.value = 'Altro';
    id('entQuantita').value = 1;
    id('entDataCarico').value = new Date().toISOString().split('T')[0];
    id('entCostoUnitario').value = 0;
    id('entFornitore').value = '';
    id('entCondizione').value = 'nuovo';
    id('entManutenzione').value = '';
    id('entNote').value = '';
    id('btnEliminaEntitaModale').style.display = 'none';
  }
}
async function salvaEntita() {
  var nome = (id('entNome').value||'').trim(); if (!nome) { alert('Nome obbligatorio'); return; }
  var cat = id('entCategoria').value;
  if (cat === '__nuova__') {
    var nuova = prompt('Nome nuova categoria:');
    if (!nuova) return;
    await fetch('/api/categorie_entita', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome:nuova})});
    STATO.categorie_entita.push(nuova);
    cat = nuova;
  }
  var eid = id('entitaId').value ? parseInt(id('entitaId').value) : null;
  var corpo = {
    nome: nome, categoria: cat,
    quantita: parseInt(id('entQuantita').value||1),
    data_carico: id('entDataCarico').value,
    costo_unitario: parseFloat(id('entCostoUnitario').value||0),
    fornitore: id('entFornitore').value,
    condizione: id('entCondizione').value,
    manutenzione: id('entManutenzione').value,
    note: id('entNote').value,
    fonte: 'manuale'
  };
  if (eid) corpo.id = eid;
  await fetch('/api/entita', {method: eid?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(corpo)});
  chiudiModale('modaleEntita'); caricaDati();
}
function eliminaEntitaDaModale() { var eid = id('entitaId').value; if (!eid) return; if (confirm('Eliminare?')) fetch('/api/entita?id='+eid,{method:'DELETE'}).then(function(){chiudiModale('modaleEntita');caricaDati();}); }

// ============================================================
// ELABORA
// ============================================================
var elaboraRisultatoCorrente = null;
function elaboraPulisci() { id('elaboraTesto').value = ''; id('elaboraFile').value = ''; }
function elaboraCaricaFile(files) {
  if (!files || !files.length) return;
  var f = files[0];
  if (f.name.endsWith('.txt') || f.name.endsWith('.csv')) {
    var reader = new FileReader();
    reader.onload = function(e) { id('elaboraTesto').value = e.target.result; };
    reader.readAsText(f);
  } else {
    alert('Per file Excel, incolla il testo o usa il formato .txt/.csv. Il supporto XLSX diretto sarà aggiunto in futuro.');
  }
}
async function elaboraAnalizza() {
  var testo = (id('elaboraTesto').value||'').trim();
  if (!testo) { alert('Scrivi qualcosa prima di elaborare'); return; }
  var r = await fetch('/api/elabora/analizza', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({testo:testo})});
  var res = await r.json();
  if (!res.success) {
    if (res.duplicato) alert('⚠️ Questo testo è già stato elaborato in passato.');
    else alert('Errore: ' + (res.error||'?'));
    return;
  }
  elaboraRisultatoCorrente = res.risultato;
  disegnaAnteprimaElabora(res.risultato, testo);
  apriModale('modaleElaboraAnteprima');
}
function disegnaAnteprimaElabora(ris, testo) {
  var h = '';
  h += '<div style="background:var(--bg);padding:10px;border-radius:8px;margin-bottom:12px;font-size:12px;color:var(--text-muted)"><strong>Testo originale:</strong><br><em>'+testo.replace(/</g,'&lt;')+'</em></div>';
  if (ris.movimenti.length) {
    h += '<h3>📦 Movimenti magazzino ('+ris.movimenti.length+')</h3>';
    ris.movimenti.forEach((m,i) => {
      h += '<div class="entita-blocco"><strong>'+(m.tipo === 'carico' ? '➕ Carico' : '➖ Scarico')+' '+m.quantita+' '+m.categoria+'</strong><br><small>Data: '+m.data+'</small></div>';
    });
  }
  if (ris.entita.length) {
    h += '<h3>🆕 Nuove entità ('+ris.entita.length+')</h3>';
    ris.entita.forEach((e,i) => {
      h += '<div class="entita-blocco">'+
        '<label>Nome</label><input value="'+e.nome+'" oninput="elaboraRisultatoCorrente.entita['+i+'].nome=this.value" style="margin-bottom:4px">'+
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">'+
        '<div><label>Quantità</label><input type="number" value="'+e.quantita+'" oninput="elaboraRisultatoCorrente.entita['+i+'].quantita=parseInt(this.value)"></div>'+
        '<div><label>Categoria</label><select onchange="elaboraRisultatoCorrente.entita['+i+'].categoria=this.value"><option value="Mezzi"'+(e.categoria==='Mezzi'?' selected':'')+'>Mezzi</option><option value="Attrezzatura"'+(e.categoria==='Attrezzatura'?' selected':'')+'>Attrezzatura</option><option value="Materiale informativo">Materiale informativo</option><option value="Altro"'+(e.categoria==='Altro'?' selected':'')+'>Altro</option></select></div>'+
        '<div><label>Data carico</label><input type="date" value="'+(e.data_carico||'')+'" oninput="elaboraRisultatoCorrente.entita['+i+'].data_carico=this.value"></div>'+
        '<div><label>Costo unitario €</label><input type="number" value="'+(e.costo_unitario||'')+'" oninput="elaboraRisultatoCorrente.entita['+i+'].costo_unitario=parseFloat(this.value)"></div>'+
        '<div><label>Fornitore</label><input value="'+(e.fornitore||'')+'" oninput="elaboraRisultatoCorrente.entita['+i+'].fornitore=this.value"></div>'+
        '<div><label>Condizione</label><select onchange="elaboraRisultatoCorrente.entita['+i+'].condizione=this.value"><option value="nuovo">Nuovo</option><option value="usato">Usato</option><option value="in stock">In stock</option><option value="da verificare">Da verificare</option></select></div>'+
        '</div>'+
        '<label style="margin-top:6px;display:block">Note</label><textarea rows="2" oninput="elaboraRisultatoCorrente.entita['+i+'].note=this.value">'+(e.note||'')+'</textarea>'+
        '</div>';
    });
  }
  if (ris.task.length) {
    h += '<h3>✅ Task ('+ris.task.length+')</h3>';
    ris.task.forEach((t,i) => {
      h += '<div class="entita-blocco"><strong>'+t.titolo+'</strong>'+(t.data_scadenza?' <small>('+t.data_scadenza+')</small>':'')+'</div>';
    });
  }
  if (ris.eventi.length) {
    h += '<h3>📅 Eventi ('+ris.eventi.length+')</h3>';
    ris.eventi.forEach(e => { h += '<div class="entita-blocco">'+e.data+' — '+e.iniziativa+'</div>'; });
  }
  id('elaboraAnteprimaContenuto').innerHTML = h;
}
async function confermaElaborazione() {
  if (!elaboraRisultatoCorrente) return;
  var testo = id('elaboraTesto').value;
  var r = await fetch('/api/elabora/applica', {method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({testo:testo, risultato: elaboraRisultatoCorrente})});
  var res = await r.json();
  if (res.success) {
    var a = res.applicati;
    var msg = '✅ Elaborazione completata!\n\n';
    if (a.movimenti) msg += '• '+a.movimenti+' movimenti magazzino\n';
    if (a.entita) msg += '• '+a.entita+' nuove entità\n';
    if (a.task) msg += '• '+a.task+' task\n';
    alert(msg);
    chiudiModale('modaleElaboraAnteprima');
    elaboraPulisci();
    elaboraRisultatoCorrente = null;
    caricaDati();
    mostra('materiali');
  }
}

// ============================================================
// LAVAGNA
// ============================================================
function renderLavagna() {
  var f = id('filtroColorePostit')?.value || '';
  var posts = STATO.postit.slice();
  if (f) posts = posts.filter(p => p.colore === f);
  var c = id('lavagnaContainer'); if (!c) return;
  c.innerHTML = '';
  posts.forEach(p => {
    var d = document.createElement('div');
    var col = p.colore || 'giallo';
    d.className = 'postit col-' + col + (p.elaborato ? ' elaborato' : '');
    d.style.transform = 'rotate('+(p.rotazione||0)+'deg)';
    d.innerHTML = '<button class="chiudi-postit" onclick="event.stopPropagation();eliminaPostit('+p.id+')">✕</button>'+
      '<div class="testo">'+(p.testo||'').replace(/</g,'&lt;')+'</div>'+
      '<div class="data-postit">'+(p.creato_il||'')+'</div>'+
      '<button class="btn-elabora-postit" onclick="event.stopPropagation();elaboraPostit('+p.id+')">⚡</button>';
    d.onclick = (function(pid){ return function(){ apriModalePostit(pid); }; })(p.id);
    c.appendChild(d);
  });
  var nuovo = document.createElement('div');
  nuovo.className = 'postit nuovo';
  nuovo.textContent = '+';
  nuovo.onclick = function() { apriModalePostit(); };
  c.appendChild(nuovo);
}
function apriModalePostit(pid) {
  apriModale('modalePostit');
  if (pid) {
    var p = STATO.postit.find(x => x.id === pid); if (!p) return;
    id('modalePostitTitolo').textContent = '📌 Modifica Post-it';
    id('postitId').value = p.id;
    id('postitTesto').value = p.testo || '';
    id('postitColore').value = p.colore || 'giallo';
  } else {
    id('modalePostitTitolo').textContent = '📌 Nuovo Post-it';
    id('postitId').value = '';
    id('postitTesto').value = '';
    id('postitColore').value = 'giallo';
  }
}
async function salvaPostit() {
  var testo = (id('postitTesto').value||'').trim(); if (!testo) { alert('Scrivi qualcosa'); return; }
  var pid = id('postitId').value ? parseInt(id('postitId').value) : null;
  var corpo = { testo: testo, colore: id('postitColore').value };
  if (pid) corpo.id = pid;
  else corpo.rotazione = Math.floor(Math.random()*7)-3;
  await fetch('/api/postit', {method: pid?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(corpo)});
  chiudiModale('modalePostit'); caricaDati();
}
async function eliminaPostit(pid) { if (confirm('Eliminare questo post-it?')) { await fetch('/api/postit?id='+pid, {method:'DELETE'}); caricaDati(); } }
function elaboraPostit(pid) {
  var p = STATO.postit.find(x => x.id === pid); if (!p) return;
  id('elaboraTesto').value = p.testo || '';
  mostra('elabora');
}

// ============================================================
// LISTE
// ============================================================
function renderListe() {
  var c = id('listeContainer'); if (!c) return;
  c.innerHTML = '';
  if (STATO.liste.length === 0) { c.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:30px;grid-column:1/-1">Nessuna lista. Creane una o scrivi un post-it con la spesa.</div>'; return; }
  STATO.liste.forEach(l => {
    var tot = (l.prodotti||[]).length;
    var comprati = (l.prodotti||[]).filter(p => p.comprato).length;
    var d = document.createElement('div'); d.className='card';
    d.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'+
      '<h3 style="margin:0;color:var(--accent)">'+l.nome+'</h3>'+
      '<div><span class="badge badge-blue">'+comprati+'/'+tot+'</span> '+
      '<button class="btn btn-red" onclick="eliminaLista('+l.id+')" style="padding:3px 8px;font-size:11px">🗑️</button></div></div>'+
      '<div>'+(l.prodotti||[]).map(p =>
        '<div class="lista-item'+(p.comprato?' comprato':'')+'">'+
        '<input type="checkbox"'+(p.comprato?' checked':'')+' onchange="toggleProdotto('+l.id+','+p.id+')">'+
        '<span class="nome">'+p.nome+'</span>'+
        '<button onclick="eliminaProdotto('+l.id+','+p.id+')" style="background:none;border:none;color:#DC2626;cursor:pointer">✕</button>'+
        '</div>').join('')+'</div>'+
      '<div style="margin-top:10px;display:flex;gap:6px">'+
      '<input id="addProd'+l.id+'" placeholder="Aggiungi prodotto..." style="flex:1">'+
      '<button class="btn btn-green" onclick="aggiungiProdotto('+l.id+')" style="padding:6px 12px">+</button></div>';
    c.appendChild(d);
  });
}
function apriModaleLista() {
  apriModale('modaleLista');
  id('modaleListaTitolo').textContent = '🛒 Nuova Lista';
  id('listaId').value = '';
  id('listaNome').value = '';
  id('listaProdotti').value = '';
}
async function salvaLista() {
  var nome = (id('listaNome').value||'').trim(); if (!nome) { alert('Nome obbligatorio'); return; }
  var prods = (id('listaProdotti').value||'').split('\n').map(s => s.trim()).filter(s => s).map(n => ({nome: n, comprato: false}));
  await fetch('/api/liste', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome: nome, prodotti: prods})});
  chiudiModale('modaleLista'); caricaDati();
}
async function toggleProdotto(lid, pid) {
  var l = STATO.liste.find(x => x.id === lid); if (!l) return;
  var p = (l.prodotti||[]).find(x => x.id === pid); if (!p) return;
  p.comprato = !p.comprato;
  if (p.comprato) p.data_acquisto = new Date().toISOString().split('T')[0];
  await fetch('/api/liste', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(l)});
  caricaDati();
}
async function aggiungiProdotto(lid) {
  var input = id('addProd'+lid);
  var nome = (input.value||'').trim(); if (!nome) return;
  var l = STATO.liste.find(x => x.id === lid); if (!l) return;
  l.prodotti = l.prodotti || [];
  l.prodotti.push({nome: nome, comprato: false});
  await fetch('/api/liste', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(l)});
  caricaDati();
}
async function eliminaProdotto(lid, pid) {
  var l = STATO.liste.find(x => x.id === lid); if (!l) return;
  l.prodotti = (l.prodotti||[]).filter(p => p.id !== pid);
  await fetch('/api/liste', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(l)});
  caricaDati();
}
async function eliminaLista(lid) { if (confirm('Eliminare la lista?')) { await fetch('/api/liste?id='+lid, {method:'DELETE'}); caricaDati(); } }

// ============================================================
// RUBRICA
// ============================================================
function renderRubrica() {
  var search = (id('cercaRubrica')?.value||'').toLowerCase();
  var f = STATO.rubrica.slice();
  if (search) f = f.filter(c => (c.nome||'').toLowerCase().includes(search) || (c.telefono||'').includes(search));
  var tbody = id('rubricaBody'); tbody.innerHTML = '';
  if (f.length === 0) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted)">Nessun contatto</td></tr>';
  else f.forEach(c => {
    tbody.innerHTML += '<tr class="riga-cliccabile" onclick="apriModaleContatto('+c.id+')">'+
      '<td><strong>'+(c.nome||'—')+'</strong></td><td>'+(c.telefono||'')+'</td>'+
      '<td>'+(c.email||'')+'</td><td>'+(c.scuola||'')+'</td>'+
      '<td>'+(c.ruolo||'')+'</td><td>'+(c.note||'')+'</td>'+
      '<td><button onclick="event.stopPropagation();eliminaContatto('+c.id+')" style="background:none;border:none;color:#DC2626;cursor:pointer">🗑️</button></td></tr>';
  });
}
function apriModaleContatto(cid, opts) {
  apriModale('modaleContatto');
  var sel = id('contattoScuola'); sel.innerHTML = '<option value="">—</option>';
  STATO.scuole.forEach(s => sel.innerHTML += '<option value="'+s.nome+'">'+s.nome+'</option>');
  if (cid) {
    var c = STATO.rubrica.find(x => x.id === cid); if (!c) return;
    id('modaleContattoTitolo').textContent = '📞 '+(c.nome||'Contatto');
    id('contattoId').value = c.id;
    id('contattoNome').value = c.nome||'';
    id('contattoTel').value = c.telefono||'';
    id('contattoEmail').value = c.email||'';
    sel.value = c.scuola||'';
    id('contattoRuolo').value = c.ruolo||'';
    id('contattoNote').value = c.note||'';
    id('btnEliminaContattoModale').style.display = 'block';
  } else {
    id('modaleContattoTitolo').textContent = '📞 Nuovo Contatto';
    id('contattoId').value = '';
    ['contattoNome','contattoTel','contattoEmail','contattoRuolo','contattoNote'].forEach(x => id(x).value = '');
    sel.value = '';
    id('btnEliminaContattoModale').style.display = 'none';
    if (opts) {
      if (opts.nome) id('contattoNome').value = opts.nome;
      if (opts.telefono) id('contattoTel').value = opts.telefono;
      if (opts.email) id('contattoEmail').value = opts.email;
      if (opts.scuola) sel.value = opts.scuola;
      if (opts.ruolo) id('contattoRuolo').value = opts.ruolo;
      if (opts.note) id('contattoNote').value = opts.note;
    }
  }
}
async function salvaContatto() {
  var cid = id('contattoId').value ? parseInt(id('contattoId').value) : null;
  var corpo = { nome: id('contattoNome').value, telefono: id('contattoTel').value, email: id('contattoEmail').value, scuola: id('contattoScuola').value, ruolo: id('contattoRuolo').value, note: id('contattoNote').value };
  if (cid) corpo.id = cid;
  await fetch('/api/rubrica', {method: cid?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(corpo)});
  chiudiModale('modaleContatto'); caricaDati();
}
function eliminaContattoDaModale() { var cid = id('contattoId').value; if (!cid) return; if (confirm('Eliminare?')) fetch('/api/rubrica?id='+cid,{method:'DELETE'}).then(function(){chiudiModale('modaleContatto');caricaDati();}); }
function eliminaContatto(cid) { if (confirm('Eliminare?')) fetch('/api/rubrica?id='+cid,{method:'DELETE'}).then(caricaDati); }
async function importRubrica(files) {
  if (!files || !files.length) return;
  var form = new FormData(); form.append('file', files[0]);
  var r = await fetch('/api/rubrica/import', {method:'POST', body:form});
  var res = await r.json();
  if (res.success) { alert('Importati '+res.importati+' contatti'); caricaDati(); }
}

// ============================================================
// ARCHIVIO
// ============================================================
function aggiornaArchivio() {
  id('aEventi').textContent = STATO.eventi.length;
  var tp=0, tb=0, tm=0, ta=0, tc=0;
  STATO.eventi.forEach(e => { tp+=e.numero_partecipanti||0; tb+=e.braccialetti||0; tm+=e.medaglie||0; ta+=e.adesivi||0; tc+=e.coppe||0; });
  id('aPartecipanti').textContent = tp; id('aBraccialetti').textContent = tb;
  id('aMedaglie').textContent = tm; id('aAdesivi').textContent = ta; id('aCoppe').textContent = tc;
  var stats = STATO.scuole.map(s => {
    var ev = STATO.eventi.filter(e => e.scuola_id === s.id);
    return { nome: s.nome, eventi: ev.length,
      partecipanti: ev.reduce((a,e)=>a+(e.numero_partecipanti||0),0),
      braccialetti: ev.reduce((a,e)=>a+(e.braccialetti||0),0),
      medaglie: ev.reduce((a,e)=>a+(e.medaglie||0),0),
      adesivi: ev.reduce((a,e)=>a+(e.adesivi||0),0),
      coppe: ev.reduce((a,e)=>a+(e.coppe||0),0) };
  }).sort((a,b)=>b.eventi-a.eventi);
  var tb2 = id('archivioBody'); tb2.innerHTML = '';
  stats.forEach(s => {
    tb2.innerHTML += '<tr><td><strong>'+s.nome+'</strong></td><td>'+s.eventi+'</td><td>'+s.partecipanti+'</td><td>'+s.braccialetti+'</td><td>'+s.medaglie+'</td><td>'+s.adesivi+'</td><td>'+s.coppe+'</td></tr>';
  });
}

// ============================================================
// WIDGET SCADENZE + STOCK
// ============================================================
function renderWidgetScadenze() {
  var c = id('widgetScadenze'); if (!c) return;
  var oggi = new Date(); var trenta = new Date(); trenta.setDate(trenta.getDate()+30);
  var os = oggi.toISOString().split('T')[0], ts = trenta.toISOString().split('T')[0];
  var items = [];
  STATO.task.filter(t => t.stato !== 'completato' && t.data_scadenza >= os && t.data_scadenza <= ts).forEach(t => items.push({data: t.data_scadenza, icona: '✅', testo: t.titolo, tipo: 'task', id: t.id}));
  STATO.eventi.filter(e => e.data >= os && e.data <= ts).forEach(e => items.push({data: e.data, icona: '📅', testo: e.iniziativa, tipo: 'evento', id: e.id}));
  STATO.entita.filter(e => e.data_carico && e.data_carico >= os && e.data_carico <= ts).forEach(e => items.push({data: e.data_carico, icona: '📦', testo: e.nome, tipo: 'entita', id: e.id}));
  items.sort((a,b) => a.data.localeCompare(b.data));
  if (items.length === 0) { c.innerHTML = '<div style="color:var(--text-muted);padding:10px">🎉 Niente in programma nei prossimi 30 giorni</div>'; return; }
  c.innerHTML = items.map(i => {
    var dataFmt = i.data.split('-').reverse().join('/');
    return '<div class="item"><span class="data">'+dataFmt+'</span><span class="icona">'+i.icona+'</span><span class="testo">'+i.testo+'</span></div>';
  }).join('');
}
function renderWidgetStock() {
  var c = id('widgetStock'); if (!c) return;
  var s = STATO.soglie_scorta || {braccialetti: 50, medaglie: 30, adesivi: 30, coppe: 3};
  var dati_q = [
    {cat: 'braccialetti', label: 'Braccialetti', icona: '📦', v: calcolaStock('braccialetti'), s: s.braccialetti},
    {cat: 'medaglie', label: 'Medaglie', icona: '🏅', v: calcolaStock('medaglie'), s: s.medaglie},
    {cat: 'adesivi', label: 'Adesivi', icona: '🔖', v: calcolaStock('adesivi'), s: s.adesivi},
    {cat: 'coppe', label: 'Coppe', icona: '🏆', v: calcolaStock('coppe'), s: s.coppe}
  ];
  c.innerHTML = dati_q.map(d => {
    var stato = d.v < d.s ? 'critico' : d.v < d.s * 1.5 ? 'basso' : 'ok';
    var icona = stato === 'critico' ? '🔴' : stato === 'basso' ? '🟡' : '🟢';
    return '<div class="quadro stato-'+stato+'"><div style="font-size:20px">'+d.icona+'</div><div class="num">'+d.v+'</div><div class="lab">'+d.label+' '+icona+'</div></div>';
  }).join('');
}
function apriModaleSoglie() {
  var s = STATO.soglie_scorta || {};
  id('sogliaBracc').value = s.braccialetti || 50;
  id('sogliaMed').value = s.medaglie || 30;
  id('sogliaAdes').value = s.adesivi || 30;
  id('sogliaCoppe').value = s.coppe || 3;
  apriModale('modaleSoglie');
}
async function salvaSoglie() {
  var corpo = { braccialetti: parseInt(id('sogliaBracc').value)||0, medaglie: parseInt(id('sogliaMed').value)||0, adesivi: parseInt(id('sogliaAdes').value)||0, coppe: parseInt(id('sogliaCoppe').value)||0 };
  await fetch('/api/soglie', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(corpo)});
  chiudiModale('modaleSoglie'); caricaDati();
}
function apriModaleGiacenza() {
  id('mgBracc').value = calcolaStock('braccialetti');
  id('mgMed').value = calcolaStock('medaglie');
  id('mgAdes').value = calcolaStock('adesivi');
  id('mgCoppe').value = calcolaStock('coppe');
  apriModale('modaleGiacenza');
}
async function salvaGiacenza() {
  if (!confirm('⚠️ Questo sostituirà tutti i movimenti precedenti. Continuare?')) return;
  await fetch('/api/primo_avvio/giacenza', {method:'POST',headers:{'Content-Type':'application/json'},
    body: JSON.stringify({braccialetti: parseInt(id('mgBracc').value)||0, medaglie: parseInt(id('mgMed').value)||0, adesivi: parseInt(id('mgAdes').value)||0, coppe: parseInt(id('mgCoppe').value)||0, carichi_extra: []})});
  chiudiModale('modaleGiacenza'); caricaDati();
}

// ============================================================
// PORTFOGLIO, CAMBIO, METEO, RADIO, CALCOLATRICE
// ============================================================
function disegnaPortafoglio() {
  var lista = STATO.portafoglio || [];
  var tbody = id('portafoglioLista'); tbody.innerHTML = '';
  var totInv = 0, totAtt = 0;
  lista.forEach(t => {
    var inv = (t.quantita||0)*(t.prezzo_acquisto||0);
    var att = (t.quantita||0)*(t.prezzo_attuale||0);
    totInv += inv; totAtt += att;
    tbody.innerHTML += '<tr><td>'+t.nome+'</td><td>'+t.quantita+'</td><td>€'+(t.prezzo_acquisto||0).toFixed(2)+'</td><td>€'+(t.prezzo_attuale||0).toFixed(2)+'</td><td>'+(inv>0?((att-inv)/inv*100).toFixed(1)+'%':'-')+'</td></tr>';
  });
  id('portInvestito').textContent = '€'+totInv.toFixed(2);
  id('portAttuale').textContent = '€'+totAtt.toFixed(2);
  id('portGuadagno').textContent = (totAtt-totInv >= 0 ? '+' : '') + '€' + (totAtt-totInv).toFixed(2);
  id('portGuadagno').style.color = totAtt >= totInv ? '#16A34A' : '#DC2626';
}
var VALUTE_LABEL = { EUR:'EUR', USD:'USD', GBP:'GBP', CHF:'CHF', JPY:'JPY', CAD:'CAD', AUD:'AUD', CNY:'CNY' };
var cambioTassi = null;
async function caricaCambio() {
  try {
    var r = await fetch('/api/cambio'); var res = await r.json();
    if (!res.success) return;
    cambioTassi = res.tassi;
    id('cambioAggiornato').textContent = 'aggiornato ' + res.aggiornato;
    ['cambioDa','cambioA'].forEach((sid, i) => {
      var sel = id(sid);
      sel.innerHTML = Object.keys(VALUTE_LABEL).filter(v => cambioTassi[v]).map(v => '<option value="'+v+'">'+VALUTE_LABEL[v]+'</option>').join('');
      sel.value = i === 0 ? 'EUR' : 'USD';
    });
    calcolaCambio();
  } catch(e) { id('cambioAggiornato').textContent = 'non raggiungibile'; }
}
function calcolaCambio() {
  if (!cambioTassi) return;
  var imp = parseFloat(id('cambioImporto').value)||0;
  var da = id('cambioDa').value, a = id('cambioA').value;
  var r = (imp/(cambioTassi[da]||1))*(cambioTassi[a]||1);
  id('cambioRisultato').value = r.toFixed(4);
}
async function cercaMeteo() {
  var c = id('meteoCitta').value.trim(); if (!c) return;
  var r = await fetch('/api/meteo?citta='+encodeURIComponent(c));
  var res = await r.json();
  if (!res.success) { id('meteoRisultato').innerHTML = '<div style="color:#DC2626">'+res.error+'</div>'; return; }
  id('meteoRisultato').innerHTML = '<div style="padding:10px;background:var(--bg);border-radius:8px"><strong>'+res.localita+'</strong><br>'+Math.round(res.attuale.temperature_2m)+'°C, umidità '+res.attuale.relative_humidity_2m+'%</div>';
}
var STAZIONI_RADIO = [
  {nome: 'RAI Radio 1', url: 'https://icestreaming.rai.it/1.mp3'},
  {nome: 'RAI Radio 2', url: 'https://icestreaming.rai.it/2.mp3'},
  {nome: 'RAI Radio 3', url: 'https://icestreaming.rai.it/3.mp3'},
  {nome: 'Radio 105', url: 'https://icy.unitedradio.it/Radio105.mp3'},
  {nome: 'Virgin Radio', url: 'https://icy.unitedradio.it/Virgin.mp3'}
];
function initRadio() {
  var c = id('radioStazioni');
  c.innerHTML = STAZIONI_RADIO.map((s, i) => '<button class="btn btn-gray" onclick="cambiaRadio('+i+')" style="text-align:left;padding:6px 10px;font-size:13px">'+s.nome+'</button>').join('');
}
function cambiaRadio(i) {
  var audio = id('radioAudio');
  audio.src = STAZIONI_RADIO[i].url;
  id('radioStatoTesto').textContent = STAZIONI_RADIO[i].nome;
  audio.play().catch(e => { id('radioStatoTesto').textContent = 'Stream non raggiungibile'; });
  id('btnRadioPlay').textContent = '⏸️';
}
function toggleRadio() {
  var a = id('radioAudio');
  if (a.paused) { a.play(); id('btnRadioPlay').textContent = '⏸️'; }
  else { a.pause(); id('btnRadioPlay').textContent = '▶️'; }
}
function cambiaVolumeRadio() { id('radioAudio').volume = id('radioVolume').value/100; }

// CALCOLATRICE
var calcV = '0', calcPrev = null, calcOp = null, calcReset = false;
function calcInput(t) {
  if (t === 'C') { calcV='0'; calcPrev=null; calcOp=null; calcReset=false; }
  else if (t === '⌫') { calcV = calcV.length>1 ? calcV.slice(0,-1) : '0'; }
  else if (t === '%') { calcV = String(parseFloat(calcV)/100); }
  else if (['+','-','*','/'].indexOf(t) !== -1) {
    if (calcOp && !calcReset) calcEsegui();
    calcPrev = parseFloat(calcV); calcOp = t; calcReset = true;
  } else if (t === '=') { calcEsegui(); calcOp = null; }
  else if (t === '.') { if (calcReset) { calcV='0'; calcReset=false; } if (calcV.indexOf('.') === -1) calcV += '.'; }
  else { if (calcReset || calcV === '0') { calcV = t; calcReset = false; } else calcV += t; }
  id('calcDisplay').value = calcV;
}
function calcEsegui() {
  if (!calcOp || calcPrev === null) return;
  var a = calcPrev, b = parseFloat(calcV), r = 0;
  if (calcOp === '+') r=a+b; else if (calcOp === '-') r=a-b;
  else if (calcOp === '*') r=a*b; else if (calcOp === '/') r = b!==0 ? a/b : 0;
  calcV = String(Math.round(r*1e8)/1e8); calcPrev = null; calcReset = true;
}

// ============================================================
// COMANDI
// ============================================================
function renderComandi() {
  try {
    var sels = id('bloccoFiltroScuola');
    if (sels) {
      sels.innerHTML = '<option value="">Tutte le scuole</option><option value="__altro__">Solo ALTRO</option>';
      STATO.scuole.forEach(function(s){ sels.innerHTML += '<option value="'+s.id+'">'+s.nome+'</option>'; });
    }
    var ta = id('bloccoFiltroAnno');
    if (ta) {
      var anni = [];
      STATO.eventi.forEach(function(e){ var a=(e.data||'').split('-')[0]; if(a && anni.indexOf(a)===-1) anni.push(a); });
      anni.sort();
      ta.innerHTML = '<option value="">Tutti gli anni</option>';
      anni.forEach(function(a){ ta.innerHTML += '<option value="'+a+'">'+a+'</option>'; });
    }
    var ts = id('bloccoScuolaTarget');
    if (ts) {
      ts.innerHTML = '<option value="">—</option>';
      STATO.scuole.forEach(function(s){ ts.innerHTML += '<option value="'+s.id+'">'+s.nome+'</option>'; });
    }
    renderEventiBlocco();
  } catch(e) { console.warn('renderComandi:', e); }
  try { caricaCronologia(); } catch(e) {}
}
function renderEventiBlocco() {
  var el_fs = id('bloccoFiltroScuola'), el_fa = id('bloccoFiltroAnno'), el_c = id('bloccoEventiLista');
  if (!el_fs || !el_fa || !el_c) return;
  var fs = el_fs.value;
  var fa = el_fa.value;
  var f = STATO.eventi.slice();
  if (fs === '__altro__') f = f.filter(e => !e.scuola_id);
  else if (fs) f = f.filter(e => e.scuola_id == fs);
  if (fa) f = f.filter(e => (e.data||'').startsWith(fa));
  el_c.innerHTML = '';
  if (f.length === 0) { el_c.innerHTML = '<div style="color:var(--text-muted);padding:10px">Nessun evento</div>'; return; }
  f.forEach(e => {
    var s = STATO.scuole.find(x => x.id === e.scuola_id);
    var div = document.createElement('div');
    div.style.cssText = 'padding:6px;border-bottom:1px solid var(--border);font-size:13px;display:flex;gap:6px;align-items:center';
    div.innerHTML = '<input type="checkbox" value="'+e.id+'" class="chk-blocco" style="width:auto"><span>'+e.data+' — '+(e.iniziativa||'')+' — <strong>'+(s?s.nome:'ALTRO')+'</strong></span>';
    el_c.appendChild(div);
  });
}
function selezionaTuttiBlocco() { document.querySelectorAll('.chk-blocco').forEach(c => c.checked = true); }
async function applicaBlocco() {
  var ids = Array.from(document.querySelectorAll('.chk-blocco:checked')).map(function(c){ return parseInt(c.value); });
  if (ids.length === 0) { alert('Seleziona almeno un evento'); return; }
  var elAz = id('bloccoAzione'), elTs = id('bloccoScuolaTarget');
  if (!elAz || !elTs) { alert('Interfaccia blocco non pronta'); return; }
  var azione = elAz.value;
  var sid = azione === 'altro' ? null : parseInt(elTs.value) || null;
  if (azione === 'scuola' && !sid) { alert('Scegli una scuola'); return; }
  var r = await fetch('/api/eventi/blocco', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids: ids, scuola_id: sid})});
  var res = await r.json();
  if (res.success) { alert('✅ '+res.spostati+' eventi spostati'); caricaDati(); }
}
async function eseguiComandi() {
  var elIn = id('consoleComandi'), elOut = id('consoleOutput');
  if (!elIn || !elOut) { alert('Console non pronta'); return; }
  var testo = elIn.value;
  if (!testo.trim()) { alert('Scrivi almeno un comando'); return; }
  var r = await fetch('/api/comandi', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({comandi: testo})});
  var res = await r.json();
  elOut.style.display = 'block';
  elOut.innerHTML = (res.log||[]).map(function(l){ return '<div>'+l+'</div>'; }).join('');
  caricaDati();
}
async function eseguiComandoRapido(cmd) {
  var r = await fetch('/api/comandi', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({comandi: cmd})});
  var res = await r.json();
  alert(res.log.join('\n'));
  caricaDati();
}

// ============================================================
// TEMA
// ============================================================
function toggleTemaDropdown() { id('temaDropdown').classList.toggle('open'); }
function impostaTema(n) {
  document.body.setAttribute('data-tema', n);
  try { localStorage.setItem('braaap_tema', n); } catch(e){}
  id('temaDropdown').classList.remove('open');
}
(function initTema() {
  try { var s = localStorage.getItem('braaap_tema'); if (s) document.body.setAttribute('data-tema', s); } catch(e){}
})();

// ============================================================
// LOGO
// ============================================================
function caricaLogo(e) {
  e.preventDefault();
  var form = e.target; var data = new FormData(form);
  fetch('/api/logo', {method:'POST', body:data}).then(r => r.json()).then(res => {
    if (res.success) { alert('✅ Logo caricato!'); location.reload(); }
  });
  return false;
}

// ============================================================
// LOGO CLICCABILE NELL'HEADER
// ============================================================
function scegliLogo() {
  var input = document.getElementById('logoInputNascosto');
  if (input) input.click();
}

function uploadLogoCliccato(files) {
  if (!files || !files.length) return;
  var file = files[0];
  if (!file.type || file.type.indexOf('image/') !== 0) {
    alert('Per favore scegli un file immagine (PNG, JPG, GIF, WEBP).');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    alert('Immagine troppo grande (max 5 MB).');
    return;
  }

  var form = new FormData();
  form.append('logo', file);

  fetch('/api/logo', { method: 'POST', body: form })
    .then(function(r) { return r.json(); })
    .then(function(res) {
      if (res.success) {
        var img = document.getElementById('logoAttuale');
        if (img && img.tagName === 'IMG') {
          // Aggiorna l'anteprima senza ricaricare
          img.src = URL.createObjectURL(file);
        }
        setTimeout(function() { location.reload(); }, 400);
      } else {
        alert('Errore: ' + (res.error || 'sconosciuto'));
      }
    })
    .catch(function(err) {
      alert('Errore di rete: ' + err.message);
    });
}


// ============================================================
// VOCE (semplificata: REC apre modale Elabora)
// ============================================================
var voceCtx = null, voceStream = null, voceProc = null, voceSource = null, voceCampioni = [];
var VOCE_SR_TARGET = 16000, voceSRNativo = 44100;

// WAV pendente in attesa di revisione
var wavPendente = null;

function premiRec() {
  // Reset eventuali stati residui
  chiudiCatturaAudio();
  wavPendente = null;

  navigator.mediaDevices.getUserMedia({audio: true}).then(stream => {
    voceStream = stream;
    voceCtx = new (window.AudioContext || window.webkitAudioContext)();
    voceSRNativo = voceCtx.sampleRate;
    voceSource = voceCtx.createMediaStreamSource(stream);
    voceCampioni = [];

    // ScriptProcessor cattura i campioni SENZA rimandarli all'output.
    // Il gainNode a volume 0 e' una rete di sicurezza: se per qualche
    // driver audio il processor ha bisogno di un output, lo mandiamo
    // a un gain MUTO (0) che non produce suono -> niente piu' effetto
    // Larsen, eco, fischio o ronzio in cuffia.
    voceProc = voceCtx.createScriptProcessor(4096, 1, 1);
    voceProc.onaudioprocess = e => voceCampioni.push(new Float32Array(e.inputBuffer.getChannelData(0)));

    var gainMuto = voceCtx.createGain();
    gainMuto.gain.value = 0;

    voceSource.connect(voceProc);
    voceProc.connect(gainMuto);
    gainMuto.connect(voceCtx.destination);

    id('btnRec').classList.add('attivo','rec-attiva');
    id('btnStop').disabled = false;
    mostraVocePanel('ascolto', 'REC — parla pure, poi premi STOP');
  }).catch(err => { mostraVocePanel('errore', 'Microfono: ' + err.message); });
}

function premiStop() {
  if (!voceStream) return;
  var uniti = uniscCampioni(voceCampioni);
  var ricamp = ricampiona(uniti, voceSRNativo, VOCE_SR_TARGET);
  var wav = codificaWav(ricamp, VOCE_SR_TARGET);
  chiudiCatturaAudio();
  id('btnRec').classList.remove('attivo','rec-attiva');
  id('btnStop').disabled = true;

  // NON manda subito al server: apre la modale di revisione
  wavPendente = wav;
  apriModaleRevisione(wav);
}

function chiudiCatturaAudio() {
  try {
    if (voceProc) { voceProc.disconnect(); voceProc.onaudioprocess = null; voceProc = null; }
    if (voceSource) { voceSource.disconnect(); voceSource = null; }
    if (voceStream) { voceStream.getTracks().forEach(t => t.stop()); voceStream = null; }
    if (voceCtx) { voceCtx.close(); voceCtx = null; }
  } catch(e) { console.warn('chiudiCatturaAudio:', e); }
}

// ============================================================
// PLAYER DI REVIEW VOCALE
// ============================================================
var reviewTimeoutHold = null;
var reviewStaHold = false;
var _reviewDirezione = 0;

function apriModaleRevisione(wavBlob) {
  var audio = id('audioReview');
  audio.src = URL.createObjectURL(wavBlob);
  audio.currentTime = 0;

  id('reviewTempo').textContent = '0:00 / 0:00';
  id('reviewBarFill').style.width = '0%';
  id('btnReviewPlay').textContent = '\u25B6\uFE0F';
  id('reviewTestoTrascritto').value = '';
  id('reviewStatoTrasc').innerHTML = '';
  id('btnReviewInvia').disabled = false;
  id('btnReviewInvia').textContent = '\u2705 Invia e trascrivi';

  audio.onloadedmetadata = function() {
    id('reviewTempo').textContent = '0:00 / ' + formattaTempo(audio.duration);
  };
  audio.ontimeupdate = function() {
    var cur = audio.currentTime || 0;
    var dur = audio.duration || 0;
    id('reviewTempo').textContent = formattaTempo(cur) + ' / ' + formattaTempo(dur);
    if (dur > 0) id('reviewBarFill').style.width = (cur / dur * 100) + '%';
  };
  audio.onended = function() {
    id('btnReviewPlay').textContent = '\u25B6\uFE0F';
  };

  apriModale('modaleRevisioneVocale');
}

function formattaTempo(sec) {
  if (!sec || isNaN(sec)) return '0:00';
  var m = Math.floor(sec / 60);
  var s = Math.floor(sec % 60);
  return m + ':' + String(s).padStart(2, '0');
}

function reviewPlayPausa() {
  var a = id('audioReview');
  if (a.paused) {
    a.play();
    id('btnReviewPlay').textContent = '\u23F8\uFE0F';
  } else {
    a.pause();
    id('btnReviewPlay').textContent = '\u25B6\uFE0F';
  }
}

// TAP = salta 3s | HOLD (>=350ms) = scorri veloce continuo
function reviewIniziaHold(direzione) {
  var a = id('audioReview');
  _reviewDirezione = direzione;
  reviewStaHold = false;

  var timeoutId = setTimeout(function() {
    reviewStaHold = true;
    var intervalId = setInterval(function() {
      var nuova = a.currentTime + direzione * 0.5;
      a.currentTime = Math.max(0, Math.min(a.duration || 0, nuova));
    }, 100);
    // Salvo l'interval per fermarlo
    window._reviewIntervalId = intervalId;
  }, 350);
  window._reviewTimeoutId = timeoutId;
}

function reviewFermaHold() {
  if (window._reviewTimeoutId) {
    clearTimeout(window._reviewTimeoutId);
    window._reviewTimeoutId = null;
  }
  if (window._reviewIntervalId) {
    clearInterval(window._reviewIntervalId);
    window._reviewIntervalId = null;
  }

  // Se NON era hold (sotto i 350ms), era un tap -> salta 3s
  if (!reviewStaHold && _reviewDirezione !== 0) {
    var a = id('audioReview');
    var nuova = a.currentTime + _reviewDirezione * 3;
    a.currentTime = Math.max(0, Math.min(a.duration || 0, nuova));
  }
  reviewStaHold = false;
  _reviewDirezione = 0;
}

function reviewInvia() {
  if (!wavPendente) {
    alert('Nessuna registrazione da inviare');
    return;
  }
  var btn = id('btnReviewInvia');
  btn.disabled = true;
  btn.textContent = '\u23F3 Trascrivo...';
  id('reviewStatoTrasc').textContent = 'Invio al server in corso...';

  var t0 = Date.now();
  var timer = setInterval(function() {
    var sec = Math.floor((Date.now() - t0) / 1000);
    id('reviewStatoTrasc').textContent = 'Trascrizione in corso... ' + sec + 's';
  }, 300);

  var form = new FormData();
  form.append('audio', wavPendente, 'audio.wav');

  fetch('/api/trascrivi', {method: 'POST', body: form})
    .then(function(r) { return r.json(); })
    .then(function(res) {
      clearInterval(timer);
      if (res.success) {
        id('reviewTestoTrascritto').value = res.trascrizione || '';
        id('reviewStatoTrasc').innerHTML =
          '<span style="color:#16A34A">\u2705 Trascrizione completata</span>' +
          ' \u2014 correggi se serve, poi premi di nuovo';
        btn.disabled = false;
        btn.textContent = '\u2705 Invia a Elabora';
        btn.onclick = function() { reviewElabora(); };
      } else {
        id('reviewStatoTrasc').innerHTML =
          '<span style="color:#DC2626">\u26A0\uFE0F ' + (res.error || 'Errore') + '</span>';
        btn.disabled = false;
        btn.textContent = '\u2705 Riprova';
      }
    })
    .catch(function(err) {
      clearInterval(timer);
      id('reviewStatoTrasc').innerHTML =
        '<span style="color:#DC2626">\u26A0\uFE0F Errore di rete: ' + err.message + '</span>';
      btn.disabled = false;
      btn.textContent = '\u2705 Riprova';
    });
}

function reviewElabora() {
  var testo = (id('reviewTestoTrascritto').value || '').trim();
  if (!testo) {
    alert('Il testo e vuoto');
    return;
  }
  id('elaboraTesto').value = testo;
  chiudiModale('modaleRevisioneVocale');
  mostra('elabora');
  mostraVocePanel('info', 'Testo pronto in Elabora. Premi ELABORA.');
}

function reviewRiscrivi() {
  chiudiModale('modaleRevisioneVocale');
  wavPendente = null;
  setTimeout(function() { premiRec(); }, 250);
}

function reviewScarta() {
  chiudiModale('modaleRevisioneVocale');
  wavPendente = null;
  mostraVocePanel('info', 'Registrazione scartata');
  setTimeout(function() { id('vocePanel').classList.remove('open'); }, 1500);
}

function chiudiModaleRevisione() {
  var a = id('audioReview');
  if (a) { a.pause(); }
  chiudiModale('modaleRevisioneVocale');
}
function uniscCampioni(chunks) {
  var tot = chunks.reduce((a,c) => a+c.length, 0);
  var out = new Float32Array(tot); var off = 0;
  chunks.forEach(c => { out.set(c, off); off += c.length; });
  return out;
}
function ricampiona(s, srIn, srOut) {
  if (srIn === srOut) return s;
  var rap = srIn/srOut; var n = Math.round(s.length/rap);
  var out = new Float32Array(n);
  for (var i=0; i<n; i++) {
    var ini = Math.floor(i*rap), fin = Math.min(Math.floor((i+1)*rap), s.length);
    var somma = 0, cnt = 0;
    for (var j=ini; j<fin; j++) { somma += s[j]; cnt++; }
    out[i] = cnt > 0 ? somma/cnt : 0;
  }
  return out;
}
function codificaWav(floatS, sr) {
  var n = floatS.length; var buf = new ArrayBuffer(44 + n*2); var view = new DataView(buf);
  function str(o, s) { for (var i=0; i<s.length; i++) view.setUint8(o+i, s.charCodeAt(i)); }
  str(0,'RIFF'); view.setUint32(4, 36+n*2, true); str(8,'WAVE'); str(12,'fmt ');
  view.setUint32(16,16,true); view.setUint16(20,1,true); view.setUint16(22,1,true);
  view.setUint32(24,sr,true); view.setUint32(28,sr*2,true); view.setUint16(32,2,true);
  view.setUint16(34,16,true); str(36,'data'); view.setUint32(40,n*2,true);
  var off = 44;
  for (var i=0; i<n; i++) {
    var v = Math.max(-1, Math.min(1, floatS[i]));
    view.setInt16(off, v < 0 ? v*0x8000 : v*0x7FFF, true); off += 2;
  }
  return new Blob([buf], {type:'audio/wav'});
}
function mostraVocePanel(stato, msg, trascrizione) {
  var p = id('vocePanel');
  if (!p) return;
  p.classList.add('open');
  id('voceStato').textContent = msg || '';
  id('voceTrascrizione').textContent = trascrizione || '';
  var icone = { 'errore':'⚠️', 'ascolto':'🎙️', 'info':'ℹ️', 'task':'✅', 'evento':'📅', 'movimento':'📦' };
  id('voceIcona').textContent = icone[stato] || '⏳';
}

// ============================================================
// AVVIO
// ============================================================
try { verificaPrimoAvvio(); } catch(e) { console.error('verificaPrimoAvvio:', e); }
try { aggiornaOrologio(); } catch(e) { console.error('orologio:', e); }
try { caricaCambio(); } catch(e) { console.error('cambio:', e); }
try { initRadio(); } catch(e) { console.error('initRadio:', e); }
try { cambiaVolumeRadio(); } catch(e) { console.error('volumeRadio:', e); }


// ============================================================
// TTS (Text-To-Speech) - voce Elsa / italiana
// ============================================================
var _voceItaliana = null;

function initVoce() {
  if (!window.speechSynthesis) return;
  var voci = speechSynthesis.getVoices();
  for (var i = 0; i < voci.length; i++) {
    var v = voci[i];
    if (v.name.toLowerCase().indexOf('elsa') >= 0) { _voceItaliana = v; break; }
  }
  if (!_voceItaliana) {
    for (var j = 0; j < voci.length; j++) {
      if (voci[j].lang && voci[j].lang.indexOf('it') === 0) { _voceItaliana = voci[j]; break; }
    }
  }
  console.log('Voce TTS:', _voceItaliana ? _voceItaliana.name + ' (' + _voceItaliana.lang + ')' : 'nessuna italiana');
}

function parla(testo) {
  if (!window.speechSynthesis || !testo) return;
  speechSynthesis.cancel();
  var u = new SpeechSynthesisUtterance(testo);
  u.lang = 'it-IT';
  if (_voceItaliana) u.voice = _voceItaliana;
  u.rate = 1.0;
  u.pitch = 1.1;
  speechSynthesis.speak(u);
}

if (window.speechSynthesis) {
  speechSynthesis.onvoiceschanged = initVoce;
  initVoce();
}

// ============================================================
// PLAYER VOCALE FISSO (note vocali)
// ============================================================
var pfNote = [];
var pfIndice = -1;
var pfHoldTimer = null;
var pfHoldInterval = null;
var pfStaHold = false;
var pfDirezione = 0;

function pfApriPlayer() {
  var el = id('playerFisso');
  if (el) el.classList.add('attivo');
}
function pfChiudi() {
  var a = id('pfAudio');
  if (a) { a.pause(); a.src = ''; }
  var el = id('playerFisso');
  if (el) el.classList.remove('attivo');
}

function pfCaricaLista() {
  fetch('/api/note_vocali').then(function(r) { return r.json(); }).then(function(lista) {
    pfNote = lista || [];
    renderNoteVocali();
    if (pfNote.length > 0 && pfIndice < 0) pfIndice = pfNote.length - 1;
    pfAggiorna();
  }).catch(function() {});
}

function formattaTempoPlayer(sec) {
  if (!sec || isNaN(sec)) return '0:00';
  var m = Math.floor(sec / 60);
  var s = Math.floor(sec % 60);
  return m + ':' + String(s).padStart(2, '0');
}

function renderNoteVocali() {
  var c = id('noteVocaliLista');
  if (!c) return;
  if (pfNote.length === 0) {
    c.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:14px">Nessuna nota vocale registrata</div>';
    return;
  }
  var html = '';
  for (var i = pfNote.length - 1; i >= 0; i--) {
    var n = pfNote[i];
    var dur = n.durata ? formattaTempoPlayer(n.durata) : '0:00';
    var testo = (n.trascrizione || '(nessuna trascrizione)').substring(0, 60);
    var attiva = (i === pfIndice);
    html += '<div class="nota-vocale-item ' + (attiva ? 'attiva' : '') + '" onclick="pfSelezionaNota(' + i + ')">';
    html += '<span class="nota-data">' + (n.data || '') + '</span>';
    html += '<span class="nota-durata">' + dur + '</span>';
    html += '<span class="nota-testo">' + testo.replace(/</g, '&lt;') + '</span>';
    html += '<span class="nota-azioni">';
    html += '<button onclick="event.stopPropagation();pfElaboraNota(' + n.id + ')" title="Elabora">\u26A1</button>';
    html += '<button onclick="event.stopPropagation();pfEliminaNota(' + n.id + ')" title="Elimina">\uD83D\uDDD1\uFE0F</button>';
    html += '</span></div>';
  }
  c.innerHTML = html;
}

function pfSelezionaNota(i) {
  if (i < 0 || i >= pfNote.length) return;
  pfIndice = i;
  pfApriPlayer();
  pfCaricaAudio();
  renderNoteVocali();
}

function pfCaricaAudio() {
  if (pfIndice < 0 || pfIndice >= pfNote.length) return;
  var n = pfNote[pfIndice];
  fetch('/api/note_vocali/' + n.id + '/audio').then(function(r) { return r.json(); }).then(function(res) {
    if (!res.success) return;
    var a = id('pfAudio');
    a.src = 'data:' + res.mimetype + ';base64,' + res.audio_b64;

    var durata = n.durata || 0;
    id('pfTempo').textContent = '0:00 / ' + formattaTempoPlayer(durata);
    id('pfBarFill').style.width = '0%';
    id('pfNotaInfo').textContent = n.data + ' \u2014 ' + (n.trascrizione || '').substring(0, 40);

    a.onloadedmetadata = function() {
      id('pfTempo').textContent = '0:00 / ' + formattaTempoPlayer(a.duration);
    };
    a.ontimeupdate = function() {
      var cur = a.currentTime || 0;
      var dur = a.duration || 0;
      id('pfTempo').textContent = formattaTempoPlayer(cur) + ' / ' + formattaTempoPlayer(dur);
      if (dur > 0) id('pfBarFill').style.width = (cur / dur * 100) + '%';
    };
    a.onended = function() {
      id('pfPlay').textContent = '\u25B6\uFE0F';
    };
  }).catch(function() {});
}

function pfAggiorna() {
  if (pfNote.length === 0) {
    id('pfNotaInfo').textContent = 'Nessuna nota';
    return;
  }
  if (pfIndice < 0) pfIndice = pfNote.length - 1;
  var n = pfNote[pfIndice];
  id('pfNotaInfo').textContent = n.data + ' \u2014 ' + (n.trascrizione || '').substring(0, 40);
}

function pfPlayPausa() {
  var a = id('pfAudio');
  if (!a.src) { pfCaricaAudio(); return; }
  if (a.paused) {
    a.play();
    id('pfPlay').textContent = '\u23F8\uFE0F';
  } else {
    a.pause();
    id('pfPlay').textContent = '\u25B6\uFE0F';
  }
}

function pfIniziaHold(direzione) {
  pfDirezione = direzione;
  pfStaHold = false;
  pfHoldTimer = setTimeout(function() {
    pfStaHold = true;
    var a = id('pfAudio');
    pfHoldInterval = setInterval(function() {
      var nuova = a.currentTime + direzione * 0.5;
      a.currentTime = Math.max(0, Math.min(a.duration || 0, nuova));
    }, 100);
  }, 350);
}

function pfFermaHold() {
  if (pfHoldTimer) { clearTimeout(pfHoldTimer); pfHoldTimer = null; }
  if (pfHoldInterval) { clearInterval(pfHoldInterval); pfHoldInterval = null; }
  if (!pfStaHold && pfDirezione !== 0) {
    if (pfDirezione < 0 && pfIndice > 0) pfSelezionaNota(pfIndice - 1);
    else if (pfDirezione > 0 && pfIndice < pfNote.length - 1) pfSelezionaNota(pfIndice + 1);
  }
  pfStaHold = false;
  pfDirezione = 0;
}

function pfElaboraNota(notaId) {
  fetch('/api/note_vocali/' + notaId + '/elabora', {method:'POST'})
    .then(function(r) { return r.json(); }).then(function(res) {
      if (res.success) {
        parla(res.message || 'Comando elaborato');
        mostraVocePanel('info', res.message || 'Elaborato');
        caricaDati();
        pfCaricaLista();
      } else {
        parla('Errore: ' + (res.error || '?'));
      }
    }).catch(function() {});
}

function pfEliminaNota(notaId) {
  if (!confirm('Eliminare questa nota vocale?')) return;
  fetch('/api/note_vocali?id=' + notaId, {method:'DELETE'}).then(function() {
    pfIndice = -1;
    pfCaricaLista();
  });
}

// ============================================================
// ON AIR con wakeword (pagina Comandi)
// ============================================================
var onAirPaginaAttivo = false;
var onAirPaginaStream = null;
var onAirPaginaCtx = null;
var onAirPaginaProc = null;
var onAirPaginaSource = null;
var onAirPaginaCampioni = [];
var onAirPaginaSilenzioTimer = null;
var onAirPaginaMsParlato = 0;
var onAirPaginaSRNativo = 48000;

var ONAIR_SOGLIA = 0.014;
var ONAIR_SILENZIO_MS = 1200;
var ONAIR_MIN_FRASE_MS = 400;

function toggleOnAir() {
  // Ponte: porta alla pagina Comandi e attiva ON AIR
  mostra('comandi');
  setTimeout(function(){ toggleOnAirPagina(); }, 200);
}

function toggleOnAirPagina() {
  if (onAirPaginaAttivo) fermaOnAirPagina();
  else avviaOnAirPagina();
}

function avviaOnAirPagina() {
  navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream) {
    onAirPaginaAttivo = true;
    onAirPaginaStream = stream;
    onAirPaginaCtx = new (window.AudioContext || window.webkitAudioContext)();
    onAirPaginaSRNativo = onAirPaginaCtx.sampleRate;
    onAirPaginaSource = onAirPaginaCtx.createMediaStreamSource(stream);
    onAirPaginaCampioni = [];
    onAirPaginaMsParlato = 0;
    onAirPaginaProc = onAirPaginaCtx.createScriptProcessor(4096, 1, 1);
    onAirPaginaProc.onaudioprocess = onAirProcessor;
    var gain = onAirPaginaCtx.createGain();
    gain.gain.value = 0;
    onAirPaginaSource.connect(onAirPaginaProc);
    onAirPaginaProc.connect(gain);
    gain.connect(onAirPaginaCtx.destination);

    id('btnOnAirPagina').textContent = '\u23F8\uFE0F DISATTIVA ON AIR';
    id('btnOnAirPagina').classList.remove('btn-green');
    id('btnOnAirPagina').classList.add('btn-red');
    id('onAirStato').style.display = 'block';
    id('onAirStatoTesto').innerHTML = '\uD83D\uDD34 In ascolto... pronuncia <strong>BRAAAP</strong> + comando';
    parla('ON AIR attivato');
  }).catch(function(err) {
    alert('Errore microfono: ' + err.message);
  });
}

function fermaOnAirPagina() {
  onAirPaginaAttivo = false;
  if (onAirPaginaSilenzioTimer) { clearTimeout(onAirPaginaSilenzioTimer); onAirPaginaSilenzioTimer = null; }
  if (onAirPaginaProc) { onAirPaginaProc.disconnect(); onAirPaginaProc.onaudioprocess = null; onAirPaginaProc = null; }
  if (onAirPaginaSource) { onAirPaginaSource.disconnect(); onAirPaginaSource = null; }
  if (onAirPaginaStream) { onAirPaginaStream.getTracks().forEach(function(t){t.stop();}); onAirPaginaStream = null; }
  if (onAirPaginaCtx) { onAirPaginaCtx.close(); onAirPaginaCtx = null; }

  id('btnOnAirPagina').textContent = '\u25B6\uFE0F ATTIVA ON AIR';
  id('btnOnAirPagina').classList.remove('btn-red');
  id('btnOnAirPagina').classList.add('btn-green');
  id('onAirStato').style.display = 'none';
  parla('ON AIR disattivato');
}

function onAirProcessor(e) {
  var input = e.inputBuffer.getChannelData(0);
  var rms = 0;
  for (var i = 0; i < input.length; i++) rms += input[i] * input[i];
  rms = Math.sqrt(rms / input.length);
  var bloccoMs = (input.length / onAirPaginaSRNativo) * 1000;

  onAirPaginaCampioni.push(new Float32Array(input));

  if (rms > ONAIR_SOGLIA) {
    onAirPaginaMsParlato += bloccoMs;
    if (onAirPaginaSilenzioTimer) { clearTimeout(onAirPaginaSilenzioTimer); onAirPaginaSilenzioTimer = null; }
  } else if (onAirPaginaMsParlato >= ONAIR_MIN_FRASE_MS && !onAirPaginaSilenzioTimer) {
    onAirPaginaSilenzioTimer = setTimeout(function() {
      onAirPaginaSilenzioTimer = null;
      finalizzaOnAir();
    }, ONAIR_SILENZIO_MS);
  }
}

function finalizzaOnAir() {
  var chunk = onAirPaginaCampioni;
  onAirPaginaCampioni = [];
  onAirPaginaMsParlato = 0;
  if (chunk.length === 0) return;

  var uniti = uniscCampioni(chunk);
  var ricamp = ricampiona(uniti, onAirPaginaSRNativo, 16000);
  if (ricamp.length < 16000 * 0.4) return;
  var wav = codificaWav(ricamp, 16000);

  var form = new FormData();
  form.append('audio', wav, 'comando.wav');
  form.append('modalita', 'onair');

  id('onAirStatoTesto').innerHTML = '\u23F3 Elaboro...';
  fetch('/api/trascrivi', {method:'POST', body:form})
    .then(function(r) { return r.json(); })
    .then(function(res) {
      if (!res.success) {
        id('onAirStatoTesto').innerHTML = '\uD83D\uDD34 In ascolto... pronuncia <strong>BRAAAP</strong> + comando';
        return;
      }
      id('onAirStatoTesto').innerHTML = '\u2705 ' + res.message;
      parla(res.message || 'Comando eseguito');
      mostraVocePanel(res.tipo_azione === 'evento' ? 'evento' :
                       res.tipo_azione === 'movimento' ? 'movimento' : 'task',
                       res.message, res.trascrizione);

      var form2 = new FormData();
      form2.append('audio', wav, 'nota.wav');
      form2.append('trascrizione', res.trascrizione || '');
      form2.append('durata', String(ricamp.length / 16000));
      fetch('/api/note_vocali', {method:'POST', body:form2}).then(function() {
        pfCaricaLista();
      });

      caricaDati();
      setTimeout(function() {
        if (onAirPaginaAttivo) {
          id('onAirStatoTesto').innerHTML = '\uD83D\uDD34 In ascolto... pronuncia <strong>BRAAAP</strong> + comando';
        }
      }, 3000);
    })
    .catch(function() {
      id('onAirStatoTesto').innerHTML = '\u26A0\uFE0F Errore di rete';
    });
}

// ============================================================
// FILTRO COMANDI + CRONOLOGIA
// ============================================================
function filtraComandi() {
  var q = (id('cercaComando').value || '').toLowerCase();
  document.querySelectorAll('.comando-item').forEach(function(el) {
    var testo = (el.getAttribute('data-testo') || '') + ' ' + el.textContent.toLowerCase();
    el.style.display = testo.indexOf(q) >= 0 ? 'block' : 'none';
  });
}

function caricaCronologia() {
  var c = id('cronologiaComandi');
  if (!c) return;
  fetch('/api/note_vocali').then(function(r) { return r.json(); }).then(function(lista) {
    var recenti = (lista || []).slice(-10).reverse();
    var html = '';
    recenti.forEach(function(n) {
      var stato = n.elaborata ? '\u2705' : '\uD83C\uDD95';
      html += '<div style="padding:6px 0;border-bottom:1px solid var(--border);font-size:13px">' +
              stato + ' ' + (n.data || '') + ' \u2014 ' + (n.trascrizione || '(vuoto)') + '</div>';
    });
    if (!html) html = '<div style="color:var(--text-muted);text-align:center;padding:8px">Nessun comando registrato</div>';
    c.innerHTML = html;
  }).catch(function() {});
}

// Collega touch ai pulsanti player fisso
(function collegaTouchPlayerFisso() {
  function collega() {
    var b1 = id('pfIndietro'), b2 = id('pfAvanti');
    if (!b1 || !b2 || b1.dataset.touchCollegato) return;
    b1.dataset.touchCollegato = '1';
    b2.dataset.touchCollegato = '1';
    var coppie = [[b1, -1], [b2, 1]];
    coppie.forEach(function(coppia) {
      var btn = coppia[0], dir = coppia[1];
      btn.addEventListener('touchstart', function(e) { e.preventDefault(); pfIniziaHold(dir); }, {passive: false});
      btn.addEventListener('touchend', function(e) { e.preventDefault(); pfFermaHold(); }, {passive: false});
      btn.addEventListener('touchcancel', function(e) { e.preventDefault(); pfFermaHold(); }, {passive: false});
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', collega);
  else collega();
})();

// Inizializza al caricamento
pfCaricaLista();
caricaCronologia();


// ============================================================
// PAGINA ESPORTA
// ============================================================
var SEZIONI_ESPORTA = [
  {id:'eventi',    nome:'📅 Eventi',     desc:'Tutti gli eventi con conteggi'},
  {id:'scuole',    nome:'🏫 Scuole',     desc:'Anagrafica scuole'},
  {id:'rubrica',   nome:'📞 Rubrica',    desc:'Contatti con telefono/email'},
  {id:'task',      nome:'✅ Task',       desc:'Task e scadenze'},
  {id:'magazzino', nome:'📦 Magazzino',  desc:'Movimenti di carico/scarico'},
  {id:'inventario',nome:'🧰 Inventario', desc:'Oggetti con valore'},
  {id:'entita',    nome:'🎁 Materiali',  desc:'Entità dinamiche'},
  {id:'liste',     nome:'🛒 Liste',      desc:'Liste e prodotti'},
  {id:'portafoglio',nome:'📈 Portafoglio',desc:'Titoli e variazioni'}
];

function renderEsporta() {
  var g = id('grigliaEsporta');
  if (!g) return;
  g.innerHTML = '';
  SEZIONI_ESPORTA.forEach(function(s){
    var d = document.createElement('div');
    d.style.cssText = 'background:var(--bg);border-radius:10px;padding:14px;display:flex;flex-direction:column;gap:8px';
    d.innerHTML =
      '<div><strong style="font-size:15px">'+s.nome+'</strong>' +
      '<div style="font-size:12px;color:var(--text-muted);margin-top:2px">'+s.desc+'</div></div>' +
      '<div style="display:flex;gap:6px;flex-wrap:wrap">' +
        '<button class="btn btn-green" onclick="esportaSezione(\''+s.id+'\',\'excel\')" style="font-size:12px;padding:6px 10px">📊 Excel</button>' +
        '<button class="btn btn-blue" onclick="esportaSezione(\''+s.id+'\',\'csv\')" style="font-size:12px;padding:6px 10px">📄 CSV</button>' +
        '<button class="btn btn-gray" onclick="esportaSezione(\''+s.id+'\',\'json\')" style="font-size:12px;padding:6px 10px">🔧 JSON</button>' +
      '</div>';
    g.appendChild(d);
  });
  popolaAnniEsporta();
  caricaListaBackup();
}

function popolaAnniEsporta() {
  var sel = id('esportaAnno');
  if (!sel) return;
  var anni = [];
  (STATO.eventi||[]).forEach(function(e){
    var a = (e.data||'').split('-')[0];
    if (a && anni.indexOf(a) === -1) anni.push(a);
  });
  anni.sort().reverse();
  sel.innerHTML = '<option value="">Tutti gli anni</option>';
  anni.forEach(function(a){ sel.innerHTML += '<option value="'+a+'">'+a+'</option>'; });
}

function esportaSezione(sezione, formato) {
  var anno = id('esportaAnno') ? id('esportaAnno').value : '';
  var url = '/api/esporta/' + sezione + '.' + formato;
  if (anno) url += '?anno=' + anno;
  window.location.href = url;
}

function esportaTutto() {
  var anno = id('esportaAnno') ? id('esportaAnno').value : '';
  var url = '/api/esporta/tutto.excel';
  if (anno) url += '?anno=' + anno;
  window.location.href = url;
}

function forzaBackupOra() {
  fetch('/api/backup/ora', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({motivo: 'manuale'})
  })
  .then(function(r){ return r.json(); })
  .then(function(res){
    if (res.success) {
      var msg = '✅ Backup creato!\n\n';
      msg += 'Locale: ' + (res.locale || '-') + '\n';
      if (res.cloud) msg += 'Cloud: ' + res.cloud + '\n';
      alert(msg);
      caricaListaBackup();
    } else {
      alert('❌ ' + (res.error || '?'));
    }
  })
  .catch(function(e){ alert('Errore di rete: ' + e.message); });
}

function caricaListaBackup() {
  var c = id('listaBackup');
  if (!c) return;
  fetch('/api/backup/lista')
    .then(function(r){ return r.json(); })
    .then(function(lista){
      if (!lista || lista.length === 0) {
        c.innerHTML = '<div style="color:var(--text-muted);padding:10px">Nessun backup ancora. I backup automatici partono dopo 10 modifiche.</div>';
        aggiornaStatBackup(lista || []);
        return;
      }
      aggiornaStatBackup(lista);
      var html = '<div style="overflow-x:auto"><table><thead><tr><th>Data</th><th>Motivo</th><th>Dimensione</th><th>Contenuto</th><th>Azioni</th></tr></thead><tbody>';
      lista.forEach(function(b){
        var motivo = b.motivo || 'auto';
        var badgeClass = 'badge-gray';
        if (motivo === 'manuale') badgeClass = 'badge-blue';
        else if (motivo === 'avvio' || motivo === 'avvio_iniziale') badgeClass = 'badge-green';
        else if (motivo.indexOf('pre_') === 0 || motivo.indexOf('azzera') >= 0) badgeClass = 'badge-red';
        else if (motivo === 'auto') badgeClass = 'badge-purple';

        var dim = b.dimensione ? (b.dimensione/1024/1024).toFixed(2)+' MB' : '-';
        var contenuto = '';
        if (b.eventi !== undefined) contenuto += b.eventi+' ev';
        if (b.scuole !== undefined) contenuto += ' · '+b.scuole+' sc';
        if (b.rubrica !== undefined) contenuto += ' · '+b.rubrica+' ru';
        if (!contenuto) contenuto = '-';
        var cloudIcon = b.cloud ? ' ☁️' : '';

        html += '<tr>'
          + '<td>'+ (b.data || b.data_file || '-') +'</td>'
          + '<td><span class="badge '+badgeClass+'">'+motivo+'</span></td>'
          + '<td>'+dim+'</td>'
          + '<td style="font-size:12px;color:var(--text-muted)">'+contenuto+cloudIcon+'</td>'
          + '<td style="white-space:nowrap">'
          + '<button class="btn btn-blue" title="Scarica" onclick="scaricaBackupUI(\'' + b.nome + '\')" style="padding:4px 10px;font-size:12px">⬇️</button> '
          + '<button class="btn btn-green" title="Ripristina" onclick="ripristinaBackupUI(\'' + b.nome + '\')" style="padding:4px 10px;font-size:12px">🔄</button> '
          + '<button class="btn btn-red" title="Elimina" onclick="eliminaBackupUI(\'' + b.nome + '\')" style="padding:4px 10px;font-size:12px">🗑️</button>'
          + '</td>'
          + '</tr>';
      });
      html += '</tbody></table></div>';
      c.innerHTML = html;
    })
    .catch(function(){ c.innerHTML = '<div style="color:#DC2626">Errore nel caricamento</div>'; });
}

function aggiornaStatBackup(lista) {
  var n = lista.length;
  var tot = 0;
  lista.forEach(function(b){ tot += (b.dimensione || 0); });
  var el1 = id('statNBackup');
  var el2 = id('statDimBackup');
  var el3 = id('statUltimoBackup');
  if (el1) el1.textContent = n;
  if (el2) el2.textContent = (tot/1024/1024).toFixed(2)+' MB';
  if (el3) el3.textContent = n > 0 ? (lista[0].data || lista[0].data_file || '-') : 'mai';
}

function ripristinaBackupUI(nome) {
  if (!confirm('ATTENZIONE!\n\nStai per RIPRISTINARE il backup:\n' + nome + '\n\nTutti i dati attuali verranno SOSTITUITI con quelli del backup.\n\nUn backup di sicurezza dello stato attuale verrà creato automaticamente.\n\nContinuare?')) return;
  var risposta = prompt('Per confermare, scrivi esattamente:\n\nRIPRISTINA');
  if (risposta !== 'RIPRISTINA') { alert('Conferma errata.'); return; }
  fetch('/api/backup/ripristina', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({nome: nome, conferma: 'RIPRISTINA'})
  })
  .then(function(r){ return r.json(); })
  .then(function(res){
    if (res.success) {
      alert('✅ Ripristinato!\n\n' + res.message + '\n\nBackup di sicurezza: ' + (res.backup_sicurezza || '-') + '\n\nLa pagina verrà ricaricata.');
      location.reload();
    } else {
      alert('❌ Errore: ' + (res.error || '?'));
    }
  })
  .catch(function(e){ alert('Errore di rete: ' + e.message); });
}

function scaricaBackupUI(nome) {
  window.location.href = '/api/backup/scarica/' + encodeURIComponent(nome);
}

function eliminaBackupUI(nome) {
  if (!confirm('Eliminare il backup?\n\n' + nome + '\n\nL\'operazione è irreversibile.')) return;
  fetch('/api/backup/elimina', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({nome: nome})
  })
  .then(function(r){ return r.json(); })
  .then(function(res){
    if (res.success) { caricaListaBackup(); }
    else { alert('❌ Errore: ' + (res.error || '?')); }
  });
}

function caricaBackupDaFile(files) {
  if (!files || !files.length) return;
  var f = files[0];
  if (!f.name.endsWith('.json')) { alert('Seleziona un file .json'); return; }
  if (!confirm('Caricare il backup\n\n' + f.name + '\n\nnel sistema? Verrà aggiunto alla lista backup.')) return;
  var form = new FormData();
  form.append('file', f);
  fetch('/api/backup/carica', {method:'POST', body: form})
    .then(function(r){ return r.json(); })
    .then(function(res){
      if (res.success) {
        alert('✅ Backup caricato: ' + res.nome);
        caricaListaBackup();
      } else {
        alert('❌ ' + (res.error || '?'));
      }
    });
}

function pulisciBackupUI() {
  if (!confirm('Applicare la rotazione gerarchica?\n\nVerranno eliminati i backup più vecchi secondo la regola:\n7 giorni + 4 settimane + 12 mesi.')) return;
  fetch('/api/backup/pulisci', {method:'POST'})
    .then(function(r){ return r.json(); })
    .then(function(res){
      if (res.success) { alert('✅ Pulizia completata'); caricaListaBackup(); }
      else { alert('❌ ' + (res.error || '?')); }
    });
}

function apriCartellaBackup() {
  fetch('/api/backup/apri-cartella', {method:'POST'})
    .then(function(r){ return r.json(); })
    .then(function(res){
      if (!res.success) alert('❌ ' + (res.error || '?'));
    })
    .catch(function(e){ alert('Errore: ' + e.message); });
}

function apriCartellaExtra() {
  fetch('/api/backup/apri-cartella-extra', {method:'POST'})
    .then(function(r){ return r.json(); })
    .then(function(res){
      if (!res.success) alert('❌ ' + (res.error || '?'));
    })
    .catch(function(e){ alert('Errore: ' + e.message); });
}

function salvaConfigBackup() {
  var path = (id('configCartellaExtra').value || '').trim();
  fetch('/api/backup/config', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({cartella_extra: path})
  })
  .then(function(r){ return r.json(); })
  .then(function(res){
    if (res.success) {
      alert('✅ Configurazione salvata');
      aggiornaConfigBackup();
    } else {
      alert('❌ ' + (res.error || '?'));
    }
  });
}

function aggiornaConfigBackup() {
  fetch('/api/backup/config')
    .then(function(r){ return r.json(); })
    .then(function(res){
      var input = id('configCartellaExtra');
      var stato = id('statoCartellaExtra');
      if (!input) return;
      input.value = res.cartella_extra || '';
      if (stato) {
        if (res.cartella_extra) {
          if (res.esiste) {
            stato.innerHTML = '✅ Cartella configurata: <code>' + res.cartella_extra + '</code> (' + (res.n_files || 0) + ' file)';
            stato.style.color = '#16A34A';
          } else {
            stato.innerHTML = '⚠️ Cartella non ancora creata: <code>' + res.cartella_extra + '</code>';
            stato.style.color = '#d97706';
          }
        } else {
          stato.textContent = 'ℹ️ Nessuna cartella extra configurata (solo backup locali)';
          stato.style.color = 'var(--text-muted)';
        }
      }
    })
    .catch(function(){});
}

// Hook nella funzione mostra() per inizializzare la pagina
(function() {
  var originalMostra = window.mostra;
  window.mostra = function(pagina) {
    originalMostra(pagina);
    if (pagina === 'esporta') {
      try { renderEsporta(); } catch(e) { console.warn('renderEsporta:', e); }
      try { caricaListaBackup(); } catch(e) { console.warn('caricaListaBackup:', e); }
      try { aggiornaConfigBackup(); } catch(e) { console.warn('aggiornaConfigBackup:', e); }
    }
  };
})();




// ============================================================
// AZZERA EVENTI — con doppia conferma
// ============================================================
function azzeraEventiConferma() {
  var n = (STATO.eventi || []).length;
  if (n === 0) {
    alert('Non ci sono eventi da azzerare.');
    return;
  }
  var msg = 'ATTENZIONE!\n\n' +
            'Stai per cancellare ' + n + ' eventi.\n\n' +
            'NON verranno toccati:\n' +
            '  - Scuole\n' +
            '  - Stock / Magazzino\n' +
            '  - Rubrica\n' +
            '  - Task, Entita, Movimenti\n' +
            '  - Note vocali, Post-it, Liste\n\n' +
            'Un backup automatico verra salvato prima di procedere.\n\n' +
            'Continuare?';
  if (!confirm(msg)) return;

  var risposta = prompt('Per confermare definitivamente, scrivi esattamente:\n\nAZZERA_SOLO_EVENTI');
  if (risposta !== 'AZZERA_SOLO_EVENTI') {
    alert('Conferma errata. Operazione annullata.');
    return;
  }

  fetch('/api/manutenzione/azzera_eventi', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({conferma: 'AZZERA_SOLO_EVENTI'})
  })
  .then(function(r) { return r.json(); })
  .then(function(res) {
    if (res.success) {
      alert('Fatto!\n\n' +
            'Eventi cancellati: ' + res.eventi_cancellati + '\n' +
            'Backup salvato in: ' + res.backup_salvato + '\n\n' +
            'Stock invariato: ' + JSON.stringify(res.stock_invariato) + '\n' +
            'Scuole invariate: ' + res.scuole_invariate);
      caricaDati();
    } else {
      alert('Errore: ' + (res.error || 'sconosciuto'));
    }
  })
  .catch(function(err) {
    alert('Errore di rete: ' + err.message);
  });
}

// ============================================================
// VOCI COSTI E RICAVI EVENTO
// ============================================================
var _vociCostiEvento = [];
var _vociRicaviEvento = [];

var CATEGORIE_COSTI = ['Materiale / Gadget', 'Animazione / Spettacolo', 'Service Audio / Luci', 'Allestimento / Noleggio', 'Stampa / Grafica', 'Trasporti / Carburante', 'Vitto / Ospitalità', 'Assicurazione / Permessi', 'Collaboratori / Staff', 'Premi / Coppe', 'Altro'];
var CATEGORIE_RICAVI = ['Contributo Scuola / Ente', 'Biglietti / Iscrizioni', 'Sponsorizzazione', 'Patrocinio / Bando', 'Servizi esterni', 'Rimborsi spese', 'Donazioni', 'Altro'];

function _nuovaVoceEvento() {
  return { id: Date.now() + Math.floor(Math.random() * 1000), descrizione: '', categoria: '', quantita: 1, prezzo_unitario: 0, note: '' };
}

function _formattaEuro(n) {
  return (parseFloat(n) || 0).toFixed(2).replace('.', ',') + ' €';
}

function aggiungiVoceCosto() {
  _vociCostiEvento.push(_nuovaVoceEvento());
  renderListaVociEvento('costi');
}

function aggiungiVoceRicavo() {
  _vociRicaviEvento.push(_nuovaVoceEvento());
  renderListaVociEvento('ricavi');
}

function rimuoviVoceCosto(idx) {
  _vociCostiEvento.splice(idx, 1);
  renderListaVociEvento('costi');
}

function rimuoviVoceRicavo(idx) {
  _vociRicaviEvento.splice(idx, 1);
  renderListaVociEvento('ricavi');
}

function renderListaVociEvento(tipo) {
  var isCosti = (tipo === 'costi'), voci = isCosti ? _vociCostiEvento : _vociRicaviEvento, categorie = isCosti ? CATEGORIE_COSTI : CATEGORIE_RICAVI;
  var container = document.getElementById(isCosti ? 'listaCostiEvento' : 'listaRicaviEvento'); if (!container) return;
  if (voci.length === 0) { container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:6px">Nessuna voce inserita</div>'; calcolaTotaliEvento(); return; }
  var html = '';
  voci.forEach(function(v, idx) {
    var valAtt = v.categoria || v.descrizione || '', opzioni = '<option value="">— Seleziona voce —</option>', trovato = false;
    categorie.forEach(function(c) { var sel = (valAtt === c); if (sel) trovato = true; opzioni += '<option value="' + c + '"' + (sel ? ' selected' : '') + '>' + c + '</option>'; });
    if (valAtt && !trovato) opzioni += '<option value="' + valAtt.replace(/"/g, '&quot;') + '" selected>' + valAtt + '</option>';
    var tot = (parseFloat(v.quantita) || 0) * (parseFloat(v.prezzo_unitario) || 0);
    html += '<div style="display:grid;grid-template-columns:1fr 68px 92px 92px 32px;gap:8px;margin-bottom:8px;align-items:center">' +
      '<select style="width:100%;min-width:180px" onchange="aggiornaVoce(\'' + tipo + '\',' + idx + ',\'categoria\',this.value);aggiornaVoce(\'' + tipo + '\',' + idx + ',\'descrizione\',this.value)">' + opzioni + '</select>' +
      '<input type="number" min="0" step="1" placeholder="Qtà" value="' + (v.quantita || 1) + '" oninput="aggiornaVoce(\'' + tipo + '\',' + idx + ',\'quantita\',this.value)">' +
      '<input type="text" inputmode="decimal" placeholder="0,00" value="' + (v.prezzo_unitario ? String(v.prezzo_unitario).replace('.',',') : '') + '" oninput="aggiornaVoce(\'' + tipo + '\',' + idx + ',\'prezzo_unitario\',this.value)">' +
      '<div id="totaleVoce_' + tipo + '_' + idx + '" style="text-align:right;font-weight:700;font-size:13px">' + _formattaEuro(tot) + '</div>' +
      '<button type="button" onclick="rimuoviVoce' + (isCosti ? 'Costo' : 'Ricavo') + '(' + idx + ')" style="background:none;border:none;color:#DC2626;cursor:pointer;font-size:16px">✕</button></div>';
  });
  container.innerHTML = html; calcolaTotaliEvento();
}

function aggiornaVoce(tipo, idx, campo, valore) {
  var voci = (tipo === 'costi') ? _vociCostiEvento : _vociRicaviEvento;
  if (!voci[idx]) return;
  if (campo === 'quantita') voci[idx][campo] = parseFloat(valore) || 0;
  else if (campo === 'prezzo_unitario') voci[idx][campo] = parseFloat(valore) || 0;
  else voci[idx][campo] = valore;
  if (campo === 'quantita' || campo === 'prezzo_unitario') {
    var elTot = document.getElementById('totaleVoce_' + tipo + '_' + idx);
    if (elTot) {
      var v = voci[idx];
      var tot = (parseFloat(v.quantita) || 0) * (parseFloat(v.prezzo_unitario) || 0);
      elTot.textContent = _formattaEuro(tot);
    }
    calcolaTotaliEvento();
  }
}

function _totaleVoci(voci) {
  var t = 0;
  voci.forEach(function(v) {
    t += (parseFloat(v.quantita) || 0) * (parseFloat(v.prezzo_unitario) || 0);
  });
  return t;
}

function calcolaTotaliEvento() {
  var totCosti = _totaleVoci(_vociCostiEvento);
  var totRicavi = _totaleVoci(_vociRicaviEvento);
  var margine = totRicavi - totCosti;

  var elCosti = document.getElementById('totaleCostiEvento');
  var elRicavi = document.getElementById('totaleRicaviEvento');
  var elMargine = document.getElementById('margineEvento');

  if (elCosti) elCosti.textContent = _formattaEuro(totCosti);
  if (elRicavi) elRicavi.textContent = _formattaEuro(totRicavi);
  if (elMargine) {
    elMargine.textContent = (margine >= 0 ? '+' : '') + _formattaEuro(margine);
    elMargine.style.color = margine >= 0 ? '#16A34A' : '#DC2626';
  }
}


// ============================================================
// Correttore automatico ortografico (Groq)
// ============================================================
async function correggiTesto(testo) {
    if (!testo || !testo.trim()) return testo;
    try {
        const res = await fetch('/api/correggi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ testo })
        });
        const data = await res.json();
        return data.success ? data.corretto : testo;
    } catch (err) {
        console.warn('Correttore non disponibile:', err);
        return testo;
    }
}

// Collega automaticamente il correttore a tutti i campi marcati
// con l'attributo data-correttore="true"
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-correttore="true"]').forEach(el => {
        el.addEventListener('blur', async (e) => {
            const originale = e.target.value;
            if (!originale.trim() || originale.length < 3) return;
            const corretto = await correggiTesto(originale);
            if (corretto && corretto !== originale) {
                e.target.value = corretto;
                e.target.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
    });
});

// ============================================================
// Calcolo automatico Data fine / Durata evento
// ============================================================
function aggiornaDataFine() {
    const dataInizio = document.getElementById('eData')?.value;
    const durata = parseInt(document.getElementById('eDurata')?.value) || 1;
    const eDataFine = document.getElementById('eDataFine');
    if (!eDataFine) return;

    if (!dataInizio) {
        eDataFine.value = '';
        return;
    }
    const d = new Date(dataInizio + 'T00:00:00');
    d.setDate(d.getDate() + durata - 1);  // -1 perché il giorno di inizio conta
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    eDataFine.value = `${yyyy}-${mm}-${dd}`;
}

// Collega gli eventi ai campi (quando la modale si apre)
document.addEventListener('DOMContentLoaded', () => {
    const eData = document.getElementById('eData');
    const eDurata = document.getElementById('eDurata');
    if (eData) eData.addEventListener('change', aggiornaDataFine);
    if (eData) eData.addEventListener('input', aggiornaDataFine);
    if (eDurata) eDurata.addEventListener('input', aggiornaDataFine);
});
// ============================================================
// FIX #5 - Modifica e cancellazione movimenti magazzino
// ============================================================

function modificaMovimento(movId, categoria) {
  var mov = null;
  (STATO.movimenti[categoria] || []).forEach(function(m) {
    if (m.id === movId) mov = m;
  });
  if (!mov) {
    // Se non trovato in STATO.movimenti, cerca nei dati del magazzino
    alert('Movimento non trovato. Ricarica la pagina.');
    return;
  }

  document.getElementById('movId').value = mov.id;
  document.getElementById('movCatOld').value = categoria;
  document.getElementById('movTipo').value = mov.tipo;
  document.getElementById('movCategoria').value = categoria;
  document.getElementById('movQuantita').value = mov.quantita;
  document.getElementById('movData').value = mov.data || '';
  document.getElementById('movMotivo').value = mov.motivo || '';
  document.getElementById('movNota').value = mov.nota_carico || '';
  document.getElementById('movPrezzoUnit').value = mov.prezzo_unitario || 0;
  document.getElementById('modaleMovTitolo').textContent = '✏️ Modifica movimento';
  apriModale('modaleMovimento');
}

function apriModaleNuovoMovimento() {
  id('movId').value = '';
  id('movCatOld').value = '';
  id('movTipo').value = 'carico';
  id('movCategoria').value = 'braccialetti';
  id('movQuantita').value = 1;
  id('movData').value = new Date().toISOString().split('T')[0];
  id('movMotivo').value = '';
  id('movNota').value = '';
  id('modaleMovTitolo').textContent = '➕ Nuovo movimento';
  apriModale('modaleMovimento');
}

async function salvaMovimento() {
  var movId = id('movId').value ? parseInt(id('movId').value) : null;
  var catOld = id('movCatOld').value;
  var puEl = document.getElementById('movPrezzoUnit');
  var corpo = {
    tipo: id('movTipo').value,
    categoria: id('movCategoria').value,
    quantita: parseInt(id('movQuantita').value) || 0,
    prezzo_unitario: puEl ? _parseFloatIt(puEl.value) : 0,
    data: id('movData').value,
    motivo: (id('movMotivo').value || '').trim(),
    nota_carico: (id('movNota').value || '').trim()
  };

  if (movId) {
    corpo.id = movId;
    corpo.categoria_old = catOld;
    await fetch('/api/movimenti', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(corpo)
    });
  } else {
    await fetch('/api/movimenti', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(corpo)
    });
  }
  chiudiModale('modaleMovimento');
  caricaDati();
}

async function eliminaMovimento(id, categoria) {
  if (!confirm('Eliminare questo movimento? Lo stock verra ricalcolato.')) return;
  try {
    var r = await fetch('/api/movimenti?id=' + encodeURIComponent(id) + '&categoria=' + encodeURIComponent(categoria), { method: 'DELETE' });
    var res = await r.json();
    if (!res.success) { alert('Errore eliminazione: ' + (res.error || 'Movimento non trovato')); return; }
    await caricaDati();
    if (typeof caricaStoricoMovimenti === 'function') await caricaStoricoMovimenti();
    if (typeof renderBilancioMagazzino === 'function') await renderBilancioMagazzino();
  } catch (e) {
    alert('Errore di rete: ' + e.message);
  }
}
// ============================================================
// TRACCIABILITÀ MAGAZZINO - Eventi/Scuole/Destinatario
// ============================================================

function popolaFiltriMovimenti() {
  var selEv = id('filtroMovEvento');
  var selSc = id('filtroMovScuola');
  if (selEv) {
    var val = selEv.value;
    selEv.innerHTML = '<option value="">Tutti gli eventi</option>';
    (STATO.eventi || []).slice().sort(function(a,b){ return (b.data||'').localeCompare(a.data||''); }).forEach(function(e) {
      var sc = STATO.scuole.find(function(s){ return s.id === e.scuola_id; });
      var label = (e.data||'') + ' — ' + (e.iniziativa||'(senza titolo)') + (sc ? ' — ' + sc.nome : '');
      selEv.innerHTML += '<option value="' + e.id + '">' + label + '</option>';
    });
    selEv.value = val;
  }
  if (selSc) {
    var val2 = selSc.value;
    selSc.innerHTML = '<option value="">Tutte le scuole</option>';
    (STATO.scuole || []).forEach(function(s) {
      selSc.innerHTML += '<option value="' + s.id + '">' + s.nome + '</option>';
    });
    selSc.value = val2;
  }
}

function popolaSelectEventi() {
  var sel = id('movEvento');
  if (!sel) return;
  sel.innerHTML = '<option value="">— Nessun evento —</option>';
  (STATO.eventi || []).slice().sort(function(a,b){ return (b.data||'').localeCompare(a.data||''); }).forEach(function(e) {
    var sc = STATO.scuole.find(function(s){ return s.id === e.scuola_id; });
    var label = (e.data||'') + ' — ' + (e.iniziativa||'(senza titolo)') + (sc ? ' [' + sc.nome + ']' : '');
    sel.innerHTML += '<option value="' + e.id + '">' + label + '</option>';
  });
}

function popolaSelectScuole() {
  var sel = id('movScuola');
  if (!sel) return;
  sel.innerHTML = '<option value="">— Nessuna —</option>';
  (STATO.scuole || []).forEach(function(s) {
    sel.innerHTML += '<option value="' + s.id + '">' + s.nome + '</option>';
  });
}

function aggiornaScuolaDaEvento() {
  var evId = parseInt(id('movEvento').value) || null;
  if (!evId) return;
  var ev = STATO.eventi.find(function(e){ return e.id === evId; });
  if (ev && ev.scuola_id) {
    id('movScuola').value = ev.scuola_id;
  }
}

function _nomeEvento(evId) {
  if (!evId) return '';
  var ev = (STATO.eventi || []).find(function(e){ return e.id === evId; });
  if (!ev) return '?';
  var sc = STATO.scuole.find(function(s){ return s.id === ev.scuola_id; });
  return (ev.iniziativa || '(senza titolo)') + (sc ? ' — ' + sc.nome : '');
}

function _nomeScuola(scId) {
  if (!scId) return '';
  var sc = (STATO.scuole || []).find(function(s){ return s.id === scId; });
  return sc ? sc.nome : '?';
}
// ============================================================
// BILANCIO UNIFICATO - Magazzino, Materiali, Inventario
// ============================================================
async function caricaBilancio(sezione) {
  try {
    const r = await fetch('/api/bilancio/' + sezione);
    if (!r.ok) return null;
    return await r.json();
  } catch (e) {
    console.warn('Bilancio non disponibile per', sezione, e);
    return null;
  }
}

function _fmtEuro(n) {
  return (parseFloat(n) || 0).toFixed(2).replace('.', ',') + ' EUR';
}

function _renderBoxBilancio(containerId, bilancio, titolo) {
  var el = document.getElementById(containerId);
  if (!el) return;
  if (!bilancio) {
    el.innerHTML = '<div style="color:var(--text-muted);font-size:12px">Bilancio non disponibile</div>';
    return;
  }
  var html = '<div style="padding:14px;background:var(--bg);border-radius:10px;margin-bottom:12px">';
  html += '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">';
  html += '<div style="font-size:14px;font-weight:700;color:var(--accent)">' + titolo + '</div>';
  html += '<div style="font-size:20px;font-weight:800;color:#16A34A">' + _fmtEuro(bilancio.totale_valore) + '</div>';
  html += '</div>';
  html += '<div style="font-size:12px;color:var(--text-muted);margin-top:4px">' + (bilancio.voci ? bilancio.voci.length : 0) + ' voci &middot; ' + (bilancio.totale_quantita || 0) + ' pezzi totali</div>';
  html += '</div>';
  el.innerHTML = html;
}

async function renderBilancioMagazzino() {
  var b = await caricaBilancio('magazzino');
  _renderBoxBilancio('bilancioMagazzino', b, 'Bilancio Magazzino');
}

async function renderBilancioMateriali() {
  var b = await caricaBilancio('materiali');
  _renderBoxBilancio('bilancioMateriali', b, 'Bilancio Materiali');
}

async function renderBilancioInventario() {
  var b = await caricaBilancio('inventario');
  _renderBoxBilancio('bilancioInventario', b, 'Bilancio Inventario');
}
// ============================================================
// Hook: quando si mostra una pagina, aggiorna il bilancio
// ============================================================
(function() {
  if (typeof window.mostra !== 'function') return;
  var _originale = window.mostra;
  window.mostra = function(page) {
    var r = _originale.apply(this, arguments);
    try {
      if (page === 'magazzino' && typeof renderBilancioMagazzino === 'function') renderBilancioMagazzino();
      if (page === 'materiali' && typeof renderBilancioMateriali === 'function') renderBilancioMateriali();
      if (page === 'inventario' && typeof renderBilancioInventario === 'function') renderBilancioInventario();
    } catch (e) { console.warn('Bilancio hook:', e); }
    return r;
  };
})();
// ============================================================
// UI PROPOSTE ELABORA - Gestione azioni suggerite da Groq
// ============================================================
function renderProposteElabora(risultato) {
    var proposte = risultato.proposte || [];
    var chiarimenti = risultato.chiarimenti || [];
    var fonte = risultato.fonte || 'locale';

    var container = document.getElementById('elaboraProposte');
    if (!container) {
        container = document.createElement('div');
        container.id = 'elaboraProposte';
        container.style.cssText = 'margin-top:14px;padding:12px;border:2px dashed var(--accent);border-radius:10px;background:rgba(37,99,235,0.05)';
        var target = document.getElementById('elaboraTesto');
        if (target && target.parentNode) {
            target.parentNode.insertBefore(container, target.nextSibling);
        }
    }

    var html = '';

    // Header fonte
    html += '<div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">';
    html += 'Fonte: <strong>' + (fonte === 'groq' ? 'Groq AI' : 'Parser locale') + '</strong>';
    html += '</div>';

    // Chiarimenti
    if (chiarimenti.length > 0) {
        html += '<div style="padding:10px;background:#FEF3C7;border-radius:8px;margin-bottom:10px;border-left:4px solid #F59E0B">';
        html += '<div style="font-weight:700;color:#92400E;margin-bottom:4px">Chiarimenti richiesti:</div>';
        chiarimenti.forEach(function(c) {
            html += '<div style="font-size:13px;color:#78350F">- ' + c + '</div>';
        });
        html += '</div>';
    }

    // Proposte
    if (proposte.length > 0) {
        html += '<div style="font-weight:700;color:var(--accent);margin-bottom:8px">Proposte da applicare:</div>';
        proposte.forEach(function(p, i) {
            var tipo = p.tipo || '?';
            var icona = tipo === 'evento' ? 'Evento' : (tipo === 'movimento_magazzino' ? 'Movimento' : (tipo === 'task' ? 'Task' : tipo));
            html += '<div style="padding:8px;background:white;border-radius:6px;margin-bottom:6px;border:1px solid var(--border);display:flex;align-items:center;gap:8px">';
            html += '<input type="checkbox" class="chk-proposta" data-idx="' + i + '" checked style="width:auto">';
            html += '<div style="flex:1;font-size:13px">';
            html += '<strong>[' + icona + ']</strong> ';
            if (tipo === 'evento') {
                html += (p.iniziativa || 'Evento') + ' - ' + (p.data || '') + (p.scuola ? ' - ' + p.scuola : '');
            } else if (tipo === 'movimento_magazzino') {
                html += (p.tipo_movimento || '?') + ' ' + (p.quantita || 0) + ' ' + (p.categoria || '');
            } else if (tipo === 'task') {
                html += p.titolo || 'Task';
            } else {
                html += JSON.stringify(p);
            }
            html += '</div>';
            html += '</div>';
        });
        html += '<button class="btn btn-green" onclick="applicaProposteSelezionate()" style="margin-top:10px;width:100%">Applica proposte selezionate</button>';
        html += '<button class="btn btn-gray" onclick="document.getElementById(\'elaboraProposte\').innerHTML=\'\'" style="margin-top:6px;width:100%">Chiudi</button>';
    } else if (chiarimenti.length === 0) {
        html += '<div style="color:var(--text-muted);font-size:13px">Nessuna proposta da applicare.</div>';
    }

    container.innerHTML = html;
    window._proposteCorrenti = proposte;
}

async function applicaProposteSelezionate() {
    var checkboxes = document.querySelectorAll('.chk-proposta:checked');
    if (checkboxes.length === 0) {
        alert('Nessuna proposta selezionata');
        return;
    }

    var proposte = window._proposteCorrenti || [];
    var applicati = { eventi: 0, movimenti: 0, task: 0 };
    var errori = [];

    for (var i = 0; i < checkboxes.length; i++) {
        var idx = parseInt(checkboxes[i].getAttribute('data-idx'));
        var p = proposte[idx];
        if (!p) continue;

        try {
            var r = await fetch('/api/elabora/applica_proposta', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ azione: p })
            });
            var data = await r.json();
            if (data.success) {
                var a = data.applicati || {};
                applicati.eventi += a.eventi || 0;
                applicati.movimenti += a.movimenti || 0;
                applicati.task += a.task || 0;
            } else {
                errori.push(data.error || 'Errore sconosciuto');
            }
        } catch (e) {
            errori.push(String(e));
        }
    }

    var msg = 'Applicate:\n';
    msg += '- Eventi: ' + applicati.eventi + '\n';
    msg += '- Movimenti: ' + applicati.movimenti + '\n';
    msg += '- Task: ' + applicati.task;
    if (errori.length > 0) {
        msg += '\n\nErrori:\n' + errori.join('\n');
    }
    alert(msg);

    if (typeof caricaDati === 'function') caricaDati();
    var el = document.getElementById('elaboraProposte');
    if (el) el.innerHTML = '';
}
// ============================================================
// CHAT ASSISTENTE BRAAAP
// ============================================================
var _chatStorico = [];  // [{role:'user'|'assistant', content:'...'}]
var _chatAperta = false;

function toggleChat() {
  var pannello = document.getElementById('chatBraaap');
  if (!pannello) return;
  _chatAperta = !_chatAperta;
  if (_chatAperta) {
    pannello.classList.add('aperto');
    // Popola il selettore voci quando apri la chat (le voci potrebbero essere pronte ora)
    if (typeof _popolaSelettoreVoci === 'function') {
      _popolaSelettoreVoci();
    }
    setTimeout(function() {
      var inp = document.getElementById('chatInput');
      if (inp) inp.focus();
    }, 350);
  } else {
    pannello.classList.remove('aperto');
  }
}

function _aggiungiBolla(testo, ruolo) {
  var cont = document.getElementById('chatMessaggi');
  if (!cont) return;
  var div = document.createElement('div');
  div.className = 'chat-bolla ' + (ruolo === 'user' ? 'chat-utente' : 'chat-bot');
  div.textContent = testo;

  // Aggiungi mini-player solo per i messaggi del bot
  if (ruolo === 'assistant' || ruolo === 'bot') {
    var player = _creaMiniPlayer(testo);
    div.appendChild(player);
  }

  cont.appendChild(div);
  cont.scrollTop = cont.scrollHeight;
}

function _mostraTyping() {
  var cont = document.getElementById('chatMessaggi');
  if (!cont) return null;
  var div = document.createElement('div');
  div.className = 'chat-bolla chat-bot chat-typing';
  div.id = 'chatTyping';
  div.innerHTML = '<span></span><span></span><span></span>';
  cont.appendChild(div);
  cont.scrollTop = cont.scrollHeight;
  return div;
}

function _rimuoviTyping() {
  var el = document.getElementById('chatTyping');
  if (el) el.remove();
}

async function inviaChat() {
  var input = document.getElementById('chatInput');
  var btn = document.getElementById('chatBtnInvia');
  if (!input || !btn) return;

  var testo = (input.value || '').trim();
  if (!testo) return;

  // Aggiungi messaggio utente alla UI e allo storico
  _aggiungiBolla(testo, 'user');
  _chatStorico.push({ role: 'user', content: testo });
  input.value = '';
  btn.disabled = true;

  // Mostra typing
  _mostraTyping();

  try {
    var r = await fetch('/api/assistente/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messaggi: _chatStorico })
    });
    var data = await r.json();
    _rimuoviTyping();

    if (data.success && data.risposta) {
      _aggiungiBolla(data.risposta, 'assistant');
      _chatStorico.push({ role: 'assistant', content: data.risposta });
      // Auto-play: se attivo, avvia la lettura della risposta appena arrivata
      if (_chatAutoLettura) {
        setTimeout(function() {
          var players = document.querySelectorAll('.chat-player');
          if (players.length > 0) {
            var ultimo = players[players.length - 1];
            var btnPlay = ultimo.querySelector('button');
            if (btnPlay) btnPlay.click();
          }
        }, 250);
      }
    } else {
      _aggiungiBolla('Errore: ' + (data.error || 'risposta vuota'), 'assistant');
    }
  } catch (e) {
    _rimuoviTyping();
    _aggiungiBolla('Errore di rete: ' + e.message, 'assistant');
  } finally {
    btn.disabled = false;
    input.focus();
  }
}

// Chiudi chat con ESC
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape' && _chatAperta) toggleChat();
});
// ============================================================
// CHAT VOCALE - Registrazione + Trascrizione Whisper + TTS
// ============================================================

// Stato
var _chatMediaRecorder = null;
var _chatChunks = [];
var _chatRegistrando = false;
var _chatAutoLettura = false;

// -----------------------------------------------------------
// Registrazione vocale
// -----------------------------------------------------------
async function toggleRegistrazioneChat() {
  if (_chatRegistrando) {
    // Ferma
    if (_chatMediaRecorder && _chatMediaRecorder.state !== 'inactive') {
      _chatMediaRecorder.stop();
    }
    return;
  }

  // Avvia
  try {
    var stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    _chatMediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    _chatChunks = [];

    _chatMediaRecorder.ondataavailable = function(e) {
      if (e.data.size > 0) _chatChunks.push(e.data);
    };

    _chatMediaRecorder.onstop = async function() {
      _chatRegistrando = false;
      _aggiornaBtnMic(false);
      stream.getTracks().forEach(function(t) { t.stop(); });

      var blob = new Blob(_chatChunks, { type: 'audio/webm' });
      if (blob.size < 1000) {
        console.warn('Audio troppo corto');
        return;
      }

      await _trascriviAudioInChat(blob);
    };

    _chatMediaRecorder.start();
    _chatRegistrando = true;
    _aggiornaBtnMic(true);
  } catch (e) {
    alert('Impossibile accedere al microfono: ' + e.message);
    console.error(e);
  }
}

function _aggiornaBtnMic(attivo) {
  var btn = document.getElementById('chatBtnMic');
  var area = document.querySelector('.chat-input-area');
  if (!btn) return;
  if (attivo) {
    btn.classList.add('registrando');
    btn.innerHTML = '&#9632;';
    btn.title = 'Ferma registrazione';
    if (area) area.classList.add('registrando');
  } else {
    btn.classList.remove('registrando');
    btn.innerHTML = '&#127908;';
    btn.title = 'Parla';
    if (area) area.classList.remove('registrando');
  }
}

async function _trascriviAudioInChat(blob) {
  var input = document.getElementById('chatInput');
  if (!input) return;
  var testoPrima = input.value;
  input.placeholder = 'Trascrizione in corso...';
  input.disabled = true;

  try {
    var fd = new FormData();
    fd.append('audio', blob, 'chat.webm');

    var r = await fetch('/api/trascrivi', { method: 'POST', body: fd });
    var data = await r.json();

    if (data.success && data.trascrizione) {
      input.value = (testoPrima ? testoPrima + ' ' : '') + data.trascrizione;
      input.focus();
    } else {
      alert('Trascrizione fallita: ' + (data.error || 'risposta vuota'));
    }
  } catch (e) {
    alert('Errore di rete durante trascrizione: ' + e.message);
  } finally {
    input.placeholder = 'Scrivi o parla...';
    input.disabled = false;
  }
}

// -----------------------------------------------------------
// Lettura vocale (TTS) - Microsoft Elsa
// -----------------------------------------------------------
function _trovaVoceItaliana() {
  if (!window.speechSynthesis) return null;
  var voci = window.speechSynthesis.getVoices();

  if (!voci || voci.length === 0) {
    window.speechSynthesis.getVoices();
    return null;
  }

  // Se l'utente ha selezionato una voce specifica, usala
  if (_voceSelezionata && _voceSelezionata !== 'auto') {
    for (var i = 0; i < voci.length; i++) {
      if (voci[i].name === _voceSelezionata) return voci[i];
    }
    // Se la voce selezionata non è più disponibile, cade nel default
  }

  // Default (auto): preferisci Elsa, poi Cosimo, poi altre it-IT
  var preferenze = ['Microsoft Elsa', 'Microsoft Cosimo'];
  for (var p = 0; p < preferenze.length; p++) {
    for (var j = 0; j < voci.length; j++) {
      if (voci[j].name.indexOf(preferenze[p]) >= 0) return voci[j];
    }
  }

  for (var k = 0; k < voci.length; k++) {
    if (voci[k].lang === 'it-IT') return voci[k];
  }

  return null;
}

function _pulisciTestoPerVoce(testo) {
  // Rimuove markdown, emoji, simboli
  return testo
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .replace(/#+\s*/g, '')
    .replace(/[📦📅🏫✅🧰🎁📜💬🤖🔊🎤🟢🔴⚠️]/g, '')
    .replace(/\n+/g, '. ')
    .trim();
}

function _eseguiLettura(testo, bottone) {
  var voce = _trovaVoceItaliana();
  var utterance = new SpeechSynthesisUtterance(_pulisciTestoPerVoce(testo));
  utterance.lang = 'it-IT';
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  if (voce) utterance.voice = voce;

  utterance.onstart = function() {
    if (bottone) bottone.classList.add('leggendo');
  };
  utterance.onend = function() {
    if (bottone) bottone.classList.remove('leggendo');
  };
  utterance.onerror = function(e) {
    console.warn('TTS errore:', e);
    if (bottone) bottone.classList.remove('leggendo');
  };

  window.speechSynthesis.speak(utterance);
}

function leggiRisposta(testo, bottone) {
  if (!window.speechSynthesis) {
    alert('Sintesi vocale non supportata dal browser');
    return;
  }

  // Se sta già leggendo, ferma
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    document.querySelectorAll('.chat-btn-audio.leggendo').forEach(function(b) {
      b.classList.remove('leggendo');
    });
    return;
  }

  // Se le voci non sono ancora caricate, aspetta un attimo
  var voci = window.speechSynthesis.getVoices();
  if (!voci || voci.length === 0) {
    // Prova a far ricaricare le voci
    window.speechSynthesis.getVoices();
    // Riprova dopo 300ms
    var tentativi = 0;
    var checkVoci = setInterval(function() {
      tentativi++;
      var v = window.speechSynthesis.getVoices();
      if (v && v.length > 0) {
        clearInterval(checkVoci);
        _eseguiLettura(testo, bottone);
      } else if (tentativi > 10) {
        clearInterval(checkVoci);
        console.warn('TTS: voci non disponibili dopo 3 secondi');
        _eseguiLettura(testo, bottone);
      }
    }, 300);
    return;
  }

  _eseguiLettura(testo, bottone);
}

function toggleAutoLettura() {
  _chatAutoLettura = !_chatAutoLettura;
  var btn = document.getElementById('chatBtnAuto');
  if (!btn) return;
  if (_chatAutoLettura) {
    btn.classList.add('attivo');
    btn.innerHTML = '&#128266; Auto ON';
  } else {
    btn.classList.remove('attivo');
    btn.innerHTML = '&#128266; Auto';
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  }
}
// Precarica voci TTS (importante per Chrome)
if (window.speechSynthesis) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = function() {
        window.speechSynthesis.getVoices();
    };
}
// ============================================================
// SELETTORE VOCE TTS
// ============================================================
var _voceSelezionata = 'auto';  // 'auto' | 'Microsoft Elsa' | 'Microsoft Cosimo' | ...

function _popolaSelettoreVoci() {
  var sel = document.getElementById('chatVoceSelect');
  if (!sel) return;

  var voci = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
  if (!voci || voci.length === 0) {
    // Riprova dopo un attimo
    setTimeout(_popolaSelettoreVoci, 300);
    return;
  }

  // Filtra solo voci italiane
  var voci_it = voci.filter(function(v) {
    return v.lang && (v.lang === 'it-IT' || v.lang.indexOf('it') === 0);
  });

  // Ordina: Microsoft prima, poi Google, poi altre
  voci_it.sort(function(a, b) {
    function peso(v) {
      if (v.name.indexOf('Microsoft Elsa') >= 0) return 1;
      if (v.name.indexOf('Microsoft Cosimo') >= 0) return 2;
      if (v.name.indexOf('Microsoft') >= 0) return 3;
      if (v.name.indexOf('Google') >= 0) return 4;
      return 5;
    }
    return peso(a) - peso(b);
  });

  // Ricostruisci le opzioni
  sel.innerHTML = '<option value="auto">&#127908; Auto (Elsa)</option>';
  voci_it.forEach(function(v) {
    var opt = document.createElement('option');
    opt.value = v.name;
    var icona = '';
    if (v.name.indexOf('Elsa') >= 0) icona = '&#128105; ';
    else if (v.name.indexOf('Cosimo') >= 0) icona = '&#128104; ';
    else if (v.name.indexOf('Google') >= 0) icona = '&#9729; ';
    else icona = '&#127908; ';
    opt.innerHTML = icona + v.name.replace('Microsoft ', '').replace(' - Italian (Italy)', '');
    sel.appendChild(opt);
  });

  // Ripristina la selezione salvata
  var salvata = localStorage.getItem('braaap_voce_tts') || 'auto';
  sel.value = salvata;
  _voceSelezionata = salvata;
}

function cambiaVoce() {
  var sel = document.getElementById('chatVoceSelect');
  if (!sel) return;
  _voceSelezionata = sel.value;
  localStorage.setItem('braaap_voce_tts', _voceSelezionata);
  console.log('Voce selezionata:', _voceSelezionata);

  // Anteprima vocale breve
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
    var testoTs = 'Ciao, sono la voce selezionata per Braaap.';
    var u = new SpeechSynthesisUtterance(testoTs);
    u.lang = 'it-IT';
    var voce = _trovaVoceItaliana();
    if (voce) u.voice = voce;
    window.speechSynthesis.speak(u);
  }
}

// ------------------------------------------------------------
// Sostituisci _trovaVoceItaliana per usare la selezione utente
// ------------------------------------------------------------
// ============================================================
// RESET CHAT - Nuova conversazione
// ============================================================
function resetChat() {
  if (!confirm('Vuoi iniziare una nuova conversazione?\n\nIl contesto attuale verra cancellato.')) {
    return;
  }

  // 1) Svuota lo storico
  _chatStorico = [];

  // 2) Ferma la lettura TTS se in corso
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }

  // 3) Svuota visivamente l'area messaggi e rimetti il benvenuto
  var cont = document.getElementById('chatMessaggi');
  if (cont) {
    cont.innerHTML = '';
    var benvenuto = document.createElement('div');
    benvenuto.className = 'chat-bolla chat-bot';
    benvenuto.textContent = 'Nuova conversazione avviata! Sono pronto per le tue domande. Cosa ti serve?';
    cont.appendChild(benvenuto);
  }

  // 4) Svuota l'input
  var inp = document.getElementById('chatInput');
  if (inp) {
    inp.value = '';
    inp.focus();
  }

  // 5) Rimuovi eventuale typing indicatore
  var typing = document.getElementById('chatTyping');
  if (typing) typing.remove();
}
// ============================================================
// PLAYER TTS AVANZATO - Pausa/Resume/Velocita
// ============================================================
var _ttsStato = {
  utterance: null,
  bottonePlay: null,
  bottoneVelocita: null,
  barraProgresso: null,
  testo: '',
  inPausa: false,
  velocita: 1.0,   // default
  inCorso: false
};

function _creaMiniPlayer(testo) {
  var div = document.createElement('div');
  div.className = 'chat-player';

  // Bottone Play/Pausa
  var btnPlay = document.createElement('button');
  btnPlay.innerHTML = '&#9654;';  // ▶
  btnPlay.title = 'Ascolta';
  btnPlay.onclick = function(ev) {
    ev.stopPropagation();
    _playPausa(testo, btnPlay, btnVel, barra);
  };
  div.appendChild(btnPlay);

  // Bottone Velocita
  var btnVel = document.createElement('select');
  btnVel.className = 'chat-velocita';
  btnVel.title = 'Velocita di lettura';
  [['0.5','0.5x'],['0.75','0.75x'],['1','1x'],['1.25','1.25x'],['1.5','1.5x'],['2','2x'],['3','3x'],['5','5x']].forEach(function(opt) {
    var o = document.createElement('option');
    o.value = opt[0];
    o.textContent = opt[1];
    if (opt[0] === String(_ttsStato.velocita)) o.selected = true;
    btnVel.appendChild(o);
  });
  btnVel.onchange = function(ev) {
    ev.stopPropagation();
    _ttsStato.velocita = parseFloat(btnVel.value);
    // Se sta leggendo, riavvia con la nuova velocita (dall'inizio)
    if (_ttsStato.inCorso) {
      _stopTTS();
      setTimeout(function() { _playPausa(testo, btnPlay, btnVel, barra); }, 100);
    }
  };
  div.appendChild(btnVel);

  // Barra progresso
  var barra = document.createElement('div');
  barra.className = 'chat-progress';
  var barraFill = document.createElement('div');
  barraFill.className = 'chat-progress-bar';
  barra.appendChild(barraFill);
  div.appendChild(barra);

  // Bottone Stop
  var btnStop = document.createElement('button');
  btnStop.innerHTML = '&#9632;';  // ■
  btnStop.title = 'Stop';
  btnStop.onclick = function(ev) {
    ev.stopPropagation();
    _stopTTS();
    btnPlay.innerHTML = '&#9654;';
    btnPlay.classList.remove('attivo');
    barraFill.style.width = '0%';
  };
  div.appendChild(btnStop);

  return div;
}

function _playPausa(testo, btnPlay, btnVel, barra) {
  if (!window.speechSynthesis) {
    alert('Sintesi vocale non supportata');
    return;
  }

  // Se sta leggendo questo testo e non e' in pausa -> pausa
  if (_ttsStato.inCorso && _ttsStato.testo === testo && !_ttsStato.inPausa) {
    window.speechSynthesis.pause();
    _ttsStato.inPausa = true;
    btnPlay.innerHTML = '&#9654;';
    btnPlay.title = 'Riprendi';
    return;
  }

  // Se era in pausa su questo testo -> riprendi
  if (_ttsStato.inCorso && _ttsStato.testo === testo && _ttsStato.inPausa) {
    window.speechSynthesis.resume();
    _ttsStato.inPausa = false;
    btnPlay.innerHTML = '&#10074;&#10074;';  // ⏸
    btnPlay.title = 'Pausa';
    return;
  }

  // Altrimenti: nuovo playback
  _stopTTS();

  var voce = _trovaVoceItaliana();
  var u = new SpeechSynthesisUtterance(_pulisciTestoPerVoce(testo));
  u.lang = 'it-IT';
  u.rate = _ttsStato.velocita;
  u.pitch = 1.0;
  if (voce) u.voice = voce;

  u.onstart = function() {
    _ttsStato.inCorso = true;
    _ttsStato.inPausa = false;
    _ttsStato.testo = testo;
    _ttsStato.utterance = u;
    _ttsStato.bottonePlay = btnPlay;
    _ttsStato.barraProgresso = barra;

    btnPlay.innerHTML = '&#10074;&#10074;';
    btnPlay.classList.add('attivo');
    btnPlay.title = 'Pausa';

    // Avvia progresso (simulato perche' speechSynthesis non ha eventi di progresso)
    _avviaProgressoSimulato(u, testo, barra);
  };

  u.onend = function() {
    if (barra) barra.querySelector('.chat-progress-bar').style.width = '100%';
    setTimeout(function() {
      _resetTTS();
      if (barra) barra.querySelector('.chat-progress-bar').style.width = '0%';
    }, 300);
  };

  u.onerror = function(e) {
    console.warn('TTS errore:', e);
    _resetTTS();
  };

  window.speechSynthesis.speak(u);
}

var _ttsProgressoTimer = null;

function _avviaProgressoSimulato(u, testo, barra) {
  if (_ttsProgressoTimer) clearInterval(_ttsProgressoTimer);

  // Stima: ~150 caratteri al secondo a 1x
  var caratteri = testo.length;
  var secondiStimati = caratteri / (15 * _ttsStato.velocita);
  var inizio = Date.now();

  _ttsProgressoTimer = setInterval(function() {
    if (!_ttsStato.inCorso) {
      clearInterval(_ttsProgressoTimer);
      return;
    }
    if (_ttsStato.inPausa) {
      // In pausa: non far avanzare la barra
      inizio += 100;
      return;
    }
    var trascorso = (Date.now() - inizio) / 1000;
    var pct = Math.min(100, (trascorso / secondiStimati) * 100);
    var barraFill = barra ? barra.querySelector('.chat-progress-bar') : null;
    if (barraFill) barraFill.style.width = pct + '%';
  }, 100);
}

function _stopTTS() {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  if (_ttsProgressoTimer) {
    clearInterval(_ttsProgressoTimer);
    _ttsProgressoTimer = null;
  }
  // Reset bottoni
  if (_ttsStato.bottonePlay) {
    _ttsStato.bottonePlay.innerHTML = '&#9654;';
    _ttsStato.bottonePlay.classList.remove('attivo');
    _ttsStato.bottonePlay.title = 'Ascolta';
  }
  _resetTTS();
}

function _resetTTS() {
  _ttsStato.inCorso = false;
  _ttsStato.inPausa = false;
  _ttsStato.testo = '';
  _ttsStato.utterance = null;
}

// ============================================================
// leggiRisposta - versione compatibile con il mini-player
// Trova l'ultimo player della chat e lo attiva
// ============================================================
function leggiRisposta(testo, bottone) {
  // Trova l'ultimo player presente nella chat e simula un click sul play
  var players = document.querySelectorAll('.chat-player');
  if (players.length === 0) {
    console.warn('leggiRisposta: nessun player trovato');
    return;
  }
  var ultimo = players[players.length - 1];
  var btnPlay = ultimo.querySelector('button');
  if (btnPlay) {
    btnPlay.click();
  }
}
// ============================================================
// MODALE VOCABOLARIO - Gestione parole apprese
// ============================================================
async function apriVocabolario() {
  var modal = document.getElementById('modaleVocabolario');
  if (!modal) {
    // Crea la modale al volo
    var html = '<div class="modale-vocabolario" id="modaleVocabolario">' +
      '<div class="modale-vocabolario-content">' +
        '<div class="modale-vocabolario-header">' +
          '<h2>&#128218; Vocabolario</h2>' +
          '<button onclick="chiudiVocabolario()" style="background:none;border:none;color:white;font-size:20px;cursor:pointer">&#10005;</button>' +
        '</div>' +
        '<div class="modale-vocabolario-body" id="vocabBody">Caricamento...</div>' +
        '<div class="vocab-form">' +
          '<input id="vocabParola" placeholder="Parola (es. gadgets)">' +
          '<input id="vocabSignificato" placeholder="Significato (es. braccialetti e medaglie)">' +
          '<button onclick="aggiungiParolaVocab()">+ Aggiungi</button>' +
        '</div>' +
      '</div>' +
    '</div>';
    document.body.insertAdjacentHTML('beforeend', html);
  }
  document.getElementById('modaleVocabolario').classList.add('aperta');
  await caricaVocabolario();
}

function chiudiVocabolario() {
  var m = document.getElementById('modaleVocabolario');
  if (m) m.classList.remove('aperta');
}

async function caricaVocabolario() {
  var body = document.getElementById('vocabBody');
  if (!body) return;
  try {
    var r = await fetch('/api/vocabolario/lista');
    var data = await r.json();

    var html = '';

    // Wake-words built-in
    html += '<h3>&#127908; Wake-word (built-in)</h3>';
    html += '<div class="vocab-wakewords">';
    ['braap', 'braaap', 'braapp', 'ehi braaap', 'ok braaap', 'forza braaap'].forEach(function(w) {
      html += '<span>' + w + '</span>';
    });
    html += '</div>';
    html += '<div style="font-size:12px;color:#607890;margin-bottom:12px">Pronuncia una di queste parole per attivare la modalita ascolto continuo.</div>';

    // Appreso
    html += '<h3>&#127891; Parole apprese (' + (data.appreso || []).length + ')</h3>';
    if (!data.appreso || data.appreso.length === 0) {
      html += '<div style="color:#90A4AE;font-size:13px;padding:12px">Nessuna parola appresa. Prova a dire in chat: "chiama gadgets braccialetti e medaglie"</div>';
    } else {
      data.appreso.forEach(function(p) {
        html += '<div class="vocab-item">' +
          '<div class="parola">' + p.parola + '</div>' +
          '<div class="significato">' + p.significato + '</div>' +
          '<div class="usi">' + p.usi + ' usi</div>' +
          '<div class="azioni"><button onclick="dimenticaParola(\'' + p.parola + '\')" title="Dimentica">&#128465;</button></div>' +
        '</div>';
      });
    }

    // Contesto
    html += '<h3>&#128218; Dizionario contestuale (' + (data.contesto || []).length + ')</h3>';
    (data.contesto || []).forEach(function(p) {
      html += '<div class="vocab-item">' +
        '<div class="parola">' + p.parola + '</div>' +
        '<div class="significato">' + p.significato + '</div>' +
      '</div>';
    });

    body.innerHTML = html;
  } catch (e) {
    body.innerHTML = '<div style="color:red">Errore: ' + e.message + '</div>';
  }
}

async function aggiungiParolaVocab() {
  var parola = (document.getElementById('vocabParola').value || '').trim();
  var significato = (document.getElementById('vocabSignificato').value || '').trim();
  if (!parola || !significato) {
    alert('Inserisci sia parola che significato');
    return;
  }
  try {
    var r = await fetch('/api/vocabolario/impara', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({parola: parola, significato: significato})
    });
    var data = await r.json();
    if (data.success) {
      document.getElementById('vocabParola').value = '';
      document.getElementById('vocabSignificato').value = '';
      await caricaVocabolario();
    } else {
      alert('Errore: ' + (data.error || 'sconosciuto'));
    }
  } catch (e) {
    alert('Errore di rete: ' + e.message);
  }
}

async function dimenticaParola(parola) {
  if (!confirm('Dimenticare la parola "' + parola + '"?')) return;
  try {
    await fetch('/api/vocabolario/dimentica/' + encodeURIComponent(parola), {method: 'DELETE'});
    await caricaVocabolario();
  } catch (e) {
    alert('Errore: ' + e.message);
  }
}

// Chiudi con ESC
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    var m = document.getElementById('modaleVocabolario');
    if (m && m.classList.contains('aperta')) chiudiVocabolario();
  }
});
// ============================================================
// FOTO EVENTO - Upload + Drag&Drop + Lightbox
// ============================================================
var _eventoFotoCorrente = null;

// Drag&drop globale (attivo solo quando la modale evento e' aperta)
document.addEventListener('DOMContentLoaded', function() {
  var drop = document.getElementById('dropZoneFoto');
  if (!drop) return;

  ['dragenter', 'dragover'].forEach(function(evt) {
    drop.addEventListener(evt, function(e) {
      e.preventDefault();
      e.stopPropagation();
      drop.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(function(evt) {
    drop.addEventListener(evt, function(e) {
      e.preventDefault();
      e.stopPropagation();
      drop.classList.remove('drag-over');
    });
  });

  drop.addEventListener('drop', function(e) {
    var files = e.dataTransfer.files;
    if (files && files.length > 0) {
      caricaFotoEvento(files);
    }
  });
});

// Carica le foto selezionate
async function caricaFotoEvento(files) {
  if (!files || files.length === 0) return;

  var eventoId = id('eId').value;
  if (!eventoId) {
    alert('Salva prima l\'evento, poi potrai caricare le foto.');
    return;
  }

  // Mostra placeholder di caricamento
  var lista = document.getElementById('listaFotoEvento');
  var placeholders = [];
  for (var i = 0; i < files.length; i++) {
    var ph = document.createElement('div');
    ph.className = 'foto-caricamento';
    ph.textContent = '...';
    lista.appendChild(ph);
    placeholders.push(ph);
  }

  // Prepara FormData
  var fd = new FormData();
  fd.append('evento_id', eventoId);
  for (var j = 0; j < files.length; j++) {
    fd.append('foto', files[j]);
  }

  try {
    var r = await fetch('/api/foto/upload', { method: 'POST', body: fd });
    var data = await r.json();

    // Rimuovi placeholder
    placeholders.forEach(function(p) { p.remove(); });

    if (data.success) {
      // Ricarica l'evento dal server per avere la lista aggiornata
      await ricaricaEventoFoto(eventoId);
      // Se ci sono errori parziali, mostrali
      if (data.errori && data.errori.length > 0) {
        alert('Alcune foto non sono state caricate:\n' + data.errori.join('\n'));
      }
    } else {
      alert('Errore: ' + (data.error || 'sconosciuto'));
    }
  } catch (e) {
    placeholders.forEach(function(p) { p.remove(); });
    alert('Errore di rete: ' + e.message);
  }
}

// Ricarica i dati dell'evento e aggiorna la lista foto
async function ricaricaEventoFoto(eventoId) {
  try {
    var r = await fetch('/api/eventi');
    var eventi = await r.json();
    var ev = eventi.find(function(e) { return String(e.id) === String(eventoId); });
    if (!ev) return;

    // Aggiorna STATO
    if (typeof STATO !== 'undefined') {
      var idx = STATO.eventi.findIndex(function(e) { return String(e.id) === String(eventoId); });
      if (idx >= 0) STATO.eventi[idx] = ev;
    }

    // Renderizza le foto
    renderFotoEvento(ev.foto || [], eventoId);
  } catch (e) {
    console.warn('Errore ricarica evento foto:', e);
  }
}

// Mostra le miniature nella modale
function renderFotoEvento(foto, eventoId) {
  var lista = document.getElementById('listaFotoEvento');
  if (!lista) return;
  lista.innerHTML = '';
  if (!foto || foto.length === 0) return;

  foto.forEach(function(media, idx) {
    // Supporta stringhe e oggetti
    var filename = typeof media === 'string' ? media : (media.file || '');
    if (!filename) return;

    var didascalia = typeof media === 'object' ? (media.didascalia || '') : '';
    var tag = typeof media === 'object' ? (media.tag || []) : [];

    var div = document.createElement('div');
    div.className = 'foto-thumb';
    var isVideo = /\.(mp4|mov|webm|avi|mkv|m4v)$/i.test(filename);
    var url = '/api/foto/file/' + encodeURIComponent(filename);

    var html = '';
    if (isVideo) {
      html += '<video src="' + url + '" muted preload="metadata" style="width:100%;height:100%;object-fit:cover"></video>';
      html += '<div class="foto-play-icon">&#9654;</div>';
    } else {
      html += '<img src="' + url + '" alt="' + didascalia + '" loading="lazy">';
    }
    html += '<button class="foto-del" onclick="event.stopPropagation(); eliminaFotoEvento(\'' + filename + '\')" title="Elimina">&#10005;</button>';
    // Mostra didascalia se presente
    if (didascalia) {
      html += '<div style="position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,0.7);color:white;padding:4px 8px;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + didascalia + '">' + didascalia + '</div>';
    }

    div.innerHTML = html;
    div.onclick = function() {
      apriLightboxAvanzato(foto, idx, eventoId);
    };
    lista.appendChild(div);
  });
}

// Cancella una foto
async function eliminaFotoEvento(filename) {
  if (!confirm('Eliminare questa foto?')) return;

  var eventoId = id('eId').value;
  if (!eventoId) return;

  try {
    var r = await fetch('/api/foto/elimina', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({evento_id: eventoId, filename: filename})
    });
    var data = await r.json();

    if (data.success) {
      await ricaricaEventoFoto(eventoId);
    } else {
      alert('Errore: ' + (data.error || 'sconosciuto'));
    }
  } catch (e) {
    alert('Errore di rete: ' + e.message);
  }
}

// Lightbox

// ============================================================
// DASHBOARD - Pulsanti rapidi (zero token Groq)
// ============================================================
async function mostraDashboard(tipo) {
  var cont = document.getElementById('chatMessaggi');
  if (!cont) return;

  // Aggiungi bolla di caricamento
  var caricamento = document.createElement('div');
  caricamento.className = 'chat-bolla chat-bot';
  caricamento.id = 'dashboardCaricamento';
  caricamento.textContent = '⏳ Carico i dati...';
  cont.appendChild(caricamento);
  cont.scrollTop = cont.scrollHeight;

  try {
    var r = await fetch('/api/dashboard/' + tipo);
    var data = await r.json();

    // Rimuovi caricamento
    caricamento.remove();

    if (data.success && data.testo) {
      // Aggiungi la dashboard come bolla con markdown semplice
      var bolla = document.createElement('div');
      bolla.className = 'chat-bolla chat-bot chat-dashboard';
      bolla.innerHTML = _formattaMarkdown(data.testo);
      cont.appendChild(bolla);

      // Salva nello storico cosi l'utente puo farci domande dopo
      if (typeof _chatStorico !== 'undefined') {
        _chatStorico.push({
          role: 'user',
          content: '[' + tipo + ']'
        });
        _chatStorico.push({
          role: 'assistant',
          content: data.testo
        });
      }
    } else {
      var err = document.createElement('div');
      err.className = 'chat-bolla chat-bot';
      err.textContent = 'Errore: ' + (data.error || 'sconosciuto');
      cont.appendChild(err);
    }
  } catch (e) {
    caricamento.remove();
    var err2 = document.createElement('div');
    err2.className = 'chat-bolla chat-bot';
    err2.textContent = 'Errore di rete: ' + e.message;
    cont.appendChild(err2);
  }

  cont.scrollTop = cont.scrollHeight;
}

// Formattazione markdown minimale (grassetto + a capo)
function _formattaMarkdown(testo) {
  if (!testo) return '';
  // Escape HTML
  var safe = testo
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  // **grassetto**
  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Preserva a capo
  safe = safe.replace(/\n/g, '<br>');
  return safe;
}

// Stile speciale per le bolle dashboard
(function() {
  var style = document.createElement('style');
  style.textContent = '.chat-dashboard { font-size: 13px !important; line-height: 1.6 !important; max-width: 95% !important; }';
  document.head.appendChild(style);
})();
// ============================================================
// NAVIGAZIONE - Storia + Indietro + Home
// ============================================================
var _storiaNavigazione = [];      // Stack delle pagine visitate
var _paginaCorrente = 'home';     // Pagina attualmente visibile
var _maxStoria = 15;              // Limite per evitare memoria infinita

// Titoli leggibili per ogni pagina
var _titoliPagine = {
  'home': '🏠 Home',
  'eventi': '📅 Eventi',
  'scuole': '🏫 Scuole & Organizzazioni',
  'rubrica': '📞 Rubrica',
  'task': '✅ Task',
  'calendario': '🗓️ Calendario',
  'magazzino': '📊 Magazzino',
  'materiali': '🎁 Materiali',
  'inventario': '🧰 Inventario',
  'lavagna': '📌 Lavagna',
  'liste': '🛒 Liste',
  'portafoglio': '💰 Portafoglio',
  'cambio': '💱 Cambio',
  'meteo': '🌤️ Meteo',
  'radio': '📻 Radio',
  'calcolatrice': '🧮 Calcolatrice',
  'elabora': '✨ Elabora',
  'comandi': '🖥️ Comandi',
  'esporta': '📤 Esporta',
  'logo': '🎨 Logo',
  'impostazioni': '⚙️ Impostazioni',
  'archivio': '📈 Archivio',
  'altro': '📦 ALTRO',
};

// Wrapper di 'mostra' che intercetta la navigazione
(function() {
  if (typeof window.mostra !== 'function') return;
  var _originale = window.mostra;
  window.mostra = function(page) {
    // Evita duplicati consecutivi nella storia
    if (page !== _paginaCorrente) {
      _storiaNavigazione.push(_paginaCorrente);
      if (_storiaNavigazione.length > _maxStoria) {
        _storiaNavigazione.shift();
      }
    }
    _paginaCorrente = page;
    _aggiornaBarraNavigazione();
    return _originale.apply(this, arguments);
  };
})();

function _aggiornaBarraNavigazione() {
  var titolo = document.getElementById('navTitoloPagina');
  var sotto = document.getElementById('navSottotitolo');
  var btnIndietro = document.getElementById('btnNavIndietro');

  if (titolo) {
    titolo.textContent = _titoliPagine[_paginaCorrente] || _paginaCorrente;
  }
  if (sotto) {
    // Sottotitolo contestuale (es. numero elementi)
    var extra = '';
    if (typeof STATO !== 'undefined' && STATO) {
      if (_paginaCorrente === 'eventi' && STATO.eventi) extra = STATO.eventi.length + ' eventi';
      else if (_paginaCorrente === 'scuole' && STATO.scuole) extra = STATO.scuole.length + ' scuole';
      else if (_paginaCorrente === 'task' && STATO.task) extra = STATO.task.length + ' task';
      else if (_paginaCorrente === 'rubrica' && STATO.rubrica) extra = STATO.rubrica.length + ' contatti';
      else if (_paginaCorrente === 'inventario' && STATO.inventario) extra = STATO.inventario.length + ' oggetti';
    }
    sotto.textContent = extra;
  }
  if (btnIndietro) {
    btnIndietro.style.display = _storiaNavigazione.length > 0 ? 'flex' : 'none';
  }
}

function vaiIndietro() {
  if (_storiaNavigazione.length === 0) {
    vaiHome();
    return;
  }
  var precedente = _storiaNavigazione.pop();
  _paginaCorrente = precedente;
  // Chiama il mostra() ORIGINALE (evita di ri-pushare la storia)
  if (typeof STATO !== 'undefined' && typeof _mostraOriginale === 'function') {
    _mostraOriginale(precedente);
  } else {
    // Fallback: chiama il mostra attuale ma bloccando il push
    var oldStoria = _storiaNavigazione.slice();
    if (typeof window.mostra === 'function') {
      window.mostra(precedente);
    }
    _storiaNavigazione = oldStoria;
  }
  _aggiornaBarraNavigazione();
}

function vaiHome() {
  // Pulisci la storia
  _storiaNavigazione = [];
  _paginaCorrente = 'home';
  if (typeof window.mostra === 'function') {
    // Chiama mostra('home') evitando di ri-pushare
    var oldStoria = _storiaNavigazione.slice();
    window.mostra('home');
    _storiaNavigazione = oldStoria;
  }
  _aggiornaBarraNavigazione();
}

// Aggiorna la barra ogni volta che si caricano nuovi dati
if (typeof window.caricaDati === 'function') {
  var _caricaDatiOrig = window.caricaDati;
  window.caricaDati = function() {
    var r = _caricaDatiOrig.apply(this, arguments);
    setTimeout(function() {
      try { _aggiornaBarraNavigazione(); } catch(e) {}
    }, 100);
    return r;
  };
}

// Scorciatoie tastiera
document.addEventListener('keydown', function(e) {
  // Alt + Freccia Sinistra = Indietro
  if (e.altKey && e.key === 'ArrowLeft') {
    e.preventDefault();
    vaiIndietro();
  }
  // Alt + H = Home
  if (e.altKey && (e.key === 'h' || e.key === 'H')) {
    e.preventDefault();
    vaiHome();
  }
});

// Inizializza al caricamento
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(_aggiornaBarraNavigazione, 200);
});
// ============================================================
// HOME HERO - Carica/rimuovi foto
// ============================================================
async function caricaFotoHomeCorrente() {
  try {
    var r = await fetch('/api/home/foto');
    var data = await r.json();
    var img = document.getElementById('homeHeroFoto');
    var svg = document.getElementById('homeHeroSVG');
    var rimuovi = document.getElementById('homeHeroRimuovi');

    if (data.success && data.foto) {
      if (img) {
        img.src = '/api/home/file/' + encodeURIComponent(data.foto);
        img.style.display = 'block';
      }
      if (svg) svg.style.display = 'none';
      if (rimuovi) rimuovi.style.display = 'flex';
    } else {
      if (img) { img.style.display = 'none'; img.src = ''; }
      if (svg) svg.style.display = 'block';
      if (rimuovi) rimuovi.style.display = 'none';
    }
  } catch (e) {
    console.warn('Errore caricamento foto home:', e);
  }
}

async function caricaFotoHome(file) {
  if (!file) return;
  var fd = new FormData();
  fd.append('foto', file);

  try {
    var r = await fetch('/api/home/foto', { method: 'POST', body: fd });
    var data = await r.json();
    if (data.success) {
      await caricaFotoHomeCorrente();
    } else {
      alert('Errore: ' + (data.error || 'sconosciuto'));
    }
  } catch (e) {
    alert('Errore di rete: ' + e.message);
  }
}

async function rimuoviFotoHome() {
  if (!confirm('Rimuovere la foto della Home?')) return;
  try {
    await fetch('/api/home/foto', { method: 'DELETE' });
    await caricaFotoHomeCorrente();
  } catch (e) {
    alert('Errore: ' + e.message);
  }
}

// Carica la foto quando si apre la Home
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(caricaFotoHomeCorrente, 500);
});

// Ricarica quando si torna alla Home
(function() {
  if (typeof window.mostra !== 'function') return;
  if (window._mostraWrapperHomeFatto) return;
  window._mostraWrapperHomeFatto = true;
  var _orig = window.mostra;
  window.mostra = function(page) {
    var r = _orig.apply(this, arguments);
    if (page === 'home') setTimeout(caricaFotoHomeCorrente, 200);
    return r;
  };
})();

// Drag & drop sulla hero
document.addEventListener('DOMContentLoaded', function() {
  var hero = document.getElementById('homeHero');
  if (!hero) return;
  ['dragenter', 'dragover'].forEach(function(evt) {
    hero.addEventListener(evt, function(e) { e.preventDefault(); hero.style.outline = '3px dashed #4FC3F7'; });
  });
  ['dragleave', 'drop'].forEach(function(evt) {
    hero.addEventListener(evt, function(e) { e.preventDefault(); hero.style.outline = ''; });
  });
  hero.addEventListener('drop', function(e) {
    var files = e.dataTransfer.files;
    if (files && files.length > 0) caricaFotoHome(files[0]);
  });
});
// ============================================================
// SYNC SCUOLE <-> RUBRICA - Link e visualizzazione
// ============================================================
function apriRubricaFiltrataScuola(scuolaId, nomeScuola) {
  // Vai alla rubrica e filtra per questa scuola
  if (typeof mostra === 'function') mostra('rubrica');
  setTimeout(function() {
    var sel = document.getElementById('filtroRubricaScuola');
    if (sel) {
      sel.value = String(scuolaId);
      if (typeof renderRubrica === 'function') renderRubrica();
    }
  }, 300);
}

// Estende apriModaleScuola per mostrare contatti collegati
(function() {
  if (typeof window.apriModaleScuola !== 'function') return;
  if (window._apriModaleScuolaWrapperFatto) return;
  window._apriModaleScuolaWrapperFatto = true;

  var _orig = window.apriModaleScuola;
  window.apriModaleScuola = function(sid) {
    var r = _orig.apply(this, arguments);
    if (sid) {
      // Mostra il numero di contatti collegati
      var contatti = (STATO.rubrica || []).filter(function(c) { return String(c.scuola_id) === String(sid); });
      // Aggiungi banner se ci sono contatti collegati
      var det = document.getElementById('scuolaDettaglioEventi');
      if (det && contatti.length > 0) {
        var sc = STATO.scuole.find(function(x) { return String(x.id) === String(sid); });
        var nome = sc ? sc.nome : '';
        // Aggiungi info contatti in cima al dettaglio
        var infoContatti = '<div style="background:#e8f4fd;padding:8px 12px;border-radius:8px;margin-bottom:8px;font-size:13px">' +
          '<strong>👥 ' + contatti.length + ' contatt' + (contatti.length === 1 ? 'o' : 'i') + ' in rubrica</strong> ' +
          '<button onclick="apriRubricaFiltrataScuola(' + sid + ', \'' + nome.replace(/'/g, "\\'") + '\')" style="background:#0288D1;color:white;border:none;border-radius:6px;padding:4px 10px;cursor:pointer;margin-left:8px;font-size:12px">Vai alla rubrica →</button>' +
        '</div>';
        
        // Inserisci prima del titolo "Eventi collegati"
        if (det.innerHTML && !det.querySelector('.info-contatti-scuola')) {
          var wrapper = document.createElement('div');
          wrapper.className = 'info-contatti-scuola';
          wrapper.innerHTML = infoContatti;
          det.insertBefore(wrapper, det.firstChild);
        }
      }
    }
    return r;
  };
})();
// ============================================================
// SELETTORE ANNO GLOBALE + PAGINA STORICO
// ============================================================
var _annoCorrente = 'tutti';

// Inizializza il selettore con gli anni disponibili
async function inizializzaSelettoreAnno() {
  try {
    var r = await fetch('/api/anno/lista');
    var data = await r.json();
    var sel = document.getElementById('selettoreAnno');
    if (!sel || !data.success) return;

    var anni = data.anni || [];
    var html = '<option value="tutti">&#128197; Tutti</option>';
    anni.forEach(function(a) {
      html += '<option value="' + a + '">&#128197; ' + a + '</option>';
    });
    sel.innerHTML = html;

    // Ripristina da localStorage
    var salvato = localStorage.getItem('braaap_anno_corrente') || 'tutti';
    sel.value = salvato;
    _annoCorrente = salvato;
    _aggiornaClasseSelettore();

    // Popola anche il select dello storico
    var storicoSel = document.getElementById('storicoAnnoSelect');
    if (storicoSel) {
      var html2 = '<option value="">— Seleziona un anno —</option>';
      anni.forEach(function(a) {
        html2 += '<option value="' + a + '">' + a + '</option>';
      });
      storicoSel.innerHTML = html2;
    }
  } catch (e) {
    console.warn('Errore caricamento anni:', e);
  }
}

function _aggiornaClasseSelettore() {
  var sel = document.getElementById('selettoreAnno');
  if (!sel) return;
  if (_annoCorrente === 'tutti') sel.classList.remove('attivo');
  else sel.classList.add('attivo');
}

function cambiaAnno(anno) {
  _annoCorrente = anno;
  localStorage.setItem('braaap_anno_corrente', anno);
  _aggiornaClasseSelettore();

  // Ricarica tutte le viste che rispettano il filtro
  if (typeof renderEventi === 'function') { try { renderEventi(); } catch(e) {} }
  if (typeof aggiornaStatistiche === 'function') { try { aggiornaStatistiche(); } catch(e) {} }
  if (typeof aggiornaEventiRecenti === 'function') { try { aggiornaEventiRecenti(); } catch(e) {} }
  if (typeof renderMagazzino === 'function') { try { renderMagazzino(); } catch(e) {} }
  if (typeof aggiornaInventario === 'function') { try { aggiornaInventario(); } catch(e) {} }
  if (typeof renderArchivio === 'function') { try { renderArchivio(); } catch(e) {} }

  // Se siamo nella pagina storico, ricarica
  if (_paginaCorrente === 'storico') {
    var ss = document.getElementById('storicoAnnoSelect');
    if (ss) {
      ss.value = anno === 'tutti' ? '' : anno;
      if (anno !== 'tutti') caricaStorico(anno);
    }
  }

  // Toast di conferma
  _toastAnno(anno);
}

function _toastAnno(anno) {
  var t = document.createElement('div');
  t.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#0288D1;color:white;padding:10px 20px;border-radius:20px;font-weight:700;z-index:9999;box-shadow:0 6px 20px rgba(0,0,0,0.3);animation:fadeInBolla 0.3s';
  t.textContent = anno === 'tutti' ? '📅 Vista: tutti gli anni' : '📅 Vista: anno ' + anno;
  document.body.appendChild(t);
  setTimeout(function() { t.remove(); }, 2000);
}

// ============================================================
// PAGINA STORICO
// ============================================================
async function caricaStorico(anno) {
  var cont = document.getElementById('storicoContenuto');
  if (!cont) return;
  cont.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted)">⏳ Caricamento...</div>';

  try {
    var r = await fetch('/api/anno/storico/' + anno);
    var data = await r.json();
    if (!data.success) {
      cont.innerHTML = '<div style="color:red">Errore: ' + (data.error || '?') + '</div>';
      return;
    }

    var s = data.dati;
    var html = '';

    // Statistiche principali
    html += '<div class="storico-grid">';
    html += '<div class="storico-stat"><div class="num">' + s.eventi.totale + '</div><div class="label">📅 Eventi totali</div></div>';
    html += '<div class="storico-stat"><div class="num">' + s.eventi.multi_giorno + '</div><div class="label">📆 Multi-giorno</div></div>';
    html += '<div class="storico-stat"><div class="num">' + _fmtNum(s.eventi.partecipanti_totali) + '</div><div class="label">👥 Partecipanti</div></div>';
    html += '<div class="storico-stat"><div class="num">' + s.task.totale + '</div><div class="label">✅ Task</div></div>';
    html += '</div>';

    // Grafico eventi per mese
    html += '<div class="storico-chart">';
    html += '<h3>📅 Eventi per mese</h3>';
    html += _renderGraficoMesi(s.eventi.per_mese, 'eventi');
    html += '</div>';

    // Grafico movimenti (carichi vs scarichi)
    html += '<div class="storico-chart">';
    html += '<h3>📦 Movimenti magazzino per mese</h3>';
    html += _renderGraficoMesi(s.movimenti.carichi_per_mese, 'carichi');
    html += '<div style="margin-top:14px"><h3 style="font-size:12px">🔴 Scarichi</h3>';
    html += _renderGraficoMesi(s.movimenti.scarichi_per_mese, 'scarichi');
    html += '</div>';
    html += '</div>';

    // Top scuole
    var topScuole = Object.entries(s.eventi.per_scuola || {});
    if (topScuole.length > 0) {
      html += '<div class="storico-chart">';
      html += '<h3>🏫 Top scuole per eventi</h3>';
      html += '<div class="storico-lista">';
      topScuole.forEach(function(entry) {
        html += '<div class="storico-lista-item"><span>' + entry[0] + '</span><strong>' + entry[1] + ' eventi</strong></div>';
      });
      html += '</div></div>';
    }

    // Top eventi
    if (s.eventi.top_5 && s.eventi.top_5.length > 0) {
      html += '<div class="storico-chart">';
      html += '<h3>🏆 Top 5 eventi per partecipanti</h3>';
      html += '<div class="storico-lista">';
      s.eventi.top_5.forEach(function(e) {
        html += '<div class="storico-lista-item"><span><strong>' + e.data + '</strong> — ' + e.iniziativa + ' <span style="color:#90A4AE">(' + e.scuola + ')</span></span><strong>' + e.partecipanti + '</strong></div>';
      });
      html += '</div></div>';
    }

    // Movimenti per categoria
    html += '<div class="storico-chart">';
    html += '<h3>📊 Magazzino - Movimenti per categoria</h3>';
    html += '<div class="storico-lista">';
    Object.entries(s.movimenti.per_categoria).forEach(function(entry) {
      var cat = entry[0];
      var d = entry[1];
      html += '<div class="storico-lista-item"><span>' + cat + '</span><span>🟢 <strong>' + d.carichi + '</strong> carichi | 🔴 <strong>' + d.scarichi + '</strong> scarichi | Netto: <strong style="color:' + (d.netto >= 0 ? '#16A34A' : '#DC2626') + '">' + d.netto + '</strong></span></div>';
    });
    html += '</div></div>';

    cont.innerHTML = html;
  } catch (e) {
    cont.innerHTML = '<div style="color:red">Errore di rete: ' + e.message + '</div>';
  }
}

function _renderGraficoMesi(valori, tipo) {
  var max = Math.max.apply(null, valori.concat([1]));
  var mesi = ['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic'];
  var html = '<div class="storico-barra-wrap">';
  valori.forEach(function(v, i) {
    var pct = (v / max) * 100;
    html += '<div class="storico-barra" style="height:' + pct + '%" title="' + mesi[i] + ': ' + v + '">';
    if (v > 0) html += '<span class="storico-barra-valore">' + v + '</span>';
    html += '<span class="storico-barra-label">' + mesi[i] + '</span>';
    html += '</div>';
  });
  html += '</div>';
  return html;
}

function _fmtNum(n) {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

// Inizializza al caricamento
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(inizializzaSelettoreAnno, 600);
});

// Quando entri nella pagina Storico, se un anno è selezionato caricato automaticamente
(function() {
  if (typeof window.mostra !== 'function') return;
  if (window._mostraWrapperStoricoFatto) return;
  window._mostraWrapperStoricoFatto = true;
  var _orig = window.mostra;
  window.mostra = function(page) {
    var r = _orig.apply(this, arguments);
    if (page === 'storico') {
      setTimeout(function() {
        var ss = document.getElementById('storicoAnnoSelect');
        if (ss && _annoCorrente !== 'tutti') {
          ss.value = _annoCorrente;
          caricaStorico(_annoCorrente);
        }
      }, 200);
    }
    return r;
  };
})();
// ============================================================
// FILTRO ANNO GLOBALE - Applica a tutte le viste
// Intercetta le funzioni di render e applica il filtro
// ============================================================
window._filtroAnnoApplicato = true;

// Helper: ritorna true se un elemento deve essere mostrato per l'anno corrente
function _rispettaAnnoCorrente(elemento) {
  if (!_annoCorrente || _annoCorrente === 'tutti') return true;
  var data = (elemento && elemento.data) || '';
  return data.startsWith(_annoCorrente + '-');
}

// Filtra una lista di eventi secondo _annoCorrente
function _filtraEventiPerAnno(eventi) {
  if (!_annoCorrente || _annoCorrente === 'tutti') return eventi;
  return eventi.filter(function(e) {
    return (e.data || '').startsWith(_annoCorrente + '-');
  });
}

// Filtra una lista di movimenti (array) secondo _annoCorrente
function _filtraMovimentiPerAnno(movimenti) {
  if (!_annoCorrente || _annoCorrente === 'tutti') return movimenti;
  var out = {};
  Object.keys(movimenti || {}).forEach(function(cat) {
    var sub = (movimenti[cat] || []).filter(function(m) {
      return (m.data || '').startsWith(_annoCorrente + '-');
    });
    if (sub.length > 0) out[cat] = sub;
  });
  return out;
}

// Ricalcola stock per un set di movimenti
function _calcolaStockFiltrato(movimenti, cat) {
  var movs = (movimenti && movimenti[cat]) || [];
  var c = 0, s = 0;
  movs.forEach(function(m) {
    var q = m.quantita || 0;
    if (m.tipo === 'carico') c += q; else s += q;
  });
  return c - s;
}

// ------------------------------------------------------------
// 1) WRAPPER: renderEventi
// ------------------------------------------------------------
(function() {
  if (typeof window.renderEventi !== 'function') return;
  var _orig = window.renderEventi;
  window.renderEventi = function() {
    if (_annoCorrente && _annoCorrente !== 'tutti' && typeof STATO !== 'undefined') {
      // Salva la lista originale
      var _backup = STATO.eventi;
      // Applica filtro temporaneo
      STATO.eventi = _filtraEventiPerAnno(_backup);
      try { var r = _orig.apply(this, arguments); } finally { STATO.eventi = _backup; }
      return r;
    }
    return _orig.apply(this, arguments);
  };
})();

// ------------------------------------------------------------
// 2) WRAPPER: aggiornaStatistiche (contatori Home)
// ------------------------------------------------------------
(function() {
  var nome = null;
  if (typeof window.aggiornaStatistiche === 'function') nome = 'aggiornaStatistiche';
  else if (typeof window.aggiornaStats === 'function') nome = 'aggiornaStats';
  if (!nome) return;
  var _orig = window[nome];
  window[nome] = function() {
    if (_annoCorrente && _annoCorrente !== 'tutti' && typeof STATO !== 'undefined') {
      var _bEv = STATO.eventi;
      var _bMov = STATO.movimenti;
      STATO.eventi = _filtraEventiPerAnno(_bEv);
      STATO.movimenti = _filtraMovimentiPerAnno(_bMov);
      try { var r = _orig.apply(this, arguments); } finally {
        STATO.eventi = _bEv;
        STATO.movimenti = _bMov;
      }
      return r;
    }
    return _orig.apply(this, arguments);
  };
})();

// ------------------------------------------------------------
// 3) WRAPPER: aggiornaEventiRecenti
// ------------------------------------------------------------
(function() {
  if (typeof window.aggiornaEventiRecenti !== 'function') return;
  var _orig = window.aggiornaEventiRecenti;
  window.aggiornaEventiRecenti = function() {
    if (_annoCorrente && _annoCorrente !== 'tutti' && typeof STATO !== 'undefined') {
      var _b = STATO.eventi;
      STATO.eventi = _filtraEventiPerAnno(_b);
      try { var r = _orig.apply(this, arguments); } finally { STATO.eventi = _b; }
      return r;
    }
    return _orig.apply(this, arguments);
  };
})();

// ------------------------------------------------------------
// 4) WRAPPER: renderMagazzino (con stock filtrato)
// ------------------------------------------------------------
(function() {
  if (typeof window.renderMagazzino !== 'function') return;
  var _orig = window.renderMagazzino;
  window.renderMagazzino = function() {
    if (_annoCorrente && _annoCorrente !== 'tutti' && typeof STATO !== 'undefined') {
      var _bMov = STATO.movimenti;
      var _bStock = STATO.stock;
      // Filtra movimenti
      var movFiltrati = _filtraMovimentiPerAnno(_bMov);
      STATO.movimenti = movFiltrati;
      // Ricalcola stock dai movimenti filtrati
      var nuovoStock = {};
      ['braccialetti', 'medaglie', 'adesivi', 'coppe'].forEach(function(cat) {
        nuovoStock[cat] = _calcolaStockFiltrato(movFiltrati, cat);
      });
      STATO.stock = nuovoStock;
      try { var r = _orig.apply(this, arguments); } finally {
        STATO.movimenti = _bMov;
        STATO.stock = _bStock;
      }
      return r;
    }
    return _orig.apply(this, arguments);
  };
})();

// ------------------------------------------------------------
// 5) WRAPPER: renderCalendario / aggiornaCalendario
// ------------------------------------------------------------
['renderCalendario', 'aggiornaCalendario', 'disegnaCalendario'].forEach(function(fn) {
  if (typeof window[fn] !== 'function') return;
  var _orig = window[fn];
  window[fn] = function() {
    if (_annoCorrente && _annoCorrente !== 'tutti' && typeof STATO !== 'undefined') {
      var _b = STATO.eventi;
      STATO.eventi = _filtraEventiPerAnno(_b);
      try { var r = _orig.apply(this, arguments); } finally { STATO.eventi = _b; }
      return r;
    }
    return _orig.apply(this, arguments);
  };
});

// ------------------------------------------------------------
// 6) WRAPPER: renderArchivio / renderArchivioTabella
// ------------------------------------------------------------
['renderArchivio', 'renderArchivioTabella', 'aggiornaArchivio'].forEach(function(fn) {
  if (typeof window[fn] !== 'function') return;
  var _orig = window[fn];
  window[fn] = function() {
    if (_annoCorrente && _annoCorrente !== 'tutti' && typeof STATO !== 'undefined') {
      var _b = STATO.eventi;
      STATO.eventi = _filtraEventiPerAnno(_b);
      try { var r = _orig.apply(this, arguments); } finally { STATO.eventi = _b; }
      return r;
    }
    return _orig.apply(this, arguments);
  };
});

// ------------------------------------------------------------
// 7) Wrapper: filtraEventi (chiamato dai filtri della pagina Eventi)
// ------------------------------------------------------------
(function() {
  if (typeof window.filtraEventi !== 'function') return;
  var _orig = window.filtraEventi;
  window.filtraEventi = function() {
    var r = _orig.apply(this, arguments);
    // Applica anche il filtro anno DOPO il filtro nativo
    if (_annoCorrente && _annoCorrente !== 'tutti') {
      var tbody = document.getElementById('listaEventi');
      if (tbody) {
        var righe = tbody.querySelectorAll('tr');
        // Non filtriamo manualmente: renderEventi gestisce gia' il filtro anno
      }
    }
    return r;
  };
})();

// ------------------------------------------------------------
// 8) Cambia anno -> ricarica TUTTO
// ------------------------------------------------------------
(function() {
  if (typeof window.cambiaAnno !== 'function') return;
  var _orig = window.cambiaAnno;
  window.cambiaAnno = function(anno) {
    var r = _orig.apply(this, arguments);
    // Ridisegna tutto dopo un attimo
    setTimeout(function() {
      try {
        if (typeof renderEventi === 'function') renderEventi();
        if (typeof aggiornaStatistiche === 'function') aggiornaStatistiche();
        if (typeof aggiornaEventiRecenti === 'function') aggiornaEventiRecenti();
        if (typeof renderMagazzino === 'function' && _paginaCorrente === 'magazzino') renderMagazzino();
        if (typeof renderCalendario === 'function') renderCalendario();
        if (typeof renderArchivio === 'function' && _paginaCorrente === 'archivio') renderArchivio();
      } catch (e) { console.warn('Errore refresh post-anno:', e); }
    }, 100);
    return r;
  };
})();

// ------------------------------------------------------------
// 9) Aggiorna label "sottotitolo" nella barra nav
// ------------------------------------------------------------
(function() {
  if (typeof window._aggiornaBarraNavigazione !== 'function') return;
  var _orig = window._aggiornaBarraNavigazione;
  window._aggiornaBarraNavigazione = function() {
    var r = _orig.apply(this, arguments);
    var sotto = document.getElementById('navSottotitolo');
    if (sotto && _annoCorrente && _annoCorrente !== 'tutti') {
      sotto.textContent = (sotto.textContent ? sotto.textContent + ' · ' : '') + 'anno ' + _annoCorrente;
    }
    return r;
  };
})();

console.log('Filtro anno globale applicato');
// ============================================================
// BACKUP CON SALVATAGGIO PERSONALIZZATO
// ============================================================
async function eseguiBackupConScelta() {
  try {
    // Chiama il backend
    var r = await fetch('/api/backup/ora', { method: 'POST' });
    var data = await r.json();

    if (!data.success) {
      alert('❌ Errore backup:\n\n' + (data.error || 'Errore sconosciuto'));
      return;
    }

    // Mostra popup con 2 scelte
    var vuoleCopia = confirm(
      '✅ Backup salvato con successo!\n\n' +
      '📁 Posizione: ' + data.percorso + '\n' +
      '📊 Dimensione: ' + data.dimensione_kb + ' KB\n\n' +
      '━━━━━━━━━━━━━━━━━━━━━━\n\n' +
      'Vuoi salvare anche una COPIA in un\'altra posizione?\n\n' +
      '• Clicca OK per scegliere dove salvarla\n' +
      '• Clicca Annulla per usare solo il backup nel sistema'
    );

    if (!vuoleCopia) {
      return; // L'utente è soddisfatto del backup nel sistema
    }

    // Apri il file picker per salvare la copia
    await salvaCopiaBackup(data.contenuto, data.file);

  } catch (e) {
    alert('❌ Errore di rete: ' + e.message);
  }
}

async function salvaCopiaBackup(contenuto, nomeSuggerito) {
  var blob = new Blob([contenuto], { type: 'application/json' });

  // Prova con showSaveFilePicker (Chrome, Edge)
  if (window.showSaveFilePicker) {
    try {
      var handle = await window.showSaveFilePicker({
        suggestedName: nomeSuggerito,
        types: [{
          description: 'File JSON di backup',
          accept: { 'application/json': ['.json'] }
        }]
      });
      var writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      alert('✅ Copia salvata in:\n' + handle.name);
      return;
    } catch (e) {
      if (e.name === 'AbortError') {
        // L'utente ha annullato: non è un errore
        return;
      }
      console.warn('showSaveFilePicker fallito, uso download classico:', e);
    }
  }

  // Fallback: download classico (Firefox, Safari, browser vecchi)
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = nomeSuggerito;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  alert('✅ Copia scaricata nella cartella Download:\n' + nomeSuggerito);
}

// ============================================================
// Sostituisci il pulsante "Backup" esistente
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    // Trova tutti i pulsanti che chiamano funzioni di backup
    var pulsanti = document.querySelectorAll('[onclick*="backup"], [onclick*="Backup"]');
    pulsanti.forEach(function(btn) {
      // Se chiama una funzione backup generica, sostituisci con la nuova
      var onclick = btn.getAttribute('onclick') || '';
      if (onclick.match(/backup(Ora|Manuale)?\s*\(\s*\)/i)) {
        btn.setAttribute('onclick', 'eseguiBackupConScelta()');
        console.log('Pulsante backup aggiornato:', btn);
      }
    });
  }, 500);
});
// ============================================================
// BILANCIO ANNUALE
// ============================================================
function _renderBarraFiltroBilancio(anniDisp, daSel, aSel) {
  var optsDa = (anniDisp || []).map(function(y) { return '<option value="' + y + '"' + (String(y) === String(daSel) ? ' selected' : '') + '>' + y + '</option>'; }).join('');
  var optsA = (anniDisp || []).map(function(y) { return '<option value="' + y + '"' + (String(y) === String(aSel) ? ' selected' : '') + '>' + y + '</option>'; }).join('');
  return '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px;background:#f8fafc;border:1px solid #e2e8f0;padding:12px 14px;border-radius:12px;margin-bottom:16px">' +
    '<span style="font-weight:700;color:#1e293b;font-size:13px">📊 Analisi Progressiva / Cumulativa:</span>' +
    '<label style="font-size:12px">Da anno:</label><select id="bilFiltroDa" style="width:auto;padding:6px 10px;margin:0">' + optsDa + '</select>' +
    '<label style="font-size:12px">A anno:</label><select id="bilFiltroA" style="width:auto;padding:6px 10px;margin:0">' + optsA + '</select>' +
    '<button class="btn btn-blue" style="padding:7px 14px;font-size:13px" onclick="filtraBilancioProgressivo()">🔍 Filtra Cumulativo</button>' +
    '<button class="btn btn-gray" style="padding:7px 14px;font-size:13px" onclick="caricaBilancioAnno(\'tutti\')">🌐 Tutti gli anni (Totale)</button></div>';
}
async function filtraBilancioProgressivo() {
  await caricaBilancioProgressivo(document.getElementById('bilFiltroDa')?.value || '', document.getElementById('bilFiltroA')?.value || '');
}
async function caricaBilancioProgressivo(da, a) {
  var cont = document.getElementById('bilancioContenuto');
  if (!cont) return;
  cont.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted)">⌛ Calcolo totale e progressione...</div>';
  try {
    var qs = [];
    if (da) qs.push('da=' + encodeURIComponent(da));
    if (a) qs.push('a=' + encodeURIComponent(a));
    var r = await fetch('/api/bilancio/progressivo' + (qs.length ? '?' + qs.join('&') : ''));
    var data = await r.json();
    if (!data.success) { cont.innerHTML = '<div style="color:red">Errore: ' + (data.error || '?') + '</div>'; return; }
    var b = data.dati;
    var lbl = (b.anno_da && b.anno_a) ? (b.anno_da === b.anno_a ? String(b.anno_da) : b.anno_da + ' - ' + b.anno_a) : 'Tutti gli anni';
    var html = _renderBarraFiltroBilancio(b.anni_disponibili, b.anno_da, b.anno_a);
    html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px">';
    html += '<div class="storico-stat" style="border-left-color:#16A34A"><div class="num" style="color:#16A34A">€ ' + _fmtNum(b.entrate.totale.toFixed(2)) + '</div><div class="label">💰 Entrate Totali (' + lbl + ')</div></div>';
    html += '<div class="storico-stat" style="border-left-color:#DC2626"><div class="num" style="color:#DC2626">€ ' + _fmtNum(b.uscite.totale.toFixed(2)) + '</div><div class="label">💸 Uscite Totali (' + lbl + ')</div></div>';
    html += '<div class="storico-stat" style="border-left-color:' + (b.ok ? '#16A34A' : '#DC2626') + '"><div class="num" style="color:' + (b.ok ? '#16A34A' : '#DC2626') + '">' + (b.margine >= 0 ? '+' : '') + '€ ' + _fmtNum(b.margine.toFixed(2)) + '</div><div class="label">' + (b.ok ? '✅' : '⚠️') + ' Margine Complessivo</div></div></div>';
    html += '<div class="storico-chart" style="overflow-x:auto"><h3 style="color:#0288D1;margin-bottom:10px">📈 Andamento Annuale e Progressivo Cumulativo</h3>';
    if (!b.righe || b.righe.length === 0) { html += '<div style="color:#90A4AE;padding:12px">Nessun dato nel periodo.</div>'; }
    else {
      html += '<table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr style="background:#f1f5f9;text-align:right">' +
        '<th style="padding:8px;text-align:left">Anno</th><th style="padding:8px;color:#16A34A">Entrate</th><th style="padding:8px;color:#DC2626">Uscite</th><th style="padding:8px">Margine</th>' +
        '<th style="padding:8px;background:#ecfdf5;color:#15803d">Entrate Cumul.</th><th style="padding:8px;background:#fef2f2;color:#b91c1c">Uscite Cumul.</th><th style="padding:8px;background:#eff6ff;color:#1d4ed8">Saldo Cumul.</th></tr></thead><tbody>';
      b.righe.forEach(function(rg) {
        var cM = rg.margine >= 0 ? '#16A34A' : '#DC2626', cC = rg.cum_margine >= 0 ? '#15803d' : '#b91c1c';
        html += '<tr style="border-bottom:1px solid #e2e8f0;text-align:right">' +
          '<td style="padding:8px;text-align:left;font-weight:700"><a href="#" onclick="caricaBilancioAnno(' + rg.anno + ');return false;" style="color:#0288D1;text-decoration:none">' + rg.anno + ' ↗</a></td>' +
          '<td style="padding:8px;color:#16A34A">€ ' + _fmtNum(rg.entrate.toFixed(2)) + '</td><td style="padding:8px;color:#DC2626">€ ' + _fmtNum(rg.uscite.toFixed(2)) + '</td>' +
          '<td style="padding:8px;font-weight:700;color:' + cM + '">' + (rg.margine >= 0 ? '+' : '') + '€ ' + _fmtNum(rg.margine.toFixed(2)) + '</td>' +
          '<td style="padding:8px;background:#f0fdf4;font-weight:600;color:#15803d">€ ' + _fmtNum(rg.cum_entrate.toFixed(2)) + '</td>' +
          '<td style="padding:8px;background:#fef2f2;font-weight:600;color:#b91c1c">€ ' + _fmtNum(rg.cum_uscite.toFixed(2)) + '</td>' +
          '<td style="padding:8px;background:#eff6ff;font-weight:800;color:' + cC + '">' + (rg.cum_margine >= 0 ? '+' : '') + '€ ' + _fmtNum(rg.cum_margine.toFixed(2)) + '</td></tr>';
      });
      html += '</tbody></table>';
    }
    html += '</div><div class="storico-chart"><h3 style="color:#475569;margin-bottom:10px">🧾 Ripartizione Uscite Totali (' + lbl + ')</h3><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px">' +
      '<div style="padding:10px;background:#ecfeff;border-radius:8px"><strong>📦 Magazzino:</strong> € ' + _fmtNum(b.uscite.magazzino.totale.toFixed(2)) + '</div>' +
      '<div style="padding:10px;background:#f5f3ff;border-radius:8px"><strong>🧰 Inventario:</strong> € ' + _fmtNum(b.uscite.inventario.totale.toFixed(2)) + '</div>' +
      '<div style="padding:10px;background:#fffbeb;border-radius:8px"><strong>🎁 Materiali:</strong> € ' + _fmtNum(b.uscite.materiali.totale.toFixed(2)) + '</div>' +
      '<div style="padding:10px;background:#f8fafc;border-radius:8px"><strong>💸 Altro:</strong> € ' + _fmtNum(b.uscite.altro.totale.toFixed(2)) + '</div></div></div>';
    cont.innerHTML = html;
  } catch (e) { cont.innerHTML = '<div style="color:red">Errore di rete: ' + e.message + '</div>'; }
}
function _renderBarraFiltroBilancio(anniDisp, daSel, aSel) {
  var oD = (anniDisp || []).map(y => '<option value="' + y + '"' + (String(y) === String(daSel) ? ' selected' : '') + '>' + y + '</option>').join('');
  var oA = (anniDisp || []).map(y => '<option value="' + y + '"' + (String(y) === String(aSel) ? ' selected' : '') + '>' + y + '</option>').join('');
  return '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px;background:#f8fafc;border:1px solid #e2e8f0;padding:12px;border-radius:12px;margin-bottom:16px"><strong>📊 Filtro Cumulativo:</strong> Da <select id="bilFiltroDa" style="width:auto;margin:0">' + oD + '</select> A <select id="bilFiltroA" style="width:auto;margin:0">' + oA + '</select> <button class="btn btn-blue" onclick="filtraBilancioProgressivo()">🔍 Filtra</button> <button class="btn btn-gray" onclick="caricaBilancioAnno(\'tutti\')">🌐 Tutti (Totale)</button></div>';
}
async function filtraBilancioProgressivo() { await caricaBilancioProgressivo(document.getElementById('bilFiltroDa')?.value || '', document.getElementById('bilFiltroA')?.value || ''); }
async function caricaBilancioProgressivo(da, a) {
  var cont = document.getElementById('bilancioContenuto'); if (!cont) return;
  cont.innerHTML = '<div style="text-align:center;padding:40px">⌛ Calcolo...</div>';
  var qs = []; if (da) qs.push('da=' + da); if (a) qs.push('a=' + a);
  var res = await fetch('/api/bilancio/progressivo' + (qs.length ? '?' + qs.join('&') : ''));
  var data = await res.json(); if (!data.success) { cont.innerHTML = 'Errore'; return; }
  var b = data.dati, lbl = (b.anno_da && b.anno_a) ? (b.anno_da + ' - ' + b.anno_a) : 'Tutti';
  var h = _renderBarraFiltroBilancio(b.anni_disponibili, b.anno_da, b.anno_a);
  h += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px">' +
    '<div class="storico-stat" style="border-left-color:#16A34A"><div class="num" style="color:#16A34A">€ ' + _fmtNum(b.entrate.totale.toFixed(2)) + '</div><div class="label">💰 Entrate Totali (' + lbl + ')</div></div>' +
    '<div class="storico-stat" style="border-left-color:#DC2626"><div class="num" style="color:#DC2626">€ ' + _fmtNum(b.uscite.totale.toFixed(2)) + '</div><div class="label">💸 Uscite Totali (' + lbl + ')</div></div>' +
    '<div class="storico-stat" style="border-left-color:' + (b.ok ? '#16A34A' : '#DC2626') + '"><div class="num" style="color:' + (b.ok ? '#16A34A' : '#DC2626') + '">' + (b.margine >= 0 ? '+' : '') + '€ ' + _fmtNum(b.margine.toFixed(2)) + '</div><div class="label">Margine Complessivo</div></div></div>';
  h += '<div class="storico-chart" style="overflow-x:auto"><h3>📈 Progressione Annuale e Cumulativa</h3><table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr style="background:#f1f5f9;text-align:right"><th style="padding:8px;text-align:left">Anno</th><th style="padding:8px">Entrate</th><th style="padding:8px">Uscite</th><th style="padding:8px">Margine</th><th style="padding:8px;background:#ecfdf5">Entrate Cum.</th><th style="padding:8px;background:#fef2f2">Uscite Cum.</th><th style="padding:8px;background:#eff6ff">Saldo Cum.</th></tr></thead><tbody>';
  (b.righe || []).forEach(rg => {
    h += '<tr style="border-bottom:1px solid #e2e8f0;text-align:right"><td style="padding:8px;text-align:left;font-weight:700"><a href="#" onclick="caricaBilancioAnno(' + rg.anno + ');return false">' + rg.anno + ' ↗</a></td><td style="padding:8px;color:#16A34A">€ ' + _fmtNum(rg.entrate.toFixed(2)) + '</td><td style="padding:8px;color:#DC2626">€ ' + _fmtNum(rg.uscite.toFixed(2)) + '</td><td style="padding:8px;font-weight:700">' + _fmtNum(rg.margine.toFixed(2)) + '</td><td style="padding:8px;background:#f0fdf4;font-weight:600">€ ' + _fmtNum(rg.cum_entrate.toFixed(2)) + '</td><td style="padding:8px;background:#fef2f2;font-weight:600">€ ' + _fmtNum(rg.cum_uscite.toFixed(2)) + '</td><td style="padding:8px;background:#eff6ff;font-weight:800">' + _fmtNum(rg.cum_margine.toFixed(2)) + '</td></tr>';
  });
  h += '</tbody></table></div>';
  cont.innerHTML = h;
}
async function caricaBilancioAnno(anno) {
  if (!anno || anno === 'tutti') return caricaBilancioProgressivo(null, null);
  if (!anno || anno === 'tutti') { return caricaBilancioProgressivo(null, null); }
  var cont = document.getElementById('bilancioContenuto');
  if (!cont) return;
  cont.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted)">&#8987; Caricamento...</div>';

  try {
    var r = await fetch('/api/bilancio/anno/' + anno);
    var data = await r.json();
    if (!data.success) {
      cont.innerHTML = '<div style="color:red">Errore: ' + (data.error || '?') + '</div>';
      return;
    }

    var b = data.dati;
    var html = '';

    // Riepilogo in alto
    html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px">';
    html += '<div class="storico-stat" style="border-left-color:#16A34A"><div class="num" style="color:#16A34A">&#8364; ' + _fmtNum(b.entrate.totale.toFixed(2)) + '</div><div class="label">&#128176; Entrate ' + anno + '</div></div>';
    html += '<div class="storico-stat" style="border-left-color:#DC2626"><div class="num" style="color:#DC2626">&#8364; ' + _fmtNum(b.uscite.totale.toFixed(2)) + '</div><div class="label">&#128184; Uscite ' + anno + '</div></div>';
    html += '<div class="storico-stat" style="border-left-color:' + (b.ok ? '#16A34A' : '#DC2626') + '"><div class="num" style="color:' + (b.ok ? '#16A34A' : '#DC2626') + '">' + (b.margine >= 0 ? '+' : '') + '&#8364; ' + _fmtNum(b.margine.toFixed(2)) + '</div><div class="label">' + (b.ok ? '&#9989;' : '&#9888;&#65039;') + ' Margine</div></div>';
    html += '</div>';

    // ENTRATE
    html += '<div class="storico-chart">';
    html += '<h3 style="color:#16A34A">&#128176; Entrate - &#8364; ' + _fmtNum(b.entrate.totale.toFixed(2)) + '</h3>';
    var tipi = Object.keys(b.entrate.voci_per_tipo);
    if (tipi.length === 0) {
      html += '<div style="color:#90A4AE;padding:12px">Nessuna entrata registrata per questo anno</div>';
    } else {
      tipi.forEach(function(tipo) {
        var voci = b.entrate.voci_per_tipo[tipo];
        var tot_tipo = voci.reduce(function(s, v) { return s + v.importo; }, 0);
        html += '<div style="margin-bottom:12px">';
        html += '<div style="font-weight:700;color:#16A34A;margin-bottom:6px;text-transform:capitalize">' + tipo + ' (&#8364; ' + _fmtNum(tot_tipo.toFixed(2)) + ')</div>';
        voci.forEach(function(v) {
          html += '<div class="storico-lista-item"><span><strong>' + v.data + '</strong> — ' + v.descrizione + '</span><strong>&#8364; ' + _fmtNum(v.importo.toFixed(2)) + '</strong></div>';
        });
        html += '</div>';
      });
    }
    html += '</div>';

    // USCITE - 4 categorie
    var categorie = [
      {key: 'magazzino', label: '&#128230; Magazzino', color: '#0891b2'},
      {key: 'inventario', label: '&#129520; Inventario', color: '#7C3AED'},
      {key: 'materiali', label: '&#127873; Materiali', color: '#F59E0B'},
      {key: 'altro', label: '&#128184; Altro', color: '#6b7280'},
    ];

    categorie.forEach(function(cat) {
      var d = b.uscite[cat.key];
      if (d.totale === 0 && d.voci.length === 0) return;
      html += '<div class="storico-chart">';
      html += '<h3 style="color:' + cat.color + '">' + cat.label + ' - &#8364; ' + _fmtNum(d.totale.toFixed(2)) + '</h3>';
      if (d.voci.length === 0) {
        html += '<div style="color:#90A4AE;padding:8px">Nessuna voce</div>';
      } else {
        d.voci.forEach(function(v) {
          html += '<div class="storico-lista-item"><span><strong>' + v.data + '</strong> — ' + v.descrizione + (v.quantita ? ' <span style="color:#90A4AE">(' + v.quantita + ' x ' + v.prezzo_unitario + ')' : '') + '</span><strong>&#8364; ' + _fmtNum(v.importo.toFixed(2)) + '</strong></div>';
        });
      }
      html += '</div>';
    });

    cont.innerHTML = html;
  } catch (e) {
    cont.innerHTML = '<div style="color:red">Errore di rete: ' + e.message + '</div>';
  }
}

// ============================================================
// Modali Entrata/Uscita
// ============================================================
var _catUscitaScelta = null;

function apriModaleEntrata() {
  document.getElementById('entrataId').value = '';
  document.getElementById('entrataData').value = new Date().toISOString().split('T')[0];
  document.getElementById('entrataImporto').value = '';
  document.getElementById('entrataDescrizione').value = '';
  document.getElementById('entrataTipo').value = 'contributo';
  document.getElementById('entrataNote').value = '';
  apriModale('modaleEntrata');
}

async function salvaEntrata() {
  var descrizione = document.getElementById('entrataDescrizione').value.trim();
  var importo = parseFloat(document.getElementById('entrataImporto').value) || 0;
  if (!descrizione || importo <= 0) {
    alert('Compila descrizione e importo');
    return;
  }

  var corpo = {
    data: document.getElementById('entrataData').value,
    descrizione: descrizione,
    importo: importo,
    tipo: document.getElementById('entrataTipo').value,
    note: document.getElementById('entrataNote').value,
  };

  try {
    var r = await fetch('/api/entrate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(corpo)
    });
    var data = await r.json();
    if (data.success) {
      chiudiModale('modaleEntrata');
      caricaBilancioAnno(_annoCorrente);
    } else {
      alert('Errore: ' + (data.error || '?'));
    }
  } catch (e) {
    alert('Errore di rete: ' + e.message);
  }
}

function apriModaleUscita() {
  _catUscitaScelta = null;
  document.getElementById('formUscitaDettagli').style.display = 'none';
  document.querySelectorAll('input[name="catUscita"]').forEach(function(r) { r.checked = false; });
  document.querySelectorAll('#modaleUscita label[onclick]').forEach(function(l) {
    l.style.borderColor = '#e0e6eb';
    l.style.background = 'white';
  });
  document.getElementById('uscitaData').value = new Date().toISOString().split('T')[0];
  document.getElementById('uscitaImporto').value = '';
  document.getElementById('uscitaDescrizione').value = '';
  document.getElementById('uscitaQuantita').value = '';
  document.getElementById('uscitaCostoUnitario').value = '';
  document.getElementById('uscitaNote').value = '';
  apriModale('modaleUscita');
}

function selezionaCategoriaUscita(cat, el) {
  _catUscitaScelta = cat;
  document.querySelectorAll('#modaleUscita label[onclick]').forEach(function(l) {
    l.style.borderColor = '#e0e6eb';
    l.style.background = 'white';
  });
  el.style.borderColor = '#0288D1';
  el.style.background = '#f0f8ff';
  document.getElementById('formUscitaDettagli').style.display = 'block';
}

async function salvaUscita() {
  if (!_catUscitaScelta) {
    alert('Scegli una categoria');
    return;
  }
  var descrizione = document.getElementById('uscitaDescrizione').value.trim();
  var importo = parseFloat(document.getElementById('uscitaImporto').value) || 0;
  if (!descrizione || importo <= 0) {
    alert('Compila descrizione e importo');
    return;
  }

  var data = document.getElementById('uscitaData').value;
  var quantita = parseInt(document.getElementById('uscitaQuantita').value) || 0;
  var costo = parseFloat(document.getElementById('uscitaCostoUnitario').value) || 0;
  var note = document.getElementById('uscitaNote').value;

  // Se magazzino: crea un movimento di carico
  if (_catUscitaScelta === 'magazzino') {
    alert('Per il magazzino usa la sezione Magazzino > Carico manuale.\nCosì scegli la categoria (braccialetti, medaglie, ecc.) e il costo unitario.');
    return;
  }

  // Se inventario o materiali: crea nell'entità rispettiva
  if (_catUscitaScelta === 'inventario') {
    try {
      var r = await fetch('/api/inventario', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          nome: descrizione,
          quantita: quantita || 1,
          valore_unitario: costo || importo,
          stato: 'nuovo',
          data_acquisto: data,
          note: note
        })
      });
      var d = await r.json();
      if (d.success) {
        chiudiModale('modaleUscita');
        caricaBilancioAnno(_annoCorrente);
      } else {
        alert('Errore: ' + (d.error || '?'));
      }
    } catch (e) {
      alert('Errore: ' + e.message);
    }
    return;
  }

  if (_catUscitaScelta === 'materiali') {
    try {
      var r2 = await fetch('/api/entita', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          nome: descrizione,
          categoria: 'Materiali',
          quantita: quantita || 1,
          costo_unitario: costo || importo,
          data_carico: data,
          note: note
        })
      });
      var d2 = await r2.json();
      if (d2.success) {
        chiudiModale('modaleUscita');
        caricaBilancioAnno(_annoCorrente);
      } else {
        alert('Errore: ' + (d2.error || '?'));
      }
    } catch (e) {
      alert('Errore: ' + e.message);
    }
    return;
  }

  // ALTRO: crea un'uscita generica
  try {
    var r3 = await fetch('/api/uscite', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        data: data,
        descrizione: descrizione,
        importo: importo,
        categoria: 'altro',
        note: note
      })
    });
    var d3 = await r3.json();
    if (d3.success) {
      chiudiModale('modaleUscita');
      caricaBilancioAnno(_annoCorrente);
    } else {
      alert('Errore: ' + (d3.error || '?'));
    }
  } catch (e) {
    alert('Errore: ' + e.message);
  }
}

// Carica il bilancio quando si apre la pagina
(function() {
  if (typeof window.mostra !== 'function') return;
  if (window._mostraWrapperBilancioFatto) return;
  window._mostraWrapperBilancioFatto = true;
  var _orig = window.mostra;
  window.mostra = function(page) {
    var r = _orig.apply(this, arguments);
    if (page === 'bilancio' && _annoCorrente !== 'tutti') {
      setTimeout(function() { caricaBilancioAnno(_annoCorrente); }, 200);
    }
    return r;
  };
})();

// Quando si cambia anno, ricarica il bilancio se siamo nella pagina
(function() {
  if (typeof window.cambiaAnno !== 'function') return;
  var _orig = window.cambiaAnno;
  window.cambiaAnno = function(anno) {
    var r = _orig.apply(this, arguments);
    if (typeof _paginaCorrente !== 'undefined' && _paginaCorrente === 'bilancio' && anno !== 'tutti') {
      setTimeout(function() { caricaBilancioAnno(anno); }, 200);
    }
    return r;
  };
})();

// ============================================================
// LIGHTBOX AVANZATO - Foto/Video con navigazione frecce
// ============================================================
var _lightboxFoto = [];
var _lightboxIndex = 0;
var _lightboxEventoId = null;

function _estVideo(nome) {
  return /\.(mp4|mov|webm|avi|mkv|m4v)$/i.test(nome);
}

function _urlFoto(nome) {
  return '/api/foto/file/' + encodeURIComponent(nome);
}

function apriLightboxAvanzato(foto, index, eventoId) {
  _lightboxFoto = foto || [];
  _lightboxIndex = index || 0;
  _lightboxEventoId = eventoId || null;
  _renderLightbox();
}

function _renderLightbox() {
  var vecchio = document.querySelector('.lightbox-foto');
  if (vecchio) vecchio.remove();
  if (_lightboxFoto.length === 0) return;

  var media = _lightboxFoto[_lightboxIndex];
  var filename = typeof media === 'string' ? media : (media.file || '');
  var didascalia = typeof media === 'object' ? (media.didascalia || '') : '';
  var tag = typeof media === 'object' ? (media.tag || []) : [];
  var isVideo = /\.(mp4|mov|webm|avi|mkv|m4v)$/i.test(filename);
  var url = '/api/foto/file/' + encodeURIComponent(filename);

  var html = '<div class="lightbox-foto" onclick="if(event.target===this) chiudiLightbox()">';
  html += '<div class="lightbox-toolbar">';
  html += '<button onclick="event.stopPropagation(); window.open(\'' + url + '\', \'_blank\')" title="Apri in browser">&#128279;</button>';
  html += '<button class="chiudi" onclick="event.stopPropagation(); chiudiLightbox()" title="Chiudi">&#10005;</button>';
  html += '</div>';

  if (_lightboxFoto.length > 1) {
    var prevDisabled = _lightboxIndex === 0 ? 'disabled' : '';
    var nextDisabled = _lightboxIndex === _lightboxFoto.length - 1 ? 'disabled' : '';
    html += '<button class="lightbox-nav lightbox-prev" ' + prevDisabled + ' onclick="event.stopPropagation(); navigaLightbox(-1)">&#8249;</button>';
    html += '<button class="lightbox-nav lightbox-next" ' + nextDisabled + ' onclick="event.stopPropagation(); navigaLightbox(1)">&#8250;</button>';
  }

  html += '<div class="lightbox-contenuto" onclick="event.stopPropagation()">';
  if (isVideo) {
    html += '<video src="' + url + '" controls autoplay style="max-height:60vh"></video>';
  } else {
    html += '<img src="' + url + '" alt="' + didascalia + '" style="max-height:60vh">';
  }

  // Campi didascalia e tag
  html += '<div style="margin-top:16px;padding:14px;background:rgba(255,255,255,0.08);border-radius:10px;width:100%;max-width:600px">';
  html += '<label style="color:rgba(255,255,255,0.7);font-size:11px;text-transform:uppercase;letter-spacing:1px;display:block;margin-bottom:6px">Didascalia</label>';
  html += '<input id="lbDidascalia" type="text" value="' + didascalia.replace(/"/g, '&quot;') + '" placeholder="Aggiungi una didascalia..." style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.2);background:rgba(0,0,0,0.3);color:white;font-size:14px;margin-bottom:10px">';

  html += '<label style="color:rgba(255,255,255,0.7);font-size:11px;text-transform:uppercase;letter-spacing:1px;display:block;margin-bottom:6px">Tag (separati da virgola)</label>';
  html += '<input id="lbTag" type="text" value="' + tag.join(', ') + '" placeholder="es. allestimento, premiazione, gazebo" style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.2);background:rgba(0,0,0,0.3);color:white;font-size:14px;margin-bottom:10px">';

  html += '<button onclick="salvaDidascaliaTag()" style="width:100%;padding:10px;background:linear-gradient(135deg,#0288D1,#01579B);color:white;border:none;border-radius:8px;cursor:pointer;font-weight:700;font-size:13px">&#128190; Salva</button>';
  html += '</div>';

  html += '</div>';

  if (_lightboxFoto.length > 1) {
    html += '<div class="lightbox-contatore" style="position:absolute;bottom:20px;left:50%;transform:translateX(-50%)">' + (_lightboxIndex + 1) + ' / ' + _lightboxFoto.length + '</div>';
  }

  html += '</div>';
  document.body.insertAdjacentHTML('beforeend', html);
}

async function salvaDidascaliaTag() {
  if (!_lightboxEventoId) {
    alert('Errore: nessun evento collegato. Apri il media da un evento.');
    return;
  }
  var media = _lightboxFoto[_lightboxIndex];
  var filename = typeof media === 'string' ? media : (media.file || '');
  var didascalia = (document.getElementById('lbDidascalia').value || '').trim();
  var tagStr = document.getElementById('lbTag').value || '';
  var tag = tagStr.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t; });

  try {
    var r = await fetch('/api/foto/aggiorna', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        evento_id: _lightboxEventoId,
        filename: filename,
        didascalia: didascalia,
        tag: tag
      })
    });
    var data = await r.json();
    if (data.success) {
      if (typeof media === 'object') {
        media.didascalia = didascalia;
        media.tag = tag;
      }
      alert('Salvato!');
      chiudiLightbox();
    } else {
      alert('Errore: ' + (data.error || '?') + '\n\n(Il backend potrebbe non essere ancora pronto)');
    }
  } catch (e) {
    alert('Errore di rete: ' + e.message);
  }
}


function navigaLightbox(direzione) {
  var nuovo = _lightboxIndex + direzione;
  if (nuovo < 0 || nuovo >= _lightboxFoto.length) return;
  _lightboxIndex = nuovo;
  _renderLightbox();
}

function chiudiLightbox() {
  var lb = document.querySelector('.lightbox-foto');
  if (lb) lb.remove();
}

// Navigazione con frecce tastiera
document.addEventListener('keydown', function(e) {
  var lb = document.querySelector('.lightbox-foto');
  if (!lb) return;
  
  if (e.key === 'Escape') chiudiLightbox();
  if (e.key === 'ArrowLeft') navigaLightbox(-1);
  if (e.key === 'ArrowRight') navigaLightbox(1);
});

// ============================================================
// Sostituisci renderFotoEvento per usare il lightbox avanzato
// ============================================================

// ============================================================
// HELPER: conta media di un evento
// ============================================================
function _contaMediaEvento(e) {
  var foto = (e && e.foto) || [];
  var video = (e && e.video) || [];
  var tot = foto.length + (Array.isArray(video) ? video.length : 0);
  return {
    foto: foto.length,
    video: Array.isArray(video) ? video.length : 0,
    totale: tot,
    haMedia: tot > 0
  };
}
function _getBadgeMedia(e) {
  var m = _contaMediaEvento(e);
  if (!m.haMedia) return '';
  var tooltip = m.foto + ' foto' + (m.video > 0 ? ', ' + m.video + ' video' : '');
  return ' <span style="display:inline-block;margin-left:6px;padding:2px 6px;background:#0288D1;color:white;border-radius:10px;font-size:10px;font-weight:700" title="' + tooltip + '">&#128248; ' + m.totale + '</span>';
}
// ============================================================
// Apri evento con scroll alla sezione foto/video
// ============================================================
function apriEventoConMedia(eventoId, tipo) {
  apriModaleEvento(eventoId);
  setTimeout(function() {
    var sezione = document.getElementById('sezioneFotoEvento');
    if (sezione) {
      sezione.scrollIntoView({ behavior: 'smooth', block: 'center' });
      sezione.style.transition = 'box-shadow 0.3s';
      sezione.style.boxShadow = '0 0 0 3px ' + (tipo === 'foto' ? '#0288D1' : '#DC2626');
      setTimeout(function() { sezione.style.boxShadow = ''; }, 1500);
    }
  }, 300);
}

// ============================================================
// GALLERIA - Carica tutti i media con filtri
// ============================================================
async function caricaGalleria() {
  var cont = document.getElementById('galleriaContenuto');
  if (!cont) return;
  cont.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:30px">Caricamento...</div>';

  var tag = (document.getElementById('galleriaTag')?.value || '').toLowerCase().trim();
  var tipo = (document.getElementById('galleriaTipo')?.value || '');

  try {
    var url = '/api/foto/galleria?';
    if (tag) url += 'tag=' + encodeURIComponent(tag) + '&';
    if (tipo) url += 'tipo=' + encodeURIComponent(tipo);

    var r = await fetch(url);
    var data = await r.json();

    if (!data.success) {
      cont.innerHTML = '<div style="grid-column:1/-1;color:red">Errore: ' + (data.error || '?') + '</div>';
      return;
    }

    var media = data.media || [];
    if (media.length === 0) {
      cont.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:30px">Nessun media trovato</div>';
      return;
    }

    var html = '';
    media.forEach(function(m) {
      var isVideo = m.tipo === 'video';
      var mediaUrl = '/api/foto/file/' + encodeURIComponent(m.file);
      html += '<div class="card" style="padding:8px;cursor:pointer" onclick="apriGalleriaLightbox(\'' + m.file + '\', \'' + m.tipo + '\', ' + m.evento_id + ', \'' + (m.didascalia || '').replace(/'/g, "\\'") + '\')">';
      html += '<div style="aspect-ratio:1;overflow:hidden;border-radius:8px;background:#eee;position:relative">';
      if (isVideo) {
        html += '<video src="' + mediaUrl + '" muted preload="metadata" style="width:100%;height:100%;object-fit:cover"></video>';
        html += '<div class="foto-play-icon" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:40px;height:40px;background:rgba(0,0,0,0.7);border-radius:50%;color:white;display:flex;align-items:center;justify-content:center;font-size:18px">&#9654;</div>';
      } else {
        html += '<img src="' + mediaUrl + '" style="width:100%;height:100%;object-fit:cover" loading="lazy">';
      }
      html += '</div>';
      html += '<div style="font-size:12px;font-weight:700;margin-top:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + (m.evento || '?') + '</div>';
      html += '<div style="font-size:11px;color:var(--text-muted)">' + (m.data || '') + '</div>';
      if (m.didascalia) html += '<div style="font-size:11px;font-style:italic;margin-top:2px">' + m.didascalia + '</div>';
      if (m.tag && m.tag.length > 0) {
        html += '<div style="font-size:10px;color:#0288D1;margin-top:2px">' + m.tag.join(', ') + '</div>';
      }
      html += '</div>';
    });
    cont.innerHTML = html;
  } catch (e) {
    cont.innerHTML = '<div style="grid-column:1/-1;color:red">Errore di rete: ' + e.message + '</div>';
  }
}

function apriGalleriaLightbox(filename, tipo, eventoId, didascalia) {
  var url = '/api/foto/file/' + encodeURIComponent(filename);
  var isVideo = /\.(mp4|mov|webm|avi|mkv|m4v)$/i.test(filename);

  var html = '<div class="lightbox-foto" onclick="if(event.target===this) this.remove()">';
  html += '<div class="lightbox-toolbar">';
  html += '<button class="chiudi" onclick="event.stopPropagation(); this.parentElement.parentElement.remove()" title="Chiudi">&#10005;</button>';
  html += '</div>';
  html += '<div class="lightbox-contenuto" onclick="event.stopPropagation()">';
  if (isVideo) {
    html += '<video src="' + url + '" controls autoplay style="max-height:80vh"></video>';
  } else {
    html += '<img src="' + url + '" alt="' + didascalia + '" style="max-height:80vh">';
  }
  if (didascalia) {
    html += '<div style="color:white;text-align:center;margin-top:14px;font-style:italic">' + didascalia + '</div>';
  }
  html += '</div></div>';
  document.body.insertAdjacentHTML('beforeend', html);
}

// Carica la galleria quando si apre la pagina
(function() {
  if (typeof window.mostra !== 'function') return;
  if (window._mostraWrapperGalleriaFatto) return;
  window._mostraWrapperGalleriaFatto = true;
  var _orig = window.mostra;
  window.mostra = function(page) {
    var r = _orig.apply(this, arguments);
    if (page === 'galleria') setTimeout(caricaGalleria, 200);
    return r;
  };
})();
// ============================================================
// RICERCA GLOBALE - Eventi, scuole, contatti, task, movimenti, media
// ============================================================
function apriRicercaGlobale() {
  apriModale('modaleRicercaGlobale');
  setTimeout(function() {
    var inp = document.getElementById('ricercaGlobaleInput');
    if (inp) { inp.value = ''; inp.focus(); }
    var res = document.getElementById('ricercaGlobaleRisultati');
    if (res) {
      res.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:30px">Digita per cercare in eventi, scuole, contatti, task, movimenti, inventario, materiali e media.</div>';
    }
  }, 100);
}

function eseguiRicercaGlobale(query) {
  var res = document.getElementById('ricercaGlobaleRisultati');
  if (!res) return;

  query = (query || '').toLowerCase().trim();
  if (query.length < 2) {
    res.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:30px">Digita almeno 2 caratteri per cercare.</div>';
    return;
  }

  var risultati = {
    eventi: [],
    scuole: [],
    contatti: [],
    task: [],
    movimenti: [],
    inventario: [],
    materiali: [],
    media: [],
  };

  // EVENTI
  (STATO.eventi || []).forEach(function(e) {
    var txt = (e.iniziativa || '') + ' ' + (e.luogo || '') + ' ' + (e.note || '') + ' ' + (e.data || '');
    if (txt.toLowerCase().indexOf(query) >= 0) {
      var sc = STATO.scuole.find(function(s) { return s.id === e.scuola_id; });
      risultati.eventi.push({
        titolo: (e.iniziativa || '(senza titolo)'),
        sotto: (e.data || '') + (sc ? ' — ' + sc.nome : ' — ALTRO'),
        id: e.id,
      });
    }
  });

  // SCUOLE
  (STATO.scuole || []).forEach(function(s) {
    var txt = (s.nome || '') + ' ' + (s.referente || '') + ' ' + (s.telefono || '') + ' ' + (s.email || '') + ' ' + (s.note || '');
    if (txt.toLowerCase().indexOf(query) >= 0) {
      risultati.scuole.push({
        titolo: s.nome || '(senza nome)',
        sotto: (s.tipo || '') + ' ' + (s.referente ? '— ' + s.referente : ''),
        id: s.id,
      });
    }
  });

  // CONTATTI
  (STATO.rubrica || []).forEach(function(c) {
    var txt = (c.nome || '') + ' ' + (c.telefono || '') + ' ' + (c.email || '') + ' ' + (c.ruolo || '') + ' ' + (c.note || '');
    if (txt.toLowerCase().indexOf(query) >= 0) {
      risultati.contatti.push({
        titolo: c.nome || '(senza nome)',
        sotto: (c.ruolo || '') + ' ' + (c.telefono || ''),
        id: c.id,
      });
    }
  });

  // TASK
  (STATO.task || []).forEach(function(t) {
    var txt = (t.titolo || '') + ' ' + (t.descrizione || '') + ' ' + (t.note || '') + ' ' + (t.referente || '');
    if (txt.toLowerCase().indexOf(query) >= 0) {
      risultati.task.push({
        titolo: t.titolo || '(senza titolo)',
        sotto: 'Scadenza: ' + (t.data_scadenza || '—') + ' — ' + (t.stato || ''),
        id: t.id,
      });
    }
  });

  // MOVIMENTI (da STATO.movimenti se caricato)
  ['braccialetti', 'medaglie', 'adesivi', 'coppe'].forEach(function(cat) {
    (STATO.movimenti?.[cat] || []).forEach(function(m) {
      var txt = (m.motivo || '') + ' ' + (m.nota_carico || '') + ' ' + (m.data || '') + ' ' + cat;
      if (txt.toLowerCase().indexOf(query) >= 0) {
        risultati.movimenti.push({
          titolo: m.tipo + ' ' + m.quantita + ' ' + cat,
          sotto: (m.data || '') + ' — ' + (m.motivo || ''),
          id: m.id,
        });
      }
    });
  });

  // INVENTARIO
  (STATO.inventario || []).forEach(function(o) {
    var txt = (o.nome || '') + ' ' + (o.note || '') + ' ' + (o.nota_carico || '');
    if (txt.toLowerCase().indexOf(query) >= 0) {
      risultati.inventario.push({
        titolo: o.nome || '(senza nome)',
        sotto: 'Qtà: ' + (o.quantita || 0) + ' — € ' + (o.valore_unitario || 0),
        id: o.id,
      });
    }
  });

  // MATERIALI (entità)
  (STATO.entita || []).forEach(function(m) {
    var txt = (m.nome || '') + ' ' + (m.categoria || '') + ' ' + (m.note || '') + ' ' + (m.fornitore || '');
    if (txt.toLowerCase().indexOf(query) >= 0) {
      risultati.materiali.push({
        titolo: m.nome || '(senza nome)',
        sotto: (m.categoria || '') + ' — Qtà: ' + (m.quantita || 0),
        id: m.id,
      });
    }
  });

  // MEDIA (foto/video con tag e didascalia)
  (STATO.eventi || []).forEach(function(e) {
    (e.foto || []).forEach(function(media) {
      if (typeof media !== 'object') return;
      var txt = (media.didascalia || '') + ' ' + (media.tag || []).join(' ') + ' ' + (e.iniziativa || '');
      if (txt.toLowerCase().indexOf(query) >= 0) {
        risultati.media.push({
          titolo: media.didascalia || media.file || 'Media',
          sotto: 'Evento: ' + (e.iniziativa || '') + ' — Tag: ' + (media.tag || []).join(', '),
          id: e.id,
          file: media.file,
        });
      }
    });
    (e.video || []).forEach(function(media) {
      if (typeof media !== 'object') return;
      var txt = (media.didascalia || '') + ' ' + (media.tag || []).join(' ') + ' ' + (e.iniziativa || '');
      if (txt.toLowerCase().indexOf(query) >= 0) {
        risultati.media.push({
          titolo: media.didascalia || media.file || 'Video',
          sotto: 'Video evento: ' + (e.iniziativa || '') + ' — Tag: ' + (media.tag || []).join(', '),
          id: e.id,
          file: media.file,
        });
      }
    });
  });

  // RENDER RISULTATI
  var gruppi = [
    { chiave: 'eventi', etichetta: '📅 Eventi', azione: 'eventi' },
    { chiave: 'scuole', etichetta: '🏫 Scuole', azione: 'scuole' },
    { chiave: 'contatti', etichetta: '📞 Contatti', azione: 'rubrica' },
    { chiave: 'task', etichetta: '✅ Task', azione: 'task' },
    { chiave: 'movimenti', etichetta: '📦 Movimenti', azione: 'magazzino' },
    { chiave: 'inventario', etichetta: '🧰 Inventario', azione: 'inventario' },
    { chiave: 'materiali', etichetta: '🎁 Materiali', azione: 'materiali' },
    { chiave: 'media', etichetta: '🖼️ Media (foto/video)', azione: 'eventi' },
  ];

  var html = '';
  var tot = 0;

  gruppi.forEach(function(g) {
    var lista = risultati[g.chiave] || [];
    if (lista.length === 0) return;
    tot += lista.length;
    html += '<div class="ric-result-gruppo">';
    html += '<div class="ric-result-gruppo-titolo">' + g.etichetta + ' (' + lista.length + ')</div>';
    lista.slice(0, 8).forEach(function(r) {
      var tipoClasse = g.chiave.slice(0, -1); // rimuove 'i' finale
      if (g.chiave === 'media') tipoClasse = 'media';
      html += '<div class="ric-result-item" onclick="vaiARisultato(\'' + g.azione + '\', ' + r.id + ')">';
      html += '<span class="ric-result-tipo ' + tipoClasse + '">' + g.etichetta.split(' ')[0] + '</span>';
      html += '<span class="ric-result-titolo">' + r.titolo + '</span>';
      html += '<div class="ric-result-sotto">' + r.sotto + '</div>';
      html += '</div>';
    });
    if (lista.length > 8) {
      html += '<div style="font-size:11px;color:var(--text-muted);padding:4px 12px">... e altri ' + (lista.length - 8) + '</div>';
    }
    html += '</div>';
  });

  if (tot === 0) {
    res.innerHTML = '<div class="ric-vuoto">Nessun risultato per "<strong>' + query + '</strong>"</div>';
  } else {
    res.innerHTML = '<div style="font-size:12px;color:var(--text-muted);margin-bottom:12px">' + tot + ' risultati trovati</div>' + html;
  }
}

function vaiARisultato(azione, id) {
  chiudiModale('modaleRicercaGlobale');
  if (typeof mostra === 'function') {
    mostra(azione);
  }
}

// Scorciatoia da tastiera: Ctrl+K
document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    apriRicercaGlobale();
  }
});

// ============================================================
// REFERENTE -> RUBRICA (dalla modale evento)
// ============================================================
function aggiungiReferenteARubrica() {
  var nome   = (id('eReferente')?.value || '').trim();
  var tel    = (id('eReferenteTel')?.value || '').trim();
  var email  = (id('eReferenteEmail')?.value || '').trim();
  var scuola = id('eScuola')?.value ? (id('eScuola').selectedOptions[0]?.textContent || '') : '';

  if (!nome) {
    alert('Inserisci prima il nome del referente.');
    id('eReferente')?.focus();
    return;
  }
  if (!tel && !email) {
    alert('Inserisci almeno un telefono o una email.');
    return;
  }

  var normNome = nome.toLowerCase().replace(/\s+/g, ' ').trim();
  var normTel  = tel.replace(/\s+/g, '').replace(/[^\d+]/g, '');
  var esistente = (STATO.rubrica || []).find(function(c) {
    var cNome = (c.nome || '').toLowerCase().replace(/\s+/g, ' ').trim();
    var cTel  = (c.telefono || '').replace(/\s+/g, '').replace(/[^\d+]/g, '');
    return (normNome && cNome === normNome) || (normTel && cTel === normTel);
  });

  var opts = { nome: nome, telefono: tel, email: email, scuola: scuola, ruolo: 'Referente', note: '' };

  if (esistente) {
    var msg = 'Contatto gia' + String.fromCharCode(39) + ' in rubrica:' + String.fromCharCode(10,10) +
              'Nome: ' + (esistente.nome || '-') + String.fromCharCode(10) +
              'Telefono: ' + (esistente.telefono || '-') + String.fromCharCode(10) +
              'Email: ' + (esistente.email || '-') + String.fromCharCode(10,10) +
              'OK = apri esistente | Annulla = crea nuovo';
    if (confirm(msg)) {
      apriModaleContatto(esistente.id);
      return;
    }
  }

  apriModaleContatto(null, opts);
}





// ============================================================

