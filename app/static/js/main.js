/* SimuRESPEL Web — JavaScript principal */
'use strict';

document.addEventListener('DOMContentLoaded', function () {

  // ---- Auto-dismiss flash messages ----
  setTimeout(function () {
    document.querySelectorAll('.alert.alert-dismissible').forEach(function (el) {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
        bsAlert.close();
      } catch (e) { /* noop */ }
    });
  }, 6500);

  // ---- Tooltips de Bootstrap ----
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
    try { new bootstrap.Tooltip(el); } catch (e) { /* noop */ }
  });

  // ---- Scroll suave para anclas internas ----
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href.length <= 1) return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ---- Scroll reveal (IntersectionObserver) ----
  const revealTargets = document.querySelectorAll(
    '.card-hover, .card-residuo, .seccion, .resultado-card, [data-reveal]'
  );
  if ('IntersectionObserver' in window && revealTargets.length) {
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry, idx) {
        if (entry.isIntersecting) {
          // Stagger by index in the batch for a wave effect
          setTimeout(() => entry.target.classList.add('is-visible'), idx * 60);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    revealTargets.forEach(function (el) {
      el.classList.add('reveal');
      io.observe(el);
    });
  } else {
    revealTargets.forEach(function (el) { el.classList.add('is-visible'); });
  }

  // ---- Highlight activo en navbar según URL ----
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar .nav-link').forEach(function (link) {
    const href = link.getAttribute('href');
    if (href && href === currentPath) {
      link.classList.add('active');
    }
  });

  // ---- Navbar shadow on scroll ----
  const nav = document.querySelector('.navbar.sticky-top');
  if (nav) {
    const onScroll = () => {
      if (window.scrollY > 8) nav.classList.add('navbar-scrolled');
      else nav.classList.remove('navbar-scrolled');
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // ---- Animated counters ----
  const counters = document.querySelectorAll('.counter[data-counter-target]');
  if (counters.length && 'IntersectionObserver' in window) {
    const easeOutCubic = t => 1 - Math.pow(1 - t, 3);
    const animateCounter = (el) => {
      const target = parseInt(el.dataset.counterTarget, 10);
      if (isNaN(target)) return;
      const duration = 1400;
      const start = performance.now();
      const tick = (now) => {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const value = Math.round(target * easeOutCubic(progress));
        el.textContent = value.toString();
        if (progress < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    const counterIO = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterIO.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    counters.forEach(c => counterIO.observe(c));
  }

  // ---- Ripple effect on .btn click ----
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn');
    if (!btn || btn.disabled) return;
    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size = Math.max(rect.width, rect.height);
    ripple.className = 'ripple';
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
    ripple.style.top  = (e.clientY - rect.top  - size / 2) + 'px';
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });

  // ---- Spinner en submits ----
  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function () {
      const btn = form.querySelector('button[type="submit"]');
      if (btn && !btn.dataset.noSpinner) {
        btn.disabled = true;
        const original = btn.innerHTML;
        btn.dataset.original = original;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Procesando...';
        // Re-enable after timeout (in case of validation error keeping the page)
        setTimeout(() => {
          if (btn.disabled) {
            btn.disabled = false;
            btn.innerHTML = original;
          }
        }, 8000);
      }
    });
  });

});
