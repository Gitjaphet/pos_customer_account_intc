from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    """Facture regroupée des tickets réglés par un règlement de dette
    (pos_settle_due), en réutilisant le moteur de facturation natif du POS
    (_generate_pos_order_invoice, qui accepte plusieurs tickets).

    Comptabilité (23/10/2026) :
    - natif : les lignes et taxes des tickets ; pour chaque ticket d'une
      session fermée, l'écriture d'annulation de la clôture de session
      (_create_misc_reversal_move), qui retire son revenu, ses taxes et sa
      dette « Compte client » ;
    - ici : la facture est lettrée avec ces annulations (elle passe à
      « Payé ») ; la dette d'origine reste soldée par le règlement
      (lettrage natif de pos_settle_due à la clôture de sa session).
    Tickets de sessions encore ouvertes : refusés (autre chemin natif).
    """
    _inherit = "pos.order"

    x_grouped_invoice_id = fields.Many2one(
        "account.move",
        string="Facture regroupée",
        copy=False,
        readonly=True,
        help="Sur un règlement de dette : la facture regroupée des tickets qu'il a réglés.",
    )

    def _prepare_invoice_lines(self, move_type):
        """Facture regroupée : un titre de section par ticket, puis ses
        lignes natives (taxes, remises, notes)."""
        if not self.env.context.get("x_grouped_invoice") or len(self) == 1:
            return super()._prepare_invoice_lines(move_type)
        lines = []
        for order in self.sorted("date_order"):
            order_date = fields.Datetime.context_timestamp(order, order.date_order)
            lines.append((0, None, {
                "display_type": "line_section",
                "name": f"{order_date.strftime('%d/%m/%Y %H:%M')} — Ticket {order.pos_reference or order.name}",
            }))
            lines += super(PosOrder, order)._prepare_invoice_lines(move_type)
        return lines

    @api.model
    def x_grouped_invoice_from_settlement(self, settlement_uuid):
        """Depuis le POS : facture regroupée des tickets réglés par le
        règlement `settlement_uuid`. Renvoie la facture (existante si déjà
        faite)."""
        settlement = self.search([("uuid", "=", settlement_uuid)], limit=1)
        if not settlement:
            raise UserError(_("Règlement introuvable. Réessayez dans un instant."))
        if settlement.x_grouped_invoice_id:
            invoice = settlement.x_grouped_invoice_id
            return {"invoice_id": invoice.id, "name": invoice.name}

        orders = settlement.lines.settled_order_id
        if not orders:
            raise UserError(_("Ce ticket ne règle aucun ticket du compte client."))
        if orders.filtered("account_move"):
            raise UserError(_(
                "Certains de ces tickets sont déjà facturés : %s.",
                ", ".join(orders.filtered("account_move").mapped("pos_reference")),
            ))
        if len(orders.partner_id.commercial_partner_id) > 1 or len(orders.config_id) > 1 \
                or len(orders.fiscal_position_id) > 1:
            raise UserError(_(
                "Ces tickets ne peuvent pas aller sur une même facture "
                "(clients, points de vente ou positions fiscales différents)."
            ))
        open_sessions = orders.session_id.filtered(lambda s: s.state != "closed")
        if open_sessions:
            raise UserError(_(
                "Ces tickets seront facturables après la clôture de la caisse "
                "(session %s encore ouverte).",
                ", ".join(open_sessions.mapped("name")),
            ))

        invoice = orders.with_context(
            x_grouped_invoice=True, generate_pdf=False
        )._generate_pos_order_invoice()

        # Lettrage de la facture avec les annulations natives des clôtures de
        # session : la facture est réglée (sa dette a été soldée par le
        # règlement).
        receivable = invoice.commercial_partner_id.property_account_receivable_id
        reversal_lines = self.env["account.move"].search([
            ("reversed_pos_order_id", "in", orders.ids),
        ]).line_ids.filtered(
            lambda l: l.account_id == receivable and l.credit > 0 and not l.reconciled
        )
        invoice_lines = invoice.line_ids.filtered(
            lambda l: l.account_id == receivable and not l.reconciled
        )
        if reversal_lines and invoice_lines:
            (reversal_lines | invoice_lines).reconcile()

        # Note : le paiement réel (espèces, carte...) du règlement.
        settle_date = fields.Datetime.context_timestamp(settlement, settlement.date_order)
        payments = settlement.payment_ids.filtered(lambda p: p.payment_method_id.type != "pay_later")
        detail = ", ".join(
            f"{p.payment_method_id.name} {invoice.currency_id.format(p.amount)}" for p in payments
        )
        note = _(
            "Réglé le %(date)s au restaurant (ticket %(ticket)s) : %(detail)s",
            date=settle_date.strftime("%d/%m/%Y"),
            ticket=settlement.pos_reference or settlement.name,
            detail=detail,
        )
        invoice.narration = f"{invoice.narration or ''}<p>{note}</p>"
        settlement.x_grouped_invoice_id = invoice
        return {"invoice_id": invoice.id, "name": invoice.name}
