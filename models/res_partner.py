from odoo import fields, models


class ResPartner(models.Model):
    """Relevé de compte client du POS : les tickets payés en « Compte client »
    qui ont encore un reste à payer.

    Même définition de la dette que pos_settle_due (champ natif
    pos.order.customer_due_total : montant mis en compte, moins ce qui a
    déjà été réglé pour ce ticket), donc le même total que le POS. Une seule
    source de données pour le ticket 80 mm et le PDF A4.
    Contrôle du dû (24/10/2026) : le résultat de x_pos_due_check est joint,
    pour signaler un écart avec la comptabilité sur le relevé.
    """
    _inherit = "res.partner"

    def _x_statement_orders(self):
        self.ensure_one()
        return self.env["pos.order"].sudo().search([
            ("commercial_partner_id", "=", self.commercial_partner_id.id),
            ("state", "in", ("paid", "done")),
            ("customer_due_total", ">", 0),
        ], order="date_order, id")

    def x_pos_account_statement(self, layout="detailed", config_id=False):
        """Données du relevé. `layout` : « detailed » (les articles de chaque
        ticket) ou « summary » (une ligne par ticket). `config_id` : point de
        vente (devise du contrôle) ; sans lui, devise de la société."""
        self.ensure_one()
        partner = self.commercial_partner_id
        orders = self._x_statement_orders()
        tz_now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        rows = []
        for order in orders:
            order_date = fields.Datetime.context_timestamp(self, order.date_order)
            lines = []
            if layout == "detailed":
                for line in order.lines.filtered(lambda l: not l.combo_parent_id):
                    amount = (
                        sum(line.combo_line_ids.mapped("price_subtotal_incl"))
                        if line.combo_line_ids else line.price_subtotal_incl
                    )
                    lines.append({
                        "name": line.full_product_name or line.product_id.display_name,
                        "qty": line.qty,
                        "amount": amount,
                        "items": line.combo_line_ids.mapped("full_product_name"),
                    })
            rows.append({
                "id": order.id,
                "reference": order.pos_reference or order.name,
                "date": order_date.strftime("%d/%m/%Y %H:%M"),
                "amount_total": order.amount_total,
                "due": order.customer_due_total,
                "lines": lines,
            })
        check = self.env["res.partner"].x_pos_due_check(partner.id, config_id)
        return {
            "partner_name": partner.name,
            "company_name": self.env.company.name,
            "currency_symbol": self.env.company.currency_id.symbol,
            "printed_on": tz_now.strftime("%d/%m/%Y %H:%M"),
            "layout": layout,
            "orders": rows,
            "total_due": sum(r["due"] for r in rows),
            "due_check": {
                "consistent": check["consistent"],
                "real_due": check["real_due"],
                "difference": check["difference"],
            },
        }
