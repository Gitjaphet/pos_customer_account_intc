import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { InvoiceButton } from "@point_of_sale/app/screens/ticket_screen/invoice_button/invoice_button";
import { openGroupedInvoice } from "@pos_customer_account_intc/app/settle_receipt/grouped_invoice";

/**
 * Écran des commandes, bouton Facture :
 * - règlement de TICKETS (isSettleDueLine) : « Facture regroupée » ;
 * - règlement de facture seul ou dépôt : bouton masqué (rien à facturer ;
 *   le serveur refuse aussi, action_pos_order_invoice) ;
 * - vente normale : natif inchangé.
 */
patch(InvoiceButton.prototype, {
    setup() {
        super.setup(...arguments);
        this.xReport = useService("report");
    },

    get xIsSettlement() {
        return (this.props.order?.lines || []).some((line) => line.isSettleDueLine?.());
    },

    get xHideInvoice() {
        const lines = this.props.order?.lines || [];
        return (
            !this.xIsSettlement &&
            !this.isAlreadyInvoiced &&
            lines.some((line) => line.isSettleInvoiceLine?.() || line.isDepositLine?.())
        );
    },

    get commandName() {
        return this.xIsSettlement ? _t("Facture regroupée") : super.commandName;
    },

    async _invoiceOrder() {
        if (!this.xIsSettlement) {
            return await super._invoiceOrder(...arguments);
        }
        const order = this.props.order;
        const done = await openGroupedInvoice({
            pos: this.pos,
            dialog: this.dialog,
            invoiceService: this.invoiceService,
            report: this.xReport,
            uuid: order.uuid,
        });
        if (done) {
            this.props.onInvoiceOrder(order.id);
        }
    },
});
