# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    branch_id = fields.Many2one('res.branch', 'Branch')

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            ,line.branch_id
        """
        return select_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """
            ,move.branch_id
        """
        return group_by_str

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select()
        select_str += """
            ,move.branch_id
        """
        return select_str
