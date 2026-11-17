(function (root) {
  'use strict';

  const en = {
    'КОНТЕНТ-ЗАВОД':'CONTENT WORKSPACE','РАБОЧЕЕ ПРОСТРАНСТВО':'WORKSPACE',
    'Главная':'Home','Главная страница':'Home page','Обзор':'Overview','Ролики':'Videos',
    'План и автопилот':'Plan and autopilot','Аналитика':'Analytics','Агент-маркетолог':'Marketing assistant',
    'Анализ ниши':'Niche analysis','Instagram-студия':'Instagram studio','Бренд и товары':'Brand and products',
    'Каналы и API':'Channels and API','Заявки (команда)':'Leads (team)','Заявки и команда':'Leads and team',
    'Проверка API':'API check','Дизайн-система':'Design system','Создать ролик':'Create video',
    'Рабочее пространство mill':'mill workspace','Подготовка, планирование и публикация контента.':'Content creation, planning, and publishing.',
    'Цветовая тема':'Color theme','Светлая тема':'Light theme','Тёмная тема':'Dark theme',
    'Светлая':'Light','Тёмная':'Dark','Язык интерфейса':'Interface language',
    'Открыть меню':'Open menu','17 ноября, вторник':'Tuesday, November 17',
    'Опубликован':'Published','Опубликованы':'Published','Готов':'Ready','Готовы':'Ready',
    'В плане':'Scheduled','Черновик':'Draft','Черновики':'Drafts','Собирается':'Processing',
    'В работе':'In progress','Все':'All','Илья':'Ilya','И':'I',
    'Здесь собраны ролики, план публикаций и результаты работы.':'Your videos, publishing plan, and results are collected here.',
    'ОТ ИДЕИ ДО ПУБЛИКАЦИИ':'FROM IDEA TO PUBLICATION',
    'Планируйте контент':'Plan your content','и создавайте ролики.':'and create videos.',
    'Добавьте материалы, выберите формат и подготовьте новый ролик.':'Add materials, choose a format, and prepare a new video.',
    'Спросить агента':'Ask the assistant','Результаты за 14 дней':'Results for 14 days',
    'Демо-данные':'Sample data','Просмотры':'Views','Пример результатов контента':'Sample content results',
    'Переходы':'Clicks','Заявки':'Leads','Из публикаций в демо-проекте':'From sample publications',
    'Последние ролики':'Recent videos','Все ролики':'All videos',
    'Примеры форматов и идеи для роликов вашего бренда':'Formats and video ideas for your brand',
    'Карусели, сторис и контент на неделю':'Carousels, stories, and a weekly content plan',
    'Идея':'Idea','Сценарий':'Script','Готовый ролик':'Finished video',
    'Студия':'Studio','для одного автора':'for one creator','Контент':'Content',
    'для бизнеса':'for businesses','Семь идей':'Seven ideas','для нового':'for a new',
    'ролика':'video','Озвучка':'Voiceover','на разных языках':'in different languages',
    'Создание':'Creating','нового ролика':'a new video','Подготовка':'Preparing',
    'контента':'content','Одна тема':'One topic','в разных':'in different',
    'форматах':'formats','Голос':'Voice','вашего бренда':'of your brand',
    'Студия для одного автора':'A studio for one creator','Контент для бизнеса':'Content for businesses',
    'Семь идей для нового ролика':'Seven ideas for a new video',
    'Озвучка на разных языках':'Voiceovers in different languages',
    'Создание нового ролика':'Creating a new video','Подготовка контента':'Preparing content',
    'Одна тема в разных форматах':'One topic in different formats','Голос вашего бренда':'Your brand voice',
    'СЦЕНАРИЙ · РОЛИК · ПУБЛИКАЦИЯ':'SCRIPT · VIDEO · PUBLICATION',
    'Здесь собраны черновики, ролики в работе и готовые публикации.':'Drafts, videos in progress, and published videos are collected here.',
    'Найти ролик':'Find a video','Пока нет роликов с такими параметрами. Измени фильтр или создай новый.':'No videos match these filters. Change the filters or create a video.',
    'Бренд':'Brand','Товар или услуга':'Product or service','Название или идея ролика':'Video title or idea',
    'Например: как подготовить ролик за один день':'For example: how to prepare a video in one day',
    'Что показать и какую мысль донести':'What to show and what to say',
    'Свои кадры и фото товара':'Your footage and product photos','Материалы используются только в этом браузере':'Files are used only in this browser',
    'Выбрать файлы':'Choose files','Формат подачи':'Presentation style','Площадка':'Platform',
    'Длительность':'Duration','15 секунд':'15 seconds','30 секунд':'30 seconds','45 секунд':'45 seconds','60 секунд':'60 seconds',
    'Соотношение сторон':'Aspect ratio','Голос бренда':'Brand voice','Энергичный':'Energetic',
    'Без озвучки':'No voiceover','Спокойный':'Calm','Русский':'Russian','Язык':'Language',
    'Стиль текста берётся из настроек бренда. В демонстрации используется заготовка сценария, без вызова AI.':'The writing style comes from your brand settings. This preview uses a sample script without calling AI.',
    'Не выбран':'Not selected','Новый ролик':'New video','Товар':'Product','Формат':'Format',
    'Настройки':'Settings','Материалы':'Materials','Запуск':'Start','Назад':'Back',
    'Сохранить черновик':'Save draft','Показать демо-сборку':'Show sample workflow','Продолжить':'Continue',
    'Твои материалы, голос бренда и подходящий формат.':'Choose your materials, brand voice, and format.',
    'ПРЕВЬЮ КОМПОЗИЦИИ':'LAYOUT PREVIEW','Обложка-заготовка · 9:16':'Sample cover · 9:16',
    'Демо-сборка покажет этапы, журнал и готовую карточку ролика. Настоящее видео не генерируется.':'The sample workflow shows each step and the completed video card. No video file is generated.',
    'Ролик не найден':'Video not found','Возможно, он был удалён.':'It may have been deleted.',
    'В библиотеку':'Back to library','Черновик готов к работе':'Draft ready to edit',
    'Собираем ролик':'Processing video','Куда публикуем':'Publishing channels',
    'Публикации':'Publications','Сценарий ролика':'Video script','Журнал агента · демонстрация':'Assistant log · sample',
    'Динамика просмотров':'View trends','От внимания к заявке':'From views to leads',
    'Проверь сценарий и материалы. Затем можно посмотреть демонстрацию процесса сборки.':'Review the script and materials, then view the sample production workflow.',
    'Сохранить сценарий':'Save script','Публикация':'Publishing','Журнал':'Log',
    'Подпись к публикации':'Post caption','Сохранить подпись':'Save caption',
    'Добавь демо-канал в разделе «Каналы и API».':'Add a sample channel in Channels and API.',
    'Опубликовать или запланировать':'Publish or schedule',
    'Демо-режим: запись появится в проекте, без отправки в соцсеть.':'A sample record will appear in the project. Nothing will be sent to a social network.',
    'Текст и последовательность сцен':'Text and scene order','Скопировать':'Copy',
    'Сохранить изменения':'Save changes','Канал удалён':'Channel removed',
    'Здесь появятся запланированные и опубликованные записи.':'Scheduled and published records will appear here.',
    'Демонстрация сборки':'Sample workflow','Скачать':'Download','Другой вариант':'Another version',
    'Удалить':'Delete','Твои исходные кадры':'Your source footage',
    'Превью обложки · видео не сгенерировано':'Cover preview · no video generated',
    'Составляйте план на неделю и выбирайте каналы для публикации.':'Plan your week and choose publishing channels.',
    'Составить план по анализу ниши':'Build a plan from niche analysis','Быстрый план':'Quick plan',
    'Список':'List','Календарь':'Calendar','Очистить':'Clear','Открыть':'Open',
    'Сделать':'Create','Предыдущая':'Previous','Следующая':'Next',
    'План пока пуст. Составь его по анализу ниши или начни с быстрого плана.':'The plan is empty. Use niche analysis or start with a quick plan.',
    'Открой готовый ролик и выбери дату публикации — запись появится здесь.':'Open a finished video and choose a publication date to add it here.',
    'Автопилот':'Autopilot','Настройки подготовки и выпуска роликов по плану.':'Settings for preparing and publishing videos on a schedule.',
    'Роликов в неделю':'Videos per week','Контент-план':'Content plan',
    'Демо-настройки сохраняются. Автопубликация на внешние площадки не выполняется.':'Sample settings are saved. Automatic publishing to external platforms is disabled.',
    'Здесь показаны просмотры, переходы и заявки по роликам.':'Views, clicks, and leads are shown for each video.',
    '7 дней':'7 days','14 дней':'14 days','30 дней':'30 days','Все площадки':'All platforms',
    'Из опубликованного контента':'From published content','Пример атрибуции по роликам':'Sample attribution by video',
    'Переходы / просмотры':'Clicks / views','Просмотры: демонстрационная динамика':'Views: sample trend',
    'Ширина ступеней условная. Точные значения показаны рядом.':'Bar widths are illustrative. Exact values appear alongside them.',
    'Результаты роликов':'Video results','Статус':'Status','Смотреть аналитику':'View analytics',
    'Обсуждай контент, результаты и следующие шаги.':'Discuss content, results, and next steps.',
    'Помощник по маркетингу':'Marketing assistant','Бренд, ролики, заявки, площадки и контент-план.':'Brand, videos, leads, channels, and content plan.',
    'Демо-ответы':'Sample responses','Ты':'You','Что разберём сегодня?':'What would you like to review?',
    'Попроси сводку по цифрам, идею ролика или помощь с планом.':'Ask for a performance summary, a video idea, or help with a plan.',
    'Как дела у проекта?':'How is the project doing?','Что снимать на этой неделе?':'What should I film this week?',
    'Откуда приходят заявки?':'Where do leads come from?','Спроси про свои цифры или контент…':'Ask about your results or content…',
    'Сообщение агенту':'Message the assistant',
    'Локальная демонстрация диалога. AI-модель пока не подключена.':'This is a local sample conversation. The AI model is not connected.',
    'Ролик об одной теме':'Video about one topic','Твой продукт':'Your product','В кадре':'On screen',
    'Хук':'Opening','Почему работает':'Why it works','Повторить':'Use format',
    'Анализ ниши выполняется':'Running niche analysis','готово':'done','работает':'working','ждёт':'waiting',
    'Здесь собраны форматы и гипотезы для контента вашего бренда.':'Formats and content ideas for your brand are collected here.',
    'Новый анализ':'New analysis','Скачать отчёт':'Download report','Составить план':'Build a plan',
    'Аккаунтов':'Accounts','Демонстрационный набор':'Sample set','Примеры для анализа':'Sample posts',
    'Форматов':'Formats','Для проверки на твоём бренде':'To test with your brand',
    'Гипотез для теста':'Ideas to test','Результаты не гарантированы':'Results are not guaranteed',
    'ОТЧЁТ ГОТОВ · ДЕМО':'SAMPLE REPORT READY','Примеры форматов':'Sample formats',
    'Примеры, а не результаты реального поиска':'Examples, not live search results',
    'Найди подачу, которая подходит твоему товару и аудитории.':'Find a format that suits your product and audience.',
    'Разобрать нишу':'Analyze niche','Анализ использует данные бренда и показывает подходящие форматы.':'The analysis uses your brand details to suggest suitable formats.',
    'Что за бренд и ниша':'Brand and niche','Аккаунты или ссылки для ориентира':'Reference accounts or links',
    '@аккаунт или ссылка, по одному на строку':'@account or link, one per line',
    'Запустить анализ · демо':'Run sample analysis','ЧТО ПОЛУЧИШЬ':'WHAT YOU GET',
    'Основа для контента':'Content starting points','Повторяемые форматы':'Reusable formats',
    'Разбор подачи, первых секунд и смысла.':'Review of the format, opening seconds, and message.',
    'Хуки и объяснения':'Openings and explanations','Что цепляет зрителя и почему он досматривает.':'What catches viewers’ attention and keeps them watching.',
    'План на неделю':'Weekly plan','Идеи с разными задачами: польза, доверие, оффер.':'Ideas for education, trust, and offers.',
    'Ролик по формуле':'Video from a format','Перенос выбранной идеи в создание ролика.':'Use the selected idea to create a video.',
    'Профиль':'Profile','Комментарии':'Comments','Аудит':'Audit','Взаимодействие':'Engagement',
    'Переработка':'Repurposing','Карусели':'Carousels','Сторис':'Stories','Неделя':'Week',
    'Инструменты Instagram':'Instagram tools','Инструменты для ведения бренда — с твоим контекстом и голосом.':'Tools for managing your brand with its own context and voice.',
    'Профиль бренда':'Brand profile','Название':'Name','О бренде':'About the brand',
    'Призыв к действию':'Call to action','Подготовить описание':'Prepare description',
    'Ответы на комментарии':'Comment replies','Комментарий':'Comment','Тон ответа':'Reply tone',
    'Подготовить ответ':'Prepare reply','Аудит профиля':'Profile audit','Название бренда':'Brand name',
    'Описание предложения':'Offer description','Аудитория':'Audience','Товары и услуги':'Products and services',
    'заполнено':'complete','нужно добавить':'needs information','Собрать рекомендации':'Prepare recommendations',
    'Вовлечение и диалоги':'Engagement and conversations','Тема':'Topic','Задача':'Goal',
    'Обсудить проблему':'Discuss a problem','Собрать вопросы':'Collect questions','Узнать мнение':'Ask for opinions',
    'Подготовить идеи':'Prepare ideas','Одна мысль — разные форматы':'One idea in different formats',
    'Исходный текст':'Source text','Переработать текст':'Repurpose text','Карусель для бренда':'Brand carousel',
    'Тема карусели':'Carousel topic','Слайды':'Slides','5 слайдов':'5 slides','7 слайдов':'7 slides',
    'Подготовить карусель':'Prepare carousel','КАРУСЕЛЬ · ПРЕВЬЮ':'CAROUSEL · PREVIEW',
    'Истории на неделю':'A week of stories','Основная тема':'Main topic','Цель':'Purpose',
    'Познакомить с продуктом':'Introduce the product','Вовлечь аудиторию':'Engage the audience',
    'Ответить на вопросы':'Answer questions','Подготовить 7 сторис':'Prepare 7 stories',
    'КАРУСЕЛЬ':'CAROUSEL','РИЛС':'REEL','Неделя контента':'Content week',
    'Добавить неделю в план':'Add week to plan','Данные бренда и товаров используются в сценариях и контент-плане.':'Brand and product details are used in scripts and the content plan.',
    'Голос и контекст бренда':'Brand voice and context','Локально':'Local',
    'Описание бренда и предложения':'Brand and offer description','Кому помогаем':'Who we help',
    'Сайт или ссылка':'Website or link','Сохранить бренд':'Save brand',
    'МАТЕРИАЛЫ БРЕНДА':'BRAND MATERIALS','Фото, исходные видео и описания для создания контента.':'Photos, source videos, and descriptions for creating content.',
    'Добавить товар':'Add product','Здесь указаны каналы публикации и сервисы создания контента.':'Publishing channels and content services are listed here.',
    'Каналы публикации':'Publishing channels','Демо-канал':'Sample channel','Не добавлен':'Not added',
    'Добавь профиль для демонстрации публикаций':'Add a profile for sample publications',
    'Настроить':'Set up','Добавить канал':'Add channel','Сервисы создания контента':'Content services',
    'Сервис':'Service','Состояние':'State','AI-модель':'AI model','Озвучка':'Voiceover',
    'Генерация видео':'Video generation','Рендер':'Rendering','Сервер не подключён':'Server not connected',
    'Отправка в подключённые аккаунты':'Publish to connected accounts',
    'Здесь можно посмотреть источник, ответственного и следующий шаг по каждой заявке.':'Review the source, assignee, and next step for each lead.',
    'Новые':'New','Завершены':'Completed','Все заявки':'All leads','Новая':'New','Завершена':'Completed',
    'Заявок с таким статусом нет.':'No leads have this status.',
    'Демонстрационные обращения':'Sample inquiries','Контакт':'Contact','Сообщение':'Message',
    'Источник':'Source','Ответственный':'Assignee','Не назначен':'Unassigned',
    'Здесь можно проверить интерфейс и параметры будущих подключений.':'Check the interface and future connection settings here.',
    'Проверить конфигурацию':'Check configuration','Готово':'Ready','Нужно внимание':'Needs attention',
    'Демо':'Sample','Не подключено':'Not connected','Скачать диагностику':'Download diagnostics',
    'Интерфейс':'Interface','Все основные разделы доступны':'All main sections are available',
    'Локальное хранилище':'Local storage','Сохранение заблокировано браузером':'Storage is blocked by the browser',
    'Настройки и изменения сохраняются в браузере':'Settings and changes are saved in the browser',
    'Добавь товар или услугу':'Add a product or service','AI, озвучка и генерация':'AI, voiceover, and generation',
    'Отправка публикаций':'Publishing','Опубликовать':'Publish','Сейчас':'Now','Когда':'When',
    'В лучшее время · демо':'Suggested time · sample','Выбрать дату и время':'Choose date and time',
    'Дата':'Date','Время по Москве':'Moscow time','Сначала добавь демо-канал':'Add a sample channel first',
    'Добавить демо-публикацию':'Add sample publication','Редактировать товар':'Edit product',
    'Новый товар или услуга':'New product or service','Описание':'Description',
    'Фото и исходные видео':'Photos and source videos','Сохранить товар':'Save product',
    'Заметка для команды':'Team note','Сохранить':'Save','Профиль или название канала':'Profile or channel name',
    'Добавить демо-канал':'Add sample channel','Отключить в демо':'Disconnect sample channel',
    'Скачать материалы':'Download materials','ПРЕВЬЮ ОБЛОЖКИ':'COVER PREVIEW',
    'Скопировать':'Copy','Отменить':'Undo','Закрыть':'Close',
    'Заготовка · демо':'Sample draft','Сохранить правки':'Save edits',
    'Копирование недоступно. Выдели текст вручную.':'Copying is unavailable. Select the text manually.',
    'Не удалось выполнить действие.':'The action could not be completed.',
    'Создан отдельный черновик':'A separate draft was created','Черновик сохранён':'Draft saved',
    'Подпись сохранена':'Caption saved','Сценарий сохранён':'Script saved',
    'Товар сохранён':'Product saved','Демо-канал сохранён':'Sample channel saved',
    'Заявка обновлена':'Lead updated','Добавлено в расписание':'Added to schedule',
    'Демо-публикация добавлена':'Sample publication added','Открыть ролик':'Open video',
    'Демонстрация завершена. Результат сохранён в проекте.':'The sample process is complete. The result was saved to the project.',
    'Цвета и компоненты':'Colors and components','интерфейса mill':'of the mill interface',
    'Визуальный язык контент-завода mill.':'Visual style of the mill workspace.',
    'Палитра':'Palette','Основные цвета интерфейса':'Main interface colors',
    'Фирменные иконки':'Brand icons','12 символов · без глаз':'12 symbols · no faces',
    'ТИПОГРАФИКА / MANROPE':'TYPOGRAPHY / MANROPE','Заголовки и текст':'Headings and text',
    'без лишних акцентов':'with a simple style','ЭЛЕМЕНТЫ ИНТЕРФЕЙСА':'INTERFACE ELEMENTS',
    'Библиотека':'Library','Три правила стиля':'Three design rules','01 / ЦВЕТ':'01 / COLOR',
    'Акцент с назначением':'Purposeful accent','02 / КОМПОЗИЦИЯ':'02 / LAYOUT',
    'Воздух и иерархия':'Space and hierarchy','03 / ДВИЖЕНИЕ':'03 / MOTION','Мягкая реакция':'Subtle feedback',
    'Фон':'Background','Карточки':'Cards','Текст':'Text','Синий':'Blue','Голубой':'Light blue',
    'Светло-синий':'Pale blue','Тёмно-синий':'Dark blue'
  };

  Object.assign(en, {
    'Хранилище недоступно':'Storage is unavailable',
    'Браузер запретил сохранение. Изменения доступны до закрытия страницы.':'The browser blocked storage. Changes will remain until this page is closed.',
    'Раздел':'Section','Демонстрация интерфейса: действия сохраняются локально, без обращения к внешним сервисам.':'This sample interface saves changes locally and does not contact external services.',
    'автопилот включён':'autopilot is on','готов к настройке':'ready to set up',
    'Проблема → решение':'Problem → solution','Монтаж':'Editing','Проверка':'Review',
    'Хук, основная мысль, пример и финал.':'Opening, main point, example, and ending.',
    'Демонстрация переходов, субтитров и музыки без рендера видео.':'Sample transitions, subtitles, and music without rendering a video.',
    'Сценарий доступен для редактирования. Готов к демо-публикации.':'The script can be edited and is ready for sample publishing.',
    'Москва, UTC+3':'Moscow, UTC+3','Ролик':'Video','Канал':'Channel',
    'Все показатели — демонстрационные. Фильтры показывают пример отчёта, без загрузки статистики из соцсетей.':'All figures are samples. Filters show an example report without loading social media data.',
    'Открыть форматы ниши':'View niche formats',
    'Это демонстрация этапов на данных-примерах. Аккаунты и соцсети не сканируются.':'This workflow uses sample data. Accounts and social networks are not scanned.',
    'В прототипе анализ пройдёт по демонстрационным материалам. Данные аккаунтов не загружаются.':'This prototype analyzes sample materials without loading account data.',
    'Можно отредактировать перед использованием':'You can edit this before using it',
    'Локальная заготовка на основе формы и голоса бренда. AI не подключён.':'A local draft based on the form and brand voice. AI is not connected.',
    'Собери понятное описание: кто ты, для кого и что предлагаешь.':'Write a clear description of who you are, whom you help, and what you offer.',
    'Посмотри, как работает контент-завод':'See how the content workspace works',
    'Подготовь ответ в тоне бренда и отредактируй его перед отправкой.':'Prepare a reply in your brand voice and edit it before sending.',
    'Сколько времени занимает создание ролика?':'How long does it take to create a video?',
    'Можно использовать свои кадры?':'Can I use my own footage?',
    'Подойдёт ли это для моей ниши?':'Will this work for my niche?',
    'Дружелюбно и коротко':'Friendly and brief','Подробно и по делу':'Detailed and direct',
    'С приглашением в диалог':'Invite a conversation',
    'Проверка заполнения данных в текущем рабочем пространстве.':'Check the information entered in the current workspace.',
    'Вопросы и механики для разговора с аудиторией.':'Questions and prompts for conversations with your audience.',
    'Создание контента без рутины':'Creating content with less routine work','О чём поговорим?':'What should we discuss?',
    'Преврати исходный текст в заготовки для ролика, карусели и сторис.':'Turn source text into drafts for a video, carousel, and stories.',
    'Одна тема, последовательность слайдов и понятный финал.':'One topic, a clear slide sequence, and an ending.',
    'Как превратить идею в неделю контента':'How to turn one idea into a week of content',
    'Сюжеты, опросы и вопросы, которые продолжают основную тему.':'Story ideas, polls, and questions that develop the main topic.',
    'За кадром контент-студии':'Behind the content studio',
    'Разные задачи: доверие, польза, мнение, история и оффер.':'Different goals: trust, education, opinion, stories, and offers.',
    'Анализ, сценарии и маркетолог':'Analysis, scripts, and marketing assistant',
    'Синтез речи в голосе бренда':'Speech synthesis in your brand voice',
    'Создание сцен и аватаров':'Creating scenes and avatars',
    'Монтаж, музыка и субтитры':'Editing, music, and subtitles',
    'Фронтенд не хранит API-ключи и не выполняет OAuth. Добавление канала создаёт только запись в демо-проекте.':'The interface does not store API keys or perform OAuth. Adding a channel creates only a sample record.',
    'Можно менять статусы, назначать ответственного и сохранять заметки. Сообщения клиентам не отправляются.':'You can change statuses, assign an owner, and save notes. No messages are sent to customers.',
    'Нужен серверный API. Реальные запросы не выполняются.':'A server API is required. No live requests are made.',
    'В прототипе записи сохраняются только локально':'Records are stored locally in this prototype',
    'Проверяются только локальные данные. Проверка доступности реальных API начнёт работать после подключения сервера.':'Only local data is checked. Live API checks require a server connection.',
    'Началась демонстрация сборки':'The sample workflow has started',
    'Выбери площадки и время для записи в демо-проекте.':'Choose channels and a time for the sample publication.',
    'Без отправки в соцсети. Запись будет видна в карточке ролика и расписании.':'Nothing is sent to social networks. The record will appear in the video card and schedule.',
    'Файлы доступны в текущей сессии браузера. После перезагрузки сохранятся только названия материалов.':'Files are available during this browser session. Only their names remain after reloading.',
    'Редактор':'Editor','Это настройка демонстрационного канала. Вход в аккаунт и выдача разрешений не выполняются.':'This is a sample channel setting. No account login or permissions are requested.',
    'Посмотри, как это работает.':'See how it works.',
    'Да, можно использовать свои фото и видео. Добавь их в материалы товара или при создании ролика.':'Yes. Add your photos and videos to the product materials or while creating a video.',
    'Время зависит от формата, исходных материалов и выбранного способа создания. Лучше начать с одного короткого ролика.':'The time depends on the format, source materials, and production method. Start with one short video.',
    'Начни с одного продукта и задачи твоей аудитории. На примере ролика будет проще понять, подходит ли формат.':'Start with one product and one audience need. A sample video will help you assess the format.',
    'Если хочешь, расскажи немного о своей задаче — подберём подходящий пример.':'Tell us about your goal and we can suggest a relevant example.',
    'Это рекомендации по данным проекта. Реальная страница профиля не проверялась.':'These recommendations use project data. The live profile page was not checked.',
    'Что важно знать?':'What should viewers know?',
    'Начни с одной задачи аудитории.':'Start with one audience need.',
    'Объясни одну мысль простыми словами.':'Explain one point in plain words.',
    'Покажи конкретный пример.':'Show a concrete example.',
    'Добавь один шаг, который можно повторить.':'Add one step viewers can try.',
    'Собери вывод в короткую фразу.':'Summarize the conclusion in one sentence.',
    'Сохрани и попробуй на своём контенте.':'Save this and try it with your content.',
    'Знакомство: покажи, над чем работаешь.':'Introduction: show what you are working on.',
    'Опрос: какая часть процесса сложнее?':'Poll: which part of the process is harder?',
    'Процесс: один короткий кадр за работой.':'Process: one short shot of the work.',
    'Польза: один совет по теме.':'Value: one useful tip.',
    'Ответ на вопрос аудитории.':'Answer an audience question.',
    'Результат: что получилось.':'Result: show the outcome.',
    'Диалог: предложи задать вопрос.':'Conversation: invite a question.',
    'Готовое видео · пока недоступно':'Finished video · not available yet',
    'Готовое видео появится после подключения генерации и рендера. Сейчас доступны сценарий и обложка-макет.':'A finished video requires generation and rendering. The script and sample cover are available now.',
    'Изменение отменено':'Change undone','Ролик удалён из демо-проекта':'Video removed from the sample project',
    'Автопилот включён в демо-проекте':'Autopilot turned on in the sample project',
    'Автопилот выключен':'Autopilot turned off',
    'Сначала запусти демонстрацию анализа ниши':'Run the sample niche analysis first',
    'Список идей очищен. Расписание публикаций сохранено.':'The idea list was cleared. The publication schedule was kept.',
    'Это пример, не реальное исследование аккаунтов.':'This is an example, not live account research.',
    'Заготовка недели подготовлена':'The weekly draft is ready',
    'Демо-канал отключён':'Sample channel disconnected','Локальная конфигурация проверена':'Local configuration checked',
    'Эти идеи уже есть в плане':'These ideas are already in the plan','Текст скопирован':'Text copied',
    'Контекст и голос бренда сохранены':'Brand context and voice saved',
    'Демонстрационная заготовка готова':'Sample draft ready','Правки сохранены':'Edits saved',
    'Такая публикация уже есть в проекте.':'This publication is already in the project.',
    'Отправка во внешние соцсети не выполнялась.':'Nothing was sent to external social networks.',
    'Белые карточки, светлый фон и чистый синий акцент.':'White cards, a light background, and a clear blue accent.',
    'Графитовые карточки, глубокий чёрный и чистый синий акцент.':'Graphite cards, a dark background, and a clear blue accent.',
    'Одинаковый размер в меню и карточках. Прозрачный фон сохраняет цвет иконок в обеих темах.':'Icons use the same size in menus and cards. A transparent background preserves their color in both themes.',
    'Аа Бб Вв Гг Дд · 0123456789':'Aa Bb Cc Dd Ee · 0123456789',
    'Заголовки 28–36 px / Текст 13–14 px / Сетка 8 px':'Headings 28–36 px / Body 13–14 px / Grid 8 px',
    'Компоненты имеют скругления 10–16 px, тонкие границы и фирменные иконки с округлыми формами.':'Components have 10–16 px corners, thin borders, and rounded brand icons.',
    'Главные действия выделены синим цветом. Статусы и вторичные кнопки оформлены нейтрально.':'Primary actions use blue. Status labels and secondary buttons use neutral colors.',
    'На каждом экране есть один главный акцент, крупные превью, короткие подписи и ровная сетка.':'Each screen has one primary focus, large previews, short labels, and a regular grid.',
    'Переходы длятся 180–240 мс, а лёгкое движение при наведении помогает заметить результат действия.':'Transitions take 180–240 ms, and subtle hover motion helps show the result of an action.'
  });

  Object.assign(en, {
    'VK Клипы':'VK Clips','Изучаю товар и нишу':'Reviewing product and niche',
    'Пишу сценарий под формат':'Writing a script for the format',
    'Генерирую сцены':'Generating scenes','Монтаж: переходы, текст, музыка':'Editing: transitions, text, and music',
    'Обложка и проверка':'Cover and review',
    'Профайлер':'Profiler','Описывает аудиторию, товар и задачи бренда':'Describes the audience, product, and brand goals',
    'Разведчик':'Researcher','Подбирает релевантные аккаунты ниши':'Finds relevant accounts in the niche',
    'Сборщик':'Collector','Собирает примеры публикаций для сравнения':'Collects posts for comparison',
    'Чистильщик':'Filter','Отделяет рекламу и нерелевантные материалы':'Filters ads and unrelated material',
    'Статистик':'Analyst','Сравнивает результаты с обычными просмотрами автора':'Compares results with the creator’s usual views',
    'Разметчик':'Classifier','Группирует ролики по подаче и формату':'Groups videos by presentation and format',
    'Визуальщик':'Visual analyst','Разбирает обложки, композицию и первые секунды':'Reviews covers, composition, and opening seconds',
    'Скептик':'Reviewer','Проверяет, какие выводы подтверждаются примерами':'Checks which conclusions are supported by examples',
    'Критик':'Critic','Отмечает ограничения и гипотезы для теста':'Notes limitations and ideas to test',
    'Собирает рекомендации для контента':'Compiles content recommendations',
    'Одна проблема — одно решение':'One problem, one solution',
    'Сколько времени уходит на подготовку одного ролика?':'How long does it take to prepare one video?',
    'Зритель узнаёт свою проблему в первые секунды и остаётся, чтобы увидеть решение.':'Viewers recognize their problem in the opening seconds and stay to see a solution.',
    'Покажи создание ролика от идеи до результата: один понятный шаг на каждый кадр.':'Show the video workflow from idea to result, with one clear step per shot.',
    'Сравнение подготовки роликов':'Comparing video workflows','Доказательство':'Demonstration',
    'Сравните подготовку роликов вручную и по контент-плану.':'Compare manual video preparation with a content plan.',
    'Два состояния рядом позволяют быстро заметить результат без длинного объяснения.':'Showing two states side by side makes the result easy to see.',
    'Сравни ручную подготовку и готовый контент-план. Покажи конкретный результат на экране.':'Compare manual preparation with a content plan and show a specific result.',
    'Список полезных советов':'List of useful tips','Обучение':'Education',
    'Пять идей для следующего ролика.':'Five ideas for your next video.',
    'Список даёт понятное обещание пользы и повод сохранить публикацию.':'A list promises clear value and gives viewers a reason to save the post.',
    'Подбери пять вопросов твоей аудитории. Ответь на каждый одной короткой сценой.':'Choose five audience questions and answer each in a short scene.',
    'Разбор типичной ошибки':'Reviewing a common mistake','Мнение':'Opinion',
    'Я начал с монтажа и пропустил работу над сценарием.':'I started editing before writing the script.',
    'Личная ошибка создаёт узнаваемую ситуацию и приглашает зрителя поделиться опытом.':'A personal mistake creates a familiar situation and invites viewers to share their experience.',
    'Расскажи, почему раньше начинал с монтажа, а теперь сначала определяешь одну мысль.':'Explain why you used to start with editing but now define the main point first.',
    'Рабочий день автора':'A creator’s workday','История':'Story',
    'Как автор готовит контент в течение дня?':'How does a creator prepare content during the day?',
    'Наблюдение за процессом делает продукт конкретнее и помогает понять его ценность.':'Showing the process makes the product easier to understand.',
    'Покажи свой день в трёх сценах: идея, подготовка, готовая публикация.':'Show your day in three scenes: idea, preparation, and finished post.',
    'Товар крупно, одна фраза':'Product close-up with one line','Оффер':'Offer',
    'Как подготовить неделю публикаций на основе одной идеи?':'How can one idea become a week of posts?',
    'Крупный план и короткая фраза удерживают внимание на одном преимуществе.':'A close-up and a short line focus attention on one benefit.',
    'Сними экран рабочего пространства и покажи один результат без списка всех функций.':'Record the workspace and show one result rather than listing every feature.',
    'AI-инструменты для создания контента: от идеи до готового ролика.':'AI tools for creating content, from idea to finished video.',
    'Предприниматели, эксперты и авторы, которые хотят выпускать контент регулярно.':'Business owners, experts, and creators who want to publish regularly.',
    'Просто, по делу, с конкретными примерами. Короткие предложения, без сложных терминов.':'Clear, direct writing with concrete examples, short sentences, and simple words.',
    'Контент-завод':'Content workspace',
    'Создание роликов, планирование и аналитика в одном рабочем пространстве.':'Video creation, planning, and analytics in one workspace.',
    'AI-аватар':'AI avatar','Видео с цифровым аватаром и голосом бренда.':'Video with a digital avatar and brand voice.',
    'Анна':'Anna','Михаил':'Mikhail','Елена':'Elena','Дмитрий':'Dmitry',
    'Можно посмотреть, как работает контент-завод для эксперта?':'Can I see how the content workspace works for an expert?',
    'Интересуют ролики для магазина. Какие материалы нужны?':'I need videos for a store. What materials do you need?',
    'Хочу узнать подробнее про AI-аватара.':'I would like to learn more about the AI avatar.',
    'Подготовить пример под нишу клиента.':'Prepare an example for the client’s niche.',
    'Нужен план публикаций на месяц.':'We need a monthly publishing plan.',
    'Материалы обсуждены.':'Materials discussed.',
    'Для ролика нужно выбрать тему, написать сценарий, подготовить материалы и собрать видео. В рабочем пространстве эти этапы можно проходить последовательно.':'Choose a topic, write a script, prepare materials, and assemble the video. These steps can be completed in the workspace.',
    'Перед съёмкой полезно определить аудиторию, её вопросы и основную мысль ролика.':'Before filming, define your audience, their questions, and the main point of the video.',
    'Если трудно выбрать тему ролика, начни с вопроса аудитории или примера из своей работы. Можно показать процесс, разобрать ошибку, сравнить два подхода или рассказать историю.':'If choosing a topic is difficult, start with an audience question or an example from your work. Show a process, review a mistake, compare approaches, or tell a story.',
    'Один и тот же сюжет можно адаптировать для разных языков, форматов и аудиторий, сохраняя узнаваемый тон бренда.':'The same story can be adapted for different languages, formats, and audiences while preserving your brand voice.'
  });

  Object.assign(en, {
    'Настроить бренд и библиотеку материалов':'Set up your brand and media library',
    'Добавить ролик':'Add video','Запланированные публикации':'Scheduled publications',
    'Открыть заявки':'Open leads','Открыть план':'Open plan','Собрать неделю':'Build a week',
    'РИЛС':'REEL','Пример за 14 дней':'Sample for 14 days','Проверка конфигурации':'Configuration check',
    'Настроить подключения':'Set up connections','Контент в центре внимания, интерфейс помогает сосредоточиться.':'The interface keeps the focus on your content.',
    'Настроить каналы':'Set up channels','В Instagram-студию':'Open Instagram studio',
    'Публикаций':'Publications','демонстрация анализа':'sample analysis',
    'ПН':'MON','ВТ':'TUE','СР':'WED','ЧТ':'THU','ПТ':'FRI','СБ':'SAT','ВС':'SUN',
    'Белые карточки, светлый фон и чистый синий акцент. Контент в центре внимания, интерфейс помогает сосредоточиться.':'White cards, a light background, and a blue accent keep the focus on your content.',
    'Графитовые карточки, глубокий чёрный и чистый синий акцент. Контент в центре внимания, интерфейс помогает сосредоточиться.':'Graphite cards, a dark background, and a blue accent keep the focus on your content.',
    'Скачать цвета':'Download colors','Обучение':'Education','Доказательство':'Demonstration',
    'Оффер':'Offer','Мнение':'Opinion','История':'Story','Хук':'Opening',
    'запланировано':'scheduled','просмотров':'views','переходов':'clicks','заявок':'leads',
    'файлов':'files','товара':'products','демо-канала':'sample channels',
    'от просмотров':'of views','от переходов':'of clicks'
  });

  const originalText = new WeakMap();
  const originalAttributes = new WeakMap();
  let language = 'ru';
  try { language = localStorage.getItem('content-mill-language') === 'en' ? 'en' : 'ru'; } catch {}

  function translate(value) {
    const match = String(value).match(/^(\s*)([\s\S]*?)(\s*)$/);
    const core = match[2];
    if (en[core]) return match[1] + en[core] + match[3];
    if (core.includes(' · ')) {
      const parts = core.split(' · ');
      const translated = parts.map(part => translate(part)).join(' · ');
      if (translated !== core) return match[1] + translated + match[3];
    }
    const openVideo = core.match(/^(Открыть ролик|Создать ролик): (.+)$/);
    if (openVideo) return match[1] + (openVideo[1] === 'Создать ролик' ? 'Create video' : 'Open video') + ': ' + translate(openVideo[2]) + match[3];
    const count = core.match(/^(Публикаций|Просмотров|Переходов|Заявок|Роликов|Идей в плане|Добавлено идей|Записей в проекте): (\d+)$/);
    if (count) return match[1] + ({'Публикаций':'Publications','Просмотров':'Views','Переходов':'Clicks','Заявок':'Leads','Роликов':'Videos','Идей в плане':'Ideas in plan','Добавлено идей':'Ideas added','Записей в проекте':'Records in project'}[count[1]]) + ': ' + count[2] + match[3];
    const amount = core.match(/^([\d.,]+(?:%|\s+[а-яё-]+)) (просмотров|переходов|заявок|файлов|товара|демо-канала|от просмотров|от переходов)$/i);
    if (amount) return match[1] + amount[1] + ' ' + en[amount[2]] + match[3];
    const metric = core.match(/^([\d.,]+)(?:\s+)(просмотров|переходов|заявок|файлов|товара|демо-канала)$/i);
    if (metric) return match[1] + metric[1] + ' ' + en[metric[2]] + match[3];
    const percent = core.match(/^([\d.,]+%) (от просмотров|от переходов)$/);
    if (percent) return match[1] + percent[1] + ' ' + en[percent[2]] + match[3];
    const hook = core.match(/^Хук: «(.+)»$/);
    if (hook) return match[1] + 'Opening: “' + translate(hook[1]) + '”' + match[3];
    const example = core.match(/^Пример за (\d+) дней$/);
    if (example) return match[1] + `Sample for ${example[1]} days` + match[3];
    const scheduled = core.match(/^Запланировано: (\d+)$/);
    if (scheduled) return match[1] + `Scheduled: ${scheduled[1]}` + match[3];
    const ideas = core.match(/^Идей в плане: (\d+) · (.+)$/);
    if (ideas) return match[1] + `Ideas in plan: ${ideas[1]} · ${translate(ideas[2])}` + match[3];
    const demoChannels = core.match(/^(\d+) демо-канала, без авторизации в соцсетях$/);
    if (demoChannels) return match[1] + `${demoChannels[1]} sample channels, without social media authorization` + match[3];
    const seconds = core.match(/^(\d+) сек$/);
    if (seconds) return match[1] + `${seconds[1]} sec` + match[3];
    const exampleNumber = core.match(/^ПРИМЕР (\d+)$/);
    if (exampleNumber) return match[1] + `EXAMPLE ${exampleNumber[1]}` + match[3];
    const quoted = core.match(/^«(.+)»$/);
    if (quoted) return match[1] + '“' + translate(quoted[1]) + '”' + match[3];
    const forBrand = core.match(/^Для (.+)$/);
    if (forBrand) return match[1] + 'For ' + translate(forBrand[1]) + match[3];
    const agentsReady = core.match(/^(\d+) из 10 агентов готовы$/);
    if (agentsReady) return match[1] + `${agentsReady[1]} of 10 agents ready` + match[3];
    const patternNote = core.match(/^Демо: обычно ([\d.,]+) просмотров · (×\d+) к базовому уровню$/);
    if (patternNote) return match[1] + `Sample: typically ${patternNote[1]} views · ${patternNote[2]} above baseline` + match[3];
    const productAdvice = core.match(/^Свяжи формат с продуктом «(.+)» и покажи один конкретный результат\.$/);
    if (productAdvice) return match[1] + `Connect the format to “${translate(productAdvice[1])}” and show one specific result.` + match[3];
    return value;
  }

  function applyText(node) {
    if (['SCRIPT','STYLE','TEXTAREA'].includes(node.parentElement?.tagName)) return;
    const value = node.nodeValue;
    let record = originalText.get(node);
    if (!record || (value !== record.ru && value !== record.en)) {
      record = {ru:value, en:translate(value)};
      originalText.set(node, record);
    }
    const next = record[language];
    if (value !== next) node.nodeValue = next;
  }

  function applyAttributes(element) {
    if (!element.hasAttribute) return;
    let records = originalAttributes.get(element);
    if (!records) { records = {}; originalAttributes.set(element, records); }
    for (const name of ['placeholder','aria-label','title']) {
      if (!element.hasAttribute(name)) continue;
      const value = element.getAttribute(name);
      let record = records[name];
      if (!record || (value !== record.ru && value !== record.en)) record = records[name] = {ru:value, en:translate(value)};
      const next = record[language];
      if (value !== next) element.setAttribute(name, next);
    }
  }

  function apply(rootNode = document.body) {
    if (!rootNode) return;
    if (rootNode.nodeType === Node.TEXT_NODE) { applyText(rootNode); return; }
    if (rootNode.nodeType !== Node.ELEMENT_NODE) return;
    applyAttributes(rootNode);
    const walker = document.createTreeWalker(rootNode, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      if (walker.currentNode.nodeType === Node.TEXT_NODE) applyText(walker.currentNode);
      else applyAttributes(walker.currentNode);
    }
    document.documentElement.lang = language;
    document.querySelectorAll('[data-lang-choice]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.langChoice === language)));
  }

  function setLanguage(next) {
    language = next === 'en' ? 'en' : 'ru';
    try { localStorage.setItem('content-mill-language', language); } catch {}
    apply();
  }

  function start() {
    apply();
    const observer = new MutationObserver(mutations => {
      for (const mutation of mutations) {
        if (mutation.type === 'characterData') applyText(mutation.target);
        else if (mutation.type === 'attributes') applyAttributes(mutation.target);
        else mutation.addedNodes.forEach(node => apply(node));
      }
    });
    observer.observe(document.body, {subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['placeholder','aria-label','title']});
  }

  root.MillI18n = {get language() { return language; }, translate, setLanguage, apply, start};
})(window);
