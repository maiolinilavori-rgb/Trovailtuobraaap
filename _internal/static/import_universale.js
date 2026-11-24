// ============================================================
// BRAAAP - Import universale (UI)
// ============================================================
// Funzioni:
//   - popolaGrigliaImporta()        : genera pulsanti per #grigliaImporta
//   - apriModaleImport(tipo)        : apre modale upload
//   - uploadFileImport(tipo)        : carica file, chiama /preview
//   - confermaImport(tipo)          : chiama /apply
//   - scaricaTemplate(tipo)         : scarica CSV di esempio
//   - chiudiModaleImport()          : chiude modale
// ============================================================

(function() {
  'use strict';

  // Tipi supportati (allineati a TIPI_SUPPORTATI in Python)
  var TIPI = [
    { id: 'eventi',      label: 'Eventi',              icona: '📅' },
    { id: 'scuole',      label: 'Scuole',              icona: '🏫' },
    { id: 'rubrica',     label: 'Rubrica',             icona: '📇' },
    { id: 'entita',      label: 'Entità / Materiali',  icona: '🎁' },
    { id: 'inventario',  label: 'Inventario',          icona: '📦' },
    { id: 'movimenti',   label: 'Movimenti magazzino', icona: '🔄' },
    { id: 'uscite',      label: 'Uscite',              icona: '💸' },
    { id: 'entrate',     label: 'Entrate',             icona: '💰' },
    { id: 'task',        label: 'Task',                icona: '✅' },
    { id: 'liste',       label: 'Liste',               icona: '📋' }
  ];

  // Stato globale per la modale
  var _stato = {
    tipo: null,
    righe_valide: [],
    strategy: 'skip'
  };

  // ----------------------------------------------------------
  // Griglia pulsanti "Importa sezione singola"
  // ----------------------------------------------------------
  window.popolaGrigliaImporta = function() {
    var griglia = document.getElementById('grigliaImporta');
    if (!griglia) return;

    var html = '';
    TIPI.forEach(function(t) {
      html += '<div style="padding:12px;border:1px solid #e2e8f0;border-radius:10px;background:#fff">';
      html += '<div style="font-weight:700;margin-bottom:8px">' + t.icona + ' ' + t.label + '</div>';
      html += '<button class="btn btn-blue" style="width:100%;padding:8px;font-size:13px" ';
      html += 'onclick="apriModaleImport(\'' + t.id + '\')">';
      html += '📥 Importa ' + t.label;
      html += '</button>';
      html += '<button class="btn btn-gray" style="width:100%;padding:6px;font-size:11px;margin-top:6px" ';
      html += 'onclick="scaricaTemplate(\'' + t.id + '\')">';
      html += '📋 Scarica template CSV';
      html += '</button>';
      html += '</div>';
    });
    griglia.innerHTML = html;
  };

  // ----------------------------------------------------------
  // Apri modale import
  // ----------------------------------------------------------
  window.apriModaleImport = function(tipo) {
    _stato.tipo = tipo;
    _stato.righe_valide = [];
    _stato.strategy = 'skip';

    var modale = document.getElementById('modaleImportUniversale');
    if (!modale) {
      alert('Modale import non trovato. Verifica index.html.');
      return;
    }

    var t = TIPI.find(function(x) { return x.id === tipo; });
    var titolo = t ? (t.icona + ' Importa ' + t.label) : ('Importa ' + tipo);

    document.getElementById('modaleImportTitolo').textContent = titolo;
    document.getElementById('modaleImportBody').innerHTML = _renderUploadForm(tipo);
    document.getElementById('modaleImportFooter').innerHTML = '';
    document.getElementById('modaleImportStato').textContent = '';

    modale.style.display = 'flex';
  };

  // ----------------------------------------------------------
  // Chiudi modale import
  // ----------------------------------------------------------
  window.chiudiModaleImport = function() {
    var modale = document.getElementById('modaleImportUniversale');
    if (modale) modale.style.display = 'none';
    _stato.tipo = null;
    _stato.righe_valide = [];
  };

  // ----------------------------------------------------------
  // Form di upload
  // ----------------------------------------------------------
  function _renderUploadForm(tipo) {
    var html = '';
    html += '<div style="padding:12px;background:#f8fafc;border-radius:8px;margin-bottom:16px;font-size:13px">';
    html += '<strong>Formato accettato:</strong> CSV (delimitatore <code>;</code> o <code>,</code>) oppure XLSX.<br>';
    html += '<strong>Intestazioni:</strong> la prima riga deve contenere i nomi delle colonne.';
    html += '</div>';

    html += '<div style="margin-bottom:16px">';
    html += '<label style="display:block;font-weight:700;margin-bottom:6px">File da importare</label>';
    html += '<input type="file" id="fileImportInput" accept=".csv,.xlsx,.xls,.txt" ';
    html += 'style="width:100%;padding:10px;border:2px dashed #cbd5e1;border-radius:10px;background:#fff">';
    html += '</div>';

    html += '<div id="importAnteprima" style="display:none"></div>';

    html += '<div style="text-align:right">';
    html += '<button class="btn btn-blue" onclick="uploadFileImport(\'' + tipo + '\')" ';
    html += 'style="padding:10px 20px;font-weight:700">';
    html += '📤 Carica e anteprima';
    html += '</button>';
    html += '</div>';

    return html;
  }

  // ----------------------------------------------------------
  // Upload file e chiama /preview
  // ----------------------------------------------------------
  window.uploadFileImport = function(tipo) {
    var input = document.getElementById('fileImportInput');
    if (!input || !input.files || !input.files[0]) {
      alert('Seleziona un file prima di caricare.');
      return;
    }

    var file = input.files[0];
    var formData = new FormData();
    formData.append('file', file);

    document.getElementById('modaleImportStato').textContent = '⏳ Analisi file in corso...';
    var cont = document.getElementById('importAnteprima');
    cont.style.display = 'block';
    cont.innerHTML = '<div style="padding:20px;text-align:center;color:#64748b">⏳ Analisi in corso...</div>';

    fetch('/api/import/' + tipo + '/preview', {
      method: 'POST',
      body: formData
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data.success) {
        cont.innerHTML = '<div style="padding:16px;background:#fef2f2;color:#dc2626;border-radius:8px">❌ ' + (data.error || 'Errore') + '</div>';
        document.getElementById('modaleImportStato').textContent = '';
        return;
      }
      _stato.righe_valide = data.righe_valide || [];
      _renderAnteprima(tipo, data);
    })
    .catch(function(e) {
      cont.innerHTML = '<div style="padding:16px;background:#fef2f2;color:#dc2626;border-radius:8px">❌ Errore di rete: ' + e.message + '</div>';
      document.getElementById('modaleImportStato').textContent = '';
    });
  };

  // ----------------------------------------------------------
  // Render anteprima
  // ----------------------------------------------------------
  function _renderAnteprima(tipo, data) {
    var cont = document.getElementById('importAnteprima');

    var html = '';
    html += '<div style="padding:12px;background:#eff6ff;border-left:4px solid #3b82f6;border-radius:8px;margin-bottom:12px">';
    html += '<strong>📊 Analisi completata:</strong> ';
    html += '<span style="color:#16a34a">✅ ' + data.valide + ' valide</span>';
    if (data.duplicati && data.duplicati.length > 0) {
      html += ' · <span style="color:#f59e0b">⚠️ ' + data.duplicati.length + ' duplicati</span>';
    }
    if (data.errori && data.errori.length > 0) {
      html += ' · <span style="color:#dc2626">❌ ' + data.errori.length + ' errori</span>';
    }
    html += ' · Totale righe: ' + data.totale_righe;
    html += '</div>';

    if (data.valide === 0) {
      html += '<div style="padding:16px;background:#fef2f2;color:#dc2626;border-radius:8px;text-align:center">';
      html += '❌ Nessuna riga valida da importare.<br>';
      html += '<small>Controlla che le colonne obbligatorie siano presenti.</small>';
      html += '</div>';
      cont.innerHTML = html;
      return;
    }

    // Anteprima prime righe
    html += '<div style="margin-bottom:12px"><strong>Anteprima prime ' + data.anteprima.length + ' righe valide:</strong></div>';
    html += '<div style="max-height:200px;overflow-x:auto;border:1px solid #e2e8f0;border-radius:8px">';
    html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';

    if (data.anteprima.length > 0) {
      var campi = Object.keys(data.anteprima[0]);
      html += '<thead><tr style="background:#f1f5f9;text-align:left">';
      campi.forEach(function(c) {
        html += '<th style="padding:6px;border-bottom:1px solid #e2e8f0">' + c + '</th>';
      });
      html += '</tr></thead><tbody>';
      data.anteprima.forEach(function(row) {
        html += '<tr>';
        campi.forEach(function(c) {
          var v = row[c];
          if (v === null || v === undefined) v = '';
          if (typeof v === 'object') v = JSON.stringify(v);
          html += '<td style="padding:6px;border-bottom:1px solid #f1f5f9">' + String(v).substring(0, 50) + '</td>';
        });
        html += '</tr>';
      });
      html += '</tbody>';
    }
    html += '</table>';
    html += '</div>';

    // Errori (primi 5)
    if (data.errori && data.errori.length > 0) {
      html += '<div style="margin-top:12px;padding:10px;background:#fffbeb;border-radius:8px;font-size:12px">';
      html += '<strong>⚠️ Primi errori:</strong><br>';
      data.errori.slice(0, 5).forEach(function(e) {
        html += '· Riga ' + e.riga + ': ' + e.messaggio + '<br>';
      });
      if (data.errori.length > 5) {
        html += '· ... e altri ' + (data.errori.length - 5) + ' errori';
      }
      html += '</div>';
    }

    // Duplicati (primi 3)
    if (data.duplicati && data.duplicati.length > 0) {
      html += '<div style="margin-top:12px;padding:10px;background:#fef3c7;border-radius:8px;font-size:12px">';
      html += '<strong>⚠️ ' + data.duplicati.length + ' duplicati trovati</strong> (saranno saltati)';
      html += '</div>';
    }

    // Strategy selector
    html += '<div style="margin-top:16px;padding:12px;background:#f8fafc;border-radius:8px">';
    html += '<label style="font-weight:700;margin-right:8px">Comportamento duplicati:</label>';
    html += '<select id="strategySelect" style="padding:6px;border-radius:6px;border:1px solid #cbd5e1">';
    html += '<option value="skip">Salta duplicati</option>';
    html += '<option value="update">Aggiorna esistenti</option>';
    html += '</select>';
    html += '</div>';

    // Bottone conferma
    html += '<div style="margin-top:16px;text-align:right">';
    html += '<button class="btn btn-green" onclick="confermaImport(\'' + tipo + '\')" ';
    html += 'style="padding:12px 24px;font-weight:800;font-size:14px">';
    html += '✅ Conferma import (' + data.valide + ' righe)';
    html += '</button>';
    html += '</div>';

    cont.innerHTML = html;
  }

  // ----------------------------------------------------------
  // Conferma import
  // ----------------------------------------------------------
  window.confermaImport = function(tipo) {
    var sel = document.getElementById('strategySelect');
    var strategy = sel ? sel.value : 'skip';

    if (_stato.righe_valide.length === 0) {
      alert('Nessuna riga valida da importare.');
      return;
    }

    document.getElementById('modaleImportStato').textContent = 'Importazione in corso...';

    fetch('/api/import/' + tipo + '/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        righe_valide: _stato.righe_valide,
        strategy: strategy
      })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data.success) {
        document.getElementById('modaleImportStato').textContent = 'Errore: ' + (data.error || '?');
        return;
      }

      var r = data.riepilogo;
      var msg = 'Import completato: ' + r.importati + ' importati';
      if (r.aggiornati > 0) msg += ', ' + r.aggiornati + ' aggiornati';
      if (r.saltati > 0) msg += ', ' + r.saltati + ' saltati';
      document.getElementById('modaleImportStato').textContent = msg;

      setTimeout(function() {
        chiudiModaleImport();
        if (typeof caricaTutto === 'function') {
          caricaTutto();
        } else {
          location.reload();
        }
      }, 2000);
    })
    .catch(function(e) {
      document.getElementById('modaleImportStato').textContent = 'Errore di rete: ' + e.message;
    });
  };

  // ----------------------------------------------------------
  // Scarica template CSV
  // ----------------------------------------------------------
  window.scaricaTemplate = function(tipo) {
    window.location.href = '/api/import/' + tipo + '/template';
  };

  console.log('[BRAAAP] import_universale.js caricato');

  // === STEP 6: Hook per popolare griglia importa quando si apre la pagina esporta ===
  // app.js definisce window.mostra (router). Lo wrappiamo per chiamare popolaGrigliaImporta().
  if (typeof window.mostra === 'function') {
    var _originalMostra = window.mostra;
    window.mostra = function(pagina) {
      _originalMostra.apply(this, arguments);
      if (pagina === 'importa') {
        // Doppio setTimeout per essere sicuri che il DOM sia pronto
        setTimeout(function() {
          try { popolaGrigliaImporta(); } catch(e) { console.warn('popolaGrigliaImporta:', e); }
        }, 50);
      }
    };
  }

  // Fallback: se l'utente ricarica direttamente su #page-importa, popola subito
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      var p = document.getElementById('page-importa');
      if (p && p.classList.contains('active')) {
        try { popolaGrigliaImporta(); } catch(e) { console.warn(e); }
      }
    });
  } else {
    // DOM già pronto
    var p = document.getElementById('page-importa');
    if (p && p.classList.contains('active')) {
      try { popolaGrigliaImporta(); } catch(e) { console.warn(e); }
    }
  }
})();