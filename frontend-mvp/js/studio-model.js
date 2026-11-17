(function (root) {
  'use strict';
  const clone = value => JSON.parse(JSON.stringify(value));
  const id = prefix => `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,8)}`;
  const day = ms => new Date(ms + 3 * 3600000).toISOString().slice(0,10);
  const addDays = (date, amount) => new Date(Date.parse(`${date}T12:00:00Z`) + amount * 86400000).toISOString().slice(0,10);
  const monday = ms => { const date = day(ms); const weekday = new Date(`${date}T12:00:00Z`).getUTCDay(); return addDays(date, -(weekday || 7) + 1); };
  const platforms = ['Instagram Reels','YouTube Shorts','VK Клипы','Telegram','TikTok'];
  const videoSteps = ['Изучаю товар и нишу','Пишу сценарий под формат','Озвучка','Генерирую сцены','Монтаж: переходы, текст, музыка','Обложка и проверка'];
  const agents = [
    ['Профайлер','Описывает аудиторию, товар и задачи бренда'],['Разведчик','Подбирает релевантные аккаунты ниши'],
    ['Сборщик','Собирает примеры публикаций для сравнения'],['Чистильщик','Отделяет рекламу и нерелевантные материалы'],
    ['Статистик','Сравнивает результаты с обычными просмотрами автора'],['Разметчик','Группирует ролики по подаче и формату'],
    ['Визуальщик','Разбирает обложки, композицию и первые секунды'],['Скептик','Проверяет, какие выводы подтверждаются примерами'],
    ['Критик','Отмечает ограничения и гипотезы для теста'],['Редактор','Собирает рекомендации для контента']
  ];
  const patterns = [
    {id:'p1',title:'Одна проблема — одно решение',type:'Проблема → решение',hook:'Сколько времени уходит на подготовку одного ролика?',why:'Зритель узнаёт свою проблему в первые секунды и остаётся, чтобы увидеть решение.',idea:'Покажи создание ролика от идеи до результата: один понятный шаг на каждый кадр.',views:248000,multiplier:'×12',cover:1},
    {id:'p2',title:'Сравнение подготовки роликов',type:'Доказательство',hook:'Сравните подготовку роликов вручную и по контент-плану.',why:'Два состояния рядом позволяют быстро заметить результат без длинного объяснения.',idea:'Сравни ручную подготовку и готовый контент-план. Покажи конкретный результат на экране.',views:176000,multiplier:'×8',cover:2},
    {id:'p3',title:'Список полезных советов',type:'Обучение',hook:'Пять идей для следующего ролика.',why:'Список даёт понятное обещание пользы и повод сохранить публикацию.',idea:'Подбери пять вопросов твоей аудитории. Ответь на каждый одной короткой сценой.',views:367000,multiplier:'×18',cover:3},
    {id:'p4',title:'Разбор типичной ошибки',type:'Мнение',hook:'Я начал с монтажа и пропустил работу над сценарием.',why:'Личная ошибка создаёт узнаваемую ситуацию и приглашает зрителя поделиться опытом.',idea:'Расскажи, почему раньше начинал с монтажа, а теперь сначала определяешь одну мысль.',views:193000,multiplier:'×9',cover:4},
    {id:'p5',title:'Рабочий день автора',type:'История',hook:'Как автор готовит контент в течение дня?',why:'Наблюдение за процессом делает продукт конкретнее и помогает понять его ценность.',idea:'Покажи свой день в трёх сценах: идея, подготовка, готовая публикация.',views:124000,multiplier:'×6',cover:1},
    {id:'p6',title:'Товар крупно, одна фраза',type:'Оффер',hook:'Как подготовить неделю публикаций на основе одной идеи?',why:'Крупный план и короткая фраза удерживают внимание на одном преимуществе.',idea:'Сними экран рабочего пространства и покажи один результат без списка всех функций.',views:289000,multiplier:'×14',cover:2}
  ];
  function initial(now = Date.now()) {
    const titles = ['Студия для одного автора','Контент для бизнеса','Семь идей для нового ролика','Озвучка на разных языках','Создание нового ролика','Подготовка контента','Одна тема в разных форматах','Голос вашего бренда'];
    const statuses = ['published','ready','planned','published','draft','published','ready','draft'];
    const scripts = [
      'Для ролика нужно выбрать тему, написать сценарий, подготовить материалы и собрать видео. В рабочем пространстве эти этапы можно проходить последовательно.',
      'Перед съёмкой полезно определить аудиторию, её вопросы и основную мысль ролика.',
      'Если трудно выбрать тему ролика, начни с вопроса аудитории или примера из своей работы. Можно показать процесс, разобрать ошибку, сравнить два подхода или рассказать историю.',
      'Один и тот же сюжет можно адаптировать для разных языков, форматов и аудиторий, сохраняя узнаваемый тон бренда.'
    ];
    const videos = titles.map((title,i) => ({id:`v${i+1}`,title,cover:i%4+1,status:statuses[i],format:i%3===1?'YouTube Shorts':'Instagram Reels',duration:[32,24,45,28,30,22,35,30][i],productId:i===3?'product-avatar':'product-content',method:patterns[i%6].type,script:scripts[i%4],caption:`${title}\n\nРолик о создании контента в Sazi AI. #saziai #контент #нейросети`,createdAt:now-i*86400000,views:[28460,0,0,19820,0,30854,0,0][i],clicks:[580,0,0,416,0,632,0,0][i],leads:[17,0,0,9,0,14,0,0][i],assets:[],publications:[]}));
    const start = monday(now);
    return {schema:2,brand:{name:'Sazi AI',handle:'@sazi_ai',description:'AI-инструменты для создания контента: от идеи до готового ролика.',audience:'Предприниматели, эксперты и авторы, которые хотят выпускать контент регулярно.',tone:'Просто, по делу, с конкретными примерами. Короткие предложения, без сложных терминов.',website:'',color:'#2563EB'},products:[{id:'product-content',name:'Контент-завод',description:'Создание роликов, планирование и аналитика в одном рабочем пространстве.',assets:[]},{id:'product-avatar',name:'AI-аватар',description:'Видео с цифровым аватаром и голосом бренда.',assets:[]}],videos,channels:[{id:'instagram',platform:platforms[0],handle:'@sazi_ai',connected:true,demo:true},{id:'youtube',platform:platforms[1],handle:'@sazi_ai',connected:true,demo:true},{id:'vk',platform:platforms[2],handle:'',connected:false,demo:true},{id:'telegram',platform:platforms[3],handle:'',connected:false,demo:true},{id:'tiktok',platform:platforms[4],handle:'',connected:false,demo:true}],plan:[{id:'plan1',title:titles[2],date:addDays(start,2),time:'12:00',type:'Обучение',description:patterns[2].idea,videoId:'v3',patternId:'p3'},{id:'plan2',title:titles[1],date:addDays(start,4),time:'18:30',type:'Доказательство',description:patterns[1].idea,videoId:'v2',patternId:'p2'},{id:'plan3',title:titles[6],date:addDays(start,6),time:'11:00',type:'Оффер',description:patterns[5].idea,videoId:'v7',patternId:'p6'}],autopilot:{enabled:false,count:3},analysis:{status:'idle',competitors:'@content_studio\n@ai_creator',description:'',startedAt:null},chat:[],studio:{tab:'week',outputs:{}},leads:[{id:'l1',name:'Анна',channel:'Instagram Reels',videoId:'v1',text:'Можно посмотреть, как работает контент-завод для эксперта?',status:'new',assignee:'Илья',note:'',createdAt:now-1800000},{id:'l2',name:'Михаил',channel:'YouTube Shorts',videoId:'v6',text:'Интересуют ролики для магазина. Какие материалы нужны?',status:'new',assignee:'Не назначен',note:'',createdAt:now-7200000},{id:'l3',name:'Елена',channel:'Instagram Reels',videoId:'v4',text:'Хочу узнать подробнее про AI-аватара.',status:'progress',assignee:'Илья',note:'Подготовить пример под нишу клиента.',createdAt:now-86400000},{id:'l4',name:'Дмитрий',channel:'YouTube Shorts',videoId:'v1',text:'Нужен план публикаций на месяц.',status:'done',assignee:'Редактор',note:'Материалы обсуждены.',createdAt:now-172800000}],publications:[{id:'pub1',videoId:'v1',channelId:'instagram',date:addDays(start,0),time:'12:00',status:'published',createdAt:now-86400000},{id:'pub2',videoId:'v4',channelId:'instagram',date:addDays(start,-1),time:'18:30',status:'published',createdAt:now-172800000},{id:'pub3',videoId:'v6',channelId:'youtube',date:addDays(start,-2),time:'12:00',status:'published',createdAt:now-259200000}],checks:null};
  }
  function load(storage, now = Date.now()) {
    const fresh = initial(now);
    try {
      const saved = JSON.parse(storage.getItem('sazi-content-workspace-v2'));
      if (saved && saved.schema === 2 && Array.isArray(saved.videos) && Array.isArray(saved.plan) && Array.isArray(saved.channels)) {
        const previousTitles = ['Один человек. Целая студия.','Контент, который работает','7 идей для твоего следующего ролика','Ваш голос. Любой язык.','Как рождается идея','Меньше рутины. Больше смысла.','Одна тема. Пять форматов.','Твой бренд звучит по-новому'];
        const previousScripts = [
          'Раньше на один ролик уходил целый день. Идея, текст, съёмка, монтаж. А теперь представь: у тебя есть своя студия, которая помогает на каждом этапе. От первой мысли до готового контента.',
          'Хороший контент начинается не с камеры. Он начинается с понимания: кому ты говоришь, что ему важно и какую одну мысль он должен унести с собой.',
          'Не знаешь, что снимать? Покажи процесс. Ответь на частый вопрос. Разбери ошибку. Расскажи историю. Сравни до и после. Поделись находкой. Предложи попробовать.',
          'Идеям не нужны границы. Один понятный сюжет можно рассказать по-разному: на другом языке, в новом формате, для другой аудитории. Сохраняя свой голос.'
        ];
        saved.videos.forEach(video => {
          const index = fresh.videos.findIndex(item => item.id === video.id);
          if (index < 0) return;
          if (video.title === previousTitles[index]) video.title = fresh.videos[index].title;
          if (video.script === previousScripts[index % previousScripts.length]) video.script = fresh.videos[index].script;
          if (video.caption === `${previousTitles[index]}\n\nСоздавай контент с Sazi AI. #saziai #контент #нейросети`) video.caption = fresh.videos[index].caption;
        });
        const previousPatternTitles = {p2:'До и после: покажи разницу',p3:'Список, который хочется сохранить',p4:'Я делал это неправильно',p5:'Один день за кадром'};
        saved.plan.forEach(item => {
          const video = saved.videos.find(candidate => candidate.id === item.videoId);
          const index = video ? fresh.videos.findIndex(candidate => candidate.id === video.id) : -1;
          if (index >= 0 && item.title === previousTitles[index]) item.title = fresh.videos[index].title;
          if (item.title === previousPatternTitles[item.patternId]) item.title = patterns.find(pattern => pattern.id === item.patternId).title;
        });
        return {...fresh,...saved};
      }
      const legacy = JSON.parse(storage.getItem('sazi-style-drafts') || '[]');
      if (Array.isArray(legacy)) fresh.videos.unshift(...legacy.filter(v=>v&&typeof v.title==='string').slice(0,50).map(v=>({...fresh.videos[4],...v,id:v.id||id('legacy'),duration:parseDuration(v.duration),createdAt:now,status:'draft',assets:[]})));
    } catch {}
    return fresh;
  }
  function save(storage,state) { try { storage.setItem('sazi-content-workspace-v2',JSON.stringify(state)); return true; } catch { return false; } }
  function parseDuration(value) { if(typeof value==='number')return value; const parts=String(value||'0:30').split(':'); return parts.length===2?Number(parts[0])*60+Number(parts[1]):Number(parts[0])||30; }
  function createVideo(state,input,now=Date.now()) {
    const title=String(input.title||'').trim().slice(0,180);
    if(!title)throw new Error('Добавь название или идею ролика.');
    const product=state.products.find(p=>p.id===input.productId)||state.products[0];
    const video={id:id('video'),title,productId:product?.id||'',format:input.format||platforms[0],duration:[15,30,45,60].includes(Number(input.duration))?Number(input.duration):30,method:input.method||'Проблема → решение',cover:input.cover||5,status:'draft',createdAt:now,views:0,clicks:0,leads:0,assets:clone(input.assets||[]),voice:input.voice||'Спокойный',language:input.language||'Русский',script:input.script||`${title}\n\n1. Хук: начни с вопроса или узнаваемой ситуации.\n2. Основная мысль: ${input.brief||product?.description||title}\n3. Результат: покажи, как это работает на конкретном примере.\n4. Финал: предложи сохранить ролик или задать вопрос.`,caption:input.caption||`${title}\n\n${state.brand.name} · ${product?.name||'Контент'}\n#контент #saziai`,publications:[]};
    state.videos.unshift(video); return video;
  }
  function startVideo(state,videoId,now=Date.now()) { const v=state.videos.find(v=>v.id===videoId);if(!v)throw new Error('Ролик не найден.');if(v.status==='generating')return v;v.status='generating';v.startedAt=now;v.jobDuration=12000;return v; }
  function advance(state,now=Date.now()) {
    let changed=false;
    state.videos.forEach(v=>{if(v.status==='generating'&&now-v.startedAt>=v.jobDuration){v.status='ready';v.completedAt=now;changed=true;}});
    if(state.analysis.status==='running'&&now-state.analysis.startedAt>=10000){state.analysis.status='ready';state.analysis.completedAt=now;changed=true;}
    return changed;
  }
  function progress(startedAt,duration,now=Date.now()) { return Math.min(100,Math.max(0,Math.floor((now-startedAt)/duration*100))); }
  function buildPlan(state,count=3,source='quick',now=Date.now()) {
    count=Math.min(7,Math.max(2,Number(count)||3));
    const first=day(now); const used=new Set(state.plan.map(p=>`${p.date}|${p.title}`)); const added=[];
    for(let i=0;i<count;i++){
      const pattern=patterns[i%patterns.length];const date=addDays(first,1+Math.floor(i*7/count));
      const key=`${date}|${pattern.title}`;if(used.has(key))continue;
      const row={id:id('plan'),title:pattern.title,date,time:i%2?'18:30':'12:00',type:pattern.type,description:pattern.idea,patternId:pattern.id,source,videoId:null};
      state.plan.push(row);added.push(row);used.add(key);
    }
    state.plan.sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time));return added;
  }
  function videoFromPlan(state,planId,now=Date.now()) {
    const item=state.plan.find(p=>p.id===planId);if(!item)throw new Error('Пункт плана не найден.');
    const existing=state.videos.find(v=>v.id===item.videoId);if(existing)return existing;
    const pattern=patterns.find(p=>p.id===item.patternId);
    const video=createVideo(state,{title:item.title,brief:item.description,method:item.type,cover:pattern?.cover||5},now);item.videoId=video.id;return video;
  }
  function publish(state,videoId,{channelIds,date,time,now=Date.now()}) {
    const video=state.videos.find(v=>v.id===videoId);if(!video)throw new Error('Ролик не найден.');
    if(!['ready','planned','published'].includes(video.status))throw new Error('Сначала заверши демонстрацию сборки ролика.');
    const channels=[...new Set(channelIds||[])].filter(id=>state.channels.some(c=>c.id===id&&c.connected));
    if(!channels.length)throw new Error('Выбери хотя бы один канал.');
    const isScheduled=Boolean(date);
    const dateStamp=Date.parse(`${date}T12:00:00Z`);const scheduledStamp=Date.parse(`${date}T${time}:00+03:00`);
    if(isScheduled&&(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!/^([01]\d|2[0-3]):[0-5]\d$/.test(time)||!Number.isFinite(dateStamp)||new Date(dateStamp).toISOString().slice(0,10)!==date||!Number.isFinite(scheduledStamp)||scheduledStamp<=now))throw new Error('Выбери дату и время в будущем.');
    const today=day(now);const currentTime=new Date(now+3*3600000).toISOString().slice(11,16);const created=[];
    channels.forEach(channelId=>{
      const publication={id:id('pub'),videoId,channelId,date:date||today,time:time||currentTime,status:isScheduled?'planned':'published',createdAt:now,demo:true};
      const duplicate=state.publications.find(p=>p.videoId===videoId&&p.channelId===channelId&&p.date===publication.date&&p.time===publication.time&&p.status===publication.status);
      if(!duplicate){state.publications.unshift(publication);created.push(publication);}
    });
    video.status=state.publications.some(p=>p.videoId===videoId&&p.status==='published')?'published':'planned';
    return created;
  }
  function removeVideo(state,videoId) { state.videos=state.videos.filter(v=>v.id!==videoId);state.publications=state.publications.filter(p=>p.videoId!==videoId);state.plan.forEach(p=>{if(p.videoId===videoId)p.videoId=null;}); }
  function totals(state) { return {views:state.videos.reduce((sum,v)=>sum+(Number(v.views)||0),0),clicks:state.videos.reduce((sum,v)=>sum+(Number(v.clicks)||0),0),leads:state.videos.reduce((sum,v)=>sum+(Number(v.leads)||0),0),videos:state.videos.length,published:state.publications.filter(p=>p.status==='published').length}; }
  const api={initial,load,save,createVideo,startVideo,advance,progress,buildPlan,videoFromPlan,publish,removeVideo,totals,id,clone,day,addDays,monday,patterns,agents,platforms,videoSteps};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.StudioModel=api;
})(typeof window!=='undefined'?window:globalThis);
