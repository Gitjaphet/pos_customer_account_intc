from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_move_lines_to_report(self):
        """Format d'impression « Facture (par ticket) » : le document de
        facture natif, avec chaque section traitée comme « composition
        masquée » (même principe que le réglage natif collapse_composition
        des sections) : une ligne par section, avec son total. La facture
        enregistrée ne change pas (23/10/2026)."""
        lines = super()._get_move_lines_to_report()
        if self.env.context.get("x_ticket_summary"):
            return lines.filtered(lambda l: l.display_type in ("line_section", "line_note"))
        return lines

    def _compute_payments_widget_reconciled_info(self):
        """Facture regroupée : la ligne de paiement venant de l'annulation
        native des clôtures de session (journal « Point de Vente ») affiche
        le mode réel du règlement (« Espèces », « Espèces, Carte »...), relu
        sur les paiements du ticket de règlement. Affichage seulement : les
        écritures ne changent pas. Le mode est mis dans journal_name (affiché
        par le module hôtel s'il est installé) et dans x_payment_label
        (affiché par ce module sinon, jamais les deux)."""
        super()._compute_payments_widget_reconciled_info()
        hotel_installed = "pos.hotel.folio.charge" in self.env
        Order = self.env["pos.order"].sudo()
        for move in self:
            widget = move.invoice_payments_widget
            if not widget or not widget.get("content") or not move.pos_order_ids:
                continue
            settlement = Order.search([("x_grouped_invoice_id", "=", move.id)], limit=1)
            if not settlement:
                continue
            payments = settlement.payment_ids.filtered(lambda p: p.payment_method_id.type != "pay_later")
            modes = ", ".join(dict.fromkeys(payments.payment_method_id.mapped("name")))
            if not modes:
                continue
            reversal_ids = self.env["account.move"].sudo().search([
                ("reversed_pos_order_id", "in", move.pos_order_ids.ids),
            ]).ids
            content = []
            for vals in widget["content"]:
                if vals.get("move_id") in reversal_ids:
                    vals = dict(
                        vals,
                        journal_name=modes,
                        payment_method_name=modes,
                        x_payment_label="" if hotel_installed else modes,
                    )
                content.append(vals)
            move.invoice_payments_widget = dict(widget, content=content)
