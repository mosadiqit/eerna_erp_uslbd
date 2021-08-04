from odoo import fields, api, models


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(Http, self).session_info()
        if res:
            allow_branch = []
            all_branch = []
            if self.env.user:
                if self.env.user.branch_ids:
                    for branch in self.env.user.branch_ids:
                        all_branch.append((branch.id, branch.name))
                if self.env.user.branch_id:
                    for branch in self.env.user.branch_id:
                        allow_branch.append((branch.id, branch.name))

                res['user_companies'].update({'all': all_branch, 'allow': allow_branch[0]})
            return res


class ResUsers(models.Model):
    _inherit = 'res.users'

    def update_data_user(self, data_dic):
        if data_dic:
            branch_id = data_dic.get('branch_id')
            self.branch_id = branch_id
