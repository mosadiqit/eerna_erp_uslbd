from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class ForeignPurchaseCosting(models.TransientModel):
    _name = 'foreign.costing.report'

    start_date = fields.Date(string="PO From Date", required=True)
    end_date = fields.Date(string="PO To Date", required=True)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    foreign_purchase_order_id = fields.Many2one('foreign.purchase.order', string='Purchase Order', required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True)

    @api.onchange('start_date', 'end_date')
    @api.depends('start_date', 'end_date')
    def related_FPO(self):

        if isinstance(self.start_date, date) and isinstance(self.end_date, date):
            # start_date = datetime.strptime(self.start_date, DATE_FORMAT)
            # end_date = datetime.strptime(self.end_date, DATE_FORMAT)
            end_date = (self.end_date+ relativedelta(days=+ 1))
            query = """select id from foreign_purchase_order where create_date between '{}' and '{}'""".format(
                self.start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT))
            self._cr.execute(query=query)
            get_result = self._cr.fetchall()
            get_all_ids = []
            for rec in get_result:
                get_all_ids.append(rec[0])
            return {'domain': {'foreign_purchase_order_id': [('id', 'in', get_all_ids)]}}
        else:
            return {'domain': {'foreign_purchase_order_id': [('id', 'in', [])]}}

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        allowed_company = []
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    @api.onchange('foreign_purchase_order_id')
    def related_invoices(self):
        get_result = self.env['account.move'].search([('invoice_origin', '=', self.foreign_purchase_order_id.name)])
        return {'domain': {
            'invoice_id': [('id', 'in', get_result.ids), ('type', '=', 'in_invoice'), ('name', 'not like', 'STJ')]}}

    def print_costing_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'start_date': self.start_date, 'end_date': self.end_date, 'company_id': self.company_id.id,
                'foreign_purchase_order_id': self.foreign_purchase_order_id.id, 'invoice_id': self.invoice_id.id
            },
        }
        print('data is', data)
        return self.env.ref('usl_foreign_purchase.foreign_costing_report').report_action(
            self, data=data)


class ReportForignCostingReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.usl_foreign_purchase.costing_report_view'



    def _get_report_values(self, docids, data=None):
        date_start = data['form']['start_date']
        date_end = data['form']['end_date']
        company_id = data['form']['company_id']
        foreign_purchase_order_id = data['form']['foreign_purchase_order_id']
        invoice_id = data['form']['invoice_id']


        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        date = (end_date + relativedelta(days=+ 1))
        default_currency_id=self.env.ref('base.main_company').currency_id.id
        bank_rate=self.env['res.currency.rate'].search([('currency_id','=',default_currency_id)]).rate
        local_rate=self.env.ref('base.main_company').currency_id.local_currency
        default_currency_id = self.env.ref('base.main_company').currency_id.id
        bank_rate = self.env['res.currency.rate'].search([('currency_id', '=', default_currency_id)]).rate
        local_rate = self.env.ref('base.main_company').currency_id.local_currency
        query="""select slc.write_date::date as costing_date,slc.name as lc_no,am.name as invoice_no,am.invoice_origin as purchase_order_no
                    from stock_landed_cost slc
                    left join account_move am on am.id=slc.vendor_bill_id
                    where slc.vendor_bill_id={}""".format(invoice_id)
        self._cr.execute(query=query)
        get_master_data=self._cr.fetchone()

        # query = """select  rc.name as currency_name,am.create_date,pt.name as item_name,aml.quantity as quantity,aml.bank_payment as ci_single_price_bank_payment,
        #         (aml.bank_payment*aml.quantity) as ci_multiple_price_bank_payment,aml.local_payment as ci_single_price_local_payment,
        #         (aml.local_payment*aml.quantity) as ci_multiple_price_local_payment
        #         from stock_landed_cost slc
        #         left join stock_landed_cost_lines slcl on slcl.cost_id=slc.id
        #         left join account_move am on am.id=slc.vendor_bill_id
        #         left join account_move_line aml on aml.move_id=am.id
        #         left join product_product pp on pp.id=aml.product_id
        #         left join product_template pt on pt.id=pp.product_tmpl_id
        #         left join res_currency rc on rc.id=am.currency_id
        #         where slc.vendor_bill_id={} and aml.account_internal_type='other' and am.company_id={}  and aml.product_id=slcl.product_id""".format(invoice_id,company_id)
        # print(query)
        # self._cr.execute(query=query)
        # get_commercial_invoice=self._cr.fetchall()
        # get_commercial_invoice_new=[]
        # for line in get_commercial_invoice:
        #     line_list=list(line)
        #     line_list.insert(8,(line[4]*bank_rate))
        #     line_list.insert(9, (line[5] * bank_rate))
        #     line_list.insert(10, (line[6] * local_rate))
        #     line_list.insert(11, (line[7] * local_rate))
        #     line_tuple = tuple(line_list)
        #     get_commercial_invoice_new.append(line_tuple)
        # query="""select  pt.name as item_name,aml.quantity as quantity,COALESCE((slcl.cd/aml.quantity),0) as custom_duty_single_price,COALESCE(slcl.cd,0) as custom_duty_total_price,
        #             COALESCE((slcl.at/aml.quantity),0) as at_single_price,COALESCE(slcl.at,0) as at_total_price,
        #             COALESCE((slcl.ait/aml.quantity),0) as ait_single_price,COALESCE(slcl.ait,0) as ait_total_price,
        #             COALESCE((slcl.df/aml.quantity),0) as df_single_price,COALESCE(slcl.df,0) as df_total_price,
        #             COALESCE((slcl.cf/aml.quantity),0) as cf_single_price,COALESCE(slcl.cf,0) as cf_total_price,
        #             COALESCE((slcl.transport/aml.quantity),0) as transport_single_price,COALESCE(slcl.transport,0) as transport_total_price,
        #             COALESCE((slcl.freight/aml.quantity),0) as freight_single_price,COALESCE(slcl.freight,0) as freight_total_price,
        #             COALESCE((slcl.insurance/aml.quantity),0) as insurance_single_price,COALESCE(slcl.insurance,0) as insurance_total_price,
        #             COALESCE((slcl.lc_commision/aml.quantity),0) as lc_commision_single_price,COALESCE(slcl.lc_commision,0) as lc_commision_total_price,
        #             COALESCE((slcl.lc_vat/aml.quantity),0) as lc_vat_single_price,COALESCE(slcl.lc_vat,0) as lc_vat_total_price,
        #             COALESCE((slcl.port_demarrage/aml.quantity),0) as port_demarrage_single_price,COALESCE(slcl.port_demarrage,0) as port_demarrage_total_price,
        #             COALESCE((slcl.other/aml.quantity),0) as other_single_price,COALESCE(slcl.other,0) as other_total_price,
        #             COALESCE((slcl.provision_for_warranty_cost/aml.quantity),0) as provision_for_warranty_cost_single_price,COALESCE(slcl.provision_for_warranty_cost,0) as provision_for_warranty_cost_total_price,
        #             COALESCE((slcl.provision_for_marketting_expenses/aml.quantity),0) as provision_for_marketting_expenses_single_price,COALESCE(slcl.provision_for_marketting_expenses,0) as provision_for_marketting_expenses_total_price,
        #             COALESCE((slcl.provision_for_salary/aml.quantity),0) as provision_for_salary_single_price,COALESCE(slcl.provision_for_salary,0) as provision_for_salary_total_price,
        #             COALESCE((slcl.provision_for_bank_interest/aml.quantity),0) as provision_for_bank_interest_single_price,COALESCE(slcl.provision_for_bank_interest,0) as provision_for_bank_interest_total_price,
        #             COALESCE((slcl.provision_for_product_insurance/aml.quantity),0) as provision_for_product_insurance_single_price,COALESCE(slcl.provision_for_product_insurance,0) as provision_for_product_insurance_total_price,
        #             COALESCE((slcl.provision_for_income_tax/aml.quantity),0) as provision_for_income_tax_single_price,COALESCE(slcl.provision_for_income_tax,0) as provision_for_income_tax_total_price,
        #             COALESCE((slcl.provision_for_trade_promotion/aml.quantity),0) as provision_for_trade_promotion_single_price,COALESCE(slcl.provision_for_trade_promotion,0) as provision_for_trade_promotion_total_price,
        #             COALESCE((slcl.provision_for_dollar_risk/aml.quantity),0) as provision_for_dollar_risk_single_price,COALESCE(slcl.provision_for_dollar_risk,0) as provision_for_dollar_risk_total_price,
        #             COALESCE((slcl.provision_for_sadaqua/aml.quantity),0) as provision_for_sadaqua_single_price,COALESCE(slcl.provision_for_sadaqua,0) as provision_for_sadaqua_total_price,
        #             COALESCE((slcl.provision_for_sales_courier/aml.quantity),0) as provision_for_sales_courier_single_price,COALESCE(slcl.provision_for_sales_courier,0) as provision_for_sales_courier_total_price,
        #             COALESCE((slcl.provision_for_house_rent/aml.quantity),0) as provision_for_house_rent_single_price,COALESCE(slcl.provision_for_house_rent,0) as provision_for_house_rent_total_price,
        #             COALESCE((slcl.provision_for_opex/aml.quantity),0) as provision_for_opex_single_price,COALESCE(slcl.provision_for_opex,0) as provision_for_opex_total_price,
        #             COALESCE((slcl.provision_for_damage_goods/aml.quantity),0) as provision_for_damage_goods_single_price,COALESCE(slcl.provision_for_damage_goods,0) as provision_for_damage_goods_total_price,
        #             COALESCE((slcl.provision_for_ta_da/aml.quantity),0) as provision_for_ta_da_single_price,COALESCE(slcl.provision_for_ta_da,0) as provision_for_ta_da_total_price,
        #             COALESCE((slcl.provision_for_bad_debt/aml.quantity),0) as provision_for_bad_debt_single_price,COALESCE(slcl.provision_for_bad_debt,0) as provision_for_bad_debt_total_price,
        #             COALESCE(aml.bank_payment,0) as bank_payment,
        #             COALESCE(aml.local_payment,0) as local_payment,
        #             COALESCE(spc.product_average_price,0) as product_average_price
        #             from stock_landed_cost slc
        #             left join stock_landed_cost_lines slcl on slcl.cost_id=slc.id
        #             left join stock_preview_costing spc on spc.cost_id=slc.id
        #             left join account_move am on am.id=slc.vendor_bill_id
        #             left join account_move_line aml on aml.move_id=am.id
        #             left join product_product pp on pp.id=aml.product_id
        #             left join product_template pt on pt.id=pp.product_tmpl_id
        #             where slc.vendor_bill_id={} and aml.account_internal_type='other' and am.company_id={}  and aml.product_id=slcl.product_id and spc.product_id=slcl.product_id
        #
        #             """.format(invoice_id,company_id)
        # print(query)
        # self._cr.execute(query=query)
        # get_all_cost_line=self._cr.fetchall()

        # cost_line_array=[]
        # for line in get_commercial_invoice:
        #     line_list=list(line)
        #     line_list.insert(8,(line[4]*bank_rate))
        #     line_list.insert(9, (line[5] * bank_rate))
        #     line_list.insert(10, (line[6] * local_rate))
        #     line_list.insert(11, (line[7] * local_rate))
        #     line_tuple = tuple(line_list)
        #     get_commercial_invoice_new.append(line_tuple)


        query="""select  rc.name as currency_name,am.create_date,pt.name as item_name,aml.quantity as quantity,aml.bank_payment as ci_single_price_bank_payment,
                (aml.bank_payment*aml.quantity) as ci_multiple_price_bank_payment,aml.local_payment as ci_single_price_local_payment,
                (aml.local_payment*aml.quantity) as ci_multiple_price_local_payment
                from stock_landed_cost slc                
                left join account_move am on am.id=slc.vendor_bill_id
                left join account_move_line aml on aml.move_id=am.id
                left join product_product pp on pp.id=aml.product_id
                left join product_template pt on pt.id=pp.product_tmpl_id
                left join res_currency rc on rc.id=am.currency_id
                where slc.vendor_bill_id={} and aml.account_internal_type='other' and am.company_id={}""".format(invoice_id,company_id)
        self._cr.execute(query=query)
        get_commercial_invoice=self._cr.fetchall()
        get_commercial_invoice_new=[]
        for line in get_commercial_invoice:
            line_list=list(line)
            line_list.insert(8,(line[4]*bank_rate))
            line_list.insert(9, (line[5] * bank_rate))
            line_list.insert(10, (line[6] * local_rate))
            line_list.insert(11, (line[7] * local_rate))
            line_tuple = tuple(line_list)
            get_commercial_invoice_new.append(line_tuple)
        # print(get_commercial_invoice_new)
        query="""select aml.product_id from account_move am
                left join  account_move_line aml on aml.move_id=am.id where am.id={} and
                aml.account_internal_type='other' 
                and am.company_id={}""".format(invoice_id,company_id)
        self._cr.execute(query=query)
        get_invoice_product=self._cr.fetchall()
        # query="""select slcl.name as cost_line_name,pt.name as product_name,aml.quantity as quantity,slcl.price_unit as total_ci_price_bdt,rc.name as currency_name,
        #         ptt.probational_cost_ok as is_provision, ptt.landed_cost_ok as is_landed,pas.percentage as percentage,sval.former_cost as bank_payment,
        #         (aml.local_payment*aml.quantity) as local_payment,aml.product_id as product_id from stock_landed_cost slc
        #         left join stock_valuation_adjustment_lines sval on sval.cost_id=slc.id
        #         left join stock_landed_cost_lines slcl on slcl.id=sval.cost_line_id
        #         left join account_move am on am.id=slc.vendor_bill_id
        #         left join account_move_line aml on aml.move_id=am.id
        #         left join product_product pp on pp.id=aml.product_id
        #         left join product_template pt on pt.id=pp.product_tmpl_id
        #         left join product_product ppp on ppp.id=slcl.product_id
        #         left join product_template ptt on ptt.id=ppp.product_tmpl_id
        #         left join probational_attribute_setup pas on pas.probational_product_id=ptt.id
        #         left join res_currency rc on rc.id=am.currency_id where slc.vendor_bill_id={}
        #         and aml.account_internal_type='other'
        #         and am.company_id={}""".format(invoice_id,company_id)
        query="""select  slcl.name as cost_line_name,pt.name as product_name,aml.quantity as quantity,slcl.price_unit as total_ci_price_bdt,rc.name as currency_name,
                ptt.probational_cost_ok as is_provision, ptt.landed_cost_ok as is_landed,sval.former_cost as bank_payment,
                (aml.local_payment*aml.quantity) as local_payment,aml.product_id as product_id,slcl.id from stock_landed_cost slc 
                left join stock_valuation_adjustment_lines sval on sval.cost_id=slc.id
                left join stock_landed_cost_lines slcl on slcl.id=sval.cost_line_id
                left join account_move am on am.id=slc.vendor_bill_id
                left join account_move_line aml on aml.move_id=am.id 
                left join product_product pp on pp.id=aml.product_id
                left join product_template pt on pt.id=pp.product_tmpl_id
                 left join product_product ppp on ppp.id=slcl.product_id
                  left join product_template ptt on ptt.id=ppp.product_tmpl_id
-- 				left join probational_attribute_setup pas on pas.probational_product_id=pt.id
                left join res_currency rc on rc.id=am.currency_id where slc.vendor_bill_id={}  
                and aml.account_internal_type='other' 
                and am.company_id={} and aml.product_id=sval.product_id order by slcl.id""".format(invoice_id,company_id)
        print(query)
        self._cr.execute(query=query)
        get_all_cost_line=self._cr.fetchall()
        get_all_cost_line_new=[]
        product_wise_total_landed_cost=dict()


        for inv_product in get_invoice_product:
            total = 0
            for line in get_all_cost_line:
                # for invoice_product in get_invoice_product:
                if  line[6]==True and inv_product[0]==line[9]:
                    total+=line[3]
                    if line[9] not in product_wise_total_landed_cost.keys():
                        product_wise_total_landed_cost[line[9]]=total
                    else:
                        product_wise_total_landed_cost[line[9]] = total

                # else:
                #
                #     else:
                #         product_wise_total_landed_cost[line[10]]=list()
                #         product_wise_total_landed_cost[line[10]].append(total)
                #         total=0
        cost_line_after_product_wise_provision=[]
        for product in product_wise_total_landed_cost:
            for line in get_all_cost_line:
                if line[9]==product:
                    if line[5]!=True:
                        line_list = list(line)
                        line_list.insert(10, 0)
                        line_list.insert(11, (line[8] * local_rate))
                        line_list.insert(12, product_wise_total_landed_cost[product])
                        line_tuple = tuple(line_list)
                        # cost_line_after_product_wise_provision.append(line_tuple)
                    if line[5]==True:
                        line_list = list(line)
                        line_list.insert(10, ((line[3]/(product_wise_total_landed_cost[product]+(line[7]+line[8]*local_rate)))*100))
                        line_list.insert(11, (line[8] * local_rate))
                        line_list.insert(12, product_wise_total_landed_cost[product])
                        line_tuple = tuple(line_list)
                    cost_line_after_product_wise_provision.append(line_tuple)



        print(cost_line_after_product_wise_provision)
        cost_line_dict=dict()
        for cost_line in cost_line_after_product_wise_provision:
            if cost_line[0] not in cost_line_dict.keys():
                cost_line_dict[cost_line[0]]=dict()
            if cost_line[6] in cost_line_dict[cost_line[0]].keys():
                cost_line_dict[cost_line[0]][cost_line[6]].append(cost_line)
            else:
                cost_line_dict[cost_line[0]][cost_line[6]]=list()
                cost_line_dict[cost_line[0]][cost_line[6]].append(cost_line)
        print(cost_line_dict)
        product_wise_provision=dict()
        for product in cost_line_after_product_wise_provision:
            if product[1]  in product_wise_provision.keys():
                product_wise_provision[product[1]].append(product)
            else:
                product_wise_provision[product[1]]=list()
                product_wise_provision[product[1]].append(product)


        print(product_wise_provision)
        # query = """
        #     select sp.name as reference_name,sl.complete_name as from_branch,sl1.complete_name as to_branch, sp.create_date,sp.id,sp.state from stock_picking sp
        #     left join stock_location sl on sl.id=sp.location_id
        #     left join stock_location sl1 on sl1.id=sp.location_dest_id
        #     left join stock_picking_type spt on spt.id=sp.picking_type_id
        #     where {} and {} and  sp.date between '{}' and '{}' and sp.state = '{}' and spt.sequence_code='{}' and sp.company_id={} order by sp.create_date asc
        #     """.format(where_from_branch_id, where_to_branch_id, start_date.strftime(DATETIME_FORMAT),
        #                date.strftime(DATETIME_FORMAT), "done", "INT", company_id)
        #
        # self._cr.execute(query=query)
        # query_result = self._cr.fetchall()
        #
        # collection_statements = dict()
        #
        # for collection in query_result:
        #     create_date = collection[3].date()
        #     if create_date in collection_statements.keys():
        #         collection_statements[create_date].append(collection)
        #     else:
        #         collection_statements[create_date] = list()
        #         collection_statements[create_date].append(collection)
        # print(collection_statements)
        # all_product_based_move_id = []
        # for get_product in query_result:
        #     picking_id = get_product[4]
        #     query = """select sml.product_id,pt.name,sp.id,sum(sml.qty_done) from stock_picking sp
        #
        #             left join stock_move_line sml on sml.picking_id=sp.id
        #             left join product_product pp on pp.id=sml.product_id
        #             left join product_template pt on pt.id= pp.product_tmpl_id
        #             where sp.id={} group by sml.product_id,pt.name,sp.id,sml.qty_done """.format(picking_id)
        #
        #     self._cr.execute(query=query)
        #     q_result = self._cr.fetchall()
        #     for res in q_result:
        #         print(res)
        #         all_product_based_move_id.append(res)
        # print(all_product_based_move_id)
        #
        # filtered_by_date_branch = list()
        # # for collection in query_result:
        # #     filtered_by_date_branch.append(collection)
        # # filtered_by_date_branch1 = list(SO.search([
        # #     ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
        # #     ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
        # #     # ('location_id','=',branch),
        # #     ('state', 'in', ['done'])
        # #
        # # ]))
        # total_orders = len(filtered_by_date_branch)
        # # amount_total = sum(order.amount_total for order in filtered_by_date_branch)
        # allsale = []
        # allsale = filtered_by_date_branch
        # print(allsale)
        #
        # docs.append({
        #     'date': start_date.strftime("%Y-%m-%d"),
        #     'total_orders': total_orders,
        #     # 'amount_total': amount_total,
        #     'company': self.env.user.company_id,
        #
        # })
        #

        # ****************************************Final cost_line_dict format***************************************
        # custom_duty_product - ---0: 'Provision For Maeketting Expenses',
        # invoice_product - -------1: 'pp-16',
        # quantity - --------------2: 50.0,
        # price_unit - ------------3: 18250.0,
        # currency - --------------4: 'USD',
        # probational_cost_ok - ---5: True,
        # landed_cost_ok - --------6: False,
        # bank_payment - ----bdt --7: 0.0,
        # local_payment - ---usd --8: 10000.0,
        # custom_duty_product_id --9: 10586,
        # percentage - -----------10: 2.0,
        # local_payment-----bdt---11: 900000.0,
        # landed_cost - ----------12: 12500.0
        # ****************************************Final cost_line_dict format***************************************
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_date,
            'date_end': end_date,
            'master_data':get_master_data,
            'get_commercial_invoice':get_commercial_invoice_new,
            'get_all_cost_line':cost_line_dict,
            'product_wise_provision':product_wise_provision,
            'bank_rate':bank_rate,
            'local_rate':local_rate,



        }
