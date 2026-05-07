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
