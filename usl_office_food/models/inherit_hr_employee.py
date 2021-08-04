from odoo import fields, models, api, _


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_guest = fields.Boolean(string='Guest')

    def check_meal_reserved(self):
        employee_meal_reserve = self.env['employee.meal.reserve']
        gest_meal_reserve = self.env['employee.meal.reserve']
        action_date = fields.Datetime.now().date()
        if not self.is_guest:
            have_reserve = employee_meal_reserve.sudo().search(
                [('employee_id', '=', self.id), ('food_reserve_date', '=', action_date)], limit=1)
            if have_reserve:
                return True
            return False
        have_guest_reserve = gest_meal_reserve.sudo().search(
            [('guest_id', '=', self.id), ('food_reserve_date''=', action_date)], limit=1)
        if have_guest_reserve:
            return True
        return False

    def check_already_eat(self):
        action_date = fields.Datetime.now().date()
        is_eat = self.env['employee.meal.eat'].sudo().search(
            [('employee_id', '=', self.id), ('eat_date', '=', action_date)], limit=1)
        if is_eat:
            return True
        return False

    def meal_eat_set(self):
        self.ensure_one()
        action_time = fields.Datetime.now()
        action_date = action_time.date()
        if not self.check_meal_reserved() or self.check_already_eat():
            print('not insert ')
            return 'already_receive_meal'
        vals = {
            'employee_id': self.id,
            'eat_date': action_date,
            'eat_time': action_time,
        }
        val = self.env['employee.meal.eat'].create(vals)
        return 'test_kiosk_mode'

    def _employee_meal_action(self):
        self.ensure_one()
        employee = self.sudo()
        action_message = self.env.ref(
            'usl_office_food.usl_office_food_cataring_service_management_action_my_attendances').read()[
            0]
        # # action_message['previous_attendance_change_date'] = employee.last_attendance_id and (
        # #         employee.last_attendance_id.check_out or employee.last_attendance_id.check_in) or False
        # action_message['employee_name'] = employee.name
        # action_message['barcode'] = employee.barcode
        # action_message['next_action'] = next_action
        # action_message['hours_today'] = employee.hours_today
        #
        if employee.user_id:
            modified_attendance = employee.with_user(employee.user_id).meal_eat_set()
        else:
            modified_attendance = employee.meal_eat_set()
        # if not isinstance(modified_attendance, bool):
        #     action_message['attendance'] = modified_attendance.read()[0]
        # else:
        #     action_message['attendance'] = 'test complete'
        return {'action': modified_attendance}

    @api.model
    def meal_eat_scan(self, barcode):
        print('barcode : ', barcode)
        employee = self.sudo().search([('barcode', '=', barcode)], limit=1)
        if employee:
            return employee._employee_meal_action()
        return {'warning': _('No employee corresponding to barcode %(barcode)s') % {'barcode': barcode}}

    @api.model
    def meal_eat_manual(self, id):
        print('id : ', id)

        employee = self.sudo().search([('id', '=', id)], limit=1)
        print('employee :', employee)
        if employee:
            return employee._employee_meal_action()
        return {'warning': _('Wrong PIN')}

    @api.model
    def employee_from_barcode(self, barcode):

        employee = self.sudo().search([('barcode', '=', barcode)], limit=1)
        print(employee.name)
        return {
            'name': employee.name,
            'url': employee.image_1920,
            'id': employee.id}

    @api.model
    def employee_from_id(self, id):

        employee = self.sudo().search([('id', '=', id)], limit=1)
        print(employee.name)
        return {
            'name': employee.name,
            'url': employee.image_1920,
            'id': employee.id}
