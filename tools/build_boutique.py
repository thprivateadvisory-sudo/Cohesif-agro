#!/usr/bin/env python3
"""Génère la boutique Cohesif Agro (distributeurs automatiques) depuis data/boutique.json.

    python3 tools/build_boutique.py

Produit :
  - boutique.html            (catalogue)
  - boutique-*.html          (une fiche par machine)
  - sitemap.xml              (ajoute les URL boutique si absentes)

Pour afficher un prix : renseigner "prix" (€ HT) et, si besoin, "leasingMois"
dans data/boutique.json, puis relancer le script. Tant que "prix" vaut null,
la fiche affiche « Prix sur demande » et le bouton ouvre la demande de prix.
"""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "boutique.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
FORM = DATA["formspree"]
WA = DATA["whatsapp"]
PRODUITS = DATA["produits"]
CATS = DATA["categories"]
# "famille": "equipement" = matériel professionnel (filmeuse…), présenté à part des distributeurs
EQUIPEMENTS = [p for p in PRODUITS if p.get("famille") == "equipement"]
DISTRIBUTEURS = [p for p in PRODUITS if p.get("famille") != "equipement"]
E = html.escape


def euros(n):
    return f"{n:,.0f}".replace(",", " ") + " €"


def prix_html(p, grand=False):
    if p.get("prix"):
        out = f'<span class="px-val">{euros(p["prix"])} <small>HT</small></span>'
        if p.get("leasingMois"):
            out += f'<span class="px-sub">ou {euros(p["leasingMois"])} HT/mois avec Cohesif Leasing</span>'
        else:
            out += '<span class="px-sub">Transport et dédouanement inclus</span>'
        return out
    return ('<span class="px-val px-dem">Prix sur demande</span>'
            '<span class="px-sub">Réponse sous 48 h · achat ou leasing</span>')


def wa_link(texte):
    return f"https://wa.me/{WA}?text={quote(texte)}"


def est_equipement(p):
    return p.get("famille") == "equipement"


def lieu_label(p):
    return p.get("lieu") or ("Intérieur" if p["emplacement"] == "interieur" else "Extérieur")


# ─────────────────────────── gabarit commun

def head(title, desc, url, image, extra_ld=""):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}"/>
<meta name="robots" content="index, follow, max-image-preview:large"/>
<link rel="canonical" href="{url}"/>
<meta property="og:title" content="{E(title)}"/>
<meta property="og:description" content="{E(desc)}"/>
<meta property="og:url" content="{url}"/>
<meta property="og:type" content="website"/>
<meta property="og:locale" content="fr_FR"/>
<meta property="og:site_name" content="Cohesif Agro"/>
<meta property="og:image" content="{SITE}/{image}"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="theme-color" content="#1A3A2A"/>
<link rel="icon" href="favicon.svg" type="image/svg+xml"/>
<link rel="manifest" href="site.webmanifest"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="boutique.css"/>
{extra_ld}
</head>
<body>
"""


NAV = """<nav class="bq-nav" aria-label="Navigation principale">
  <a href="index.html" class="bq-logo"><img src="img/boutique/logo-cohesif-agro-trim.webp" alt="Cohesif Agro" width="520" height="133"/></a>
  <ul class="bq-links">
    <li><a href="boutique.html#machines">Les machines</a></li>
    <li><a href="boutique.html#equipements">Équipements pro</a></li>
    <li><a href="boutique.html#rentabilite">Rentabilité</a></li>
    <li><a href="boutique.html#financement">Financement</a></li>
    <li><a href="boutique.html#faq">Questions</a></li>
    <li><a href="index.html">Cohesif Agro</a></li>
  </ul>
  <div class="bq-nav-r">
    <a href="#devis" class="bq-btn bq-btn-sm">Demander les prix</a>
    <button class="bq-burger" id="bqBurger" aria-label="Ouvrir le menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</nav>
<div class="bq-mmenu" id="bqMenu">
  <a href="boutique.html#machines">Les machines</a>
  <a href="boutique.html#equipements">Équipements pro</a>
  <a href="boutique.html#rentabilite">Rentabilité</a>
  <a href="boutique.html#financement">Financement</a>
  <a href="boutique.html#faq">Questions</a>
  <a href="index.html">Cohesif Agro</a>
  <a href="#devis" class="bq-btn">Demander les prix</a>
</div>
"""


def form_html(selected=None, titre="Recevez les prix et un devis sous 48 h"):
    sel = next((p for p in PRODUITS if p["slug"] == selected), None)
    if sel and est_equipement(sel):
        sujet = f"Cohesif Agro · Demande de prix {sel['court'].lower()}"
        wa_txt = f"Bonjour, je souhaite recevoir le prix de la « {sel['nom']} »."
    else:
        sujet = "Cohesif Agro · Demande de prix distributeur automatique"
        wa_txt = "Bonjour, je souhaite recevoir les prix de vos distributeurs automatiques."
    opts = "".join(
        f'<option value="{E(p["nom"])}" data-slug="{p["slug"]}"{" selected" if p["slug"] == selected else ""}>{E(p["nom"])}</option>'
        for p in PRODUITS)
    return f"""<section class="bq-devis" id="devis">
  <div class="bq-in bq-devis-grid">
    <div class="bq-devis-txt">
      <p class="bq-kicker">Demande de prix gratuite</p>
      <h2>{titre}</h2>
      <p>Dites-nous quelle machine vous intéresse et où vous voulez l'installer. Vous recevez un devis <strong>tout compris</strong> : machine, transport, dédouanement et livraison en France. Sans engagement.</p>
      <ul class="bq-checks">
        <li>Réponse d'un conseiller sous 48 h</li>
        <li>Achat comptant ou financement en leasing</li>
        <li>Conseil sur l'emplacement et la rentabilité</li>
      </ul>
      <a class="bq-wa-inline" href="{wa_link(wa_txt)}" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12.05 2a9.9 9.9 0 0 0-8.5 14.95L2 22l5.2-1.5A9.9 9.9 0 1 0 12.05 2zm5.8 14.1c-.25.7-1.45 1.33-2 1.4-.52.08-1.17.11-1.88-.12-.43-.13-.99-.32-1.7-.62-3-1.3-4.94-4.3-5.1-4.5-.14-.2-1.2-1.6-1.2-3.07s.76-2.18 1.04-2.48c.27-.3.6-.37.8-.37h.57c.18 0 .43-.07.67.5.25.6.84 2.06.92 2.2.07.15.12.33.02.52-.1.2-.15.32-.3.5-.14.17-.3.38-.44.52-.15.15-.3.3-.13.6.17.3.77 1.27 1.65 2.05 1.14 1.01 2.1 1.33 2.4 1.48.3.15.47.12.64-.07.18-.2.75-.87.94-1.17.2-.3.4-.25.67-.15.27.1 1.73.82 2.03.97.3.15.5.22.57.35.07.12.07.7-.18 1.4z"/></svg>
        Ou écrivez-nous sur WhatsApp
      </a>
    </div>
    <form class="bq-form" action="{FORM}" method="POST" data-bq-form>
      <input type="hidden" name="_subject" value="{E(sujet)}"/>
      <input type="hidden" name="source" value="Boutique Cohesif Agro"/>
      <input type="text" name="_gotcha" class="bq-hp" tabindex="-1" autocomplete="off" aria-hidden="true"/>
      <div class="bq-frow">
        <label>Nom et prénom<input type="text" name="nom" required autocomplete="name"/></label>
        <label>Société <span>(facultatif)</span><input type="text" name="societe" autocomplete="organization"/></label>
      </div>
      <div class="bq-frow">
        <label>Email<input type="email" name="email" required autocomplete="email"/></label>
        <label>Téléphone<input type="tel" name="telephone" required autocomplete="tel"/></label>
      </div>
      <label>Machine qui vous intéresse
        <select name="machine" required>
          <option value="">Choisir une machine…</option>
          {opts}
          <option value="Plusieurs machines / je ne sais pas encore">Plusieurs machines / je ne sais pas encore</option>
        </select>
      </label>
      <div class="bq-frow">
        <label>Emplacement prévu
          <select name="emplacement">
            <option value="">Sélectionner…</option>
            <option>Centre commercial / galerie</option>
            <option>Parking / station-service</option>
            <option>Entreprise / zone d'activité</option>
            <option>Gare, campus, hôpital</option>
            <option>Devant mon commerce</option>
            <option>Lieu de loisirs / tourisme</option>
            <option>Usine / entrepôt / atelier</option>
            <option>Pas encore trouvé</option>
          </select>
        </label>
        <label>Financement
          <select name="financement">
            <option value="">Sélectionner…</option>
            <option>Achat comptant</option>
            <option>Leasing (paiement mensuel)</option>
            <option>Je souhaite comparer les deux</option>
          </select>
        </label>
      </div>
      <label>Votre projet <span>(facultatif)</span><textarea name="message" rows="3" placeholder="Nombre de machines, ville, date souhaitée…"></textarea></label>
      <button type="submit" class="bq-btn bq-btn-lg">Recevoir les prix</button>
      <p class="bq-form-note">Vos données servent uniquement à vous répondre. <a href="politique-confidentialite.html">Confidentialité</a></p>
      <div class="bq-form-ok" role="status" hidden>
        <strong>Merci, votre demande est bien envoyée.</strong>
        <span>Un conseiller Cohesif Agro vous recontacte sous 48 h avec les prix et les délais.</span>
      </div>
    </form>
  </div>
</section>
"""


FOOTER = f"""<footer class="bq-foot">
  <div class="bq-in bq-foot-grid">
    <div>
      <img src="img/boutique/logo-cohesif-agro-trim.webp" alt="Cohesif Agro" width="520" height="133" class="bq-foot-logo"/>
      <p>Équipements agroalimentaires et distributeurs automatiques, conformes CE, livrés en France. Une société du Groupe Cohesif.</p>
    </div>
    <div>
      <h4>Boutique</h4>
      {"".join(f'<a href="{p["slug"]}.html">{E(p["court"])}</a>' for p in PRODUITS)}
    </div>
    <div>
      <h4>Cohesif Agro</h4>
      <a href="index.html">Accueil</a>
      <a href="index.html#equipements">Équipements IAA</a>
      <a href="index.html#offres">Packaging alimentaire</a>
      <a href="https://www.cohesifleasing.fr" target="_blank" rel="noopener">Cohesif Leasing</a>
    </div>
    <div>
      <h4>Contact</h4>
      <a href="mailto:cohesifagro@outlook.com">cohesifagro@outlook.com</a>
      <a href="{wa_link("Bonjour, j'ai une question sur vos distributeurs automatiques.")}" target="_blank" rel="noopener">WhatsApp : 07 56 85 57 27</a>
      <span>200 rue de la Croix-Nivert, 75015 Paris</span>
    </div>
  </div>
  <div class="bq-in bq-foot-bot">
    <span>2026 Groupe Cohesif · cohesifagro.fr</span>
    <span><a href="mentions-legales.html">Mentions légales</a> · <a href="politique-confidentialite.html">Confidentialité</a></span>
  </div>
</footer>
"""


def wa_float(texte):
    return f"""<a href="{wa_link(texte)}" class="bq-wa" target="_blank" rel="noopener" aria-label="Nous écrire sur WhatsApp">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12.05 2a9.9 9.9 0 0 0-8.5 14.95L2 22l5.2-1.5A9.9 9.9 0 1 0 12.05 2zm5.8 14.1c-.25.7-1.45 1.33-2 1.4-.52.08-1.17.11-1.88-.12-.43-.13-.99-.32-1.7-.62-3-1.3-4.94-4.3-5.1-4.5-.14-.2-1.2-1.6-1.2-3.07s.76-2.18 1.04-2.48c.27-.3.6-.37.8-.37h.57c.18 0 .43-.07.67.5.25.6.84 2.06.92 2.2.07.15.12.33.02.52-.1.2-.15.32-.3.5-.14.17-.3.38-.44.52-.15.15-.3.3-.13.6.17.3.77 1.27 1.65 2.05 1.14 1.01 2.1 1.33 2.4 1.48.3.15.47.12.64-.07.18-.2.75-.87.94-1.17.2-.3.4-.25.67-.15.27.1 1.73.82 2.03.97.3.15.5.22.57.35.07.12.07.7-.18 1.4z"/></svg>
</a>
"""


TAIL = '<script src="boutique.js" defer></script>\n</body>\n</html>\n'


def card(p):
    chips = "".join(f'<li><b>{E(v)}</b> {E(l)}</li>' for v, l in p["chiffres"][:3])
    lieu = lieu_label(p)
    return f"""<article class="bq-card" data-cat="{p["categorie"]}" data-lieu="{p["emplacement"]}">
  <a href="{p["slug"]}.html" class="bq-card-img">
    <span class="bq-badge">{E(p["badge"])}</span>
    <img src="{p["image"]}" alt="{E(p["nom"])}" loading="lazy"/>
  </a>
  <div class="bq-card-body">
    <p class="bq-card-cat">{E(CATS[p["categorie"]])} · {lieu}</p>
    <h3><a href="{p["slug"]}.html">{E(p["nom"])}</a></h3>
    <p class="bq-card-acc">{E(p["accroche"])}</p>
    <ul class="bq-chips">{chips}</ul>
    <div class="bq-card-foot">
      <div class="bq-px">{prix_html(p)}</div>
      <div class="bq-card-btns">
        <a href="{p["slug"]}.html" class="bq-btn bq-btn-ghost">Voir la fiche</a>
        <a href="#devis" class="bq-btn" data-machine="{p["slug"]}">Demander le prix</a>
      </div>
    </div>
  </div>
</article>"""


FAQ = [
    ("Pourquoi les prix ne sont-ils pas affichés ?",
     "Le prix dépend de la version, de la personnalisation (habillage à vos couleurs) et du lieu de livraison. Nous vous envoyons un devis tout compris sous 48 h : machine, transport, dédouanement et livraison en France."),
    ("Les machines sont-elles conformes pour la France ?",
     "Oui. Les machines sont livrées avec le marquage CE et la déclaration UE de conformité, comme tous les équipements Cohesif Agro. Les paiements par carte bancaire sont pris en charge."),
    ("Quel est le délai de livraison ?",
     "Comptez en moyenne 30 à 45 jours entre la validation de la commande et la livraison sur site. Le planning précis figure dans votre devis."),
    ("Faut-il du personnel pour faire tourner la machine ?",
     "Non. Le client commande, paie et récupère son produit tout seul. Vous passez seulement pour recharger les produits et faire l'entretien courant, et vous suivez vos ventes et vos stocks à distance sur votre smartphone."),
    ("Où puis-je installer un distributeur ?",
     "Dans tout lieu de passage : centre commercial, parking, station-service, entreprise, gare, campus, devant votre commerce… Sur un terrain privé, il suffit de l'accord du propriétaire. Sur la voie publique, une autorisation d'occupation doit être demandée à la mairie. Nous vous aidons à choisir la bonne machine selon l'emplacement."),
    ("Y a-t-il des démarches pour vendre de l'alimentaire ?",
     "Oui, comme toute activité alimentaire : une déclaration auprès de la DDPP de votre département et le respect des règles d'hygiène (chaîne du froid, traçabilité des produits). Ces démarches sont simples, nous vous indiquons les étapes."),
    ("Puis-je payer en plusieurs fois ?",
     "Oui. Avec Cohesif Leasing, la société de financement du Groupe Cohesif, vous payez une mensualité fixe et la machine commence à rapporter dès son installation. Indiquez « Leasing » dans votre demande."),
    ("Peut-on mettre la machine à nos couleurs ?",
     "Oui. L'habillage, le logo et la langue de l'écran sont personnalisables. C'est idéal pour créer votre propre marque ou développer un réseau."),
    ("Qui fournit les pizzas, frites ou burgers ?",
     "Vous choisissez librement vos fournisseurs de produits. Et comme Cohesif Agro source aussi le packaging alimentaire (boîtes à pizza, barquettes, gobelets), nous pouvons fournir vos emballages au meilleur prix."),
]


def faq_html(items):
    return "".join(f'<details class="bq-faq-it"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in items)


def faq_ld(items):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


# ─────────────────────────── bloc SAV (fiche produit)

ICONES = {
    "bouclier": '<path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6l8-3z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    "camion": '<path d="M3 6h11v10H3zM14 9h4l3 3v4h-7"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    "personne": '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
    "engrenage": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
    "cle": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4 2.6-2.6z"/>',
    "telephone": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
}


def sav_html(p):
    s = p.get("sav")
    if not s:
        return ""
    items = "".join(
        f'<div class="bq-sav-it"><span class="bq-ico"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONES[i]}</svg></span>'
        f'<h3>{E(h)}</h3><p>{E(d)}</p></div>' for i, h, d in s["items"])
    tel = WA[2:]
    tel_txt = "0" + tel[0] + " " + " ".join(tel[i:i + 2] for i in range(1, 9, 2))
    return f"""<section class="bq-sec bq-sav" id="sav">
    <div class="bq-in">
      <div class="bq-sec-head">
        <p class="bq-kicker">{E(s["kicker"])}</p>
        <h2>{E(s["titre"])} <span class="bq-accent">{E(s["accent"])}</span></h2>
        <p>{E(s["intro"])}</p>
      </div>
      <div class="bq-sav-grid">{items}</div>
      <div class="bq-sav-cta">
        <div><b>Un interlocuteur unique, avant et après l'achat.</b><span>{E(s["horaires"])}</span></div>
        <div class="bq-sav-btns">
          <a href="tel:+{WA}" class="bq-btn bq-btn-lg bq-btn-light"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONES["telephone"]}</svg> {tel_txt}</a>
          <a href="{wa_link(f"Bonjour, j'ai une question sur la « {p['nom']} ».")}" class="bq-btn bq-btn-lg bq-btn-wa" target="_blank" rel="noopener">WhatsApp</a>
        </div>
      </div>
    </div>
  </section>"""


# ─────────────────────────── page catalogue

def equipements_html():
    if not EQUIPEMENTS:
        return ""
    return f"""<section class="bq-sec bq-pro" id="equipements">
  <div class="bq-in">
    <div class="bq-sec-head">
      <p class="bq-kicker">Équipements professionnels</p>
      <h2>Pour votre usine, votre entrepôt ou votre atelier</h2>
      <p>Le même sérieux que pour nos distributeurs : machines sélectionnées, conformes CE, livrées en France avec un prix tout compris.</p>
    </div>
    <div class="bq-grid">
      {"".join(card(p) for p in EQUIPEMENTS)}
      <aside class="bq-card-more">
        <p class="bq-kicker">Pourquoi acheter chez Cohesif Agro</p>
        <h3>Un interlocuteur en France, du devis à la livraison</h3>
        <ul class="bq-checks bq-checks-dark">
          <li>Machines conformes CE, déclaration UE de conformité fournie</li>
          <li>Garantie 12 mois, pièces détachées et SAV assurés par nos soins</li>
          <li>Livraison sur site, mise en service et prise en main</li>
          <li>Composants industriels de grandes marques (Omron, Panasonic…)</li>
          <li>Transport, dédouanement et livraison gérés par nos soins</li>
          <li>Consommables fournis : film étirable, packaging alimentaire</li>
          <li>Achat comptant ou leasing avec Cohesif Leasing</li>
        </ul>
        <a href="#devis" class="bq-btn bq-btn-lg">Demander un devis</a>
      </aside>
    </div>
  </div>
</section>
"""


def build_catalogue():
    url = f"{SITE}/boutique.html"
    title = "Distributeurs automatiques de pizzas, frites, glaces et café | Boutique Cohesif Agro"
    desc = ("Achetez votre distributeur automatique de pizzas, frites, burgers, glaces ou café, conforme CE et livré en France. "
            "Vente 24 h/24 sans personnel. Aussi : filmeuse à palettes pour l'industrie. Devis tout compris sous 48 h, achat ou leasing.")
    ld_obj = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": "Boutique Cohesif Agro : distributeurs automatiques", "url": url, "description": desc},
        {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{p['slug']}.html", "name": p["nom"]}
            for i, p in enumerate(DISTRIBUTEURS + EQUIPEMENTS)]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Boutique", "item": url}]},
        faq_ld(FAQ)]}
    filtres = '<button class="bq-filter is-on" data-f="tout">Toutes <span>' + str(len(DISTRIBUTEURS)) + '</span></button>'
    for k, v in CATS.items():
        n = sum(1 for p in DISTRIBUTEURS if p["categorie"] == k)
        if n:
            filtres += f'<button class="bq-filter" data-f="{k}">{E(v)} <span>{n}</span></button>'
    filtres += '<button class="bq-filter" data-f="exterieur">Extérieur <span>' + str(
        sum(1 for p in DISTRIBUTEURS if p["emplacement"] == "exterieur")) + '</span></button>'
    sim_opts = "".join(
        f'<option value="{k}">{v}</option>' for k, v in
        [("pizza", "Pizzas"), ("frites", "Frites"), ("burger", "Burgers"), ("glace", "Glaces"), ("cafe", "Cafés")])

    body = head(title, desc, url, "img/boutique/pizza-interieur.webp", ld(ld_obj)) + NAV + f"""
<header class="bq-hero">
  <div class="bq-in bq-hero-grid">
    <div class="bq-hero-txt">
      <p class="bq-kicker">Boutique · Distributeurs automatiques</p>
      <h1>Votre point de vente ouvert <em>24 h/24</em>, sans personnel.</h1>
      <p class="bq-hero-p">Pizzas chaudes en 90 secondes, frites à la minute, burgers, glaces et café : des distributeurs automatiques conformes CE, livrés et prêts à vendre partout en France.</p>
      <div class="bq-hero-btns">
        <a href="#machines" class="bq-btn bq-btn-lg">Voir les machines</a>
        <a href="#rentabilite" class="bq-btn bq-btn-lg bq-btn-line">Calculer mes revenus</a>
      </div>
    </div>
    <div class="bq-hero-vis" aria-hidden="true">
      <img src="img/boutique/frites.webp" alt="" class="hv hv-l"/>
      <img src="img/boutique/pizza-interieur.webp" alt="" class="hv hv-c"/>
      <img src="img/boutique/glace.webp" alt="" class="hv hv-r"/>
      <div class="hv-tag"><b>90 s</b><span>une pizza chaude</span></div>
    </div>
  </div>
  <ul class="bq-in bq-trust">
    <li><b>Conformes CE</b><span>Normes françaises et européennes</span></li>
    <li><b>Prix tout compris</b><span>Machine, transport, douane</span></li>
    <li><b>Achat ou leasing</b><span>Avec Cohesif Leasing</span></li>
    <li><b>Suivi à distance</b><span>Ventes et stocks sur mobile</span></li>
  </ul>
</header>

<main>
<section class="bq-sec" id="machines">
  <div class="bq-in">
    <div class="bq-sec-head">
      <p class="bq-kicker">Notre sélection</p>
      <h2>{len(DISTRIBUTEURS)} machines choisies pour le marché français</h2>
      <p>Nous avons retenu les modèles les plus rentables et les plus simples à exploiter. La pizza est notre spécialité, en intérieur comme en extérieur.</p>
    </div>
    <div class="bq-filters" role="group" aria-label="Filtrer les machines">{filtres}</div>
    <div class="bq-grid" id="bqGrid">
      {"".join(card(p) for p in DISTRIBUTEURS)}
      <aside class="bq-card-more">
        <p class="bq-kicker">Sur commande</p>
        <h3>Vous cherchez un autre distributeur ?</h3>
        <p>Bubble tea, plats chauds, café avec robot barista, glaces sans robot, versions kiosque… D'autres modèles sont disponibles sur commande, avec les mêmes garanties.</p>
        <a href="#devis" class="bq-btn bq-btn-lg">Nous consulter</a>
      </aside>
    </div>
  </div>
</section>

{equipements_html()}
<section class="bq-sec bq-why">
  <div class="bq-in">
    <div class="bq-sec-head">
      <p class="bq-kicker">Pourquoi un distributeur</p>
      <h2>Un commerce qui travaille pendant que vous dormez</h2>
    </div>
    <div class="bq-why-grid">
      <div><span class="bq-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></span><h3>Ouvert 24 h/24, 7 j/7</h3><p>Nuits, dimanches, jours fériés : la machine vend quand tous les commerces sont fermés.</p></div>
      <div><span class="bq-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg></span><h3>Zéro salarié</h3><p>Le client commande, paie et se sert seul. Vous passez seulement pour recharger.</p></div>
      <div><span class="bq-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg></span><h3>Tout sur votre téléphone</h3><p>Ventes, stocks, alertes de panne ou de rupture : vous pilotez tout à distance.</p></div>
      <div><span class="bq-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/></svg></span><h3>Paiement sans contact</h3><p>Carte bancaire et, selon les modèles, pièces et billets : aucune vente perdue.</p></div>
    </div>
  </div>
</section>

<section class="bq-sec bq-sim-sec" id="rentabilite">
  <div class="bq-in bq-sim">
    <div class="bq-sim-txt">
      <p class="bq-kicker">Simulateur</p>
      <h2>Combien peut rapporter votre machine ?</h2>
      <p>Choisissez un produit, réglez le prix de vente et le nombre de ventes par jour. Le calcul se met à jour tout seul.</p>
      <p class="bq-sim-note">Estimation indicative du chiffre d'affaires, avant coût des produits, emplacement et charges. Les résultats réels dépendent surtout de l'emplacement.</p>
    </div>
    <div class="bq-sim-box" data-sim>
      <label>Produit vendu<select data-sim-prod>{sim_opts}</select></label>
      <label>Prix de vente <output data-sim-pv></output><input type="range" min="1" max="15" step="0.5" value="9" data-sim-prix/></label>
      <label>Ventes par jour <output data-sim-nv></output><input type="range" min="5" max="150" step="1" value="30" data-sim-ventes/></label>
      <div class="bq-sim-res">
        <div><span>Par mois</span><b data-sim-mois>0 €</b></div>
        <div><span>Par an</span><b data-sim-an>0 €</b></div>
      </div>
      <a href="#devis" class="bq-btn bq-btn-lg bq-btn-full">Recevoir le prix de la machine</a>
    </div>
  </div>
</section>

<section class="bq-sec bq-steps-sec">
  <div class="bq-in">
    <div class="bq-sec-head">
      <p class="bq-kicker">Comment ça se passe</p>
      <h2>De votre demande à la première vente</h2>
    </div>
    <ol class="bq-steps">
      <li><b>1</b><h3>Votre demande</h3><p>Vous choisissez une machine et nous parlons de votre emplacement.</p></li>
      <li><b>2</b><h3>Devis sous 48 h</h3><p>Un prix tout compris, en achat ou en leasing, sans surprise.</p></li>
      <li><b>3</b><h3>Fabrication et transport</h3><p>Contrôle qualité, transport et dédouanement gérés par nos soins.</p></li>
      <li><b>4</b><h3>Livraison et ventes</h3><p>La machine est livrée chez vous, vous la remplissez, elle vend.</p></li>
    </ol>
  </div>
</section>

<section class="bq-sec bq-lease" id="financement">
  <div class="bq-in bq-lease-grid">
    <div>
      <p class="bq-kicker">Financement</p>
      <h2>Lancez-vous sans avancer le prix de la machine</h2>
      <p>Avec <strong>Cohesif Leasing</strong>, la société de financement du Groupe Cohesif, vous réglez une mensualité fixe. Votre distributeur commence à vendre dès sa livraison : ce sont ses ventes qui paient la mensualité.</p>
      <ul class="bq-checks">
        <li>Mensualité fixe, durée au choix</li>
        <li>Préserve votre trésorerie</li>
        <li>Une seule demande pour la machine et le financement</li>
      </ul>
    </div>
    <div class="bq-lease-card">
      <img src="cohesif-leasing-logo.png" alt="Cohesif Leasing" width="120" height="60"/>
      <p>Cochez « Leasing » dans votre demande de prix : vous recevez le prix comptant et la mensualité.</p>
      <a href="#devis" class="bq-btn bq-btn-lg bq-btn-full" data-financement="Leasing (paiement mensuel)">Demander un financement</a>
    </div>
  </div>
</section>

<section class="bq-sec bq-faq" id="faq">
  <div class="bq-in bq-faq-in">
    <div class="bq-sec-head">
      <p class="bq-kicker">Questions fréquentes</p>
      <h2>Tout savoir avant de se lancer</h2>
    </div>
    {faq_html(FAQ)}
  </div>
</section>

{form_html()}
</main>
""" + FOOTER + wa_float("Bonjour, je souhaite des informations sur vos distributeurs automatiques.") + TAIL
    (ROOT / "boutique.html").write_text(body, encoding="utf-8")


# ─────────────────────────── fiches produit

def build_fiche(p):
    url = f"{SITE}/{p['slug']}.html"
    title = f"{p['nom']} | Boutique Cohesif Agro"
    desc = f"{p['accroche']} Conforme CE, livré en France. Devis tout compris sous 48 h, achat ou leasing."
    lieu = lieu_label(p)
    faq_ld_fiche = [faq_ld([tuple(x) for x in p["faq"]])] if p.get("faq") else []
    produit_ld = {"@type": "Product", "name": p["nom"], "sku": p["ref"], "description": p["accroche"],
                  "image": [f"{SITE}/{g}" for g in p["galerie"]], "category": p.get("typeLd", "Distributeur automatique"),
                  "brand": {"@type": "Brand", "name": "Cohesif Agro"}}
    if p.get("prix"):
        produit_ld["offers"] = {"@type": "Offer", "price": p["prix"], "priceCurrency": "EUR", "url": url,
                                "availability": "https://schema.org/PreOrder",
                                "seller": {"@type": "Organization", "name": "Cohesif Agro"}}
    ld_obj = {"@context": "https://schema.org", "@graph": [
        produit_ld,
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Boutique", "item": f"{SITE}/boutique.html"},
            {"@type": "ListItem", "position": 3, "name": p["nom"], "item": url}]}] + faq_ld_fiche}

    thumbs = "".join(
        f'<button class="bq-thumb{" is-on" if i == 0 else ""}" data-src="{g}" aria-label="Photo {i + 1}"><img src="{g}" alt="" loading="lazy"/></button>'
        for i, g in enumerate(p["galerie"]))
    chiffres = "".join(f'<div><b>{E(v)}</b><span>{E(l)}</span></div>' for v, l in p["chiffres"])
    points = "".join(f'<div class="bq-pt"><h3>{E(t)}</h3><p>{E(d)}</p></div>' for t, d in p["points"])
    specs = "".join(f'<tr><th>{E(k)}</th><td>{E(v)}</td></tr>' for k, v in p["specs"])
    cibles = "".join(f"<li>{E(c)}</li>" for c in p["cible"])
    prevoir = "".join(f"<li>{E(c)}</li>" for c in p["prevoir"])
    wa_txt = f"Bonjour, je souhaite recevoir le prix {'de la' if est_equipement(p) else 'du'} « {p['nom']} »."

    gamme = ""
    if p["categorie"] == "pizza":
        gamme = f"""<section class="bq-sec bq-gamme">
  <div class="bq-in">
    <div class="bq-sec-head">
      <p class="bq-kicker">Toute la gamme pizza</p>
      <h2>6 versions pour s'adapter à votre emplacement</h2>
      <p>Même cuisson en 90 secondes et même capacité de 69 pizzas. Seuls l'habillage et les écrans changent.</p>
    </div>
    <div class="bq-gamme-grid">
      {"".join(f'<figure><img src="{i}" alt="Distributeur de pizzas {E(a)}, {E(b)}" loading="lazy"/><figcaption><b>{E(a)}</b>{E(b)}</figcaption></figure>' for i, a, b in DATA["gammePizza"])}
    </div>
  </div>
</section>"""

    autres = [q for q in PRODUITS if q["slug"] != p["slug"] and est_equipement(q) == est_equipement(p)]
    autres = sorted(autres, key=lambda q: (q["categorie"] != p["categorie"]))[:3]
    alt = f"""<section class="bq-sec bq-alt">
    <div class="bq-in">
      <div class="bq-sec-head"><p class="bq-kicker">Complétez votre offre</p><h2>Ces machines peuvent aussi vous intéresser</h2></div>
      <div class="bq-grid bq-grid-3">{"".join(card(q) for q in autres)}</div>
    </div>
  </section>""" if autres else ""

    faq_fiche = [tuple(x) for x in p["faq"]] if p.get("faq") else [FAQ[0], FAQ[2], FAQ[6], FAQ[4]]
    tags = ('<ul class="bq-ptags">' + "".join(f"<li>{E(x)}</li>" for x in p["tags"]) + "</ul>") if p.get("tags") else ""
    reass = "".join(f"<li>{E(r)}</li>" for r in p.get("reass", [
        "Conforme CE, déclaration UE de conformité fournie",
        "Prix tout compris : transport et dédouanement inclus",
        "Livraison en France en 30 à 45 jours en moyenne",
        "Achat comptant ou leasing avec Cohesif Leasing"]))

    body = head(title, desc, url, p["image"], ld(ld_obj)) + NAV + f"""
<main class="bq-fiche">
  <div class="bq-in">
    <nav class="bq-crumb" aria-label="Fil d'Ariane"><a href="index.html">Accueil</a> › <a href="boutique.html">Boutique</a> › <span>{E(p["court"])}</span></nav>
  </div>
  <section class="bq-in bq-prod">
    <div class="bq-gal">
      <div class="bq-gal-main"><span class="bq-badge">{E(p["badge"])}</span><img src="{p["image"]}" alt="{E(p["nom"])}" id="bqMainImg"/></div>
      <div class="bq-thumbs">{thumbs}</div>
      <p class="bq-gal-note">{E(p.get("galNote", "Habillage personnalisable à vos couleurs."))}</p>
    </div>
    <div class="bq-info">
      <p class="bq-card-cat">{E(CATS[p["categorie"]])} · {lieu} · Réf. {E(p["ref"])}</p>
      <h1>{E(p["nom"])}</h1>
      {tags}
      <p class="bq-acc">{E(p["accroche"])}</p>
      <div class="bq-kpis">{chiffres}</div>
      <div class="bq-buy">
        <div class="bq-px bq-px-lg">{prix_html(p)}</div>
        <a href="#devis" class="bq-btn bq-btn-lg bq-btn-full">Recevoir le prix et le devis</a>
        <a href="{wa_link(wa_txt)}" class="bq-btn bq-btn-lg bq-btn-full bq-btn-wa" target="_blank" rel="noopener">Demander sur WhatsApp</a>
        <ul class="bq-reass">{reass}</ul>
      </div>
    </div>
  </section>

  <section class="bq-sec">
    <div class="bq-in">
      <div class="bq-sec-head"><p class="bq-kicker">Pourquoi cette machine</p><h2>{E(p.get("pointsTitre", "Ce qui la rend rentable"))}</h2></div>
      <div class="bq-pts">{points}</div>
    </div>
  </section>

  <section class="bq-sec bq-where">
    <div class="bq-in bq-where-grid">
      <div class="bq-where-card">
        <h2>Idéale pour</h2>
        <ul class="bq-tags">{cibles}</ul>
      </div>
      <div class="bq-where-card">
        <h2>À prévoir pour l'installer</h2>
        <ul class="bq-checks">{prevoir}</ul>
      </div>
    </div>
  </section>

  <section class="bq-sec">
    <div class="bq-in bq-spec-wrap">
      <div class="bq-sec-head"><p class="bq-kicker">Fiche technique</p><h2>Caractéristiques</h2></div>
      <table class="bq-specs"><tbody>{specs}</tbody></table>
    </div>
  </section>

  {sav_html(p)}

  {gamme}

  <section class="bq-sec bq-faq">
    <div class="bq-in bq-faq-in">
      <div class="bq-sec-head"><p class="bq-kicker">Questions fréquentes</p><h2>Avant de commander</h2></div>
      {faq_html(faq_fiche)}
    </div>
  </section>

  {form_html(p["slug"], "Recevez le prix de cette machine sous 48 h")}

  {alt}
</main>
<div class="bq-sticky" aria-hidden="false">
  <div><b>{E(p["court"])}</b><span>{"Prix sur demande" if not p.get("prix") else euros(p["prix"]) + " HT"}</span></div>
  <a href="#devis" class="bq-btn">Recevoir le prix</a>
</div>
""" + FOOTER + wa_float(wa_txt) + TAIL
    (ROOT / f"{p['slug']}.html").write_text(body, encoding="utf-8")


def update_sitemap():
    path = ROOT / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")
    urls = ["boutique.html"] + [f"{p['slug']}.html" for p in PRODUITS]
    ajout = ""
    for u in urls:
        loc = f"{SITE}/{u}"
        if f"<loc>{loc}</loc>" in xml:
            xml = re.sub(rf"(<loc>{re.escape(loc)}</loc>\s*<lastmod>)[^<]*", rf"\g<1>{DATA['misAJour']}", xml)
            continue
        ajout += (f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{DATA['misAJour']}</lastmod>\n"
                  f"    <changefreq>weekly</changefreq>\n    <priority>{'0.9' if u == 'boutique.html' else '0.8'}</priority>\n  </url>\n")
    xml = xml.replace("</urlset>", ajout + "</urlset>")
    path.write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    build_catalogue()
    for p in PRODUITS:
        build_fiche(p)
    update_sitemap()
    print(f"Boutique générée : boutique.html + {len(PRODUITS)} fiches")
