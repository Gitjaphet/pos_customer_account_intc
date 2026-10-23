import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

/** Impression de la facture regroupée : détaillée ou par ticket. */
export class GroupedInvoiceLayoutPopup extends Component {
    static template = "pos_customer_account_intc.GroupedInvoiceLayoutPopup";
    static components = { Dialog };
    static props = {
        partnerName: String,
        count: Number,
        invoiceName: { type: String, optional: true },
        getPayload: Function,
        close: Function,
    };

    setup() {
        this.state = useState({ layout: "detailed" });
    }

    confirm() {
        this.props.getPayload(this.state.layout);
        this.props.close();
    }
}
