from odoo import api, models


class ResPartner(models.Model):
    """Contrôle du dû (24/10/2026) : le dû des tickets du POS
    (customer_due_total, figé à la création du ticket par pos_settle_due)
    peut différer du dû réel, si une partie a été réglée hors caisse ou si
    le client d'un ticket a été changé après la clôture de sa session.

    Règle de cohérence : dû des tickets + dû des factures = dû réel
    (comptabilité + sessions POS encore ouvertes), trois chiffres déjà
    calculés par pos_settle_due. Aucun nouveau calcul : on compare.
    Un écart n'est pas toujours une erreur (un dépôt non utilisé en crée un) :
    le POS avertit, il ne bloque pas.
    """
    _inherit = "res.partner"

    @api.model
    def x_pos_due_check(self, partner_id, config_id):
        partner = self.browse(partner_id).commercial_partner_id
        currency = self.env["pos.config"].browse(config_id).currency_id or self.env.company.currency_id
        orders_due = partner.sudo().pos_orders_amount_due
        invoices_due = partner.sudo().invoices_amount_due
        real_due = partner.get_total_due(config_id)["res.partner"][0]["total_due"]
        difference = real_due - (orders_due + invoices_due)
        return {
            "partner_name": partner.name,
            "orders_due": orders_due,
            "invoices_due": invoices_due,
            "real_due": real_due,
            "difference": difference,
            "consistent": currency.is_zero(difference),
        }
