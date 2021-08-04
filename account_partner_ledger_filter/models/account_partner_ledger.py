from dateutil.relativedelta import relativedelta
from num2words import num2words
import time
import logging
from odoo import api, models, _, fields
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.gts_financial_pdf_report.report_partnerledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('_get_report_values on report.gts_financial_pdf_report.report_partnerledger')
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}

        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        print('query_get_data',data['form'].get('used_context', {}))
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        if data['form'].get('target_move') == 'all':
            print(query_get_data[1])
            new_string=query_get_data[1].replace("date","collection_date")
            query_get_data=list(query_get_data)
            query_get_data.pop(1)
            query_get_data.insert(1,new_string)
            query_get_data=tuple(query_get_data)
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.internal_type IN %s
            AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[1] + reconcile_clause
        print(query)
        self.env.cr.execute(query, tuple(params))
        # ---------------------Taking only selected partners---------------------------
        if data['form']['partner_ids']:
            partner_ids = data['form']['partner_ids']
        else:
            partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        # -----------------------------------------------------------------------------
        # partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        where_partner_ids = "1=1"
        where_pay_partner_ids = "1=1"
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))

        is_mis_summery = data['form'].get('mis_summery')
        branch_ids = data['form'].get('branch_ids')
        branch_id = branch_ids['branch_ids']
        company_id = data['form'].get('company_id')[0]
        target_move = data['form'].get('target_move')
        from_date = data['form'].get('date_from')
        to_date = data['form'].get('date_to')
        security_money = 0
        if is_mis_summery:

            if partner_ids:
                where_partner_ids = " id in %s" % str(tuple(partner_ids)).replace(',)', ')')
                where_pay_partner_ids = "rp.id in %s" % str(tuple(partner_ids)).replace(',)', ')')
            #Credit Limit
            # query1 = """select COALESCE(res_partner.credit_limit) from res_partner where {}""".format(where_partner_ids)
            # self._cr.execute(query=query1)
            # result_credit = self._cr.fetchall()
            # crLimit = result_credit[0][0]
            crLimit = 0
            # security_money = 0
            partner_info = self.env['res.partner'].browse(partner_ids)
            if partner_info:
                crLimit = partner_info.credit_limit
                security_money = partner_info.security_money
            # print('credit limit - ',result_credit)

            # Current Month Sales
            if target_move == 'posted':
                query2 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id in (50053, 52048) and date between (select cast(date_trunc('month', current_date) as date)) and (cast(date_trunc('month',
                        current_date)+INTERVAL '1 MONTH - 1 day' as date)) and parent_state = 'posted' and company_id = {}""".format(partner_ids[0], company_id)
            else:
                query2 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id in (50053, 52048) and date between (select cast(date_trunc('month', current_date) as date)) and (cast(date_trunc('month',
                            current_date)+INTERVAL '1 MONTH - 1 day' as date)) and parent_state = 'posted' and company_id = {}""".format(partner_ids[0], company_id)

            self._cr.execute(query=query2)
            cm_sales = self._cr.fetchall()
            current_month_sales = cm_sales[0][0]
            # current_month_sales = 0
            # val = self.env['account.move.line'].search([('partner_id', '=', partner_ids)]).sum('credit')
            # val = self.env['account.move.line'].search([('partner_id', '=', partner_ids)]).credit
            # current_month_sale = sum(self.env['account.move.line'].search([('partner_id', '=', partner_ids)]).credit)

            # Last Month Sales
            if target_move == 'posted':
                query3 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id in (50053, 52048) and date between (select cast(date_trunc('month', current_date)-INTERVAL '1 MONTH' as date)) and (select cast(date_trunc('month',
                        current_date)-INTERVAL '1 MONTH'+INTERVAL '1 MONTH - 1 day' as date)) and parent_state = 'posted' and company_id = {}""".format(partner_ids[0], company_id)
            else:
                query3 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id in (50053, 52048) and date between (select cast(date_trunc('month', current_date)-INTERVAL '1 MONTH' as date)) and (select cast(date_trunc('month',
                        current_date)-INTERVAL '1 MONTH'+INTERVAL '1 MONTH - 1 day' as date)) and company_id = {}""".format(partner_ids[0], company_id)
            self._cr.execute(query=query3)
            last_month_sales = self._cr.fetchall()
            previous_month_sales = last_month_sales[0][0]

            # Last Previous Month Sales
            if target_move == 'posted':
                query4 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id in (50053, 52048) and date between (select cast(date_trunc('month', current_date)-INTERVAL '1 MONTH'-INTERVAL '1 MONTH' as date)) and (select cast(date_trunc('month',
                        current_date)-INTERVAL '1 MONTH'-INTERVAL '1 MONTH'+INTERVAL '1 MONTH - 1 day' as date)) and parent_state = 'posted' and company_id = {}""".format(partner_ids[0], company_id)
            else:
                query4 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id in (50053, 52048) and date between (select cast(date_trunc('month', current_date)-INTERVAL '1 MONTH'-INTERVAL '1 MONTH' as date)) and (select cast(date_trunc('month',
                        current_date)-INTERVAL '1 MONTH'-INTERVAL '1 MONTH'+INTERVAL '1 MONTH - 1 day' as date)) and company_id = {}""".format(partner_ids[0], company_id)
            self._cr.execute(query=query4)
            bm_sales = self._cr.fetchall()
            last_before_month_sales = bm_sales[0][0]

            # Collection Amount From Month to Date(without openning balance)
            if branch_id:
                collection_amt_query=sum(value.amount for value in self.env['account.payment'].search([]))
                collection_amt_query = """select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and  state='posted' and payment_date::date between '{}'::date and '{}'::date and branch_id = {} and company_id_new = {}""".format(
                    partner_ids[0], data['form']['date_from'], data['form']['date_to'], branch_id[0], self.env.company.id)
            else:
                collection_amt_query = """select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and  state='posted' and payment_date::date between '{}'::date and '{}'::date and company_id_new = {}""".format(
                    partner_ids[0], data['form']['date_from'], data['form']['date_to'], self.env.company.id)
            self._cr.execute(query=collection_amt_query)
            collection_amt_month_to_date_dt = self._cr.fetchall()
            collection_amt_month_to_date = collection_amt_month_to_date_dt[0][0]

            # Cheque amount in Cheque In Hand mode
            if branch_id:
                query5 = """select COALESCE(sum(amount),0::numeric) as amount from  account_payment where partner_id = {} and state in('draft', 'sent') and branch_id = {} and company_id_new = {} AND (initial_create_status is null or initial_create_status = false) """.format(
                    partner_ids[0], branch_id[0], company_id)
            else:
                query5 = """select COALESCE(sum(amount),0::numeric) as amount from  account_payment where partner_id = {} and state in('draft', 'sent') and company_id_new = {} AND (initial_create_status is null or initial_create_status = false) """.format(partner_ids[0], company_id)

            self._cr.execute(query=query5)
            check_in_hand = self._cr.fetchall()
            cheque_in_hand = check_in_hand[0][0]

            # Cheque amount in Sent to Bank mode
            if branch_id:
                sent_to_bank_query = """select COALESCE(sum(amount),0::numeric) as amount from  account_payment where partner_id = {} and  state='waiting_for_approval' and branch_id = {} and company_id_new = {} """.format(
                    partner_ids[0], branch_id[0], company_id)
            else:
                sent_to_bank_query = """select COALESCE(sum(amount),0::numeric) as amount from  account_payment where partner_id = {} and  state='waiting_for_approval' and company_id_new = {}""".format(partner_ids[0], company_id)

            self._cr.execute(query=sent_to_bank_query)
            sent_to_bank_amt_dt = self._cr.fetchall()
            sent_to_bank_amt = sent_to_bank_amt_dt[0][0]

            # Cheque amount in Dishonored mode
            if branch_id:
                query6 = """select (COALESCE(sum(amount),0::numeric) - COALESCE(sum(dishonor_balance_adjust_amt),0::numeric) )as amount from account_payment where partner_id = {} and  state='dishonored' and branch_id = {} and company_id_new = {} """.format(
                    partner_ids[0], branch_id[0], company_id)
            else:
                query6 = """select (COALESCE(sum(amount),0::numeric) - COALESCE(sum(dishonor_balance_adjust_amt),0::numeric) )as amount from account_payment where partner_id = {} and  state='dishonored' and company_id_new = {}""".format(partner_ids[0], company_id)
            self._cr.execute(query=query6)
            dishonured_check = self._cr.fetchall()
            dishonored_cheque = dishonured_check[0][0]

            # Cheque amount in Coming mode
            if branch_id:
                coming_cheque = """
                                    select COALESCE(sum(amount),0::numeric) as amount from account_payment ap
                                    left join batch_payment bp on ap.batch_payment_id = bp.id
                                    where ap.partner_id = {} and ap.state not in ('posted', 'dishonored') 
                                    and (bp.state = 'approve' or bp.state is null)
                                    and ap.effective_date between CURRENT_DATE+1 and CURRENT_DATE+15 and ap.branch_id = {} and company_id_new = {} """.format(
                    partner_ids[0], branch_id[0], company_id)
            else:
                coming_cheque = """
                                    select COALESCE(sum(amount),0::numeric) as amount from account_payment ap
                                    left join batch_payment bp on ap.batch_payment_id = bp.id
                                    where ap.partner_id = {} and ap.state not in ('posted', 'dishonored') 
                                    and (bp.state = 'approve' or bp.state is null)
                                    and ap.effective_date between CURRENT_DATE+1 and CURRENT_DATE+15 and company_id_new = {}""".format(
                    partner_ids[0], company_id)

            self._cr.execute(query=coming_cheque)
            com_cheque = self._cr.fetchall()
            coming_cheque_amt = com_cheque[0][0]
            #
            # # Cheque amount in Sent mode
            # clearing_cheque = """select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and state='sent'""".format(partner_ids[0])
            # self._cr.execute(query=clearing_cheque)
            # clear_cheque = self._cr.fetchall()
            # clearing_cheque_amt = clear_cheque[0][0]

            # Cheque amount not in Posted and Canceled mode
            if branch_id:
                clearing_cheque = """
                    select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and state not in ('init', 'posted', 'dishonored') 
                    and effective_date between CURRENT_DATE and CURRENT_DATE and branch_id = {} and company_id_new = {} """.format(partner_ids[0], branch_id[0], company_id)
            else:
                clearing_cheque = """
                    select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and state not in ('init', 'posted', 'dishonored') 
                    and effective_date between CURRENT_DATE and CURRENT_DATE and company_id_new = {} """.format(partner_ids[0], company_id)
            self._cr.execute(query=clearing_cheque)
            clear_cheque = self._cr.fetchall()
            clearing_cheque_amt = clear_cheque[0][0]

            # Collection Against Dishonor Amount
            if branch_id:
                dishonor_collection_query = """
                    select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and state = 'posted' and collection_reference = 'cheque_adjustment'
                    and branch_id = {} and company_id_new = {} """.format(partner_ids[0], branch_id[0], company_id)
            else:
                dishonor_collection_query = """
                    select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and state = 'posted' and collection_reference = 'cheque_adjustment'
                     and company_id_new = {} """.format(partner_ids[0], company_id)
            self._cr.execute(query=dishonor_collection_query)
            dishonor_collection_dt = self._cr.fetchall()
            dishonor_collection_amt = dishonor_collection_dt[0][0]

            # Additional Credit Limit
            # additional_credit_limit_qry = """
            #                     select sum(ammount) from additional_credit_limit where partner_id = {} and is_deducted = false and is_sheduled_update = true and
            #                     from_date between '{}' and '{}' and to_date between '{}' and '{}'""".format(
            #     partner_ids[0], from_date, to_date, from_date, to_date)
            additional_credit_limit_qry = """
                                select sum(ammount) from additional_credit_limit where partner_id = {} and is_deducted = false and is_sheduled_update = true""".format(partner_ids[0])
            self._cr.execute(query=additional_credit_limit_qry)
            additional_credit_limit_data = self._cr.fetchall()
            additional_credit_limit = additional_credit_limit_data[0][0]

            # In Word
            # words_val = num2words(self._sum_partner(data, partners[0],'debit - credit')+dishonured_check[0][0], lang='en').title()
            if data['form'].get('target_move') == 'all':
                words_val = num2words(self._sum_partner(data, partners[0],'debit - credit') + check_in_hand[0][0] + sent_to_bank_amt_dt[0][0], lang='en').title()
            else:
                words_val = num2words(
                    self._sum_partner(data, partners[0], 'debit - credit'), lang='en').title()
            print(words_val)

            #Credit Limit Days
            payment_term_query = """select apt.name from ir_property ip left join res_partner rp on ip.res_id = concat('res.partner,',rp.id)
            left join account_payment_term apt on ip.value_reference =concat('account.payment.term,',apt.id)
            where ip.name like '%property_payment%' and {}""".format(where_pay_partner_ids)
            self._cr.execute(query=payment_term_query)
            payment_days = self._cr.fetchall()
            payment_day = 0
            if len(payment_days) > 0:
                payment_day = payment_days[0][0]
            else:
                payment_day = str('0 days')
            print('payment - ',payment_days)



        else:
            crLimit=0.00
            current_month_sales=0.00
            previous_month_sales=0.00
            last_before_month_sales=0.00
            cheque_in_hand=0.00
            sent_to_bank_amt=0.00
            dishonored_cheque=0.00
            coming_cheque_amt=0.00
            clearing_cheque_amt=0.00
            words_val=0.00
            payment_day=0.00
            collection_amt_month_to_date=0.00
            additional_credit_limit = 0.00
            dishonor_collection_amt = 0.00


        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
            'credit_limit': crLimit,
            'security_money': security_money,
            'current_month_sale':current_month_sales,
            'last_month_sale':previous_month_sales,
            'mb_sales':last_before_month_sales,
            'check_in_hand':cheque_in_hand,
            'sent_to_bank_amt':sent_to_bank_amt,
            'dishonured_check':dishonored_cheque,
            'com_cheque':coming_cheque_amt,
            'clear_cheque':clearing_cheque_amt,
            'dishonor_collection':dishonor_collection_amt,
            'words_val':words_val,
            'payment_days':payment_day,
            'is_mis':is_mis_summery,
            'collection_amt_month_to_date':collection_amt_month_to_date,
            'additional_credit_limit':additional_credit_limit
        }