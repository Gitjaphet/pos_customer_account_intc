import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";

/**
 * Contrôle du dû avant un règlement (24/10/2026) : si le dû du POS (tickets
 * + factures) diffère du dû réel du compte client (res.partner
 * .x_pos_due_check), le barman est averti avant que les documents arrivent
 * dans la caisse : « Continuer quand même » ou « Annuler ». Cohérent : rien
 * ne change. Serveur injoignable : pas de blocage (la caisse continue).
 */
patch(PosStore.prototype, {
    async xConfirmDueCheck(partner) {
        const partnerId = partner?.id ?? partner;
        if (!partnerId) {
            return true;
        }
        let check;
        try {
            check = await this.data.call("res.partner", "x_pos_due_check", [
                partnerId,
                this.config.id,
            ]);
        } catch {
            return true;
        }
        if (!check || check.consistent) {
            return true;
        }
        const fmt = (amount) => this.env.utils.formatCurrency(amount);
        return await ask(this.dialog, {
            title: _t("Écart sur le compte de %s", check.partner_name),
            body: _t(
                "Le POS indique %(pos)s dû (tickets %(orders)s, factures %(invoices)s), la comptabilité %(real)s. Écart : %(diff)s. Causes possibles : un paiement ou un remboursement saisi hors caisse, un ticket dont le client a été changé, une avance. Vérifiez avec la comptabilité avant d'encaisser.",
                {
                    pos: fmt(check.orders_due + check.invoices_due),
                    orders: fmt(check.orders_due),
                    invoices: fmt(check.invoices_due),
                    real: fmt(check.real_due),
                    diff: fmt(check.difference),
                }
            ),
            confirmLabel: _t("Continuer quand même"),
            cancelLabel: _t("Annuler"),
        });
    },

    async onClickSettleDue(orderIds, partnerId, commercialPartnerId) {
        if (!(await this.xConfirmDueCheck(partnerId))) {
            return;
        }
        return await super.onClickSettleDue(...arguments);
    },

    async onClickSettleInvoices(invoiceIds, partnerId, commercialPartnerId) {
        if (!(await this.xConfirmDueCheck(partnerId))) {
            return;
        }
        return await super.onClickSettleInvoices(...arguments);
    },
});
