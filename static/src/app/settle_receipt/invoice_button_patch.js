import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { InvoiceButton } from "@point_of_sale/app/screens/ticket_screen/invoice_button/invoice_button";

/**
 * Écran des commandes, bouton Facture : sur un règlement de dette, la
 * facture regroupée des tickets réglés (créée la première fois, la même
 * ensuite), au lieu de facturer le règlement lui-même (commande à 0).
 * Tous les autres tickets : comportement natif inchangé.
 */
patch(InvoiceButton.prototype, {
    get xIsSettlement() {
        return (this.props.order?.lines || []).some(
            (line) => line.isSettleDueLine?.() || line.isSettleInvoiceLine?.()
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
        try {
            const result = await this.pos.data.call(
                "pos.order",
                "x_grouped_invoice_from_settlement",
                [order.uuid]
            );
            await this.invoiceService.downloadPdf(result.invoice_id);
            this.props.onInvoiceOrder(order.id);
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("Facture regroupée impossible"),
                body: error?.data?.message || error?.message || _t("Erreur inconnue."),
            });
        }
    },
});
