from datetime import datetime, timedelta

from odoo import models


class ReportDailySalesDetailsReportView(models.AbstractModel):
    _name = 'report.usl_office_food.current_month_meal_report_view'

    def _get_current_employee(self, user_id):
        hr_employee = self.env['hr.employee']
        employee = hr_employee.sudo().search([('user_id', '=', user_id)], limit=1)
        if employee:
            return employee
        return False

    def _get_meal_eat_count(self, ids, date):
        meal_eat_model = self.env['employee.meal.eat']
        count = meal_eat_model.sudo().search_count([('employee_id', 'in', ids), ('eat_date', '=', date)])
        return count

    def _get_current_month_report_data(self):
        meal_reserve_model = self.env['employee.meal.reserve']

        last_month_last_date = datetime.now().date().replace(day=1) - timedelta(days=1)
        this_month_last_date = datetime.now().date().replace(month=(datetime.now().month) + 1, day=1) - timedelta(
            days=1)
        current_employee = self._get_current_employee(self.env.user.id)
        if not current_employee:
            return False

        reserves_meals = meal_reserve_model.sudo().search(
            [('employee_id', '=', current_employee.id), ('food_reserve_date', '>', last_month_last_date),
             ('food_reserve_date', '<=', this_month_last_date)])
        employee_meal_date = list()
        for reserve in reserves_meals:
            reserve_employee_ids = [reserve.employee_id.id]
            for guest in reserve.reserve_guest:
                reserve_employee_ids.append(guest.guest_id.id)
            eat_count = self._get_meal_eat_count(reserve_employee_ids, reserve.food_reserve_date)
            val = {
                'employee': reserve.employee_id.name,
                'date': reserve.food_reserve_date,
                'reserve': reserve.reserve_count,
                'eat': eat_count
            }
            employee_meal_date.append(val)

        return employee_meal_date

    def _get_report_values(self, docids, data=None):
        return {
            'report_name': 'Current Month Meal Report',
            'doc_id': self._get_current_month_report_data()
        }
