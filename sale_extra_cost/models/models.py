# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderExtra(models.Model):
    _inherit = "sale.order"

    BP_amount = fields.Float('Sale Incentive')
    Security_money = fields.Float('Security Money')

    def _prepare_invoice(self):
        res = super(SaleOrderExtra, self)._prepare_invoice()
        res['BP_amount'] = self.BP_amount
        res['Security_money'] = self.Security_money
        return res


class InvoiceExtra(models.Model):
    _inherit = "account.move"

    BP_amount = fields.Float('Sale Incentive')
    Security_money = fields.Float('Security Money')

    def approve_invoice_order(self):
        res = super(InvoiceExtra, self).action_post()
        self.env['account.move'].browse(self.env.context.get('active_ids'))
        all_product_total = 0.0
        avg_value = 0.0
        old_avg_value = 0.0
        if self.BP_amount > 0:
            # for item in self.line_ids:
            #     # product_sale_price = self.env['sale.order.line'].filtered(lambda p: p.name == self.invoice_origin)
            #     if item.product_id.id > 0 and item.product_uom_id.id > 0:
            #         all_product_total += item.price_unit
            # avg_value = self.BP_amount / all_product_total
            #
            # for pd in self.line_ids:
            #     if pd.product_id.id > 0 and pd.product_uom_id.id > 0:
            #         old_avg = self.line_ids.filtered(lambda f: f.name == "BP").credit / all_product_total
            #         old_avg_value = (pd.quantity * pd.price_unit) * old_avg
            #         # pd.with_context(check_move_validity=False).credit += old_avg_value
            #         old_price = pd.price_unit
            #         pd.with_context(check_move_validity=False).credit -= pd.price_unit * avg_value
            #         pd.price_unit = old_price


            lines_to_delete = self.line_ids.filtered(lambda f: f.name == "Expense")
            lines_to_delete_BP = self.line_ids.filtered(lambda f: f.name == "BP")
            if self != self._origin:
                self.line_ids -= lines_to_delete
            else:
                lines_to_delete.with_context(check_move_validity=False).unlink()
                lines_to_delete_BP.with_context(check_move_validity=False).unlink()

            bp_payable_account_id = self.env['saleotherexpense'].search([]).bp_account_id.ids[0]
            bp_expense_account_id = self.env['saleotherexpense'].search([]).bp_exp_account_id.ids[0]

            # query = """select bp_account_id from saleotherexpense"""
            # self._cr.execute(query=query)
            # bp_payable_account_id = self._cr.fetchone()
            #
            # query = """select bp_exp_account_id from saleotherexpense"""
            # self._cr.execute(query=query)
            # bp_expense_account_id = self._cr.fetchone()



            vals_list = []

            vals_list.append(
                (
                    0,
                    0,
                    {
                        "name": "BP",
                        "debit": 0.0,
                        "credit": self.BP_amount,
                        "account_id": bp_payable_account_id,
                        # "analytic_account_id": 2,
                        "exclude_from_invoice_tab": True,
                    },
                )
            )

            vals_list.append(
                (
                    0,
                    0,
                    {
                        "name": "Expense",
                        "debit": self.BP_amount,
                        "credit": 0.0,
                        "account_id": bp_expense_account_id,
                        # "analytic_account_id": 2,
                        "exclude_from_invoice_tab": True,
                    },
                )
            )

            if self.BP_amount > 0:
                self.line_ids = vals_list
                # self._onchange_recompute_dynamic_lines()
            else:
                return
        else:
            # if self.BP_amount < 0:
            #      raise ValidationError(_('''Negative BP not allow!'''
            #                         ))
            # return

            # for item in self.line_ids:
            #     if item.product_id.id > 0 and item.product_uom_id.id > 0:
            #         all_product_total += item.price_unit
            # avg_value = self.line_ids.filtered(lambda f: f.name == "BP").credit / all_product_total
            #
            # for pd in self.line_ids:
            #     if pd.product_id.id > 0 and pd.product_uom_id.id > 0:
            #         pd.with_context(check_move_validity=False).credit += avg_value

            lines_to_delete = self.line_ids.filtered(lambda f: f.name == "Expense")
            lines_to_delete_BP = self.line_ids.filtered(lambda f: f.name == "BP")
            if self != self._origin:
                self.line_ids -= lines_to_delete
            else:
                lines_to_delete.with_context(check_move_validity=False).unlink()
                lines_to_delete_BP.with_context(check_move_validity=False).unlink()
            return

        # if self.Security_money > 0:
        #     lines_to_delete_scr = self.line_ids.filtered(lambda f: f.name == "Security Deposit")
        #     lines_to_delete_sc = self.line_ids.filtered(lambda f: f.name == "Security Money")
        #     if self != self._origin:
        #         self.line_ids -= lines_to_delete
        #     else:
        #         lines_to_delete_scr.with_context(check_move_validity=False).unlink()
        #         lines_to_delete_sc.with_context(check_move_validity=False).unlink()
        #
        #     vals_list_sc = []
        #
        #     vals_list_sc.append(
        #         (
        #             0,
        #             0,
        #             {
        #                 "name": "Security Deposit",
        #                 "debit": self.Security_money,
        #                 "credit": 0.0,
        #                 "account_id": 538,
        #                 # "analytic_account_id": 2,
        #                 "exclude_from_invoice_tab": True,
        #             },
        #         )
        #     )
        #
        #     vals_list_sc.append(
        #         (
        #             0,
        #             0,
        #             {
        #                 "name": "Security Money",
        #                 "debit": 0.0,
        #                 "credit": self.Security_money,
        #                 "account_id": 539,
        #                 # "analytic_account_id": 2,
        #                 "exclude_from_invoice_tab": True,
        #             },
        #         )
        #     )
        #
        #     if self.Security_money > 0:
        #         self.line_ids = vals_list_sc
        #         # self._onchange_recompute_dynamic_lines()
        #     else:
        #         return
        # else:
        #     lines_to_delete_scr = self.line_ids.filtered(lambda f: f.name == "Security Deposit")
        #     lines_to_delete_sc = self.line_ids.filtered(lambda f: f.name == "Security Money")
        #     if self != self._origin:
        #         self.line_ids -= lines_to_delete_sc
        #         self.line_ids -= lines_to_delete_scr
        #     else:
        #         lines_to_delete_scr.with_context(check_move_validity=False).unlink()
        #         lines_to_delete_sc.with_context(check_move_validity=False).unlink()
        #     return
    # @api.onchange("BP_amount")
    # def _onchange_BP(self):
    #     """Trigger BP amount onchange"""
    #     return self._onchange_BP_amount()
    #
    # def _onchange_BP_amount(self):
    #     """Append BP move lines"""
    #     lines_to_delete = self.line_ids.filtered("BP")
    #     if self != self._origin:
    #         self.line_ids -= lines_to_delete
    #     else:
    #         lines_to_delete.with_context(check_move_validity=False).unlink()
    #
    #     vals_list = [(
    #         0,
    #         0,
    #         {
    #             "BP": True,
    #             "name": "BP",
    #             "debit": self.BP_amount > 0.0 and self.BP_amount or 0.0,
    #             "credit": 0.0,
    #             "account_id": 534,
    #             # "analytic_account_id": 2,
    #             "exclude_from_invoice_tab": True,
    #         },
    #     )]
    #
    #     if self.BP_amount > 0:
    #         self.line_ids = vals_list
    #         self._onchange_recompute_dynamic_lines()
    #     else:
    #         return

# class AccountMoveLine(models.Model):
#     _inherit = "account.move.line"
#
#     BP_amount = fields.Float('BP Amount')
#     BP = fields.Boolean()
