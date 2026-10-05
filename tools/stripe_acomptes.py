#!/usr/bin/env python3
"""Crée les liens de paiement Stripe des acomptes (distributeurs avec un prix) et les branche sur le site.

    STRIPE_API_KEY=rk_live_... python3 tools/stripe_acomptes.py

Pour chaque machine avec un prix et sans "stripeAcompte" : crée un produit, un prix
(acompte TTC calculé comme sur le site) et un lien de paiement Stripe, puis
enregistre le lien dans data/boutique.json et régénère la boutique.
Relancer le script ne recrée pas les liens déjà enregistrés. Si un prix change,
remettre "stripeAcompte" à null puis relancer (et désactiver l'ancien lien dans Stripe).

Clé conseillée : clé restreinte Stripe avec les droits en écriture sur
Products, Prices et Payment Links (jamais la clé secrète sk_ complète dans le dépôt).
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "boutique.json"
API = "https://api.stripe.com/v1/"
CGV = "https://www.cohesifagro.fr/cgv.html#vente-en-ligne"
PIED = "Groupe Cohesif — Cohesif Agro · 200 rue de la Croix Nivert, 75015 Paris · SIRET 889 287 462 00036"


def stripe(path, params):
    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        sys.exit("STRIPE_API_KEY manquante : ajoutez-la dans les variables d'environnement.")
    req = urllib.request.Request(API + path, data=urllib.parse.urlencode(params).encode(),
                                 headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(json.load(e).get("error", {}).get("message", str(e))) from None


def montant(c):
    return f"{c / 100:,.2f}".replace(",", " ").replace(".", ",") + " €"


def lien_acompte(p, centimes, resa):
    ref = p["ref"]
    ht = round(centimes / (1 + resa["tva"] / 100))
    produit = stripe("products", {"name": f"Acompte {resa['acomptePct']} % — {p['nom']} {ref}",
                                  "description": "Acompte de commande. Le solde est réglé par virement avant l'expédition. Livraison en France incluse.",
                                  "images[0]": f"https://www.cohesifagro.fr/img/boutique/stripe/{ref.lower()}.jpg",
                                  "metadata[marque]": "Cohesif Agro", "metadata[ref]": ref})
    prix = stripe("prices", {"product": produit["id"], "currency": "eur",
                             "unit_amount": centimes, "metadata[cohesif_ref]": ref})
    return stripe("payment_links", {
        "line_items[0][price]": prix["id"], "line_items[0][quantity]": 1,
        "billing_address_collection": "required",
        "phone_number_collection[enabled]": "true",
        "tax_id_collection[enabled]": "true",
        "shipping_address_collection[allowed_countries][0]": "FR",
        "metadata[marque]": "Cohesif Agro", "metadata[ref]": ref,
        "custom_text[submit][message]": f"Acompte de commande ({resa['acomptePct']} %). Le solde est réglé par virement avant "
                                        f"l'expédition, livraison en France incluse. En payant, vous acceptez nos CGV : {CGV}",
        "custom_text[shipping_address][message]": "Adresse d'installation de la machine (commerce, site ou entrepôt).",
        "after_completion[type]": "hosted_confirmation",
        "after_completion[hosted_confirmation][custom_message]":
            f"Merci ! Votre {p['nom'][0].lower() + p['nom'][1:]} est commandé. Un conseiller Cohesif Agro vous appelle sous 48 h "
            "pour confirmer la commande (options de paiement, habillage) et la date de livraison. Une question : 07 56 85 57 27.",
        "invoice_creation[enabled]": "true",
        "invoice_creation[invoice_data][description]": f"Acompte {resa['acomptePct']} % — {p['nom']} {ref}",
        "invoice_creation[invoice_data][footer]": PIED,
        "invoice_creation[invoice_data][custom_fields][0][name]": "Montant HT",
        "invoice_creation[invoice_data][custom_fields][0][value]": montant(ht),
        "invoice_creation[invoice_data][custom_fields][1][name]": f"TVA {resa['tva']} %",
        "invoice_creation[invoice_data][custom_fields][1][value]": montant(centimes - ht),
        "invoice_creation[invoice_data][custom_fields][2][name]": "Total TTC",
        "invoice_creation[invoice_data][custom_fields][2][value]": montant(centimes),
    })


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    resa = data["reservation"]
    crees = 0
    for p in data["produits"]:
        if not p.get("prix") or p.get("stripeAcompte"):
            continue
        centimes = round(p["prix"] * resa["acomptePct"] / 100 * (1 + resa["tva"] / 100) * 100)
        print(f"{p['ref']} : acompte {centimes / 100:.2f} € TTC…")
        p["stripeAcompte"] = lien_acompte(p, centimes, resa)["url"]
        print(f"  → {p['stripeAcompte']}")
        crees += 1
        # enregistrement après chaque lien : pas de doublon si le script s'arrête en route
        DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not crees:
        print("Aucun lien à créer : toutes les machines avec un prix ont déjà leur lien d'acompte.")
        return
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_boutique.py")], check=True)


if __name__ == "__main__":
    main()
