from odoo import api, models


class ResPartner(models.Model):
    """Contrôle du dû (24/10/2026) : le dû des tickets du POS
    (customer_due_total, figé à la création du ticket par pos_settle_due)
    peut différer du dû réel, si une partie a été réglée hors caisse ou si
    le client d'un ticket a été changé après la clôture de sa session.

    Règle de cohérence : dû des tickets + dû des factures = dû réel du
    « Compte client ».
    Dû réel = écritures non lettrées sur LE compte client du contact
    (property_account_receivable_id, celui de « Compte client ») + paiements
    « Compte client » des sessions encore ouvertes (dettes, règlements,
    dépôts du jour). Les comptes d'autres usages (créances de chambre d'un
    hôtel : 411200, 411300) sont d'autres comptes, donc exclus ; les
    paiements « Transfert Chambre » (is_room_charge, champ du module hôtel
    s'il est installé) aussi. Un écart n'est pas toujours une erreur : le POS
    avertit, il ne bloque pas.
    """
    _inherit = "res.partner"

    @api.model
    def _x_is_room_charge_method(self, method):
        """Moyen de paiement « Transfert Chambre » du module hôtel, s'il est
        installé (sans dépendre de lui)."""
        return "is_room_charge" in method._fields and bool(method.is_room_charge)

    @api.model
    def x_pos_due_check(self, partner_id, config_id):
        partner = self.browse(partner_id).commercial_partner_id.sudo()
        config = self.env["pos.config"].browse(config_id)
        currency = config.currency_id or self.env.company.currency_id
        receivable = partner.property_account_receivable_id

        # 1. Comptabilité : le compte client du contact, non lettré.
        lines = self.env["account.move.line"].sudo().search([
            ("partner_id", "child_of", partner.id),
            ("account_id", "=", receivable.id),
            ("parent_state", "=", "posted"),
            ("reconciled", "=", False),
        ])
        posted_due = sum(lines.mapped("amount_residual"))

        # 2. Sessions ouvertes : paiements « Compte client » pas encore en
        #    comptabilité (hors Transfert Chambre).
        open_orders = self.env["pos.order"].sudo().search([
            ("commercial_partner_id", "=", partner.id),
            ("state", "=", "paid"),
            ("session_id.state", "!=", "closed"),
        ])
        pending = sum(
            p.amount for p in open_orders.payment_ids
            if p.payment_method_id.type == "pay_later"
            and not self._x_is_room_charge_method(p.payment_method_id)
        )

        orders_due = partner.pos_orders_amount_due
        invoices_due = partner.invoices_amount_due
        real_due = posted_due + pending
        difference = real_due - (orders_due + invoices_due)
        return {
            "partner_name": partner.name,
            "orders_due": orders_due,
            "invoices_due": invoices_due,
            "posted_due": posted_due,
            "pending": pending,
            "real_due": real_due,
            "difference": difference,
            "consistent": currency.is_zero(difference),
        }
