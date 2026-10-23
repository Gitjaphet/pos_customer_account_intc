from odoo import api, models


class ReportAccountStatement(models.AbstractModel):
    """PDF du relevé de compte client : mêmes données que le ticket du POS
    (res.partner.x_pos_account_statement). `data['layout']` : « detailed »
    (par défaut, aussi depuis le menu Imprimer) ou « summary »."""
    _name = "report.pos_customer_account_intc.report_account_statement"
    _description = "Relevé de compte client (POS)"

    @api.model
    def _get_report_values(self, docids, data=None):
        layout = (data or {}).get("layout") or "detailed"
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
