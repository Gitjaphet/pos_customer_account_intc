import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { GroupedInvoiceLayoutPopup } from "@pos_customer_account_intc/app/settle_receipt/grouped_invoice_layout_popup";

/**
 * Facture regroupée d'un règlement : vérification serveur, choix de la
 * présentation (à chaque impression), création de la facture la première
 * fois, puis le PDF : détaillé = PDF officiel (service account_move),
 * par ticket = format « Facture (par ticket) » (même facture).
 * Renvoie true si un PDF a été produit.
 */
export async function openGroupedInvoice({ pos, dialog, invoiceService, report, uuid }) {
    try {
        const info = await pos.data.call("pos.order", "x_grouped_invoice_info", [uuid]);
        const layout = await makeAwaitable(dialog, GroupedInvoiceLayoutPopup, {
            partnerName: info.partner_name,
            count: info.count,
            invoiceName: info.invoice_name || "",
        });
        if (!layout) {
            return false;
        }
        let invoiceId = info.invoice_id;
        if (!invoiceId) {
            const result = await pos.data.call(
                "pos.order",
                "x_grouped_invoice_from_settlement",
                [uuid]
            );
            invoiceId = result.invoice_id;
        }
        if (layout === "summary") {
            await report.doAction("pos_customer_account_intc.action_report_invoice_by_ticket", [
                invoiceId,
            ]);
        } else {
            await invoiceService.downloadPdf(invoiceId);
        }
        return true;
    } catch (error) {
        dialog.add(AlertDialog, {
            title: _t("Facture regroupée impossible"),
            body: error?.data?.message || error?.message || _t("Erreur inconnue."),
        });
        return false;
    }
}
