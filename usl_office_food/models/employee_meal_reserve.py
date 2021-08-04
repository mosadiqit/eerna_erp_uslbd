from odoo import fields, models, api, _, exceptions
from datetime import date, timedelta, datetime


def days_current_month():
    m = datetime.now().month
    y = datetime.now().year
    ndays = (date(y, m + 1, 1) - date(y, m, 1)).days
    d1 = date(y, m, 1)
    d2 = date(y, m, ndays)
    delta = d2 - d1

    return [(d1 + timedelta(days=i)) for i in range(delta.days + 1)]


class EmployeeMealReserve(models.Model):
    _name = 'employee.meal.reserve'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'This table is store all meal reserve date . Also it can store guest  '

    # @api.onchange('employee_id')
    def _get_default_employee(self):
        active_user = self.env.user.id
        get_active_employee = self.env['hr.employee'].sudo().search([('user_id', '=', active_user)], limit=1)
        print('employee id : ', get_active_employee)
        if get_active_employee:
            return get_active_employee.id
        else:
            return False
            # self.employee_id = get_active_employee.id

    # default = lambda self: self._get_default_employee
    @api.depends('reserve_guest')
    def _get_reserve_count(self):
        if self.reserve_guest:
            self.reserve_count = len(self.reserve_guest) + 1
        else:
            self.reserve_count = 1

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string='Employee')
    food_reserve_date = fields.Date(string='Date')
    has_guest = fields.Boolean(default=False)
    reserve_guest = fields.One2many('guest.reserve.line', 'whose_guest', string='Reserve guest')
    reserve_count = fields.Integer(compute=_get_reserve_count, store=True)

    # @api.onchange('employee_id', 'food_reserve_date')
    def _check_duplicate_in_same_date_and_user(self):
        for rec in self:
            dulicate = self.env['employee.meal.reserve'].sudo().search(
                [('food_reserve_date', '=', rec.food_reserve_date), ('employee_id', '=', rec.employee_id.id)])
            print(dulicate)
            if dulicate:
                raise exceptions.ValidationError(
                    _("Cannot create new food reservation record for %(empl_name)s, the employee already booked %(datetime)s") % {
                        'empl_name': rec.employee_id.name,
                        'datetime': str(rec.food_reserve_date)
                        # 'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self,
                        #                                                                         fields.Datetime.from_string(
                        #                                                                             self.food_reserve_date))),
                    })

    @api.model
    def create(self, vals_list):

        if not vals_list.get('employee_id', False):
            print('employee_id not in')
            active_user = self.env.user.id
            get_active_employee = self.env['hr.employee'].sudo().search([('user_id', '=', active_user)], limit=1)

            vals_list['employee_id'] = get_active_employee.id
        if vals_list.get('name', _('New')) == _('New'):
            vals_list['name'] = self.env['ir.sequence'].next_by_code('employee.meal.reserve') or _('New')
        varify_date = vals_list.get('food_reserve_date', False)
        employee_id_to_varify = vals_list.get('employee_id', False)
        dulicate = self.env['employee.meal.reserve'].sudo().search(
            [('food_reserve_date', '=', varify_date), ('employee_id', '=', employee_id_to_varify)])

        if dulicate:
            get_employee_object = self.env['hr.employee'].sudo().search([('id', '=', employee_id_to_varify)],
                                                                        limit=1)
            raise exceptions.ValidationError(
                _("Cannot create new food reservation record for %(empl_name)s, the employee already booked %(datetime)s") % {
                    'empl_name': get_employee_object.name,
                    'datetime': str(varify_date)
                    # 'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self,
                    #                                                                         fields.Datetime.from_string(
                    #                                                                             self.food_reserve_date))),
                })
        return super(EmployeeMealReserve, self).create(vals_list)

    def get_all_employee(self):
        employee_ids = self.env['hr.employee'].sudo().search([])
        return employee_ids

    def get_holidays(self):
        holidays = self.env['holiday.month.date'].sudo().search([])
        holidays_date = list()
        for holiday in holidays:
            holidays_date.append(holiday.date)
        return holidays_date

    def _check_date_is_friday(self, date):
        if date.weekday() == 4:
            return True
        return False

    def _check_date_is_reservable(self, date):
        if (date not in self.get_holidays()) and (not self._check_date_is_friday(date)):
            return True
        return False

    def _reserve_meal_all_month_automatically(self):
        print('corn job start ')
        # {'has_guest': False, 'employee_id': 66, 'food_reserve_date': '2021-06-23', 'message_attachment_count': 0}
        employee_reserve = self.env['employee.meal.reserve']
        today = datetime.now().date()
        print(type(today))
        for employee in self.get_all_employee():
            for date in days_current_month():
                if self._check_date_is_reservable(date) and date >= today:
                    val_list = {
                        'employee_id': employee.id,
                        'food_reserve_date': date,
                        'has_guest': False,
                        'message_attachment_count': 0,
                    }
                    print('corn job create : ', val_list)
                    employee_reserve.create(val_list)
    def meal_print_report(self):
        print(self.ids)
        return self.env.ref('usl_office_food.current_month_meal_report').report_action(docids=[1])



class GuestReserveLine(models.Model):
    _name = 'guest.reserve.line'
    guest_name = fields.Char(string='Name')
    guest_id = fields.Many2one('hr.employee', sring='Gust Id')
    whose_guest = fields.Many2one('employee.meal.reserve', string='Employee')
    food_reserve_date = fields.Date(string='Date', related='whose_guest.food_reserve_date', store=True)
