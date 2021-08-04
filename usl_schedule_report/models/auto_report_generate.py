from odoo import api, fields, models


class AutoReportGeneration(models.Model):
    _name = 'auto.report'
    # _rec_name = 'name'
    _description = 'This module will be used to generate report monthly and email them to the selected user'

    report_heading = fields.Char(string="Heading")
    report_list = fields.One2many('auto.report.line','report_id',string="Report List")

    def create_auto_report(self):
        account = self.env['account.move'].search([('id','=',23357)])
        menu_item = self.env['ir.ui.menu'].search([('')])
        return self.env.ref('account.account_invoices').report_action(account)

class AutoReportLine(models.Model):
    _name = 'auto.report.line'

    report_id = fields.Many2one('auto.report',string="Report ID")
    report_list = fields.Selection([
        ('balance_sheet','Balance Sheet'),
        ('profit_loss','Profit & Loss'),
        ('trial_balance','Trial Balance')
    ],string="Report List")
    branch_id = fields.Many2many('res.branch','branch_report_rel')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    status = fields.Selection([
        ('active','Active'),
        ('inactive','In Active')
    ],string="Status")



