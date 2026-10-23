import { Component, onWillStart, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { AccountStatementReceipt } from "@pos_customer_account_intc/app/account_statement/account_statement_receipt";

/**
 * Relevé de compte d'un client : détaillé ou par ticket, imprimé sur le
 * ticket (80 mm) ou en PDF. Mêmes données serveur pour les deux
 * (res.partner.x_pos_account_statement).
 */
export class AccountStatementPopup extends Component {
    static template = "pos_customer_account_intc.AccountStatementPopup";
    static components = { Dialog };
    static props = {
        partner: Object,
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.report = useService("report");
        this.state = useState({ layout: "detailed", summary: null, busy: false });
        onWillStart(() => this.loadSummary());
    }

    async fetchStatement(layout) {
        return await this.pos.data.call("res.partner", "x_pos_account_statement", [
            [this.props.partner.id],
            layout,
        ]);
    }

    async loadSummary() {
        this.state.summary = await this.fetchStatement("summary");
    }

    async printTicket() {
        this.state.busy = true;
        try {
            const data = await this.fetchStatement(this.state.layout);
            // Mêmes options d'impression que l'Addition (pos.printReceipt) :
            // imprimante reliée au POS, sinon le navigateur (choix de
            // l'imprimante), selon la configuration du point de vente.
            await this.pos.printer.print(
                AccountStatementReceipt,
                { data, company: this.pos.company },
                this.pos.printOptions
            );
        } finally {
            this.state.busy = false;
        }
    }

    async printPdf() {
        const reportXmlId =
            this.state.layout === "summary"
                ? "pos_customer_account_intc.action_report_account_statement_summary"
                : "pos_customer_account_intc.action_report_account_statement";
        await this.report.doAction(reportXmlId, [this.props.partner.id]);
    }
}
