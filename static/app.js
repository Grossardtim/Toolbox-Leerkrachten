(() => {
  document.querySelectorAll('[data-select-class]').forEach(row => {
    const selectClass = () => { window.location.href = row.dataset.selectClass; };
    row.querySelector('input[type="radio"]').addEventListener('change', selectClass);
    row.addEventListener('click', event => {
      if (event.target.closest('a,button,input,select,textarea,label') || window.getSelection()?.toString()) return;
      selectClass();
    });
  });
  const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('nl').trim();
  document.querySelectorAll('[data-browser]').forEach(browser => {
    const table = browser.querySelector('[data-table]');
    const body = table.tBodies[0];
    const originalRows = [...body.rows];
    const filters = [...table.querySelectorAll('[data-column-filter]')];
    const search = browser.querySelector('[data-table-search]');
    const buttons = [...table.querySelectorAll('[data-sort]')];
    buttons.forEach(button => button.setAttribute('aria-label', button.textContent.replace(/↕/g, '').trim()));
    let sortColumn = -1, direction = 1;
    const cellText = cell => cell.dataset.filterValue ?? cell.textContent;
    const update = () => {
      const words = normalize(search?.value || '').split(/\s+/).filter(Boolean);
      let shown = 0;
      originalRows.forEach(row => {
        const values = [...row.cells].map(cell => normalize(cellText(cell)));
        row.hidden = !words.every(word => values.join(' ').includes(word)) ||
          !filters.every((filter, i) => !filter.value || (filter.tagName === 'SELECT' ? values[i] === normalize(filter.value) : values[i].includes(normalize(filter.value))));
        if (!row.hidden) shown++;
      });
      browser.querySelector('[data-table-count]').textContent = `${shown} van ${originalRows.length}`;
      browser.querySelector('[data-table-empty]').hidden = shown !== 0;
    };
    search?.addEventListener('input', update);
    filters.forEach(filter => {
      filter.addEventListener('input', update);
      filter.addEventListener('change', update);
    });
    buttons.forEach((button, index) => button.addEventListener('click', () => {
      direction = sortColumn === index ? -direction : 1;
      sortColumn = index;
      buttons.forEach((item, i) => item.closest('th').setAttribute('aria-sort', i === index ? (direction === 1 ? 'ascending' : 'descending') : 'none'));
      const value = row => row.cells[index].dataset.sortValue ?? cellText(row.cells[index]).trim();
      const rows = [...originalRows].sort((a, b) => {
        const av = value(a), bv = value(b);
        const number = v => v !== '' && /^-?\d+(?:[.,]\d+)?$/.test(v);
        const compared = number(av) && number(bv) ? Number(av.replace(',', '.')) - Number(bv.replace(',', '.')) : av.localeCompare(bv, 'nl', {numeric: true, sensitivity: 'base'});
        return direction * compared;
      });
      rows.forEach(row => body.appendChild(row));
    }));
    browser.querySelector('[data-table-reset]').addEventListener('click', () => {
      if (search) search.value = '';
      filters.forEach(filter => { filter.value = ''; });
      sortColumn = -1; direction = 1;
      buttons.forEach(button => button.closest('th').setAttribute('aria-sort', 'none'));
      originalRows.forEach(row => body.appendChild(row));
      update();
    });
    update();
  });
  document.querySelectorAll('[data-select-lessons]').forEach(button => {
    button.addEventListener('click', () => document.querySelectorAll('#export-form input[name="lessons"]').forEach(input => { input.checked = button.dataset.selectLessons === 'all'; }));
  });
  const exportForm = document.getElementById('export-form');
  if (exportForm) {
    const toggleStudent = () => {
      const student = exportForm.querySelector('select[name="student"]');
      const individual = exportForm.querySelector('input[name="mode"]:checked')?.value === 'student';
      student.disabled = !individual;
      student.required = individual;
      document.getElementById('student-export-choice').hidden = !individual;
    };
    exportForm.querySelectorAll('input[name="mode"]').forEach(input => input.addEventListener('change', toggleStudent));
    toggleStudent();
    ['year', 'classroom'].forEach(name => exportForm.querySelector(`[name="${name}"]`).addEventListener('change', () => {
      if (name === 'year') exportForm.querySelector('[name="classroom"]').value = '';
      exportForm.querySelector('[name="subject"]').value = '';
      exportForm.querySelector('[name="student"]').value = '';
      exportForm.requestSubmit(document.getElementById('export-filter'));
    }));
    exportForm.addEventListener('submit', event => {
      if (event.submitter?.formMethod === 'get') {
        exportForm.querySelector('[name="csrfmiddlewaretoken"]').disabled = true;
        exportForm.querySelectorAll('[name="lessons"]').forEach(input => { input.disabled = true; });
        return;
      }
      document.getElementById('export-status').textContent = 'Het Excel-bestand wordt samengesteld. De download start zodra het klaar is.';
    });
  }
  let dirty = false;
  let submitting = false;
  const status = document.getElementById('save-status');
  const markDirty = (event) => {
    if (event?.target?.matches('[data-view-control]')) return;
    dirty = true;
    if (status) status.textContent = 'Niet-opgeslagen wijzigingen';
  };
  document.querySelectorAll('[data-dirty-form]').forEach(form => {
    form.addEventListener('input', markDirty);
    form.addEventListener('change', markDirty);
    form.addEventListener('submit', () => { submitting = true; });
  });
  window.addEventListener('beforeunload', e => {
    if (dirty && !submitting) { e.preventDefault(); e.returnValue = ''; }
  });
  document.querySelectorAll('select.score').forEach(select => {
    select.addEventListener('change', () => { select.dataset.score = select.value; });
  });
  // Goal changes submit separately. Require saving pending grades first.
  document.querySelectorAll('form.goal-action').forEach(form => {
    form.addEventListener('submit', e => {
      if (dirty) {
        e.preventDefault();
        alert('Sla eerst je scores en feedback op. Daarna kun je de doelen wijzigen.');
        return;
      }
      if (form.dataset.confirmRemove && !confirm('Verwijder '+form.dataset.confirmRemove+' en de bijbehorende scores uit deze les? Het leerplan zelf blijft behouden.')) e.preventDefault();
    });
  });
  const dropzone = document.getElementById('goal-dropzone');
  const scoreTable = document.querySelector('.score-table');
  let draggedGroup = null;
  const recordOrder = () => {
    document.getElementById('goal-order').value = [...scoreTable.querySelectorAll('[data-lesson-goal]')].map(group => group.dataset.lessonGoal).join(',');
    markDirty();
  };
  document.querySelectorAll('[data-lesson-goal]').forEach(group => {
    const filter = group.querySelector('[data-hide-empty]');
    if (filter) {
      const filterRows = () => {
        const label=group.querySelector('[data-fold-label]');
        if(label) label.textContent=filter.checked?'Lege rijen tonen':'Lege rijen verbergen';
        group.querySelectorAll('[data-score-row]').forEach(row => {
          row.hidden = filter.checked && [...row.querySelectorAll('select.score')].every(s => s.value === '');
        });
      };
      filter.addEventListener('change', filterRows);
      filterRows();
      group.querySelectorAll('select.score').forEach(s => s.addEventListener('change', filterRows));
    }
    const handle = group.querySelector('.drag-handle');
    let pointerStart = null, pointerTarget = null;
    const finishDrag = () => {
      draggedGroup = null; pointerStart = null; pointerTarget = null;
      document.querySelectorAll('.moving-goal,.goal-drop-target').forEach(el => el.classList.remove('moving-goal', 'goal-drop-target'));
    };
    handle.addEventListener('pointerdown', e => {
      if (e.button !== 0) return;
      e.preventDefault();
      pointerStart = e.clientY;
      draggedGroup = group;
      handle.setPointerCapture(e.pointerId);
    });
    handle.addEventListener('pointermove', e => {
      if (pointerStart === null || Math.abs(e.clientY - pointerStart) < 5) return;
      group.classList.add('moving-goal');
      const target = document.elementFromPoint(e.clientX, e.clientY)?.closest('[data-lesson-goal]');
      document.querySelectorAll('.goal-drop-target').forEach(el => el.classList.remove('goal-drop-target'));
      pointerTarget = target && target !== group ? target : null;
      pointerTarget?.classList.add('goal-drop-target');
    });
    handle.addEventListener('pointerup', e => {
      if (pointerTarget) {
        const groups = [...scoreTable.querySelectorAll('[data-lesson-goal]')];
        const movingDown = groups.indexOf(group) < groups.indexOf(pointerTarget);
        scoreTable.insertBefore(group, movingDown ? pointerTarget.nextElementSibling : pointerTarget);
        recordOrder();
      }
      if (handle.hasPointerCapture(e.pointerId)) handle.releasePointerCapture(e.pointerId);
      finishDrag();
    });
    handle.addEventListener('pointercancel', finishDrag);
    handle.addEventListener('lostpointercapture', finishDrag);
    group.querySelectorAll('[data-move-goal]').forEach(button => button.addEventListener('click', () => {
      const sibling = button.dataset.moveGoal === 'up' ? group.previousElementSibling : group.nextElementSibling;
      if (!sibling?.matches('[data-lesson-goal]')) return;
      scoreTable.insertBefore(group, button.dataset.moveGoal === 'up' ? sibling : sibling.nextElementSibling);
      recordOrder();
      button.focus();
    }));
  });
  document.querySelectorAll('[draggable][data-goal]').forEach(card => {
    card.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', card.dataset.goal);
      e.dataTransfer.effectAllowed = 'copy';
    });
  });
  if (dropzone) {
    dropzone.addEventListener('dragover', e => { if (draggedGroup) return; e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', e => {
      e.preventDefault(); dropzone.classList.remove('dragover');
      const id = e.dataTransfer.getData('text/plain');
      const form = [...document.querySelectorAll('[data-goal-form]')].find(f => f.dataset.goalForm === id);
      if (form) form.requestSubmit();
    });
  }
})();

// Compact navigation, screen space controls and live evaluation metrics.
(() => {
  document.querySelectorAll('details[data-active-module]').forEach(module => {
    module.addEventListener('toggle', () => { if (!module.open) module.open = true; });
  });
  const left = document.querySelector('[data-toggle-sidebar]');
  left?.addEventListener('click', () => {
    const closed = document.body.classList.toggle('sidebar-collapsed');
    left.setAttribute('aria-expanded', String(!closed));
  });
  document.querySelector('[data-toggle-tools]')?.addEventListener('click', event => {
    const closed = document.body.classList.toggle('tools-collapsed');
    event.currentTarget.setAttribute('aria-expanded', String(!closed));
  });
  document.querySelector('[data-fullscreen]')?.addEventListener('click', async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch { alert('Gebruik F11 of de volledig-schermoptie van je browser.'); }
  });
  const table = document.querySelector('.score-table:not(.coverage-table)');
  if (!table) return;
  const metrics = selects => {
    const values = selects.map(s => s.value);
    const numbers = values.filter(v => v !== '' && v !== 'absent').map(Number);
    const sum = numbers.reduce((a,b) => a+b,0);
    return {sum, count:numbers.length, possible:selects.length,
      absent:values.filter(v=>v==='absent').length, average:numbers.length?sum/numbers.length:null};
  };
  const decimal = value => value.toLocaleString('nl-BE',{minimumFractionDigits:1,maximumFractionDigits:1});
  const show = (cell, m) => {
    cell.replaceChildren();
    const title = document.createElement('strong');
    title.textContent = m.count ? decimal(m.average) : 'Nog geen cijfers';
    const detail = document.createElement('span'); detail.className='metric-detail';
    detail.textContent = m.count ? 'Totaal '+decimal(m.average*1.25)+'/100 · '+m.count+'/'+m.possible : '0/'+m.possible;
    cell.append(title,detail);
    if(m.absent) { const absent=document.createElement('span'); absent.className='metric-detail'; absent.textContent=m.absent+'× afwezig'; cell.append(absent); }
  };
  const update = () => {
    const groups=[...table.querySelectorAll('[data-lesson-goal]')];
    const allRows=[...table.querySelectorAll('[data-score-row]')];
    const pupilCount=table.tHead.rows[0].cells.length-1;
    const column=(rows,index)=>rows.map(row=>row.querySelectorAll('select.score')[index]).filter(Boolean);
    groups.forEach(group=>{
      const rows=[...group.querySelectorAll('[data-score-row]')];
      [...group.querySelector('.subtotal').cells].slice(1).forEach((cell,i)=>show(cell,metrics(column(rows,i))));
    });
    const foot=table.tFoot;
    if(foot) for(let i=0;i<pupilCount;i++){
      const m=metrics(column(allRows,i));
      foot.rows[0].cells[i+1].textContent=m.count+' / '+m.possible;
      foot.rows[1].cells[i+1].textContent=m.count?decimal(m.average*1.25)+'/100':'—';
      show(foot.rows[2].cells[i+1],m);
    }
    const all=metrics([...table.querySelectorAll('select.score')]);
    const overall=document.querySelector('.class-totals strong');
    if(overall) overall.textContent=all.count?decimal(all.average):'—';
    document.querySelectorAll('[data-result-goal]').forEach(row=>{
      const selects=allRows.filter(r=>r.dataset.sourceGoal===row.dataset.resultGoal).flatMap(r=>[...r.querySelectorAll('select.score')]);
      const m=metrics(selects);
      [m.count?decimal(m.average*1.25)+'/100':'—',m.count?decimal(m.average):'—',m.count,m.absent].forEach((value,i)=>row.cells[i+2].textContent=value);
      row.cells[3].dataset.sortValue=m.average??'';
    });
  };
  table.querySelectorAll('select.score').forEach(select=>select.addEventListener('change',update));
  update();
})();



// Desktop evaluation: a full-width workspace with a separate goal picker.
(() => {
  const dialog = document.querySelector('#lesson-goals-dialog');
  if (!dialog) return;
  const tabs = [...dialog.querySelectorAll('[data-goal-tab-button]')];
  const selectTab = key => {
    tabs.forEach(button => {
      const selected = button.dataset.goalTabButton === key;
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
    dialog.querySelectorAll('[data-goal-tab]').forEach(panel => panel.hidden = panel.dataset.goalTab !== key);
  };
  tabs.forEach(button => button.addEventListener('click', () => selectTab(button.dataset.goalTabButton)));
  if (tabs.length) selectTab(tabs[0].dataset.goalTabButton);
  document.querySelector('[data-open-goals]')?.addEventListener('click', () => dialog.showModal());
  dialog.querySelectorAll('[data-close-goals]').forEach(button=>button.addEventListener('click', () => dialog.close()));
  const all=dialog.querySelector('[data-select-curriculum]');
  const boxes=[...dialog.querySelectorAll('input[name=goals]:not(:disabled),input[name=points]:not(:disabled)')];
  const refresh=()=>{
    dialog.querySelectorAll('[data-goal]').forEach(row=>{
      const bk=row.querySelector('[data-select-bk]');
      const points=[...row.querySelectorAll('input[name=points]:not(:disabled)')];
      if(points.length) {
        bk.checked=points.every(p=>p.checked);
        bk.indeterminate=points.some(p=>p.checked)&&!bk.checked;
      }
    });
    const count=boxes.filter(b=>b.checked && (b.name==='points'||!b.closest('[data-goal]').querySelector('input[name=points]'))).length;
    dialog.querySelector('[data-selection-count]').textContent=count?count+' beoordelingspunten geselecteerd':'Nog niets geselecteerd';
    const submit=dialog.querySelector('[data-add-selection]');
    if(submit) submit.disabled=!count;
    if(all) {all.checked=boxes.length>0&&boxes.every(b=>b.checked);all.indeterminate=boxes.some(b=>b.checked)&&!all.checked;}
  };
  boxes.forEach(box=>box.addEventListener('change',()=>{
    if(box.matches('[data-select-bk]')) box.closest('[data-goal]').querySelectorAll('input[name=points]:not(:disabled)').forEach(p=>p.checked=box.checked);
    refresh();
  }));
  all?.addEventListener('change',()=>{boxes.forEach(b=>b.checked=all.checked);refresh();});
  refresh();
})();

(() => {
  const buttons = [...document.querySelectorAll('[data-editor-view]')];
  if (!buttons.length) return;
  const select = key => {
    document.body.dataset.editorView = key;
    buttons.forEach(button => {
      const active=button.dataset.editorView===key;
      button.classList.toggle('selected',active);
      button.setAttribute('aria-pressed',String(active));
    });
    document.querySelectorAll('[data-editor-panel]').forEach(panel => panel.hidden = panel.dataset.editorPanel!==key);
  };
  buttons.forEach(button => button.addEventListener('click',()=>select(button.dataset.editorView)));
  select('scores');
})();


// Shared desktop frame for every standard screen: title/filters stay fixed.
(() => {
  const main=document.querySelector('.page > main');
  if (!main || main.querySelector('.desktop-evaluation')) return;
  const titlebar=document.createElement('div');titlebar.className='workspace-titlebar';
  const editor=document.createElement('div');editor.className='workspace-editor';
  let contentStarted=false;
  [...main.children].forEach(element=>{
    const heading=element.matches('.heading-row,.eyebrow,h1,p,.management-nav,.filters,.stats,.notice');
    if(!heading) contentStarted=true;
    (contentStarted?editor:titlebar).appendChild(element);
  });
  main.classList.add('standard-workspace');
  main.append(titlebar,editor);

  // Handle goal and point removal with confirmation dialogs
  const lessonPk = window.location.pathname.split('/')[2];
  const formRevision = document.querySelector('input[name="revision"]')?.value || '';

  // Helper function to get CSRF token
  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  };

  // Handle BK (goal) removal
  document.querySelectorAll('[data-remove-goal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const goalId = btn.dataset.removeGoal;
      const goalCode = btn.dataset.confirmRemove;
      if (confirm(`Weet je zeker dat je BK "${goalCode}" en ALLE bijbehorende subdoelen en scores wilt verwijderen? Deze actie kan niet ongedaan worden gemaakt.`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/lesson/${lessonPk}/goal_action/`;
        form.innerHTML = `
          <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
          <input type="hidden" name="action" value="remove">
          <input type="hidden" name="goal" value="${goalId}">
          <input type="hidden" name="confirm" value="yes">
          <input type="hidden" name="revision" value="${formRevision}">
        `;
        document.body.appendChild(form);
        form.submit();
      }
    });
  });

  // Handle subdoel (point) removal
  document.querySelectorAll('[data-remove-point]').forEach(btn => {
    btn.addEventListener('click', () => {
      const pointId = btn.dataset.removePoint;
      const pointName = btn.dataset.confirmRemove;
      if (confirm(`Weet je zeker dat je subdoel "${pointName}" en de bijbehorende scores wilt verwijderen? Deze actie kan niet ongedaan worden gemaakt.`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/lesson/${lessonPk}/goal_action/`;
        form.innerHTML = `
          <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
          <input type="hidden" name="action" value="remove_point">
          <input type="hidden" name="point" value="${pointId}">
          <input type="hidden" name="confirm" value="yes">
          <input type="hidden" name="revision" value="${formRevision}">
        `;
        document.body.appendChild(form);
        form.submit();
      }
    });
  });

})();
