from odoo import api, fields, models, _
# from . import assign_all_users_menu
from odoo.http import request


class ResUsersInherit(models.Model):
    _inherit = 'res.users'


    # def check_ac_menu(self):
    #     ac_menu = self.env['ir.ui.menu'].browse(595)
    #
    #     # query = """select * from ir_ui_menu where id = 595"""
    #     # self._cr.execute(query=query)
    #     # result = self._cr.fetchone()
    #     print(ac_menu)

    def get_ac_menu(self):
        ac_report = self.env['ir.ui.menu'].browse(595)
        self.ac_menu = ac_report
        print(self.ac_menu)


    @api.model
    def assign_previous_menu(self):
        users_list = self.env['res.users'].search([])
        for users in users_list:
            menu_list = []
            query = """select im.id,im.name,im.parent_id,im.parent_path,rgl.gid,rs.id from ir_ui_menu im
                               left join ir_ui_menu_group_rel imr on imr.menu_id = im.id
                               left join res_groups_users_rel rgl on rgl.gid = imr.gid
                               left join res_users rs on rs.id = rgl.uid where rs.id = {}
                               group by rs.id,im.id,imr.menu_id,imr.gid,rgl.gid,rgl.uid,im.parent_path""".format(
                users.id)
            self._cr.execute(query=query)
            result = self._cr.fetchall()
            for menu_id in result:
                menu_list.append(menu_id[0])
            previous_menu = self.env['ir.ui.menu'].search([('id', 'in', menu_list)])
            inv_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '218/%'), ('parent_id', '!=', None)]).ids)])
            users.inv_menu = inv_menu_new
            purchase_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '167/%'), ('parent_id', '!=', None)]).ids)])
            users.hide_menu = purchase_menu_new
            sales_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '190/%'), ('parent_id', '!=', None)]).ids)])
            users.sales_menu = sales_menu_new
            accounting_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '101/%'), ('parent_id', '!=', None)]).ids)])
            users.accounting_menu = accounting_menu_new
            # users.accounting_menu += ac_menu
            crm_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '374/%'), ('parent_id', '!=', None)]).ids)])
            users.crm_menu = crm_menu_new
            emp_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '341/%'), ('parent_id', '!=', None)]).ids)])
            users.emp_menu = emp_menu_new
            contact_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '361/%'), ('parent_id', '!=', None)]).ids)])
            users.contact_menu = contact_menu_new
            payroll_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '786/%'), ('parent_id', '!=', None)]).ids)])
            users.payroll_menu = payroll_menu_new
            pos_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '255/%'), ('parent_id', '!=', None)]).ids)])
            users.pos_menu = pos_menu_new
            website_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '279/%'), ('parent_id', '!=', None)]).ids)])
            users.website_menu = website_menu_new
            apps_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '5/%'), ('parent_id', '!=', None)]).ids)])
            users.apps_menu = apps_menu_new
            settings_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '4/%'), ('parent_id', '!=', None)]).ids)])
            users.settings_menu = settings_menu_new
            discuss_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '79/%'), ('parent_id', '!=', None)]).ids)])
            users.discuss_menu = discuss_menu_new
            dashboard_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '1/%'), ('parent_id', '!=', None)]).ids)])
            users.dashboard_menu = dashboard_menu_new
            config_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '189/%'), ('parent_id', '!=', None)]).ids)])
            users.config_menu = config_menu_new
            calendar_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '357/%'), ('parent_id', '!=', None)]).ids)])
            users.calendar_menu = calendar_menu_new
            expense_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '405/%'), ('parent_id', '!=', None)]).ids)])
            users.expense_menu = expense_menu_new
            link_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '184/%'), ('parent_id', '!=', None)]).ids)])
            users.link_menu = link_menu_new
            events_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '497/%'), ('parent_id', '!=', None)]).ids)])
            users.events_menu = events_menu_new
            lc_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '813/%'), ('parent_id', '!=', None)]).ids)])
            users.lc_menu = lc_menu_new
            cost_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '817/%'), ('parent_id', '!=', None)]).ids)])
            users.cost_menu = cost_menu_new
            inv_report_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '218/231%'), ('parent_id', '!=', None)]).ids)])
            users.inventory_reporting = inv_report_menu_new
            acc_report_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '101/111%'), ('parent_id', '!=', None)]).ids)])
            users.account_reporting = acc_report_menu_new
            sales_report_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '190/194%'), ('parent_id', '!=', None)]).ids)])
            users.sales_report = sales_report_menu_new
            purchase_report_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '167/182%'), ('parent_id', '!=', None)]).ids)])
            users.purchase_report = purchase_report_menu_new
            vat_menu_new = previous_menu.search([('id', 'in', self.env['ir.ui.menu'].search(
                [('parent_path', '=like', '804/%'), ('parent_id', '!=', None)]).ids)])
            users.vat_menu = vat_menu_new
            self._cr.commit()
            parent_menu = self.env['ir.ui.menu'].search([('parent_id','=',None)])
            self._cr.commit()
            users.users_menu += parent_menu
            users.users_menu += sales_menu_new
            users.users_menu += inv_menu_new
            users.users_menu += purchase_menu_new
            users.users_menu += accounting_menu_new
            users.users_menu += crm_menu_new
            users.users_menu += emp_menu_new
            users.users_menu += contact_menu_new
            users.users_menu += payroll_menu_new
            users.users_menu += pos_menu_new
            users.users_menu += website_menu_new
            users.users_menu += apps_menu_new
            users.users_menu += settings_menu_new
            users.users_menu += discuss_menu_new
            users.users_menu += dashboard_menu_new
            users.users_menu += config_menu_new
            users.users_menu += calendar_menu_new
            users.users_menu += expense_menu_new
            users.users_menu += link_menu_new
            users.users_menu += events_menu_new
            users.users_menu += lc_menu_new
            users.users_menu += cost_menu_new
            users.users_menu += inv_report_menu_new
            users.users_menu += acc_report_menu_new
            users.users_menu += sales_report_menu_new
            users.users_menu += purchase_report_menu_new
            users.users_menu += vat_menu_new
            ac_menu = self.env['ir.ui.menu'].browse(595)
            users.users_menu += ac_menu
            self._cr.commit()
            print(users.users_menu)

    def switch_user_dashboard(self):
        return {
            'name': _('User'),
            'view_type': 'tree',
            'view_mode': 'tree',
            'view_id': self.env.ref('base.view_users_tree').id,
            'res_model': 'res.users',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    users_menu = fields.Many2many('ir.ui.menu', 'users_menu_rel')
    users_ac_menu = fields.Many2many('ir.ui.menu','users_menu_rel_ac')
    parent_menu = fields.Many2many('ir.ui.menu','parent_menu_users_rel')
    hide_menu = fields.Many2many('ir.ui.menu','groups_menu_rel',string="Purchase", domain="[('parent_path','=like', '167/%'),('parent_id','!=',None)]")
    ac_menu = fields.Many2many('ir.ui.menu', 'groups_menu_rel_ac', string="A/C Reports",
                                 domain="[('parent_path','=', '101/595/')]")
    inv_menu = fields.Many2many('ir.ui.menu', 'groups_menu_rel_inv', string="Inventory",domain="[('parent_path','=like','218/%'),('parent_id','!=',None)]")
    vat_menu = fields.Many2many('ir.ui.menu', 'groups_menu_rel_vat',domain="[('parent_path','=like','804/%'),('parent_id','!=',None)]")
    sales_menu = fields.Many2many('ir.ui.menu','users_menu_rel_sales',domain="[('parent_path','=like','190/%'),('parent_id','!=',None)]",string="Sales Menu")
    accounting_menu = fields.Many2many('ir.ui.menu','users_menu_rel_acc',domain="[('parent_path','=like','101/%'),('parent_id','!=',None)]",string="Accounting Menu")
    crm_menu = fields.Many2many('ir.ui.menu','users_menu_rel_crm',domain="[('parent_path','=like','374/%'),('parent_id','!=',None)]",string="CRM Menu")
    emp_menu = fields.Many2many('ir.ui.menu','users_menu_rel_emp',domain="[('parent_path','=like','341/%'),('parent_id','!=',None)]",string="emp Menu")
    contact_menu = fields.Many2many('ir.ui.menu','users_menu_rel_cont',domain="[('parent_path','=like','361/%'),('parent_id','!=',None)]",string="Contact Menu")
    payroll_menu = fields.Many2many('ir.ui.menu','users_menu_rel_pay',domain="[('parent_path','=like','786/%'),('parent_id','!=',None)]",string="Payroll Menu")
    pos_menu = fields.Many2many('ir.ui.menu','users_menu_rel_pos',domain="[('parent_path','=like','255/%'),('parent_id','!=',None)]",string="Pos Menu")
    website_menu = fields.Many2many('ir.ui.menu','users_menu_rel_web',domain="[('parent_path','=like','279/%'),('parent_id','!=',None)]",string="Web Menu")
    apps_menu = fields.Many2many('ir.ui.menu','users_menu_rel_apps',domain="[('parent_path','=like','5/%'),('parent_id','!=',None)]",string="Apps Menu")
    settings_menu = fields.Many2many('ir.ui.menu','users_menu_rel_settings',domain="[('parent_path','=like','4/%'),('parent_id','!=',None)]",string="Settings Menu")
    discuss_menu = fields.Many2many('ir.ui.menu','users_menu_rel_discuss',domain="[('parent_path','=like','79/%'),('parent_id','!=',None)]",string="Discuss Menu")
    dashboard_menu = fields.Many2many('ir.ui.menu','users_menu_rel_dboard',domain="[('parent_path','=like','1/%'),('parent_id','!=',None)]",string="Dashboard Menu")
    config_menu = fields.Many2many('ir.ui.menu','users_menu_rel_config',domain="[('parent_path','=like','189/%'),('parent_id','!=',None)]",string="Config Menu")
    calender_menu = fields.Many2many('ir.ui.menu','users_menu_rel_calendar',domain="[('parent_path','=like','357/%'),('parent_id','!=',None)]",string="Calendar Menu")
    expense_menu = fields.Many2many('ir.ui.menu','users_menu_rel_expense',domain="[('parent_path','=like','405/%'),('parent_id','!=',None)]",string="Expense Menu")
    link_menu = fields.Many2many('ir.ui.menu','users_menu_rel_link',domain="[('parent_path','=like','184/%'),('parent_id','!=',None)]",string="Link Menu")
    events_menu = fields.Many2many('ir.ui.menu','users_menu_rel_events',domain="[('parent_path','=like','497/%'),('parent_id','!=',None)]",string="Events Menu")
    lc_menu = fields.Many2many('ir.ui.menu','users_menu_rel_lc',domain="[('parent_path','=like','813/%'),('parent_id','!=',None)]",string="LC Menu")
    cost_menu = fields.Many2many('ir.ui.menu','users_menu_rel_cost',domain="[('parent_path','=like','817/%'),('parent_id','!=',None)]",string="Landed Cost Menu")
    inventory_reporting = fields.Many2many('ir.ui.menu','users_menu_rel_inv_report',domain="[('parent_path','=like','218/231%'),('parent_id','!=',None)]",string="Inventory Reporting")
    account_reporting = fields.Many2many('ir.ui.menu', 'users_menu_rel_account_report',domain="[('parent_path','=like','101/111%'),('parent_id','!=',None)]", string="Accounting Reporting")
    sales_report = fields.Many2many('ir.ui.menu', 'users_menu_rel_sales_report',domain="[('parent_path','=like','190/194%'),('parent_id','!=',None)]", string="Sales Reporting")
    purchase_report = fields.Many2many('ir.ui.menu', 'users_menu_rel_purchase_report',domain="[('parent_path','=like','167/182%'),('parent_id','!=',None)]", string="Purchase Reporting")
    previous_menu_ids = fields.Many2many('ir.ui.menu','previous_menu_users_rel')

    def assign_parent_menu(self):
       parent_ids = self.env['ir.ui.menu'].search([('parent_id','=',None)])
       self.parent_menu = parent_ids

    @api.onchange('sales_menu')
    def append_menu_sales(self):
        self.users_menu = self.sales_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('accounting_menu')
    def append_menu_accounting(self):
        self.users_menu = self.accounting_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('vat_menu')
    def append_menu_vat(self):
        self.users_menu = self.vat_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('hide_menu')
    def append_menu(self):
        self.users_menu = self.hide_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('inv_menu')
    def append_menu_inv(self):
        self.users_menu = self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        print(self.parent_menu)
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu


    @api.onchange('crm_menu')
    def append_menu_crm(self):
        self.users_menu = self.crm_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('emp_menu')
    def append_menu_emp(self):
        self.users_menu = self.emp_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('contact_menu')
    def append_menu_contact(self):
        self.users_menu = self.contact_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('payroll_menu')
    def append_menu_payroll(self):
        self.users_menu = self.payroll_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('pos_menu')
    def append_menu_pos(self):
        self.users_menu = self.pos_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('website_menu')
    def append_menu_website(self):
        self.users_menu = self.website_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('apps_menu')
    def append_menu_apps(self):
        self.users_menu = self.apps_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('settings_menu')
    def append_menu_settings(self):
        self.users_menu = self.settings_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('discuss_menu')
    def append_menu_discuss(self):
        self.users_menu = self.discuss_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('dashboard_menu')
    def append_menu_dashboard(self):
        self.users_menu = self.dashboard_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('config_menu')
    def append_menu_config(self):
        self.users_menu = self.config_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('calender_menu')
    def append_menu_calendar(self):
        self.users_menu = self.calender_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('expense_menu')
    def append_menu_expense(self):
        self.users_menu = self.expense_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('link_menu')
    def append_menu_link(self):
        self.users_menu = self.link_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('events_menu')
    def append_menu_events(self):
        self.users_menu = self.events_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.lc_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('lc_menu')
    def append_menu_lc(self):
        self.users_menu = self.lc_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.cost_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('cost_menu')
    def append_menu_cost(self):
        self.users_menu = self.cost_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('inventory_reporting')
    def append_menu_inv_report(self):
        self.users_menu = self.inventory_reporting
        self.users_menu += self.cost_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        self.inv_menu   += self.inventory_reporting
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('account_reporting')
    def append_menu_account_report(self):
        self.users_menu = self.account_reporting
        self.users_menu += self.inventory_reporting
        self.users_menu += self.cost_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        # self.inv_menu += self.inventory_reporting
        self.accounting_menu += self.account_reporting
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu

    @api.onchange('sales_report')
    def append_menu_sales_report(self):
        self.users_menu = self.sales_report
        self.users_menu += self.account_reporting
        self.users_menu += self.inventory_reporting
        self.users_menu += self.cost_menu
        self.users_menu += self.inv_menu
        self.users_menu += self.hide_menu
        self.users_menu += self.vat_menu
        self.users_menu += self.sales_menu
        self.users_menu += self.accounting_menu
        self.users_menu += self.crm_menu
        self.users_menu += self.emp_menu
        self.users_menu += self.contact_menu
        self.users_menu += self.payroll_menu
        self.users_menu += self.pos_menu
        self.users_menu += self.website_menu
        self.users_menu += self.apps_menu
        self.users_menu += self.settings_menu
        self.users_menu += self.discuss_menu
        self.users_menu += self.dashboard_menu
        self.users_menu += self.config_menu
        self.users_menu += self.calender_menu
        self.users_menu += self.expense_menu
        self.users_menu += self.link_menu
        self.users_menu += self.events_menu
        self.users_menu += self.lc_menu
        # self.inv_menu += self.inventory_reporting
        self.sales_menu += self.sales_report
        self.assign_parent_menu()
        self.users_menu += self.parent_menu
        self.get_ac_menu()
        self.users_menu += self.ac_menu