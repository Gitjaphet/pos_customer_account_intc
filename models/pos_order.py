from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    """Facture regroupée des tickets réglés par un règlement de dette
    (pos_settle_due), avec le moteur de facturation natif du POS
    (_generate_pos_order_invoice, qui accepte plusieurs tickets).

    Comptabilité (23/10/2026) :
    - natif : lignes et taxes des tickets ; pour chaque ticket d'une session
      fermée, l'annulation de la clôture de session
      (_create_misc_reversal_move), qui retire son revenu, ses taxes et sa
      dette « Compte client » ;
    - ici : la facture est lettrée avec ces annulations (« Payé ») ; la
      dette d'origine reste soldée par le règlement (lettrage natif de
      pos_settle_due à la clôture de sa session).
    La facture est TOUJOURS enregistrée en détaillé (un titre par ticket,
    puis ses articles, sans les descriptions de vente). La présentation
    « par ticket » est un format d'impression (account_move.py), jamais une
    autre facture. Tickets de sessions encore ouvertes : refusés.
    """
    _inherit = "pos.order"

    x_grouped_invoice_id = fields.Many2one(
        "account.move",
        string="Facture regroupée",
        copy=False,
        readonly=True,
        help="Sur un règlement de dette : la facture regroupée des tickets qu'il a réglés.",
    )

    # --- Lignes de la facture regroupée ---------------------------------

    def _get_invoice_lines_values(self, line_values, pos_line, move_type):
        vals = super()._get_invoice_lines_values(line_values, pos_line, move_type)
        if self.env.context.get("x_grouped_invoice"):
            if vals.get("display_type") == "line_section":
                # Formule (combo) : sous-section, sous le titre de son ticket.
                vals["display_type"] = "line_subsection"
            elif vals.get("product_id"):
                # Le nom de l'article, comme sur le ticket (sans la description de vente).
                vals["name"] = pos_line.full_product_name or pos_line.product_id.display_name
        return vals

    def _x_ticket_label(self):
        self.ensure_one()
        order_date = fields.Datetime.context_timestamp(self, self.date_order)
        return f"{order_date.strftime('%d/%m/%Y %H:%M')} — Ticket {self.pos_reference or self.name}"

    def _prepare_invoice_lines(self, move_type):
        if not self.env.context.get("x_grouped_invoice"):
            return super()._prepare_invoice_lines(move_type)
        lines = []
        for order in self.sorted("date_order"):
            lines.append((0, None, {"display_type": "line_section", "name": order._x_ticket_label()}))
            lines += super(PosOrder, order)._prepare_invoice_lines(move_type)
        return lines

    # --- Depuis le POS ---------------------------------------------------

    @api.model
    def _x_find_settlement(self, settlement_uuid):
        settlement = self.search([("uuid", "=", settlement_uuid)], limit=1)
        if not settlement:
            raise UserError(_("Règlement introuvable. Réessayez dans un instant."))
        return settlement

    def _x_check_settled_orders(self):
        """`self` : le règlement. Renvoie les tickets à facturer, ou refuse
        avec un message clair."""
        self.ensure_one()
        orders = self.lines.settled_order_id
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
        return orders

    @staticmethod
    def _x_ensure_invoice_pdf(invoice):
        """PDF officiel rangé avec la facture, SANS envoi (méthode
        « manual ») ; la réception l'envoie elle-même avec le bouton Envoyer."""
        if not invoice.invoice_pdf_report_id:
            invoice.with_context(skip_invoice_sync=True)._generate_and_send(sending_methods=["manual"])

    @api.model
    def x_grouped_invoice_info(self, settlement_uuid):
        """Avant la fenêtre d'impression : la facture si elle existe déjà,
        sinon vérifie que la facturation est possible."""
        settlement = self._x_find_settlement(settlement_uuid)
        invoice = settlement.x_grouped_invoice_id
        if invoice:
            self._x_ensure_invoice_pdf(invoice)
            return {
                "invoice_id": invoice.id,
                "invoice_name": invoice.name,
                "partner_name": invoice.partner_id.name,
                "count": len(invoice.pos_order_ids),
            }
        orders = settlement._x_check_settled_orders()
        return {
            "invoice_id": False,
            "invoice_name": "",
            "partner_name": orders.partner_id.commercial_partner_id.name,
            "count": len(orders),
        }

    @api.model
    def x_grouped_invoice_from_settlement(self, settlement_uuid):
        """Crée la facture regroupée des tickets réglés par le règlement
        (ou renvoie la facture existante)."""
        settlement = self._x_find_settlement(settlement_uuid)
        if settlement.x_grouped_invoice_id:
            return self.x_grouped_invoice_info(settlement_uuid)
        orders = settlement._x_check_settled_orders()

        invoice = orders.with_context(
            x_grouped_invoice=True, generate_pdf=False
        )._generate_pos_order_invoice()

        # Lettrage avec les annulations natives des clôtures de session.
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

        # Note : le paiement réel du règlement.
        settle_date = fields.Datetime.context_timestamp(settlement, settlement.date_order)
        # Montant net par mode : la monnaie rendue (ligne d'espèces négative)
        # est déduite ; deux modes donnent « Espèces X, Carte Y ».
        payments = settlement.payment_ids.filtered(lambda p: p.payment_method_id.type != "pay_later")
        net_by_method = {}
        for payment in payments:
            net_by_method[payment.payment_method_id] = net_by_method.get(payment.payment_method_id, 0.0) + payment.amount
        detail = ", ".join(
            f"{method.name} {invoice.currency_id.format(amount)}"
            for method, amount in net_by_method.items()
            if not invoice.currency_id.is_zero(amount)
        )
        note = _(
            "Réglé le %(date)s au restaurant (ticket %(ticket)s) : %(detail)s",
            date=settle_date.strftime("%d/%m/%Y"),
            ticket=settlement.pos_reference or settlement.name,
            detail=detail,
        )
        invoice.narration = f"{invoice.narration or ''}<p>{note}</p>"
        settlement.x_grouped_invoice_id = invoice
        # PDF officiel APRÈS le lettrage et la note (« Payé », mode de paiement).
        self._x_ensure_invoice_pdf(invoice)
        return {"invoice_id": invoice.id, "invoice_name": invoice.name}
