from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta

class CollectedChequeWithoutTreatmentWizard(models.TransientModel):
    _name = 'collected.cheque.without.treatment'

    date_start = fields.Date(string='Start Batch Approve Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Batch Approve Date', required=True, default=fields.Date.today)
    customer=fields.Many2many('res.partner', string='Customer')
    group=fields.Many2many('res.partner.category',string='Group')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),default=lambda self: self.env.user.company_id,required=True)
    location_ids = fields.Many2many('res.branch', string='Branch')
    def _get_companies(self):
        print(self.env.user)
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        print(allowed_companies)
        allowed_company = []
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    def get_report(self):
        data = self.read()[0]

        date_start = data['date_start']  # start_date from the corresponding id
        date_end = data['date_end']
        customer = data['customer']
        group = data['group']
        company_id = data['company_id']
        location_ids = data['location_ids']

        where_customer = "1=1"
        where_group = "1=1"
        where_company_id="1=1"
        where_branch_ids = "1=1"
        if group:
            where_group = " rpc.id in %s" % str(tuple(group)).replace(',)', ')')
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print("Group",where_group)

        if customer:
            where_customer = " rp.id in %s" % str(tuple(customer)).replace(',)', ')')
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print(where_customer)
        if company_id:

            where_company_id = "ap.company_id_new = {}".format(company_id[0])
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print(where_company_id)

        if location_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        #company _id should be added

        query = """ select rp.name as a_customer,ap.cheque_reference as a_cheque_number,ap.payment_date as a_rec_date, ap.effective_date as a_cheque_date, bk.bank_name as a_bank_name,
						ap.name as a_collection_no, sp.name a_sales_p, ap.amount as a_amount, rpc.name as a_group, rb.name
						from account_payment ap 
                        inner join res_partner rp on ap.partner_id=rp.id
                        inner join res_branch rb on ap.branch_id = rb.id
                        inner join bank_info_all_bank bk on bk.id = ap.bank_id
                        left join res_partner customer on customer.id = ap.partner_id
                        left join res_users ru on ru.id = customer.user_id
                        left join res_partner sp on sp.id = ru.partner_id
						left join res_partner_res_partner_category_rel as rl on ap.partner_id = rl.partner_id
						left join res_partner_category rpc on rpc.id = rl.category_id
                        where ap.state = 'draft' and (dishonor_count is null or dishonor_count = 0) and ap.cih_date::DATE between '{}'::DATE and '{}'::DATE
                        and {} and {} and {} and {} AND (initial_create_status is null or initial_create_status = false)""".format(date_start.strftime(DATETIME_FORMAT),
                                                              date_end.strftime(DATETIME_FORMAT), where_customer,
                                                              where_group, where_company_id, where_branch_ids)

        self._cr.execute(query)
        result = self._cr.fetchall()
        data = {
            'result': result,
            'date_start': date_start,
            'date_end': date_end,

        }
        return self.env.ref('accounting_report.collected_cheque_without_treatment_report').report_action(
            self, data=data)

    def get_excel_report(self):
        data = self.read()[0]

        date_start = data['date_start']  # start_date from the corresponding id
        date_end = data['date_end']
        customer = data['customer']
        group = data['group']
        company_id = data['company_id']
        location_ids = data['location_ids']

        where_customer = "1=1"
        where_group = "1=1"
        where_company_id = "1=1"
        where_branch_ids = "1=1"
        print(type(group))
        if group:
            where_group = " rpc.id in %s" % str(tuple(group)).replace(',)', ')')
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print("Group", where_group)

        if customer:
            where_customer = " rp.id in %s" % str(tuple(customer)).replace(',)', ')')
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print(where_customer)
        if company_id:
            where_company_id = "ap.company_id_new = {}".format(company_id[0])
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print(where_company_id)

        if location_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # company _id should be added
        query = """select rp.name as a_customer,ap.cheque_reference as a_cheque_number,ap.payment_date as a_rec_date, ap.effective_date as a_cheque_date, bk.bank_name as a_bank_name,
						ap.name as a_collection_no, sp.name a_sales_p, ap.amount as a_amount, rpc.name as a_group, rb.name
						from account_payment ap 
                        inner join res_partner rp on ap.partner_id=rp.id
                        inner join res_branch rb on ap.branch_id = rb.id
                        inner join bank_info_all_bank bk on bk.id = ap.bank_id
                        left join res_partner customer on customer.id = ap.partner_id
                        left join res_users ru on ru.id = customer.user_id
                        left join res_partner sp on sp.id = ru.partner_id
						left join res_partner_res_partner_category_rel as rl on ap.partner_id = rl.partner_id
						left join res_partner_category rpc on rpc.id = rl.category_id
                        where ap.state = 'draft' and (dishonor_count is null or dishonor_count = 0) and ap.cih_date::DATE between '{}'::DATE and '{}'::DATE
                        and {} and {} and {} and {} AND (initial_create_status is null or initial_create_status = false)""".format(date_start.strftime(DATETIME_FORMAT),
                                                              date_end.strftime(DATETIME_FORMAT), where_customer,
                                                              where_group, where_company_id, where_branch_ids)
        self._cr.execute(query)
        result = self._cr.fetchall()
        data = {
            'result': result,
            'date_start': date_start,
            'date_end': date_end,

        }
        return self.env.ref('accounting_report.collected_cheque_without_treatment_report_xls').report_action(
            self, data=data)

    #date_start.strftime(DATETIME_FORMAT),date_end.strftime(DATETIME_FORMAT),
    #ap.effective_date::DATE between '{}' and '{}' and
class CollectedChequeWithoutTreatmentGetValue(models.AbstractModel):
    _name= 'report.accounting_report.cheque_without_treatment_view'

    def _get_report_values(self, docids, data=None):
        if 'date_start' in data.keys():
            date_start = data['date_start']
            date_end = data['date_end']
        else :
            date_start = data['star_date']
            date_end = data['end_date']

        results = data['result']
        buyer_dict = dict()
        # for result in results:
        #     if result[8] not in buyer_dict.keys():
        #         if result[0]not in buyer_dict.keys():# result[2] is 'buyer_category' in sql
        #             buyer_dict[result[0]] = list()
        #             buyer_dict[result[0]].append(result)
        #         else:
        #             buyer_dict[result[0]].append(result)
        #     else:
        #         buyer_dict[result[8]].append(result)
        # print(buyer_dict)
        for result in data['result']:
            if result[8] not in buyer_dict.keys():  # for the first time for vendor/production etc create a dictionary by creating a key which is 'buyer_group'
                buyer_dict[result[8]] = dict()  # create a new dictionary inside current dictionary in this index
            if result[0] not in buyer_dict[result[8]].keys():  # check this item inside the dictionary of dictionary,then create a list inside the dictionary of dictionary
                buyer_dict[result[8]][result[0]] = list()
                buyer_dict[result[8]][result[0]].append(result)  # append items inside the list under the dictionary of dictionary
            else:
                buyer_dict[result[8]][result[0]].append(result)  # if the dictionary and list already created on this

        return {
            'group_value': results,
            'date_start': date_start,
            'date_end': date_end,
            'data': buyer_dict,

        }