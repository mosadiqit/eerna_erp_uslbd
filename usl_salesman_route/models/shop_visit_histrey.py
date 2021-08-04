from odoo import api, fields, models
import datetime


class ShopVisitingHistory(models.Model):
    _name = 'salesman.shop_visiting_history'
    _description = 'ShopVisitingHistory'

    date_time = fields.Datetime(string='Date Time', default=datetime.datetime.now())
    store_id = fields.Many2one('res.partner', string='Store Id')
    store = fields.Char('Store', related='store_id.shop_name')
    visit_start = fields.Char(string="Visit Start")
    end_date = fields.Char(string="Visit Start",)
    time_durations = fields.Char(string='Visit Durations')
    visit_status = fields.Char(string='status')
    is_ordered = fields.Boolean(string='Is ordered')
    has_task = fields.Boolean(string='Has Task')
    is_task_completed = fields.Boolean(string='is_task_completed')
    is_delivery_completed = fields.Boolean(string='is delivery completed')
    reason = fields.Text(string='reason')
    remarks = fields.Text(string='remarks')
    user_id = fields.Many2one('res.users', string='user_id')
