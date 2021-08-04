from odoo import api, fields, models


class ResUserInherit(models.Model):
    # _name = 'new_module.new_module'
    # _rec_name = 'name'
    # _description = 'New Description'
    _name = 'menu.permission'
    # _inherit = 'res.users'

    # company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    user_id = fields.Many2one('res.users',string="Select User")
    users_menu = fields.Many2many('ir.ui.menu','groups_menu_rel',string="All Menu")

    @api.onchange('user_id')
    def create_user(self):
        if self.user_id:
            menu_list = []
            menu_checked = self.env['ir.ui.menu']
            query = """select count(im.id),im.id from ir_ui_menu im left join ir_ui_menu_group_rel
                imr on imr.menu_id = im.id 
                left join res_groups_users_rel rgl on rgl.gid = imr.gid 
                where rgl.uid = {} group by im.id,imr.menu_id,imr.gid,rgl.gid,rgl.uid""".format(self.user_id.id)
            # menu_ids = self.env['ir.ui.menu'].search([],order="id asc")
            self._cr.execute(query=query)
            result = self._cr.fetchall()
            print(query)
            print(result)
            for res in result:
                menu_list.append(res[1])
            for val in menu_list:
                menu_permission = self.env['ir.ui.menu'].search([('id','=',val)])
                menu_checked += menu_permission

            print(menu_list)
            self.users_menu = menu_checked.ids
            print("checked")

