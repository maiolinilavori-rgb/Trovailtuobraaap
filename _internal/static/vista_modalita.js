(function() {
  if (window._gestoreVisteCelleInit) return;
  window._gestoreVisteCelleInit = true;
  var css = document.createElement('style');
  css.textContent = [
    '.barra-vista-box{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:0 0 12px;padding:6px 10px;background:var(--card,#fff);border:1px solid rgba(148,163,184,.28);border-radius:10px}',
    '.barra-vista-grp{display:flex;align-items:center;gap:5px;flex-wrap:wrap}',
    '.btn-mode-sel{padding:5px 11px;border-radius:7px;border:1px solid rgba(148,163,184,.35);background:transparent;color:inherit;font-size:12px;font-weight:600;cursor:pointer}',
    '.btn-mode-sel.attivo{background:#0288D1;color:#fff;border-color:#0288D1}',
    '.pannello-colonne{display:none;margin:0 0 12px;padding:10px 12px;background:var(--card,#fff);border:1px solid #0288D1;border-radius:10px}',
    '.pannello-colonne.aperto{display:block}',
    '.col-resizer{position:absolute;top:0;right:-3px;width:8px;height:100%;cursor:col-resize;user-select:none;z-index:10;border-right:2px solid transparent;transition:border-color .15s}',
    '.col-resizer:hover,.col-resizer.attivo{border-right-color:#0288D1;background:rgba(2,136,209,.12)}',
    'table.tabella-ridimensionabile{table-layout:fixed!important}',
    'table.tabella-ridimensionabile th,table.tabella-ridimensionabile td{position:relative;overflow:hidden;text-overflow:ellipsis}',
    '.vista-compatta [id^="griglia"]>.card>*{position:relative;min-width:0}',
    '.col-chip{display:inline-flex;align-items:center;gap:5px;padding:4px 8px;margin:3px;border-radius:7px;background:rgba(2,136,209,.08);border:1px solid rgba(2,136,209,.25);font-size:12px}',
    '.col-chip button{border:none;background:rgba(0,0,0,.08);border-radius:4px;cursor:pointer;padding:1px 5px;font-size:11px;font-weight:700}',
    '.vista-compatta table{width:100%;border-collapse:collapse;font-size:12.5px}',
    '.vista-compatta table th{background:rgba(2,136,209,.08);padding:6px 8px!important;font-size:11.5px!important;text-transform:uppercase;white-space:nowrap}',
    '.vista-compatta table td{padding:5px 8px!important;border-bottom:1px solid rgba(148,163,184,.2)}',
    '.vista-compatta [id^="griglia"],.vista-compatta [id^="materialiContainer"]{display:flex!important;flex-direction:column!important;gap:4px!important}',
    '.vista-compatta [id^="griglia"]>.card,.vista-compatta [id^="materialiContainer"]>.card{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(140px,1fr))!important;align-items:center!important;gap:8px!important;padding:7px 12px!important;margin:0!important;border-radius:8px!important;font-size:12.5px!important}',
    '.vista-compatta [id^="griglia"]>.card h3{font-size:13.5px!important;margin:0!important}',
    '.vista-standard [id^="griglia"]{grid-template-columns:repeat(auto-fill,minmax(260px,1fr))!important;gap:12px!important}',
    '.vista-dettagli [id^="griglia"]{grid-template-columns:repeat(auto-fill,minmax(340px,1fr))!important;gap:16px!important}',
    '.vista-dettagli [id^="griglia"]>.card{padding:18px!important;font-size:14px!important;line-height:1.5!important}',
    '.vista-dettagli table td,.vista-dettagli table th{padding:10px 12px!important;font-size:13.5px!important}'
  ].join('\n');
  document.head.appendChild(css);
  var PAGINE=['page-inventario','page-eventi','page-scuole','page-magazzino','page-materiali','page-altro','page-rubrica','page-task','page-archivio','page-bilancio','page-liste'];
  function _getCfg(p){try{return JSON.parse(localStorage.getItem('braaap_cols_'+p)||'null');}catch(e){return null;}}
  function _setCfg(p,c){try{localStorage.setItem('braaap_cols_'+p,JSON.stringify(c));}catch(e){}}
  function _getW(p){try{return JSON.parse(localStorage.getItem('braaap_widths_'+p)||'{}');}catch(e){return {};}}
  function _setW(p,w){try{localStorage.setItem('braaap_widths_'+p,JSON.stringify(w));}catch(e){}}
  function _attivaResize(pid){
    var pg=document.getElementById(pid);if(!pg)return;setTimeout(function(){_attivaResize(pid);},20);
    var wmap=_getW(pid),tbl=pg.querySelector('table');
    if(tbl&&tbl.tHead&&tbl.tHead.rows.length){
      tbl.classList.add('tabella-ridimensionabile');
      var ths=Array.from(tbl.tHead.rows.item(0).cells);
      ths.forEach(function(th,i){
        var oi=th.dataset.oi||String(i);
        if(wmap[oi]){th.style.width=wmap[oi]+'px';th.style.minWidth=wmap[oi]+'px';}
        if(th.querySelector('.col-resizer'))return;
        var rz=document.createElement('span');rz.className='col-resizer';rz.title='Trascina per allargare/stringere';
        rz.onmousedown=function(e){
          e.preventDefault();e.stopPropagation();rz.classList.add('attivo');
          var startX=e.clientX,startW=th.getBoundingClientRect().width;
          function onMove(ev){var nw=Math.max(48,Math.round(startW+(ev.clientX-startX)));th.style.width=nw+'px';th.style.minWidth=nw+'px';wmap[oi]=nw;}
          function onUp(){rz.classList.remove('attivo');document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);_setW(pid,wmap);}
          document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',onUp);
        };
        th.appendChild(rz);
      });
      tbl.querySelectorAll('td').forEach(function(td){var txt=(td.textContent||'').trim();if(/^[\d.,\s€+-]+$/.test(txt))td.style.whiteSpace='nowrap';});
      return;
    }
    var gr=pg.querySelector('[id^="griglia"],[id^="materialiContainer"]');
    if(gr&&gr.children.length&&pg.classList.contains('vista-compatta')){
      var cards=Array.from(gr.children),cols=[];
      cards.forEach(function(card){
        Array.from(card.children).forEach(function(cell,i){
          var oi=cell.dataset.oi||String(i);cols[i]=wmap[oi]?wmap[oi]+'px':'minmax(110px,1fr)';
          if(cell.style.display==='none')cols[i]='0px';
          if(cell.querySelector('.col-resizer'))return;
          var rz=document.createElement('span');rz.className='col-resizer';rz.title='Trascina per allargare/stringere';
          rz.onmousedown=function(e){
            e.preventDefault();e.stopPropagation();rz.classList.add('attivo');
            var startX=e.clientX,startW=cell.getBoundingClientRect().width;
            function onMove(ev){
              var nw=Math.max(55,Math.round(startW+(ev.clientX-startX)));wmap[oi]=nw;
              cards.forEach(function(c2){var tpl=Array.from(c2.children).map(function(k,idx){if(k.style.display==='none')return'';var koi=k.dataset.oi||String(idx);return wmap[koi]?wmap[koi]+'px':'minmax(110px,1fr)';}).filter(Boolean).join(' ');c2.style.setProperty('grid-template-columns',tpl,'important');});
            }
            function onUp(){rz.classList.remove('attivo');document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);_setW(pid,wmap);}
            document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',onUp);
          };
          cell.appendChild(rz);
        });
        var tplInit=Array.from(card.children).map(function(k,idx){if(k.style.display==='none')return'';var koi=k.dataset.oi||String(idx);return wmap[koi]?wmap[koi]+'px':'minmax(110px,1fr)';}).filter(Boolean).join(' ');
        if(tplInit)card.style.setProperty('grid-template-columns',tplInit,'important');
      });
    }
  }
  function applicaCelle(pid){
    var pg=document.getElementById(pid);if(!pg)return;setTimeout(function(){_attivaResize(pid);},20);
    var cfg=_getCfg(pid),tbl=pg.querySelector('table');
    if(tbl&&tbl.tHead&&tbl.tHead.rows.length){
      var ths=Array.from(tbl.tHead.rows.item(0).cells);
      ths.forEach(function(th,i){if(!th.dataset.oi){th.dataset.oi=i;th.dataset.on=(th.textContent||('Col '+(i+1))).trim();}});
      if(!cfg||!Array.isArray(cfg.ordine)||cfg.ordine.length!==ths.length)cfg={ordine:ths.map(function(_,i){return i;}),nascoste:[]};
      var rows=[tbl.tHead.rows.item(0)].concat(tbl.tBodies.length?Array.from(tbl.tBodies.item(0).rows):[]);
      rows.forEach(function(tr){
        var cs=Array.from(tr.cells);if(cs.length!==ths.length)return;
        var m={};cs.forEach(function(c,i){if(!c.dataset.oi)c.dataset.oi=i;m[c.dataset.oi]=c;});
        cfg.ordine.forEach(function(oi){var el=m[oi];if(!el)return;el.style.display=cfg.nascoste.indexOf(oi)!==-1?'none':'';tr.appendChild(el);});
      });return;
    }
    var gr=pg.querySelector('[id^="griglia"],[id^="materialiContainer"]');
    if(gr&&gr.children.length&&cfg&&Array.isArray(cfg.ordine)){
      Array.from(gr.children).forEach(function(card){
        var bs=Array.from(card.children),m={};bs.forEach(function(b,i){if(!b.dataset.oi)b.dataset.oi=i;m[b.dataset.oi]=b;});
        cfg.ordine.forEach(function(oi){var el=m[oi];if(!el)return;el.style.display=cfg.nascoste.indexOf(oi)!==-1?'none':'';card.appendChild(el);});
      });
    }
  }
  function renderPan(pid){
    var pg=document.getElementById(pid),pan=pg&&pg.querySelector('.pannello-colonne');if(!pan)return;
    var nomi=[],tbl=pg.querySelector('table');
    if(tbl&&tbl.tHead&&tbl.tHead.rows.length){
      Array.from(tbl.tHead.rows.item(0).cells).forEach(function(th,i){var oi=parseInt(th.dataset.oi||i,10);nomi[oi]=th.dataset.on||('Col '+(oi+1));});
    }else{
      var gr=pg.querySelector('[id^="griglia"],[id^="materialiContainer"]'),pr=gr&&gr.firstElementChild;
      if(pr)Array.from(pr.children).forEach(function(el,i){var oi=parseInt(el.dataset.oi||i,10);var t=(el.textContent||'').trim().replace(/\s+/g,' ').slice(0,18);nomi[oi]='Cella '+(oi+1)+(t?' ('+t+')':'');});
    }
    if(!nomi.length){pan.innerHTML='<small>Nessuna cella configurabile qui.</small>';return;}
    var cfg=_getCfg(pid);if(!cfg||!Array.isArray(cfg.ordine)||cfg.ordine.length!==nomi.length){cfg={ordine:nomi.map(function(_,i){return i;}),nascoste:[]};_setCfg(pid,cfg);}
    var h='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:6px"><strong style="font-size:12px">🎛️ Posizione celle (salvata in automatico)</strong><div style="display:flex;gap:5px"><button type="button" class="btn-mode-sel" data-act="rst">↺ Reset</button><button type="button" class="btn-mode-sel attivo" data-act="ok">✓ Fine</button></div></div><div>';
    cfg.ordine.forEach(function(oi,pos){
      var vis=cfg.nascoste.indexOf(oi)===-1;
      h+='<span class="col-chip"><input type="checkbox" data-oi="'+oi+'" '+(vis?'checked':'')+'> '+nomi.at(oi)+(pos>0?' <button type="button" data-mv="-1" data-p="'+pos+'">◀</button>':'')+(pos<cfg.ordine.length-1?' <button type="button" data-mv="1" data-p="'+pos+'">▶</button>':'')+'</span>';
    });
    pan.innerHTML=h+'</div>';
    pan.querySelectorAll('input').forEach(function(cb){cb.onchange=function(){var oi=parseInt(cb.dataset.oi,10),ix=cfg.nascoste.indexOf(oi);if(cb.checked&&ix!==-1)cfg.nascoste.splice(ix,1);if(!cb.checked&&ix===-1)cfg.nascoste.push(oi);_setCfg(pid,cfg);applicaCelle(pid);};});
    pan.querySelectorAll('button[data-mv]').forEach(function(b){b.onclick=function(){var p=parseInt(b.dataset.p,10),t=p+parseInt(b.dataset.mv,10),x=cfg.ordine.at(p);cfg.ordine.splice(p,1);cfg.ordine.splice(t,0,x);_setCfg(pid,cfg);applicaCelle(pid);renderPan(pid);};});
    pan.querySelector('[data-act="rst"]').onclick=function(){localStorage.removeItem('braaap_cols_'+pid);localStorage.removeItem('braaap_widths_'+pid);location.reload();};
    pan.querySelector('[data-act="ok"]').onclick=function(){pan.classList.remove('aperto');};
  }
  function setVista(pid,m){
    var pg=document.getElementById(pid);if(!pg)return;setTimeout(function(){_attivaResize(pid);},20);
    pg.classList.remove('vista-compatta','vista-standard','vista-dettagli','vista-pag-compatta','vista-pag-estesa','vista-pag-dettagli');
    pg.classList.add('vista-'+m);try{localStorage.setItem('braaap_mode_'+pid,m);}catch(e){}
    pg.querySelectorAll('.btn-mode-sel[data-m]').forEach(function(b){b.classList.toggle('attivo',b.dataset.m===m);});
    applicaCelle(pid);
  }
  document.addEventListener('DOMContentLoaded',function(){
    document.querySelectorAll('.barra-viste').forEach(function(e){(e.parentElement||e).remove();});
    PAGINE.forEach(function(pid){
      var pg=document.getElementById(pid);if(!pg)return;setTimeout(function(){_attivaResize(pid);},20);
      if(!pg.querySelector('.barra-vista-box')){
        var box=document.createElement('div');box.className='barra-vista-box';
        box.innerHTML='<div class="barra-vista-grp"><span style="font-size:11.5px;font-weight:700;opacity:.75;margin-right:4px">Vista:</span><button type="button" class="btn-mode-sel" data-m="compatta">☰ Compatta</button><button type="button" class="btn-mode-sel" data-m="standard">⊞ Standard</button><button type="button" class="btn-mode-sel" data-m="dettagli">📇 Dettagli</button></div><button type="button" class="btn-mode-sel" data-act="cols">⚙️ Celle / Colonne</button>';
        var pan=document.createElement('div');pan.className='pannello-colonne';
        pg.insertBefore(pan,pg.firstChild);pg.insertBefore(box,pan);
        box.querySelectorAll('[data-m]').forEach(function(b){b.onclick=function(){setVista(pid,b.dataset.m);};});
        box.querySelector('[data-act="cols"]').onclick=function(){pan.classList.toggle('aperto');if(pan.classList.contains('aperto'))renderPan(pid);};
      }
      setVista(pid,localStorage.getItem('braaap_mode_'+pid)||'standard');
    });
    setInterval(function(){PAGINE.forEach(function(pid){var pg=document.getElementById(pid);if(pg&&pg.classList.contains('attiva'))applicaCelle(pid);});},700);
  });
})();


