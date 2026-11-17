'use strict';

// Approved icon family: blue object pictograms without eyes or facial features.
// The flower mascot is deliberately separate until its final variant is chosen.
window.SaziBrandIcons = Object.freeze({
  sources: Object.freeze({
    publications: 'assets/publications.png',
    analytics: 'assets/analytics.png',
    plan: 'assets/plan.png',
    leads: 'assets/leads.png',
    home: 'assets/home.png',
    niche: 'assets/niche.png',
    agent: 'assets/agent.png',
    brand: 'assets/brand.png',
    videos: 'assets/videos.png',
    studio: 'assets/studio.png',
    channels: 'assets/channels.png',
    checks: 'assets/checks.png'
  }),
  aliases: Object.freeze({
    video: 'videos', calendar: 'plan', chart: 'analytics', trend: 'analytics',
    chat: 'leads', flame: 'niche', spark: 'agent', box: 'brand', plug: 'channels',
    shield: 'checks', globe: 'publications', search: 'niche'
  }),
  labels: Object.freeze({
    home: 'Главная', videos: 'Ролики', plan: 'План и автопилот',
    analytics: 'Аналитика', agent: 'Агент-маркетолог', niche: 'Анализ ниши',
    studio: 'Instagram-студия', brand: 'Бренд и товары', channels: 'Каналы и API',
    leads: 'Заявки', checks: 'Проверка API', publications: 'Публикации'
  })
});
