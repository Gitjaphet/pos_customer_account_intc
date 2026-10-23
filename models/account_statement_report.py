from odoo import api, models


class ReportAccountStatement(models.AbstractModel):
    """PDF du relevé de compte client : mêmes données que le ticket du POS
    (res.partner.x_pos_account_statement).

    Deux rapports, car le service de rapport du POS ne transmet que les
    identifiants : celui-ci (détaillé) et sa variante « par ticket »
    ci-dessous. `data['layout']` reste possible depuis le code."""
    _name = "report.pos_customer_account_intc.report_account_statement"
    _description = "Relevé de compte client (POS)"

    _x_layout = "detailed"

    @api.model
    def _get_report_values(self, docids, data=None):
        layout = (data or {}).get("layout") or self._x_layout
        partners = self.env["res.partner"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "res.partner",
            "docs": partners,
            "company": self.env.company,
            "currency": self.env.company.currency_id,
            "statements": [
                {"partner": partner, "data": partner.x_pos_account_statement(layout)}
                for partner in partners
            ],
        }


class ReportAccountStatementSummary(models.AbstractModel):
    _name = "report.pos_customer_account_intc.report_account_statement_summary"
    _inherit = "report.pos_customer_account_intc.report_account_statement"
    _description = "Relevé de compte client (POS, par ticket)"

    _x_layout = "summary"
