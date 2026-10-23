import { patch } from "@web/core/utils/patch";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

/**
 * Ticket de règlement de dette (pos_settle_due) lisible : au lieu des lignes
 * à quantité 0 et du « Total 0 », la liste des tickets réglés, le montant
 * réglé, le paiement et la dette retirée du compte client. La commande et
 * sa comptabilité (pos_settle_due) ne changent pas. Une vente normale garde
 * son ticket natif.
 */
patch(OrderReceipt.prototype, {
    _xSettleLines() {
        return this.order.lines.filter(
            (line) => line.isSettleDueLine?.() || line.isSettleInvoiceLine?.()
        );
    },

    get isSettleReceipt() {
        return this._xSettleLines().length > 0;
    },

    get settledRows() {
        return this._xSettleLines().map((line) => {
            const settled = line.settled_order_id;
            const date = settled?.date_order?.toFormat?.("dd/MM/yyyy") || "";
            return {
                name: line.full_product_name || line.product_id?.display_name || "",
                date,
                amount: line.price_unit,
            };
        });
    },

    get settledTotal() {
        return this._xSettleLines().reduce((sum, line) => sum + line.price_unit, 0);
    },

    get realPaymentLines() {
        return this.paymentLines.filter((p) => p.payment_method_id?.type !== "pay_later");
    },

    get accountPaymentLines() {
        return this.paymentLines.filter((p) => p.payment_method_id?.type === "pay_later");
    },
});
