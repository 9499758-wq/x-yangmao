(function(){
  const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.documentElement.style.colorScheme = 'dark';
  try { document.body.classList.add('page-enter'); } catch(e) {}
  const root = document.documentElement;
  window.addEventListener('pointermove', function(e){
    root.style.setProperty('--spot-x', e.clientX + 'px');
    root.style.setProperty('--spot-y', e.clientY + 'px');
  }, {passive:true});

  function bindTilt(el){
    el.addEventListener('pointermove', function(e){
      if (reduced) return;
      var r = el.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width;
      var y = (e.clientY - r.top) / r.height;
      el.style.setProperty('--mx', (x*100)+'%');
      el.style.setProperty('--my', (y*100)+'%');
      el.style.transform = 'perspective(900px) rotateX(' + ((0.5-y)*8) + 'deg) rotateY(' + ((x-0.5)*10) + 'deg) translateY(-2px)';
    });
    el.addEventListener('pointerleave', function(){ el.style.transform = ''; });
  }
  Array.prototype.forEach.call(document.querySelectorAll('.card, .module-tile'), bindTilt);

  function animateCount(el, target){
    var t0 = performance.now(), dur = 900;
    function frame(t){
      var p = Math.min(1, (t - t0)/dur);
      var eased = 1 - Math.pow(1-p, 3);
      el.textContent = String(Math.round(target * eased));
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-count]'), function(el){
    var n = parseInt(el.getAttribute('data-count')||'0',10);
    if (!reduced) animateCount(el, n); else el.textContent = String(n);
  });

  var reveals = Array.prototype.slice.call(document.querySelectorAll('.reveal, .card, .module-tile, .panel-box, .hero'));
  reveals.forEach(function(el){ el.classList.add('reveal'); });
  if (!reduced && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){ if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, {threshold: 0.12, rootMargin: '0px 0px -8% 0px'});
    reveals.forEach(function(el){ io.observe(el); });
  } else {
    reveals.forEach(function(el){ el.classList.add('in'); });
  }

  var canvas = document.getElementById('fx-particles');
  if (!canvas || reduced || !canvas.getContext) return;
  var ctx = canvas.getContext('2d');
  var w=0,h=0, particles=[], mouse={x:-9999,y:-9999};
  var mobile = Math.min(window.innerWidth, window.innerHeight) < 720;
  var COUNT = mobile ? 28 : 70;
  function resize(){ w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight; }
  function init(){
    particles = [];
    for (var i=0;i<COUNT;i++) particles.push({
      x: Math.random()*w, y: Math.random()*h,
      vx: (Math.random()-.5)*.35, vy: (Math.random()-.5)*.35,
      r: Math.random()*1.6 + .4
    });
  }
  function step(){
    ctx.clearRect(0,0,w,h);
    for (var i=0;i<particles.length;i++){
      var p = particles[i];
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
      var dx = p.x - mouse.x, dy = p.y - mouse.y;
      if (dx*dx + dy*dy < 16000) { p.vx += dx * -0.00003; p.vy += dy * -0.00003; }
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle = 'rgba(92,225,255,.75)'; ctx.fill();
    }
    var maxD = mobile ? 110 : 140;
    for (var i=0;i<particles.length;i++){
      for (var j=i+1;j<particles.length;j++){
        var a=particles[i], b=particles[j];
        var dx=a.x-b.x, dy=a.y-b.y, dist=Math.hypot(dx,dy);
        if (dist < maxD){
          ctx.strokeStyle = 'rgba(167,139,250,' + ((1-dist/maxD)*0.35) + ')';
          ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
        }
      }
    }
    requestAnimationFrame(step);
  }
  window.addEventListener('pointermove', function(e){ mouse.x=e.clientX; mouse.y=e.clientY; }, {passive:true});
  window.addEventListener('resize', function(){ resize(); init(); });
  resize(); init(); step();
})();
