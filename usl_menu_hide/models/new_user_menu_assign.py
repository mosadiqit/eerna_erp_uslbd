from odoo import api, fields, models, _

class AssignselfMenu(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AssignselfMenu, self).create(vals_list)
        res.assign_new_users_menu()
        return res

    def write(self, vals):
        if 'sel_groups_32_33_34' in vals.keys():
            if vals['sel_groups_32_33_34'] is not False:
                sales_id = self.env['ir.ui.menu'].search([('name', '=', 'Sales'), ('parent_id', '=', None)])
                all_sales_id = self.env['ir.ui.menu'].search([('parent_id', '=', sales_id.id)])
                for s_id in all_sales_id:
                    self.sales_menu += s_id
                    sales_menu = self.env['ir.ui.menu'].search([('parent_id', '=', s_id.id)])
                    self.sales_menu += sales_menu
                    self.sales_report += self.sales_menu
                    self.users_menu += self.sales_menu
                    self.users_menu += self.sales_report
            else:
                self.sales_menu = None
                self.sales_report = None
                self.users_menu += self.sales_menu
                self.users_menu += self.sales_report
        if 'sel_groups_42_43' in vals.keys():
            if vals['sel_groups_42_43'] is not False:
                inv_id = self.env['ir.ui.menu'].search([('name', '=', 'Inventory'), ('parent_id', '=', None)])
                all_inv_id = self.env['ir.ui.menu'].search([('parent_id', '=', inv_id.id)])
                for s_id in all_inv_id:
                    self.inv_menu += s_id
                    inv_menu = self.env['ir.ui.menu'].search([('parent_id', '=', s_id.id)])
                    self.inv_menu += inv_menu
                    self.inventory_reporting += self.inv_menu
                    self.users_menu += self.inv_menu
                    self.users_menu += self.inventory_reporting
            else:
                self.inv_menu = None
                self.inventory_reporting = None
                self.users_menu += self.inv_menu
                self.users_menu += self.inventory_reporting
        if 'sel_groups_29_30' in vals.keys():
            if vals['sel_groups_29_30'] is not False:
                purchase_id = self.env['ir.ui.menu'].search([('name', '=', 'Purchase'), ('parent_id', '=', None)])
                all_purchase_id = self.env['ir.ui.menu'].search([('parent_id', '=', purchase_id.id)])
                for p_id in all_purchase_id:
                    self.hide_menu += p_id
                    added_menu = self.env['ir.ui.menu'].search([('parent_id', '=', p_id.id)])
                    self.hide_menu += added_menu
                    self.purchase_report += added_menu
                    self.users_menu += self.hide_menu
                    self.users_menu += self.purchase_report
            else:
                self.hide_menu = None
                self.purchase_report = None
                self.users_menu += self.hide_menu
                self.users_menu += self.purchase_report
        res = super().write(vals)
        return res

    def assign_new_users_menu(self):
        if 101 in self.groups_id.menu_access.ids:
            acc_id = self.env['ir.ui.menu'].search([('name', '=', 'Accounting'), ('parent_id', '=', None)])
            all_acc_id = self.env['ir.ui.menu'].search([('parent_id', '=', acc_id.id)])
            for s_id in all_acc_id:
                self.accounting_menu += s_id
                acc_menu = self.env['ir.ui.menu'].search([('parent_id', '=', s_id.id)])
                self.accounting_menu += acc_menu
                self.account_reporting += self.accounting_menu

        if 17 in self.groups_id.category_id.ids:
            inv_id = self.env['ir.ui.menu'].search([('name', '=', 'Inventory'), ('parent_id', '=', None)])
            all_inv_id = self.env['ir.ui.menu'].search([('parent_id', '=', inv_id.id)])
            for s_id in all_inv_id:
                self.inv_menu += s_id
                inv_menu = self.env['ir.ui.menu'].search([('parent_id', '=', s_id.id)])
                self.inv_menu += inv_menu
                self.inventory_reporting += self.inv_menu

        if 24 in self.groups_id.category_id.ids:
            sales_id = self.env['ir.ui.menu'].search([('name', '=', 'Sales'), ('parent_id', '=', None)])
            all_sales_id = self.env['ir.ui.menu'].search([('parent_id', '=', sales_id.id)])
            for s_id in all_sales_id:
                self.sales_menu += s_id
                sales_menu = self.env['ir.ui.menu'].search([('parent_id', '=', s_id.id)])
                self.sales_menu += sales_menu
                self.sales_report += self.sales_menu

        if 27 in self.groups_id.category_id.ids:
            purchase_id = self.env['ir.ui.menu'].search([('name', '=', 'Purchase'), ('parent_id', '=', None)])
            all_purchase_id = self.env['ir.ui.menu'].search([('parent_id', '=', purchase_id.id)])
            for p_id in all_purchase_id:
                self.hide_menu += p_id
                added_menu = self.env['ir.ui.menu'].search([('parent_id', '=', p_id.id)])
                self.hide_menu += added_menu
                self.purchase_report += added_menu

            # for i in self.groups_id.menu_access:
            #
            #     if i.display_name == 'Purchase':
            #
            #     if '24' in self.groups_id.category_id.ids:
            #         if 'Sales' in i.display_name:
            #
            #     if 'Inventory' in i.display_name:

            # menu_list = []
            # self._cr.commit()
            # max_user = """select max(id) from res_users"""
            # self._cr.execute(query=max_user)
            # max_id = self._cr.fetchone()
            # query = """select im.id,im.name,im.parent_id,im.parent_path,rgl.gid,rs.id from ir_ui_menu im
            #                    left join ir_ui_menu_group_rel imr on imr.menu_id = im.id
            #                    left join res_groups_users_rel rgl on rgl.gid = imr.gid
            #                    left join res_users rs on rs.id = rgl.uid where rs.id = {}
            #                    group by rs.id,im.id,imr.menu_id,imr.gid,rgl.gid,rgl.uid,im.parent_path""".format(
            #     self.id)
            # self._cr.execute(query=query)
            # result = self._cr.fetchall()
            # for menu_id in result:
            #     menu_list.append(menu_id[0])
            # previous_menu = self.env['ir.ui.menu'].search([('id', 'in', menu_list)])
            # print(len(previous_menu))
            # inv_menu_id = self.env['ir.ui.menu'].search([('parent_path', '=like', '167/%'), ('parent_id', '!=', None)])
            # inv_list = list()
            # print(len(inv_menu_id))
            # for i in inv_menu_id:
            #     inv_list.append(i.id)
            #
            # purchase_menu_new = previous_menu.filtered(lambda i:i.id in inv_list)
            # self._cr.commit()
            # self.hide_menu = purchase_menu_new
            # purchase_menu_new = previous_menu.filtered(lambda id: id in self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '167/%'), ('parent_id', '!=', None)]).ids)
            # self.hide_menu = purchase_menu_new
            # print(self)
            # sales_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '190/%'), ('parent_id', '!=', None)]).ids)])
            # self.sales_menu = sales_menu_new
            # accounting_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '101/%'), ('parent_id', '!=', None)]).ids)])
            # self.accounting_menu = accounting_menu_new
            # # self.accounting_menu += ac_menu
            # crm_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '374/%'), ('parent_id', '!=', None)]).ids)])
            # self.crm_menu = crm_menu_new
            # emp_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '341/%'), ('parent_id', '!=', None)]).ids)])
            # self.emp_menu = emp_menu_new
            # contact_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '361/%'), ('parent_id', '!=', None)]).ids)])
            # self.contact_menu = contact_menu_new
            # payroll_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '786/%'), ('parent_id', '!=', None)]).ids)])
            # self.payroll_menu = payroll_menu_new
            # pos_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '255/%'), ('parent_id', '!=', None)]).ids)])
            # self.pos_menu = pos_menu_new
            # website_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '279/%'), ('parent_id', '!=', None)]).ids)])
            # self.website_menu = website_menu_new
            # apps_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '5/%'), ('parent_id', '!=', None)]).ids)])
            # self.apps_menu = apps_menu_new
            # settings_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '4/%'), ('parent_id', '!=', None)]).ids)])
            # self.settings_menu = settings_menu_new
            # discuss_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '79/%'), ('parent_id', '!=', None)]).ids)])
            # self.discuss_menu = discuss_menu_new
            # dashboard_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '1/%'), ('parent_id', '!=', None)]).ids)])
            # self.dashboard_menu = dashboard_menu_new
            # config_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '189/%'), ('parent_id', '!=', None)]).ids)])
            # self.config_menu = config_menu_new
            # calendar_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '357/%'), ('parent_id', '!=', None)]).ids)])
            # self.calendar_menu = calendar_menu_new
            # expense_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '405/%'), ('parent_id', '!=', None)]).ids)])
            # self.expense_menu = expense_menu_new
            # link_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '184/%'), ('parent_id', '!=', None)]).ids)])
            # self.link_menu = link_menu_new
            # events_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '497/%'), ('parent_id', '!=', None)]).ids)])
            # self.events_menu = events_menu_new
            # lc_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '813/%'), ('parent_id', '!=', None)]).ids)])
            # self.lc_menu = lc_menu_new
            # cost_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '817/%'), ('parent_id', '!=', None)]).ids)])
            # self.cost_menu = cost_menu_new
            # inv_report_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '218/231%'), ('parent_id', '!=', None)]).ids)])
            # self.inventory_reporting = inv_report_menu_new
            # acc_report_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '101/111%'), ('parent_id', '!=', None)]).ids)])
            # self.account_reporting = acc_report_menu_new
            # sales_report_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '190/194%'), ('parent_id', '!=', None)]).ids)])
            # self.sales_report = sales_report_menu_new
            # purchase_report_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '167/182%'), ('parent_id', '!=', None)]).ids)])
            # self.purchase_report = purchase_report_menu_new
            # vat_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
            #     [('parent_path', '=like', '804/%'), ('parent_id', '!=', None)]).ids)])
            # self.vat_menu = vat_menu_new
        parent_menu = self.env['ir.ui.menu'].search([('parent_id', '=', None)])
        self.users_menu += self.hide_menu
        self.users_menu += parent_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.sales_report
        self.users_menu += self.inv_menu
        self.users_menu += self.inventory_reporting
        self.users_menu += self.purchase_report
        self.users_menu += self.accounting_menu
        self.users_menu += self.account_reporting
        # self.users_menu += pos_menu_new
        # self.users_menu += website_menu_new
        # self.users_menu += apps_menu_new
        # self.users_menu += settings_menu_new
        # self.users_menu += discuss_menu_new
        # self.users_menu += dashboard_menu_new
        # self.users_menu += config_menu_new
        # self.users_menu += calendar_menu_new
        # self.users_menu += expense_menu_new
        # self.users_menu += link_menu_new
        # self.users_menu += events_menu_new
        # self.users_menu += lc_menu_new
        # self.users_menu += cost_menu_new
        # self.users_menu += inv_report_menu_new
        # self.users_menu += acc_report_menu_new
        # self.users_menu += sales_report_menu_new
        # self.users_menu += purchase_report_menu_new
        # self.users_menu += vat_menu_new
        # ac_menu = self.env['ir.ui.menu'].browse(595)
        # self.users_menu += ac_menu
        print(self.users_menu)
