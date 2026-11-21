# POS Customer Account INTC

Module Odoo 19 pour les **clients extérieurs du restaurant** qui consomment à crédit (moyen de paiement « Compte client ») et règlent plus tard.

Le caissier peut leur imprimer un **relevé de tout ce qu'ils doivent**, puis, une fois la dette réglée, leur remettre **une seule facture regroupée** au lieu d'une facture par ticket.

![Odoo 19](https://img.shields.io/badge/Odoo-19.0-714B67)
![Python](https://img.shields.io/badge/Python-3.11-3776AB)
![POS](https://img.shields.io/badge/Odoo-Point%20of%20Sale-875A7B)
![License](https://img.shields.io/badge/License-OPL--1-blue)

## Le problème

En standard, Odoo :
- n'offre pas de relevé clair des tickets restés « en compte » ;
- crée **une facture par ticket** ;
- imprime un ticket de règlement à **−montant / total 0 Ar**, illisible pour le client.

## Ce que fait le module

### Relevé de compte (depuis le POS)
- Nouvelle entrée **« Relevé de compte »** dans le menu du client, juste après « Settle orders ».
- Deux présentations : **détaillée** (chaque article) ou **par ticket** (un total par ticket).
- Impression sur l'**imprimante de tickets (80 mm)** ou en **PDF A4**.
- Le PDF suit le **modèle de document de la société** (le même que les factures).

### Facture regroupée (après règlement)
- Après un règlement de dette, un bouton **« Facture regroupée »** crée une seule facture pour tous les tickets réglés.
- La facture est toujours enregistrée en détail (un titre par ticket, puis ses articles) ; l'impression **par ticket** est un simple format d'impression, jamais une deuxième facture.
- La facture est marquée **« Payé »** automatiquement, avec le **mode de paiement réellement utilisé** affiché.
- La **TVA** est gérée : affichée seulement si les produits en ont (clients avec ou sans TVA).

### Contrôle du dû
- À l'ouverture du relevé, le module compare le dû des tickets au dû réel en comptabilité.
- En cas d'écart (règlement hors caisse, client changé après clôture…), le POS **avertit sans bloquer**.

## Prérequis

| Élément | Détail |
|---|---|
| Odoo | 19.0 |
| Modules requis | `point_of_sale`, `pos_settle_due` |
| Module optionnel | [POS_HOTEL_INTC](https://github.com/Gitjaphet/POS_HOTEL_INTC) : s'il est installé, les paiements « Transfert Chambre » sont exclus du compte client |

`pos_settle_due` fait partie d'Odoo Enterprise. Ce module s'appuie sur son calcul de la dette **sans le modifier**.

## Installation

```bash
# 1. Cloner le module dans le dossier des addons personnalisés
cd /chemin/vers/vos/addons
git clone https://github.com/Gitjaphet/pos_customer_account_intc.git

# 2. Ajouter ce dossier à addons_path dans odoo.conf, puis redémarrer Odoo

# 3. Installer le module (ou depuis Applications, après mise à jour de la liste)
python odoo-bin -c odoo.conf -d <base> -i pos_customer_account_intc --stop-after-init
```

## Utilisation

1. Au POS, le client paie avec le moyen **« Compte client »**.
2. Pour lui montrer ce qu'il doit : menu du client → **Relevé de compte** → choisir détaillé ou par ticket → **Imprimer** (ticket) ou **PDF**.
3. Quand il paie : menu du client → **Settle orders** (natif).
4. Sur l'écran du reçu : **Facture regroupée** → choisir la présentation → la facture est créée et imprimée.

> Les tickets d'une session encore **ouverte** ne peuvent pas être facturés : fermez d'abord la session.

## Structure du dépôt

```
pos_customer_account_intc/
├── models/                    Logique serveur
│   ├── res_partner.py         Données du relevé (une seule source pour ticket et PDF)
│   ├── res_partner_due_check.py  Contrôle du dû (tickets vs comptabilité)
│   ├── pos_order.py           Facture regroupée après règlement
│   ├── account_move.py        Format « par ticket » et mode de paiement sur la facture
│   └── account_statement_report.py  Rapports PDF du relevé
├── report/                    Modèles PDF (relevé, facture par ticket, mode de paiement)
├── static/src/app/            Interface POS (OWL)
│   ├── account_statement/     Fenêtre et ticket du relevé
│   ├── settle_receipt/        Bouton et fenêtre « Facture regroupée »
│   ├── partner_line/          Entrée « Relevé de compte » dans le menu client
│   └── due_check/             Avertissement en cas d'écart
└── .github/workflows/         Déploiement automatique
```

## Déploiement

Chaque `push` sur `main` lance GitHub Actions :
1. **test** : vérification de la syntaxe Python ;
2. **build** : validation du `__manifest__.py` ;
3. **deploy** : sur le serveur, le module est mis à jour sur **toutes les bases** où il est installé. Chaque base est sauvegardée avant ; si une mise à jour échoue, la base et le code sont remis comme avant.

Après une modification de vue ou de champ, faire **Mettre à jour** le module dans Applications.

## Auteur

Développé par **Japhet Valeureux BEZANAKA** pour [INTC Madagascar](https://intc.mg).

Licence : OPL-1.
