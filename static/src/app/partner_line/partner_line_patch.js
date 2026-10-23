import { patch } from "@web/core/utils/patch";
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { AccountStatementPopup } from "@pos_customer_account_intc/app/account_statement/account_statement_popup";

patch(PartnerLine.prototype, {
    openAccountStatement() {
        this.env.services.dialog.add(AccountStatementPopup, {
            partner: this.props.partner,
        });
    },
});
