import { patch } from "@web/core/utils/patch";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

/**
 * Tickets lisibles pour les opérations de compte client de pos_settle_due,
 * reconnues par ses méthodes natives :
 * - règlement : tickets réglés (isSettleDueLine) et factures réglées
 *   (isSettleInvoiceLine), montant réglé, paiement, compte client ;
 * - dépôt (isDepositLine) : montant déposé, paiement, compte client.
 * Au lieu des lignes à quantité 0 et du « Total 0 ». La commande et sa
 * comptabilité ne changent pas. Une vente normale garde son ticket natif.
 */
patch(OrderReceipt.prototype, {
    _xRow(line) {
        const date = line.settled_order_id?.date_order?.toFormat?.("dd/MM/yyyy") || "";
        return {
            name: line.full_product_name || line.product_id?.display_name || "",
            date,
            amount: line.price_unit,
        };
    },

    get _xSettleOrderLines() {
        return this.order.lines.filter((line) => line.isSettleDueLine?.());
    },

    get _xSettleInvoiceLines() {
        return this.order.lines.filter((line) => line.isSettleInvoiceLine?.());
    },

    get _xDepositLines() {
        return this.order.lines.filter((line) => line.isDepositLine?.());
    },

    get isSettleReceipt() {
        return this._xSettleOrderLines.length > 0 || this._xSettleInvoiceLines.length > 0;
    },

    get isDepositReceipt() {
        return !this.isSettleReceipt && this._xDepositLines.length > 0;
    },

    /** Ticket remplacé par un bloc lisible (règlement ou dépôt). */
    get isAccountReceipt() {
        return this.isSettleReceipt || this.isDepositReceipt;
    },

    get settledOrderRows() {
        return this._xSettleOrderLines.map((line) => this._xRow(line));
    },

    get settledInvoiceRows() {
        return this._xSettleInvoiceLines.map((line) => this._xRow(line));
    },

    get settledTotal() {
        return [...this._xSettleOrderLines, ...this._xSettleInvoiceLines].reduce(
            (sum, line) => sum + line.price_unit,
            0
        );
    },

    get depositTotal() {
        return this._xDepositLines.reduce((sum, line) => sum + line.price_unit, 0);
    },

    get realPaymentLines() {
        return this.paymentLines.filter((p) => p.payment_method_id?.type !== "pay_later");
    },

    get accountPaymentLines() {
        return this.paymentLines.filter((p) => p.payment_method_id?.type === "pay_later");
    },
});
