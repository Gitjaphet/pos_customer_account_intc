import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { openGroupedInvoice } from "@pos_customer_account_intc/app/settle_receipt/grouped_invoice";

/**
 * Écran du ticket : « Facture regroupée » seulement si le règlement règle
 * des TICKETS (isSettleDueLine). Facture réglée ou dépôt : rien à facturer.
 */
patch(ReceiptScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.xInvoiceService = useService("account_move");
        this.xReport = useService("report");
        this.xGrouped = useState({ busy: false });
    },

    get xIsSettlement() {
        return (this.currentOrder?.lines || []).some((line) => line.isSettleDueLine?.());
    },

    async xGroupedInvoice() {
        this.xGrouped.busy = true;
        try {
            await openGroupedInvoice({
                pos: this.pos,
                dialog: this.env.services.dialog,
                invoiceService: this.xInvoiceService,
                report: this.xReport,
                uuid: this.currentOrder.uuid,
            });
        } finally {
            this.xGrouped.busy = false;
        }
    },
});
