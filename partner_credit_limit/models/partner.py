# See LICENSE file for full copyright and licensing details.
import datetime

from odoo import fields, models,api,exceptions,_
from datetime import date
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    over_credit = fields.Boolean('Allow Over Credit?',default=True)
    additional_credit_limit=fields.Float(string='Additional Credit Limit',readonly=1,compute="calculate_amount",store=True)
    security_money=fields.Float(string='Security Money')
    additional_credit_limit_line=fields.One2many('additional.credit.limit', 'partner_id', string='Additional Credit Limit Lines')

    # @api.onchange('additional_credit_limit_line')
    @api.depends('additional_credit_limit_line')
    def calculate_amount(self):
        for rec in self:
            rec.additional_credit_limit=0
            print(date.today())
            for line in rec.additional_credit_limit_line:
                # if line.from_date and line.to_date:
                #     if line.from_date<date.today():
                #         raise exceptions.UserError(_('From date must be equal or greater then today!!!'))
                #     if line.to_date<date.today():
                #         raise exceptions.UserError(_('To date must be equal or greater then today!!!'))
                if line.from_date :
                    if line.from_date < date.today():
                       raise  ValidationError(_('From date must be equal or greater then today!!!'))
                    if line.to_date:
                        if line.to_date<line.from_date:
                            raise ValidationError(_('To date must be equal or greater then form date!!!'))
                        if line.to_date < date.today():
                            raise ValidationError(_('To date must be equal or greater then today!!!'))

                    if isinstance(line.to_date,date) and line.to_date>=date.today()>=line.from_date:
                        line.is_deducted=None
                        line.is_sheduled_update=True
                    if isinstance(line.to_date,date) and line.to_date<date.today():
                        line.is_deducted=True
                    if line.is_deducted==False:
                        if isinstance(line.to_date, date) and line.to_date >= date.today() >= line.from_date:
                            rec.additional_credit_limit += line.ammount
    # @api.model
    # def write(self,id,vals):
    #     for rec in self:
    #         print('******')

    @api.model
    def update_additional_credit_limit(self):
        print("ABCD")
        today_date=datetime.date.today()
        get_partner_detail = self.env['res.partner'].search([])
        for rec in get_partner_detail:
            total_amount=0
            sheduled_update_amount=0
            get_scheduling_list = self.env['additional.credit.limit'].search([('to_date', '<', date.today()),('partner_id','=',rec.id),('is_deducted','=',False)])
            get_apply_list=self.env['additional.credit.limit'].search([('partner_id','=',rec.id)])
            if get_apply_list:
                for line in get_apply_list:
                    if line.to_date>=date.today()>=line.from_date and line.is_sheduled_update==False:
                        sheduled_update_amount+=line.ammount
                        line.is_deducted=False
                        line.is_sheduled_update=True
                    if line.to_date<date.today() and line.is_deducted==False:
                        total_amount+=line.ammount
                        line.is_deducted = True

            rec.additional_credit_limit+=sheduled_update_amount-total_amount


            # if get_scheduling_list:
            #     for line in get_scheduling_list:
            #         total_amount+=line.ammount
            #         line.is_deducted=True
            # rec.additional_credit_limit-=total_amount
    # @api.model
    # def update_additional_credit_limit_scheduling(self):
    #     print("Done")
        # today_date=datetime.date.today()
        # get_partner_detail = self.env['res.partner'].search([])
        # for rec in get_partner_detail:
        #     total_amount=0
        #     get_scheduling_list = self.env['additional.credit.limit'].search([('to_date', '<', date.today()),('partner_id','=',rec.id),('is_deducted','=',False)])
        #     if get_scheduling_list:
        #         for line in get_scheduling_list:
        #             total_amount+=line.ammount
        #     rec.additional_credit_limit-=total_amount
