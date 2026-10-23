import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

/** Choix de la présentation de la facture regroupée (une seule fois). */
export class GroupedInvoiceLayoutPopup extends Component {
    static template = "pos_customer_account_intc.GroupedInvoiceLayoutPopup";
    static components = { Dialog };
    static props = {
        partnerName: String,
        count: Number,
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
