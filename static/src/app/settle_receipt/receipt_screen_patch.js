import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";

/**
 * Écran du ticket : sur un règlement de dette, bouton « Facture regroupée »
 * (pos.order.x_grouped_invoice_from_settlement), puis téléchargement du PDF
 * comme les factures natives du POS (service account_move). Recliquer
 * renvoie la même facture.
 */
patch(ReceiptScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.xInvoiceService = useService("account_move");
        this.xGrouped = useState({ busy: false });
    },

    get xIsSettlement() {
        return (this.currentOrder?.lines || []).some(
            (line) => line.isSettleDueLine?.() || line.isSettleInvoiceLine?.()
        );
    },

    async xGroupedInvoice() {
        this.xGrouped.busy = true;
        try {
            const result = await this.pos.data.call(
                "pos.order",
                "x_grouped_invoice_from_settlement",
                [this.currentOrder.uuid]
            );
            await this.xInvoiceService.downloadPdf(result.invoice_id);
        } catch (error) {
            this.env.services.dialog.add(AlertDialog, {
                title: _t("Facture regroupée impossible"),
                body: error?.data?.message || error?.message || _t("Erreur inconnue."),
            });
        } finally {
            this.xGrouped.busy = false;
        }
    },
});
