from odoo import fields, models, api


class SalesInvoiceDelivery(models.Model):
    _inherit = 'sale.order'

    check_invoice_status_view = fields.Boolean(string="Invoice Status", compute='_check_invoice_status')

    def _check_invoice_status(self):
        query = """
                select am.state from sale_order as so
                inner join account_move as am on so.name = am.invoice_origin
                where so.id = {}
                """.format(self.id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        for collection in query_result:
            if collection[0] == "posted":
                self.check_invoice_status_view = True
