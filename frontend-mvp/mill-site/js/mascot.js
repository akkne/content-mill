'use strict';

// Keep the selected PNG silhouette; render the eyes as independent SVG parts.
window.MillMascot = (() => {
  const source = 'assets/mill-logo.png';
  const eyes = [{x:533,y:565,rx:82,ry:99},{x:716,y:562,rx:80,ry:99}];

  function markup() {
    return `<svg class="hero-mascot flower-avatar" data-mill-mascot viewBox="0 0 1254 1254" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <mask id="mill-flower-shape" x="0" y="0" width="1254" height="1254" maskUnits="userSpaceOnUse" style="mask-type:alpha">
          <image href="${source}" x="0" y="0" width="1254" height="1254"/>
        </mask>
        <linearGradient id="mill-flower-blue" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#2563EB"/><stop offset="1" stop-color="#2452E8"/>
        </linearGradient>
      </defs>
      <rect width="1254" height="1254" fill="url(#mill-flower-blue)" mask="url(#mill-flower-shape)"/>
      ${eyes.map(({x,y,rx,ry},i)=>`<g class="flower-eye">
        <g class="flower-eye-open">
          <ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="#fff"/>
          <g class="flower-pupil" data-eye="${i}" transform="translate(10 -10)">
            <ellipse cx="${x}" cy="${y}" rx="37" ry="43" fill="#102650"/>
          </g>
        </g>
        <path class="flower-eye-closed" d="M${x-60} ${y} Q${x} ${y+24} ${x+60} ${y}"/>
      </g>`).join('')}
    </svg>`;
  }

  function mount(root) {
    if (!root) return () => {};
    const pupils = [...root.querySelectorAll('.flower-pupil')];
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const current = eyes.map(() => ({x:10,y:-10}));
    let point = null, visible = true, active = false, disposed = false;
    let frame = 0, previousTime = 0, blinkTimer = 0, openTimer = 0, touchTimer = 0;

    function paint() {
      pupils.forEach((pupil,i) => pupil.setAttribute('transform',`translate(${current[i].x.toFixed(2)} ${current[i].y.toFixed(2)})`));
    }

    function stopFrame() {
      cancelAnimationFrame(frame);
      frame = 0;
      previousTime = 0;
    }

    function neutral() {
      point = null;
      if (active) requestFrame();
    }

    function tick(time) {
      frame = 0;
      if (!active || disposed) return;
      const rect = root.getBoundingClientRect();
      const blend = 1-Math.exp(-Math.min(previousTime ? time-previousTime : 16,48)/75);
      previousTime = time;
      let unsettled = false;
      eyes.forEach((eye,i) => {
        let target = {x:10,y:-10};
        if (point && rect.width && rect.height) {
          const dx = point.x-(rect.left+eye.x/1254*rect.width);
          const dy = point.y-(rect.top+eye.y/1254*rect.height);
          const distance = Math.hypot(dx,dy);
          const strength = Math.min(1,distance/240);
          target = distance ? {x:dx/distance*28*strength,y:dy/distance*37*strength} : {x:0,y:0};
        }
        current[i].x += (target.x-current[i].x)*blend;
        current[i].y += (target.y-current[i].y)*blend;
        unsettled ||= Math.abs(target.x-current[i].x)+Math.abs(target.y-current[i].y)>.08;
      });
      paint();
      if (unsettled) requestFrame();
      else previousTime = 0;
    }

    function requestFrame() {
      if (!frame && active && !disposed) frame = requestAnimationFrame(tick);
    }

    function scheduleBlink(first=false) {
      clearTimeout(blinkTimer);
      blinkTimer = setTimeout(() => {
        if (!active || disposed) return;
        root.classList.add('is-blinking');
        openTimer = setTimeout(() => {
          root.classList.remove('is-blinking');
          if (active) scheduleBlink();
        },220);
      },first ? 1600+Math.random()*1400 : 3200+Math.random()*3200);
    }

    function sync() {
      const next = visible && !document.hidden && !motion.matches && !disposed;
      if (next === active) return;
      active = next;
      if (active) { scheduleBlink(true); requestFrame(); }
      else {
        stopFrame();
        clearTimeout(blinkTimer);
        clearTimeout(openTimer);
        clearTimeout(touchTimer);
        root.classList.remove('is-blinking');
        point = null;
        current.forEach(p=>{p.x=10;p.y=-10;});
        paint();
      }
    }

    function follow(event) {
      if (!active || event.pointerType === 'touch') return;
      point = {x:event.clientX,y:event.clientY};
      requestFrame();
    }

    function touch(event) {
      if (!active || event.pointerType !== 'touch') return;
      clearTimeout(touchTimer);
      point = {x:event.clientX,y:event.clientY};
      requestFrame();
      touchTimer = setTimeout(neutral,1600);
    }

    function leave(event) { if (event.pointerType !== 'touch' && !event.relatedTarget) neutral(); }
    const observer = new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync();});
    observer.observe(root);
    document.addEventListener('pointermove',follow,{passive:true});
    document.addEventListener('pointerdown',touch,{passive:true});
    document.addEventListener('pointerout',leave,{passive:true});
    document.addEventListener('visibilitychange',sync);
    window.addEventListener('blur',neutral);
    motion.addEventListener('change',sync);
    sync();

    return () => {
      disposed = true;
      active = false;
      stopFrame();
      clearTimeout(blinkTimer);
      clearTimeout(openTimer);
      clearTimeout(touchTimer);
      observer.disconnect();
      document.removeEventListener('pointermove',follow);
      document.removeEventListener('pointerdown',touch);
      document.removeEventListener('pointerout',leave);
      document.removeEventListener('visibilitychange',sync);
      window.removeEventListener('blur',neutral);
      motion.removeEventListener('change',sync);
    };
  }

  return Object.freeze({markup,mount});
})();
