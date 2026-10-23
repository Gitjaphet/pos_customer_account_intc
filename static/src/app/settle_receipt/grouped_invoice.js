import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { GroupedInvoiceLayoutPopup } from "@pos_customer_account_intc/app/settle_receipt/grouped_invoice_layout_popup";

/**
 * Facture regroupée d'un règlement : la facture existante, sinon (après
 * vérification serveur) le choix de la présentation puis la création ;
 * enfin le PDF, comme les factures natives (service account_move).
 * Renvoie true si une facture a été téléchargée.
 */
export async function openGroupedInvoice({ pos, dialog, invoiceService, uuid }) {
    try {
        const info = await pos.data.call("pos.order", "x_grouped_invoice_info", [uuid]);
        let invoiceId = info.invoice_id;
        if (!invoiceId) {
            const layout = await makeAwaitable(dialog, GroupedInvoiceLayoutPopup, {
                partnerName: info.partner_name,
                count: info.count,
            });
            if (!layout) {
                return false;
            }
            const result = await pos.data.call(
                "pos.order",
                "x_grouped_invoice_from_settlement",
                [uuid, layout]
            );
            invoiceId = result.invoice_id;
        }
        await invoiceService.downloadPdf(invoiceId);
        return true;
    } catch (error) {
        dialog.add(AlertDialog, {
            title: _t("Facture regroupée impossible"),
            body: error?.data?.message || error?.message || _t("Erreur inconnue."),
        });
        return false;
    }
}
