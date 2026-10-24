{
    "name": "INTC POS — Compte client : relevé et facture regroupée",
    "version": "19.0.1.0.22",
    "category": "Sales/Point of Sale",
    "summary": "Relevé des tickets en compte client (ticket et PDF), facture regroupée après règlement",
    "description": """
Clients extérieurs du restaurant qui consomment à crédit (moyen de paiement
« Compte client ») et règlent plus tard.

* Relevé de tout ce qu'ils doivent, détaillé ou par ticket, sur l'imprimante de tickets ou en PDF.
* À venir : ticket de règlement lisible et facture regroupée après paiement.

S'appuie sur pos_settle_due (calcul natif de la dette), sans le modifier.
""",
    "author": "INTC Madagascar",
    "website": "https://intc.mg",
    "license": "OPL-1",
    "depends": ["point_of_sale", "pos_settle_due"],
    "data": [
        "report/account_statement_report.xml",
        "report/invoice_by_ticket_report.xml",
        "report/invoice_payment_mode_report.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_customer_account_intc/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
