'use strict';
// This file changes only the knowledge-base tab in index-finder.html.
(() => {
  const key = 'mill-finder-knowledge-v1';
  const folder = (id, parent, name) => ({id, parent, name, type:'folder'});
  const file = (id, parent, name, content) => ({id, parent, name, type:'file', content});
  const mediaFile = (id, parent, name, type, src) => ({id, parent, name, type, src});
  const initial = [
    folder('root', null, 'Проект'),
    folder('brand', 'root', 'Бренд'),
    folder('products', 'brand', 'Товары'),
    folder('product-one', 'products', 'Контент-завод mill'),
    file('product-about', 'product-one', 'О продукте.md', '# Контент-завод mill\n\nПлатформа для подготовки, планирования, публикации и анализа короткого контента.\n\n## Кому помогает\nКомандам, которые регулярно выпускают короткие ролики.'),
    file('product-facts', 'product-one', 'Подтверждённые факты.txt', 'Продукт: Content Mill\nФормат: короткие ролики\nДлительность ролика: 15–35 секунд\nФормат кадра по умолчанию: 9:16'),
    folder('audiences', 'brand', 'Аудитории'),
    file('audience-main', 'audiences', 'Основная аудитория.md', '# Основная аудитория\n\nНебольшие команды и создатели контента, которым нужен понятный процесс от идеи до публикации.'),
    folder('brand-rules', 'brand', 'Правила бренда'),
    file('tone', 'brand-rules', 'Tone of Voice.md', '# Голос бренда\n\nПисать ясно и по делу. Показывать конкретный результат. Сохранять дружелюбный тон.'),
    file('restrictions', 'brand-rules', 'Запрещённые формулировки.txt', 'Не обещать гарантированные просмотры или продажи.\nНе публиковать неподтверждённые факты о продукте.'),
    file('sources', 'brand', 'Источники.md', '# Источники\n\nЗдесь хранятся ссылки на подтверждённые материалы бренда и товаров.'),
    folder('avatars', 'root', 'Аватары'),
    folder('avatar-main', 'avatars', 'Основной аватар'),
    file('avatar-consent', 'avatar-main', 'Согласие.md', '# Согласие\n\nДокумент согласия и его версия.'),
    folder('references', 'root', 'Референсы'),
    file('reference-one', 'references', 'Разбор монтажа.md', '# Разбор монтажа\n\nХук в первые секунды, один тезис на сцену, читаемые субтитры и короткий финальный призыв.'),
    folder('formulas', 'root', 'Формулы роликов'),
    file('formula-one', 'formulas', 'Проблема — решение.md', '# Проблема — решение\n\n1. Покажите знакомую проблему.\n2. Продемонстрируйте решение.\n3. Завершите конкретным действием.'),
    folder('prompts', 'root', 'Промпты'),
    ...[['common','Общие'],['instagram','Instagram'],['tiktok','TikTok'],['youtube','YouTube'],['telegram','Telegram'],['vk','VK']].map(([id,name]) => folder(`prompts-${id}`, 'prompts', name)),
    file('prompt-common', 'prompts-common', 'Сценарий.md', '# Промпт для сценария\n\nИспользуй подтверждённые факты о товаре и правила бренда. Предложи хук, основную мысль и финальную фразу.'),
    folder('videos', 'root', 'Ролики'),
    folder('video-123', 'videos', 'CM-000123'),
    folder('video-assets', 'video-123', 'Материалы'),
    folder('video-video', 'video-assets', 'Видео'),
    mediaFile('sample-video', 'video-video', 'Пример ролика.mp4', 'video', 'assets/knowledge/sample-video.mp4'),
    folder('video-audio', 'video-assets', 'Аудио'),
    mediaFile('sample-audio', 'video-audio', 'Пример озвучки.m4a', 'audio', 'assets/knowledge/sample-audio.m4a'),
    folder('video-images', 'video-assets', 'Изображения'),
    folder('video-scripts', 'video-123', 'Документы'),
    ...[
      ['01-brief.md', '# Задача\n\nКороткий ролик о том, как команда готовит контент в одном рабочем пространстве.'],
      ['02-sources.md', '# Источники\n\nТовар: Контент-завод mill.\nФормула: Проблема — решение.'],
      ['03-hooks.md', '# Хуки\n\nВариант 1: Сколько времени уходит на один короткий ролик?'],
      ['04-script.md', '# Сценарий\n\nХук: контент отнимает много времени.\nРешение: план, материалы и производство в одном месте.'],
      ['05-storyboard.md', '# Раскадровка\n\nСцена 1: проблема.\nСцена 2: интерфейс.\nСцена 3: готовый ролик.'],
      ['06-voice.md', '# Озвучка\n\nТон: спокойный и уверенный.'],
      ['07-avatar.md', '# Аватар\n\nИспользовать утверждённый образ.'],
      ['08-media.md', '# Медиа\n\nПроверить происхождение каждого кадра.'],
      ['09-animation.md', '# Анимация\n\nПлавные движения камеры и акценты на ключевых словах.'],
      ['10-edit.md', '# Монтаж\n\nБыстрый темп и читаемые субтитры.'],
      ['11-render.md', '# Рендер\n\nФормат: 9:16. Длительность: 30 секунд.'],
      ['12-review.md', '# Проверка\n\nПроверить звук, субтитры и утверждения о продукте.'],
      ['13-variants.md', '# Версии\n\nВерсия 1.'],
      ['14-publication.md', '# Публикация\n\nПодпись и площадки выбираются после проверки.']
    ].map(([name,content],i) => file(`script-${i+1}`, 'video-scripts', name, content)),
    file('edit-project', 'video-scripts', 'edit-project.json', '{\n  "format": "9:16",\n  "duration": 30\n}'),
    file('prompts-used', 'video-scripts', 'prompts-used.json', '{\n  "prompts": []\n}'),
    file('manifest', 'video-123', 'manifest.json', '{\n  "video": "CM-000123",\n  "version": 1\n}')
  ];
  let nodes;
  try { const saved = JSON.parse(localStorage.getItem(key)); nodes = Array.isArray(saved) && saved.some(n=>n.id==='root') ? saved : initial; }
  catch { nodes = initial; }
  for(const sample of initial.filter(node=>node.type==='video'||node.type==='audio')) {
    if(!nodes.some(node=>node.id===sample.id) && nodes.some(node=>node.id===sample.parent)) nodes.push(sample);
  }
  const consent=nodes.find(node=>node.id==='avatar-consent');
  if(consent?.content?.includes('Демо-запись.')) consent.content='# Согласие\n\nДокумент согласия и его версия.';
  const variants=nodes.find(node=>node.id==='script-13');
  if(variants?.content==='# Версии\n\nДемо-версия 1.') variants.content='# Версии\n\nВерсия 1.';
  let current = 'root';
  let query = '';
  let selected = null;
  const safe = value => escapeHTML(value);
  const get = id => nodes.find(node => node.id === id);
  const children = id => nodes.filter(node => node.parent === id).sort((a,b) => (a.type===b.type ? a.name.localeCompare(b.name,'ru') : a.type==='folder' ? -1 : 1));
  const lineage = id => { const path=[]; let node=get(id); while(node){path.unshift(node);node=get(node.parent);}return path; };
  const persist = () => { try {localStorage.setItem(key, JSON.stringify(nodes));} catch {toast('Не удалось сохранить изменения в браузере');} };
  const folderIcon = '<svg class="kb-folder-icon" viewBox="0 0 48 40" aria-hidden="true"><path fill="#51A2FF" d="M4 7a4 4 0 0 1 4-4h12l5 5h15a4 4 0 0 1 4 4v21a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/><path fill="#2783ED" d="M4 14h40v19a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/></svg>';
  const fileIcon = '<svg class="kb-file-icon" viewBox="0 0 36 42" aria-hidden="true"><path fill="currentColor" opacity=".15" d="M5 1h17l9 9v29a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2z"/><path fill="none" stroke="currentColor" stroke-width="2" d="M5 1h17l9 9v29a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2zM22 1v9h9M9 17h16M9 23h16M9 29h12"/></svg>';
  const mediaIcon = '<svg class="kb-file-icon" viewBox="0 0 36 42" aria-hidden="true"><rect x="3" y="5" width="30" height="32" rx="6" fill="currentColor" opacity=".15"/><path d="m14 13 12 8-12 8z" fill="currentColor"/></svg>';
  function tree(id, depth=0) {return children(id).filter(n=>n.type==='folder').map(n=>`<div class="kb-tree-branch"><button type="button" class="kb-tree-item ${current===n.id?'active':''}" data-kb="folder" data-id="${safe(n.id)}" style="--depth:${depth}">${folderIcon}<span>${safe(n.name)}</span><small>${children(n.id).length}</small></button>${tree(n.id,depth+1)}</div>`).join('');}
  function row(n) {const kind=n.type==='folder'?`${children(n.id).length} элементов`:n.type==='video'?'Видео · 5 секунд':n.type==='audio'?'Аудио · 5 секунд':n.name.split('.').pop().toUpperCase()+' · текстовый файл';return `<div class="kb-row ${selected===n.id?'selected':''}" data-kb-row="${safe(n.id)}" tabindex="0" role="button" aria-label="${n.type==='folder'?'Открыть папку':'Выбрать файл'} ${safe(n.name)}">${n.type==='folder'?folderIcon:n.type==='file'?fileIcon:mediaIcon}<div class="kb-row-copy"><strong>${safe(n.name)}</strong><small>${kind}</small></div>${n.type!=='folder'?`<button type="button" class="kb-open" data-kb="open" data-id="${safe(n.id)}">Открыть</button>`:'<span class="kb-row-arrow">›</span>'}</div>`;}
  function finderPage() {
    if(!get(current)) current='root';
    const matches=query.trim()?nodes.filter(n=>n.id!=='root'&&n.name.toLocaleLowerCase('ru').includes(query.trim().toLocaleLowerCase('ru'))):children(current);
    return `${heading('База знаний','Материалы бренда, товаров и каждого ролика в одном дереве.')}<section class="kb-shell"><div class="kb-toolbar"><div class="kb-crumbs" aria-label="Путь к папке">${lineage(current).map((n,i)=>`<button type="button" data-kb="folder" data-id="${safe(n.id)}">${i?' / ':''}${safe(n.name)}</button>`).join('')}</div><label class="kb-search"><svg aria-hidden="true"><use href="#i-search"/></svg><input id="kb-search" type="search" placeholder="Поиск файлов и папок" aria-label="Поиск файлов и папок" value="${safe(query)}"></label></div><div class="kb-layout"><aside class="kb-tree"><div class="kb-tree-title">ПАПКИ</div><button type="button" class="kb-tree-item ${current==='root'?'active':''}" data-kb="folder" data-id="root">${folderIcon}<span>Проект</span></button>${tree('root')}</aside><div class="kb-content"><div class="kb-content-head"><div><span class="kb-eyebrow">${query?'РЕЗУЛЬТАТЫ ПОИСКА':'СОДЕРЖИМОЕ ПАПКИ'}</span><h2>${safe(query?'Поиск':get(current).name)}</h2><p>${matches.length} элементов · дважды нажмите файл или выберите «Открыть»</p></div><div class="kb-actions"><button type="button" class="btn" data-kb="new-folder">+ Папка</button><button type="button" class="btn btn-gradient" data-kb="new-file">+ Файл</button></div></div><div class="kb-list">${matches.map(row).join('')||'<div class="kb-empty">Здесь пока нет файлов и папок.</div>'}</div></div></div></section>`;
  }
  window.brandPage = finderPage;
  const preview=document.createElement('dialog');
  preview.id='kb-preview';
  preview.className='kb-preview';
  preview.setAttribute('aria-labelledby','kb-preview-title');
  document.body.append(preview);
  preview.addEventListener('close',()=>{preview.querySelector('video,audio')?.pause();openId=null;});
  let openId=null;
  function previewBody(n, editing=false) {
    if(n.type==='video') return `<video class="kb-media" controls playsinline preload="metadata" src="${safe(n.src)}">Ваш браузер не поддерживает видео.</video>`;
    if(n.type==='audio') return `<div class="kb-audio-wrap"><audio controls preload="metadata" src="${safe(n.src)}">Ваш браузер не поддерживает аудио.</audio></div>`;
    return editing?`<label class="kb-editor-label" for="kb-editor">Содержимое файла</label><textarea id="kb-editor" class="kb-editor" spellcheck="false">${safe(n.content||'')}</textarea>`:`<pre class="kb-preview-text">${safe(n.content||'Файл пуст.')}</pre>`;
  }
  function drawPreview(n, editing=false) {
    const actions=n.type==='file'&&auth.canEdit('brand')?(editing?'<button type="button" class="btn btn-gradient" data-kb="save">Сохранить</button><button type="button" class="btn" data-kb="cancel-edit">Отменить</button>':'<button type="button" class="btn" data-kb="edit">Редактировать</button>'):'';
    preview.innerHTML=`<div class="kb-preview-head"><div>${n.type==='file'?fileIcon:mediaIcon}<div><h2 id="kb-preview-title">${safe(n.name)}</h2><p>${lineage(n.parent).map(p=>safe(p.name)).join(' / ')}</p></div></div><button type="button" class="kb-close" data-kb="close" aria-label="Закрыть">×</button></div>${previewBody(n,editing)}<div class="kb-preview-foot"><span>${n.type==='file'?'Документ':n.type==='video'?'Видео':'Аудио'}</span><div class="kb-preview-actions">${actions}<button type="button" class="btn" data-kb="close">Закрыть</button></div></div>`;
    if(editing)preview.querySelector('#kb-editor').focus();
  }
  function openFile(id) {const n=get(id);if(!n||n.type==='folder')return;selected=id;openId=id;drawPreview(n);preview.showModal();}
  function refresh() {render(true);const input=document.getElementById('kb-search');if(input&&query){input.focus();input.setSelectionRange(query.length,query.length);}}
  document.addEventListener('click',event=>{
    const action=event.target.closest('[data-kb]');if(!action)return;
    event.preventDefault();event.stopImmediatePropagation();
    const id=action.dataset.id;
    if(action.dataset.kb==='close'){preview.close();openId=null;return;}
    if(action.dataset.kb==='open'){openFile(id);return;}
    if(action.dataset.kb==='folder'){current=id;query='';selected=null;refresh();return;}
    if(!auth.canEdit('brand')){toast(authText().denied);return;}
    if(action.dataset.kb==='edit'){drawPreview(get(openId),true);return;}
    if(action.dataset.kb==='cancel-edit'){drawPreview(get(openId));return;}
    if(action.dataset.kb==='save'){const node=get(openId);node.content=preview.querySelector('#kb-editor').value;persist();drawPreview(node);toast('Файл сохранён');return;}
    const isFolder=action.dataset.kb==='new-folder';
    const name=window.prompt(isFolder?'Название папки':'Название файла (.md или .txt)',isFolder?'Новая папка':'Новый документ.md');
    if(name===null)return;
    const clean=name.trim();
    if(!clean || clean.length>100 || (!isFolder&&!/\.(md|txt)$/i.test(clean))){toast('Укажите название до 100 символов; файл должен иметь расширение .md или .txt');return;}
    if(children(current).some(n=>n.name.toLocaleLowerCase('ru')===clean.toLocaleLowerCase('ru'))){toast('Такое название уже есть в папке');return;}
    const node={id:'kb-'+Date.now()+'-'+Math.random().toString(36).slice(2,7),parent:current,name:clean,type:isFolder?'folder':'file'};
    if(!isFolder)node.content='# '+clean.replace(/\.(md|txt)$/i,'')+'\n\nНовый документ.';
    nodes.push(node);persist();refresh();if(!isFolder)openFile(node.id);
  },true);
  document.addEventListener('click',event=>{const row=event.target.closest('[data-kb-row]');if(!row||event.target.closest('[data-kb]'))return;selected=row.dataset.kbRow;document.querySelectorAll('.kb-row').forEach(item=>item.classList.toggle('selected',item.dataset.kbRow===selected));});
  document.addEventListener('dblclick',event=>{const row=event.target.closest('[data-kb-row]');if(!row)return;const n=get(row.dataset.kbRow);if(!n)return;if(n.type==='folder'){current=n.id;query='';refresh();}else openFile(n.id);});
  document.addEventListener('keydown',event=>{const row=event.target.closest('[data-kb-row]');if(row&&(event.key==='Enter'||event.key===' ')){event.preventDefault();const n=get(row.dataset.kbRow);if(n?.type==='folder'){current=n.id;query='';refresh();}else if(n)openFile(n.id);}});
  document.addEventListener('input',event=>{if(event.target.id!=='kb-search')return;query=event.target.value;refresh();});
  const css=document.createElement('style');css.textContent=`
  .kb-shell{background:var(--surface);border:1px solid var(--border);border-radius:18px;overflow:hidden;min-height:600px}
  .kb-toolbar{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 22px;border-bottom:1px solid var(--border)}
  .kb-crumbs{display:flex;flex-wrap:wrap;gap:3px}.kb-crumbs button{border:0;background:none;color:var(--muted);font-size:11px;cursor:pointer}.kb-crumbs button:last-child{color:var(--text);font-weight:700}
  .kb-search{display:flex;align-items:center;gap:8px;width:235px;padding:8px 10px;background:var(--control-bg);border:1px solid var(--border);border-radius:9px}.kb-search svg{width:15px;height:15px}.kb-search input{border:0;outline:0;background:none;color:var(--text);width:100%;font:inherit;font-size:11px}
  .kb-layout{display:grid;grid-template-columns:235px minmax(0,1fr);min-height:550px}.kb-tree{border-right:1px solid var(--border);padding:20px 12px;overflow:auto}.kb-tree-title,.kb-eyebrow{font-size:9px;letter-spacing:.12em;color:var(--faint);font-weight:750}.kb-tree-title{padding:0 12px 13px}.kb-tree-item{display:flex;align-items:center;gap:8px;width:100%;padding:7px 9px 7px calc(9px + var(--depth,0)*14px);border:0;border-radius:8px;background:none;text-align:left;color:var(--muted);cursor:pointer;font-size:11px}.kb-tree-item:hover,.kb-tree-item.active{background:var(--soft-blue);color:var(--accent)}.kb-tree-item span{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.kb-tree-item small{opacity:.6}.kb-folder-icon{width:28px;height:24px;flex:none}.kb-file-icon{width:24px;height:29px;flex:none;color:var(--accent)}
  .kb-content{min-width:0;padding:25px}.kb-content-head{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:22px}.kb-content-head h2{font-size:21px;margin:5px 0}.kb-content-head p{color:var(--muted);font-size:10px}.kb-actions{display:flex;gap:8px}.kb-actions .btn{white-space:nowrap}.kb-list{border:1px solid var(--border);border-radius:12px;overflow:hidden}.kb-row{display:flex;align-items:center;gap:15px;padding:12px 15px;min-height:65px;border-bottom:1px solid var(--border);cursor:pointer}.kb-row:last-child{border:0}.kb-row:hover,.kb-row:focus-visible,.kb-row.selected{background:var(--soft-blue);outline:0}.kb-row-copy{min-width:0;flex:1}.kb-row-copy strong{display:block;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.kb-row-copy small{display:block;font-size:9px;color:var(--muted);margin-top:5px}.kb-open{border:1px solid var(--border);background:var(--surface);color:var(--accent);border-radius:7px;padding:7px 10px;font-size:10px;cursor:pointer}.kb-row-arrow{font-size:24px;color:var(--faint)}.kb-empty{padding:50px;text-align:center;color:var(--muted);font-size:11px}
  .kb-preview{width:min(780px,calc(100vw - 30px));max-height:85vh;border:1px solid var(--border);border-radius:16px;padding:0;background:var(--surface);color:var(--text);box-shadow:0 25px 80px #0006}.kb-preview::backdrop{background:rgba(8,15,28,.72);backdrop-filter:blur(3px)}.kb-preview-head,.kb-preview-foot{display:flex;justify-content:space-between;align-items:center;padding:18px 23px;border-bottom:1px solid var(--border)}.kb-preview-head>div{display:flex;align-items:center;gap:13px}.kb-preview-head h2{font-size:16px;margin:0}.kb-preview-head p{font-size:10px;color:var(--muted);margin:4px 0 0}.kb-close{border:0;background:none;color:var(--muted);font-size:26px;cursor:pointer}.kb-preview-text{white-space:pre-wrap;overflow-wrap:anywhere;max-height:55vh;overflow:auto;margin:0;padding:28px 35px;line-height:1.8;font-size:13px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}.kb-preview-foot{border-top:1px solid var(--border);border-bottom:0;font-size:10px;color:var(--muted)}.kb-preview-actions{display:flex;gap:8px}.kb-editor-label{display:block;margin:20px 25px 8px;font-size:11px;color:var(--muted)}.kb-editor{display:block;width:calc(100% - 50px);min-height:300px;max-height:55vh;margin:0 25px 20px;padding:17px;border:1px solid var(--border);border-radius:10px;background:var(--control-bg);color:var(--text);resize:vertical;font:13px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace}.kb-media{display:block;width:100%;max-height:55vh;background:#111}.kb-audio-wrap{padding:45px 28px}.kb-audio-wrap audio{display:block;width:100%}
  @media(max-width:850px){.kb-layout{grid-template-columns:170px minmax(0,1fr)}.kb-content{padding:18px}.kb-content-head{align-items:flex-start;flex-direction:column}}@media(max-width:640px){.kb-toolbar{align-items:stretch;flex-direction:column}.kb-search{width:100%}.kb-layout{grid-template-columns:1fr}.kb-tree{border-right:0;border-bottom:1px solid var(--border);max-height:170px}.kb-content-head{gap:12px}.kb-preview-text{padding:20px}.kb-preview-foot{gap:10px}.kb-preview-actions{flex-wrap:wrap;justify-content:flex-end}}
  `;document.head.append(css);
  authCopy.ru.subtitle='Выберите роль и способ входа.';
  authCopy.ru.demo='Изменения сохраняются в браузере.';
  authCopy.en.subtitle='Choose a role and a sign-in option.';
  authCopy.en.demo='Changes are saved in this browser.';
  if(!auth.session||location.hash==='#brand')render();
})();
