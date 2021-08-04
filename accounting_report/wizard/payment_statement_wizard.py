# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class CollectionStatementReportWizard(models.TransientModel):
    _name = 'accounting.payment.report.wizard'

    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),default=lambda self: self.env.user.company_id,required=True)
    branch_ids = fields.Many2one('res.branch', string='Branch')
    payment_method = fields.Many2one('account.payment.method', string='Payment Method')

    def _get_companies(self):
        print(self.env.user)
        query="""select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies=self._cr.fetchall()
        print(allowed_companies)
        allowed_company=[]
        for company in allowed_companies:
            allowed_company.append(company[0])
        return  [('id', 'in', allowed_company)]

    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end,'company_id':self.company_id.id, 'branch_id': self.branch_ids.id,
                'branch_name': self.branch_ids.name, 'payment_method': self.payment_method.id,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('accounting_report.account_payment_statement_report').report_action(
            self, data=data)

    def get_excel_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_id': self.branch_ids.id,
                'branch_name': self.branch_ids.name, 'payment_method': self.payment_method.id,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('accounting_report.account_payment_statement_report_xls').report_action(
            self, data=data)


class CollectionStatementReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.accounting_report.payment_statement_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        branch_name = data['form']['branch_name']
        payment_method = data['form']['payment_method']
        company_id = data['form']['company_id']

        if payment_method:
            payment_method = " ap.payment_method_id  = %s" % payment_method
        else:
            payment_method = "1=1"

        if branch_id:
            branch_id = " ap.branch_id = %s" % branch_id

        else:
            branch_id = "1=1"

        if company_id:
            company_id = " am.company_id = %s" % company_id

        else:
            company_id = "1=1"

        query = """
            select to_char(ap.create_date,'DD-MON-YYYY') create_date, aj.name as payment_type, pm.name as paymentMethod, res_p.name as buyer, e.name as sales_person, ap.move_name as money_recipt, e.name as collected_by, ap.communication as invoice_no, ap.amount as collected_amount,ap.branch_id,br.name as branch_name  
            from account_payment ap 
            left join account_move am  on ap.move_name = am.name
            left join hr_employee eap on ap.create_uid = eap.user_id
            left join res_partner res_p on am.partner_id = res_p.id
            left join account_journal aj on ap.journal_id = aj.id
            left join account_payment_method pm on ap.payment_method_id = pm.id
            left join account_move amc on ap.communication = amc.invoice_payment_ref
            left join hr_employee e on amc.create_uid = e.user_id
            left join res_branch br on br.id=ap.branch_id
            where ap.payment_type = 'outbound'  and ap.partner_type <> 'customer' and ap.state='posted' and {} and {}  and ap.create_date::date between '{}' and '{}' and {}
            ORDER BY ap.create_date,br.name
            """.format(branch_id,company_id, date_start, date_end, payment_method)
        # else:
        #     query = """
        #     select ap.create_date, aj.name as payment_type, pm.name as paymentMethod, res_p.name as buyer, e.name as sales_person, ap.move_name as money_recipt, e.name as collected_by, ap.communication as invoice_no, ap.amount as collected_amount,ap.branch_id,br.name as branch_name
        #      from account_payment ap
        #     left join account_move am  on ap.move_name = am.name
        #     left join hr_employee eap on ap.create_uid = eap.user_id
        #     left join res_partner res_p on am.partner_id = res_p.id
        #     left join account_journal aj on ap.journal_id = aj.id
        #     left join account_payment_method pm on ap.payment_method_id = pm.id
        #     left join account_move amc on ap.communication = amc.invoice_payment_ref
        #     left join hr_employee e on amc.create_uid = e.user_id
        #     left join res_branch br on br.id=ap.branch_id
        #     where ap.payment_type = 'outbound' and ap.partner_type <> 'customer' and ap.state='posted' and ap.create_date::date between '{}' and '{}' and {}
        #     ORDER BY ap.create_date
        #     """.format(date_start, date_end, payment_method)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        # collection_statements = dict()
        # for collection in query_result:
        #     print(collection[10])
        #     collection_date = str(collection[0].date())
        #     if collection[10] not in collection_statements.keys():
        #         collection_statements[collection[10]]=dict()
        #     if collection_date not in collection_statements[collection[10]].keys():
        #         collection_statements[collection[10]][collection_date] = dict()
        #     if collection[2] not in collection_statements[collection[10]][collection_date].keys():
        #         collection_statements[collection[10]][collection_date][collection[2]] = dict()
        #     if collection[1] in collection_statements[collection[10]][collection_date][collection[2]].keys():
        #         collection_statements[collection[10]][collection_date][collection[2]][collection[1]].append(collection)
        #     else:
        #         collection_statements[collection[10]][collection_date][collection[2]][collection[1]] = list()
        #         collection_statements[collection[10]][collection_date][collection[2]][collection[1]].append(collection)
        collection_statements = dict()
        for collection in query_result:
            print(collection[10])
            print(collection[0])
            collection_date = collection[0]
            if collection_date not in collection_statements.keys():
                collection_statements[collection_date] = dict()
            if collection[10] not in collection_statements[collection_date].keys():
                collection_statements[collection_date][collection[10]] = dict()
            if collection[2] not in collection_statements[collection_date][collection[10]].keys():
                collection_statements[collection_date][collection[10]][collection[2]] = dict()
            if collection[1] in collection_statements[collection_date][collection[10]][collection[2]].keys():
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]].append(collection)
            else:
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]] = list()
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]].append(collection)
        print(collection_statements)

        total_collection = dict()
        date_wise_payment_method = dict()
        branch_wise_payment_method=dict()

        # for single_collection in query_result:
        #     # print(single_collection)
        #     # Date wise payment
        #     collection_date = str(single_collection[0].date())
        #     if collection_date not in date_wise_payment_method.keys():
        #         date_wise_payment_method[collection_date] = dict()
        #
        #     if single_collection[2] not in date_wise_payment_method[collection_date].keys():
        #         date_wise_payment_method[collection_date][single_collection[2]] = single_collection[-3]
        #     else:
        #         date_wise_payment_method[collection_date][single_collection[2]] += single_collection[-3]
        #
        #     # branch wise payment
        #     br_name=str(single_collection[10])
        #     if br_name not in branch_wise_payment_method.keys():
        #         branch_wise_payment_method[br_name]=dict()
        #     if single_collection[2] not in branch_wise_payment_method[br_name].keys():
        #         branch_wise_payment_method[br_name][single_collection[2]]=single_collection[-3]
        #     else:
        #         branch_wise_payment_method[br_name][single_collection[2]] += single_collection[-3]
        #
        #     # total payment
        #     if single_collection[2] not in total_collection.keys():
        #         total_collection[single_collection[2]] = single_collection[-3]
        #     else:
        #         total_collection[single_collection[2]] += single_collection[-3]

        for single_collection in query_result:
            collection_date = single_collection[0]

            # branch wise payment
            if single_collection[10] not in branch_wise_payment_method.keys():
                branch_wise_payment_method[single_collection[10]] = dict()

            if collection_date not in branch_wise_payment_method[single_collection[10]].keys():
                branch_wise_payment_method[single_collection[10]][collection_date] = dict()

            if single_collection[2] not in branch_wise_payment_method[single_collection[10]][collection_date].keys():
                branch_wise_payment_method[single_collection[10]][collection_date][single_collection[2]] = \
                    single_collection[-3]
            else:
                branch_wise_payment_method[single_collection[10]][collection_date][single_collection[2]] += \
                    single_collection[-3]
            if collection_date not in date_wise_payment_method.keys():
                date_wise_payment_method[collection_date] = dict()
            if single_collection[2] not in date_wise_payment_method[collection_date].keys():
                date_wise_payment_method[collection_date][single_collection[2]] = single_collection[-3]
            else:
                date_wise_payment_method[collection_date][single_collection[2]] += single_collection[-3]

            # total payment
            if single_collection[2] not in total_collection.keys():
                total_collection[single_collection[2]] = single_collection[-3]
            else:
                total_collection[single_collection[2]] += single_collection[-3]

        # print(date_wise_payment_method)
        # print(total_collection)
        # for key, value in total_collection.items():
        #     print(key, value)

        # for date, date_value in collection_statements.items():
        #     print(date)
        #     for p_type, p_type_value in date_value.items():
        #         total_collection[p_type] = 0
        #         print(p_type)
        #         for journal, journal_value in p_type_value.items():
        #             print(journal)
        #             for c in journal_value:
        #                 print(c)

        return {
            'date_start': date_start,
            'date_end': date_end,
            'branch': branch_name,
            'collection_statements': collection_statements,
            'date_wise_payment_method': date_wise_payment_method,
            'total_collection': total_collection,
            'username': self.env.user.name,
            'branch_wise_payment_method':branch_wise_payment_method,
        }
