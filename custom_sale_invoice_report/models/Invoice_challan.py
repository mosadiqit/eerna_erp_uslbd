from odoo import api, fields, models


class ReportInvoiceChallan(models.AbstractModel):
    _name = "report.custom_sale_invoice_report.report_invoice_challan"

    @api.model
    def _get_report_values(self, docids, data=None):

        # all_entries="""select  aml.price_unit,aml.id,aml.product_id,aml.quantity from account_move_line aml
        #                  left join account_tax at on at.id=aml.tax_line_id where aml.move_id={} and aml.account_root_id={} order by aml.product_id asc""".format(docids[0], 52048)
        # self._cr.execute(query=all_entries)
        # all_entries_res = self._cr.fetchall()
        print(docids[0])
        product_lot="""select stml.product_id,prd.name from account_move accm
                        left join stock_move stm on stm.origin=accm.invoice_origin
                        left join stock_move_line stml on stml.move_id=stm.id
                        left join stock_production_lot prd on prd.id=stml.lot_id
                        Where accm.id={}""".format(docids[0])
        self._cr.execute(query=product_lot)
        all_lot=self._cr.fetchall()




        all_entries = """select  aml.product_id,pt.name,pt.warranty,aml.price_unit,aml.quantity,rc.symbol,am.narration from account_move_line aml
                         left join account_tax at on at.id=aml.tax_line_id 
						 left join product_product pp on pp.id=aml.product_id
						 left join product_template pt on pt.id=pp.product_tmpl_id 
						 left join account_move am on am.id=aml.move_id
						 left join res_currency rc on rc.id=am.currency_id
						 where aml.move_id={} and aml.account_root_id={} and aml.name not like '{}' and aml.name not like '{}'  order by aml.create_date asc""".format(
            docids[0], 52048,'%VAT%','%TAX%')
        self._cr.execute(query=all_entries)
        all_entries_res = self._cr.fetchall()
        print(all_entries)

        all_vat_entries="""select  aml.price_unit,aml.id,aml.product_id,at.description from account_move_line aml
                         left join account_tax at on at.id=aml.tax_line_id where aml.move_id={} and aml.name like '{}' order by aml.create_date asc""".format(docids[0], '%VAT%')
        self._cr.execute(query=all_vat_entries)
        all_vat_entries_res = self._cr.fetchall()
        print(all_vat_entries_res)
        final_res=[]
        count=0
        for a_e in all_entries_res:
            count = 0
            for a_v_e in all_vat_entries_res:

                if count==1:
                    continue
                if a_e[0]==a_v_e[2]:
                    vat_amount = a_v_e[0] / a_e[4]
                    a_e=list(a_e)
                    a_e.insert(7,a_v_e[0])
                    # vat=a_v_e[3].split('%')
                    # vat_value=a_v_e[0]
                    new_unit_price=a_e[3]
                    new_amount=new_unit_price*a_e[4]
                    a_e.insert(8,a_v_e[3])
                    a_e.insert(9,new_unit_price)
                    a_e.insert(10, new_amount)
                    final_res.append(tuple(a_e))
                    count+=1


            if count==0:
                a_e = list(a_e)
                a_e.insert(7, 0)
                a_e.insert(8,'0%')
                new_unit_price = a_e[3]
                new_amount = new_unit_price * a_e[4]
                a_e.insert(9, new_unit_price)
                a_e.insert(10, new_amount)
                final_res.append(tuple(a_e))
        print(final_res)

        after_lot_add_final_result = []
        for all_result in final_res:
            lot_string = ""
            for lot_result in all_lot:
                if all_result[0] == lot_result[0]:
                    if lot_result[1] != None:
                        lot_string += lot_result[1] + ', '

            as_list = list(all_result)
            # as_list[1] = as_list[1] + '/n' + lot_string
            as_list.insert(11,lot_string)
            after_lot_add_final_result.append(tuple(as_list))
            # as_tuple = tuple(as_list)
            # print(as_tuple)

        print(after_lot_add_final_result)

        total_vat=0
        if all_vat_entries_res:
            vat_percentage=all_vat_entries_res[0][3]
        else:
            vat_percentage='0%'
        print(vat_percentage)
        for r in all_vat_entries_res:
            total_vat += r[0]



        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'invoice_details':after_lot_add_final_result,
            'total_vat':total_vat,
            'vat_percentage':vat_percentage,
            # 'line_wise_vat':res,
            # 'line_wise_without_vat':res_without_vat,
            # 'product_quantity':product_quantity,
            'docs': self.env['account.move'].browse(docids),
            'report_type': data.get('report_type') if data else '',
        }

class ReportChallan(models.AbstractModel):
    _name = "report.custom_sale_invoice_report.custom_delivery_slip"

    @api.model
    def _get_report_values(self, docids, data=None):
        state_query="""select state from stock_move_line where stock_move_line.picking_id={}""".format(docids[0])
        self._cr.execute(query=state_query)
        stock = self._cr.fetchone()
        print(stock)
        if stock[0]=='done':
                    query="""select sum(stock_move_line.qty_done) from stock_move_line where stock_move_line.picking_id={}""".format(docids[0])
        else:
                    query="""select sum(stock_move_line.product_qty) from stock_move_line where stock_move_line.picking_id={}""".format(docids[0])
        self._cr.execute(query=query)
        res=self._cr.fetchall()

        if stock[0] == 'done':
                query="""select sml.product_id,pt.name,sum(sml.qty_done),sml.move_id from stock_move_line sml
                            left join product_product pp on sml.product_id=pp.id
                            left join product_template pt on pt.id=pp.product_tmpl_id 
                            where sml.picking_id={} group by sml.product_id,pt.name,sml.move_id order by sml.move_id asc""".format(docids[0])
        else:
            query = """select sml.product_id,pt.name,sum(sml.product_qty),sml.move_id from stock_move_line sml
                                       left join product_product pp on sml.product_id=pp.id
                                       left join product_template pt on pt.id=pp.product_tmpl_id 
                                       where sml.picking_id={} group by sml.product_id,pt.name,sml.move_id order by sml.move_id asc""".format(docids[0])
        self._cr.execute(query=query)
        main_table=self._cr.fetchall()
        print(main_table)

        query="""select sml.product_id,spl.name from stock_move_line sml
                        left join stock_production_lot spl on spl.id=sml.lot_id where sml.picking_id={} order by sml.move_id asc""".format(docids[0])
        self._cr.execute(query=query)
        product_lot = self._cr.fetchall()

        print(docids[0])
        query="""select am.name from stock_picking sp
                    left join account_move am on am.invoice_origin=sp.origin
                    where sp.id={}""".format(docids[0])
        self._cr.execute(query=query)
        invoice_no=self._cr.fetchone()
        print(invoice_no)

        after_lot_add_final_result = []
        for all_result in main_table:
            lot_string = ""
            for lot_result in product_lot:
                if all_result[0] == lot_result[0]:
                    if lot_result[1] != None:
                        lot_string += lot_result[1] + ', '

            as_list = list(all_result)
            # as_list[1] = as_list[1] + '/n' + lot_string
            as_list.insert(4,lot_string)
            after_lot_add_final_result.append(tuple(as_list))
        print(after_lot_add_final_result)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'total_quantity':res[0][0],
            'invoice_no':invoice_no[0],
            'main_table':after_lot_add_final_result,
            'docs': self.env['stock.picking'].browse(docids),
            'report_type': data.get('report_type') if data else '',
        }







