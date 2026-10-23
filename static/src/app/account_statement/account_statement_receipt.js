import { Component } from "@odoo/owl";

/**
 * Relevé de compte sur l'imprimante de tickets (80 mm), dans le style des
 * reçus du POS (pos-receipt). En-tête propre : l'en-tête natif des reçus
 * (ReceiptHeader) exige une commande, qu'un relevé n'a pas.
 */
export class AccountStatementReceipt extends Component {
    static template = "pos_customer_account_intc.AccountStatementReceipt";
    static props = {
        data: Object,
        company: Object,
        logoUrl: { type: String, optional: true },
    };
}
