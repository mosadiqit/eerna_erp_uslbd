import datetime

from odoo import fields, models, api


class HolidayMonthDate(models.Model):
    _name = 'holiday.month.date'
    _description = 'this table store all holiday of a year'

    name = fields.Char(string='Name')
    date = fields.Date(string='Date')
    type_of_holiday = fields.Char(string='Holiday Type')
    holiday_description = fields.Text(string='description')

    def check_is_holiday(self, day, month, year):
        date = str(day) + '/' + str(month) + '/' + str(year)
        date = datetime.datetime.strptime(date, "%d/%M/%Y")
        print('date : ',date)
        holiday = self.env['holiday.month.date'].sudo().search([('date', '=', date)])
        if holiday:
            return True
        return False
