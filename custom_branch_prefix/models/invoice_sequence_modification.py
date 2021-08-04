from odoo import api, fields, models, _
from datetime import datetime, timedelta
import logging
import pytz

from odoo.exceptions import UserError


class InvoiceSequenceModification(models.Model):
    _inherit = ['ir.sequence']

    def _get_prefix_suffix(self, date=None, date_range=None):
        def _interpolate(s, d):
            print(s)
            if type(s)!=bool:
                if "/" in s:
                    splited_prefix=s.split("/")
                    if splited_prefix[0]=='INV' or splited_prefix[0]=='RINV' or splited_prefix[0]=='BILL' or splited_prefix[0]=='RBILL' or splited_prefix[0]=='CUST.IN' or splited_prefix[0]=='SUPP.OUT':
                        # inv_user = self.env['res.users'].search([('id','=',self.env.context['default_user_id'])])
                        account_move_list = list()
                        for i in self.env.envs.towrite['account.move'].keys():
                            account_move_list.append(i)
                            break
                        if len(account_move_list) >= 1:
                            account_move_branch = self.env['account.move'].search([('id','=',account_move_list[0])])
                            branch_id = self.env['res.branch'].search([('id','=',account_move_branch.branch_id.id)])
                            if branch_id:
                                s = branch_id.branch_code + "-" + s
                            else:
                                s = self.env.user.branch_id.branch_code + "-" + s
                            # s=s.replace("INV",self.env.user.branch_id.branch_code+"-"+"INV")
                            print(s)
                elif 'S' in s:
                    if self.env.user.branch_id:
                        s = self.env.user.branch_id.branch_code + "-"+ s
                        print(s)


            print(s)

            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self._context.get('ir_sequence_date_range'))

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }
            res = {}
            for key, format in sequences.items():
                res[key] = effective_date.strftime(format)
                res['range_' + key] = range_date.strftime(format)
                res['current_' + key] = now.strftime(format)

            return res

        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except ValueError:
            raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % (self.get('name')))
        return interpolated_prefix, interpolated_suffix