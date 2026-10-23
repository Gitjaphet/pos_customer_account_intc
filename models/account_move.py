from odoo import models


class AccountMove(models.Model):
    """Format d'impression « Facture (par ticket) » : le document de facture
    natif, avec chaque section traitée comme « composition masquée » (même
    principe que le réglage natif collapse_composition des sections) : une
    ligne par section, avec son total. La facture enregistrée ne change pas
    (23/10/2026)."""
    _inherit = "account.move"

    def _get_move_lines_to_report(self):
        lines = super()._get_move_lines_to_report()
        if self.env.context.get("x_ticket_summary"):
            return lines.filtered(lambda l: l.display_type in ("line_section", "line_note"))
        return lines
