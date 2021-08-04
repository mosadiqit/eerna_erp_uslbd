from odoo import _, api, fields, models, tools


class HelpdeskService(models.Model):

    _name = 'helpdesk.service'
    _description = 'Helpdesk Service'
    _rec_name = 'user_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one('res.users', string='Engineer', tracking=True)
    start_date_time_from_office = fields.Datetime(string='Start Date & Time From Office')
    activity_start_time = fields.Float(string="Activity Start Time")
    activity_end_time = fields.Float(string='Activity End Time')
    return_date_time_from_office = fields.Datetime(string='Return Date & Time at Office')
    findings = fields.Text(string='Findings')
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Helpdesk Ticket')


class HelpdeskDefectiveSparePart(models.Model):
    _name = 'helpdesk.defective.spare.part'
    _description = 'Helpdesk Defective Spare Part Details'
    _rec_name = 'part_number'

    part_number = fields.Char(string='Part Number')
    part_serial_no = fields.Char(string='Part Serial Number')
    part_description = fields.Text(string='Part Description')
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Helpdesk Ticket')


class HelpdeskReplacementSparePart(models.Model):
    _name = 'helpdesk.replacement.spare.part'
    _description = 'Helpdesk Replacement Spare Part Details'
    _rec_name = 'part_number'

    part_number = fields.Char(string='Part Number')
    part_serial_no = fields.Char(string='Part Serial Number')
    part_description = fields.Text(string='Part Description')
    warranty_event_no = fields.Char(string='Warranty Event No')
    air_way_bill = fields.Float(string='Air Way Bill')
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Helpdesk Ticket')


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'product template for helpdesk'

    helpdesk_ticket_id = fields.One2many('helpdesk.ticket', 'product_template_id', string='Helpdesk Tickets')
