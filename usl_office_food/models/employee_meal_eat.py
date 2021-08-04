from datetime import datetime

from odoo import fields, models, api,_


class EmployeeMealEat(models.Model):
    _name = 'employee.meal.eat'
    _description = 'This table store all meal eat '

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string='Employee')
    eat_date = fields.Date(string='Eat', default=datetime.today())
    eat_time = fields.Datetime(string='Time', default=lambda self: fields.datetime.now())
    
    def create(self, vals_list):
        if vals_list.get('name', _('New')) == _('New'):
            vals_list['name'] = self.env['ir.sequence'].next_by_code('employee.meal.eat') or _('New')
        return super(EmployeeMealEat, self).create(vals_list)
        

