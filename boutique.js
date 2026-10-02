/* Boutique Cohesif Agro : menu, filtres, simulateur, galerie, formulaire */
(function () {
  'use strict';

  // Menu mobile
  var burger = document.getElementById('bqBurger');
  var menu = document.getElementById('bqMenu');
  if (burger && menu) {
    burger.addEventListener('click', function () {
      var nav = burger.closest('.bq-nav');
      if (nav) menu.style.top = nav.getBoundingClientRect().bottom + 'px';
      var open = menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    menu.addEventListener('click', function (e) {
      if (e.target.closest('a')) { menu.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); }
    });
  }

  // Filtres du catalogue
  var filters = document.querySelectorAll('.bq-filter');
  var cards = document.querySelectorAll('#bqGrid .bq-card');
  filters.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var f = btn.getAttribute('data-f');
      filters.forEach(function (b) { b.classList.toggle('is-on', b === btn); });
      cards.forEach(function (c) {
        var ok = f === 'tout' || c.getAttribute('data-cat') === f || c.getAttribute('data-lieu') === f;
        c.hidden = !ok;
      });
    });
  });

  // Simulateur de chiffre d'affaires
  var sim = document.querySelector('[data-sim]');
  if (sim) {
    var DEFAUTS = { pizza: [9, 30], frites: [4, 40], burger: [6, 30], glace: [4, 50], cafe: [2, 60] };
    var prod = sim.querySelector('[data-sim-prod]');
    var prix = sim.querySelector('[data-sim-prix]');
    var ventes = sim.querySelector('[data-sim-ventes]');
    var fmt = function (n) { return Math.round(n).toLocaleString('fr-FR') + ' €'; };
    var calc = function () {
      var p = parseFloat(prix.value), v = parseInt(ventes.value, 10);
      sim.querySelector('[data-sim-pv]').textContent = p.toLocaleString('fr-FR', { minimumFractionDigits: p % 1 ? 2 : 0 }) + ' €';
      sim.querySelector('[data-sim-nv]').textContent = v;
      sim.querySelector('[data-sim-mois]').textContent = fmt(p * v * 30);
      sim.querySelector('[data-sim-an]').textContent = fmt(p * v * 365);
    };
    prod.addEventListener('change', function () {
      var d = DEFAUTS[prod.value]; prix.value = d[0]; ventes.value = d[1]; calc();
    });
    prix.addEventListener('input', calc);
    ventes.addEventListener('input', calc);
    calc();
  }

  // Galerie fiche produit
  var main = document.getElementById('bqMainImg');
  document.querySelectorAll('.bq-thumb').forEach(function (t) {
    t.addEventListener('click', function () {
      main.src = t.getAttribute('data-src');
      document.querySelectorAll('.bq-thumb').forEach(function (x) { x.classList.toggle('is-on', x === t); });
    });
  });

  // Présélection de la machine / du financement dans le formulaire
  var form = document.querySelector('[data-bq-form]');
  var selectMachine = form && form.querySelector('select[name="machine"]');
  var choisir = function (slug) {
    if (!selectMachine || !slug) return;
    var opt = selectMachine.querySelector('option[data-slug="' + slug + '"]');
    if (opt) selectMachine.value = opt.value;
  };
  document.addEventListener('click', function (e) {
    var a = e.target.closest('[data-machine]');
    if (a) choisir(a.getAttribute('data-machine'));
    var f = e.target.closest('[data-financement]');
    if (f && form) form.querySelector('select[name="financement"]').value = f.getAttribute('data-financement');
  });
  var q = new URLSearchParams(location.search).get('machine');
  if (q) choisir(q);

  // Envoi du formulaire (Formspree)
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]');
      var label = btn.textContent;
      btn.disabled = true; btn.textContent = 'Envoi en cours…';
      fetch(form.action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error();
          form.querySelector('.bq-form-ok').hidden = false;
          form.reset();
        })
        .catch(function () {
          alert("L'envoi n'a pas fonctionné. Réessayez ou écrivez-nous sur WhatsApp au 07 56 85 57 27.");
        })
        .finally(function () { btn.disabled = false; btn.textContent = label; });
    });
  }

  // Barre mobile : masquée quand le formulaire est visible
  var sticky = document.querySelector('.bq-sticky');
  var devis = document.getElementById('devis');
  if (sticky && devis && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (en) {
      sticky.classList.toggle('is-hidden', en[0].isIntersecting);
    }).observe(devis);
  }
})();
