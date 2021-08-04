from datetime import date, datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict

from odoo.osv.osv import osv

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}


class AccountBatchPaymentInherit(models.Model):
    _inherit = 'account.payment'

    @api.model
    def _selection_collection_reference(self, context=None):
        print(context)
        active_model = self._context.get('active_model')
        if self.payment_type == 'outbound':
            return [
                ('previous_invoice', 'Previous Invoice'),
                ('multiple_invoice', 'Multiple Invoice')]
        else:
            return [
                ('advance_collection', 'Advance Collection'),
                ('previous_invoice', 'Previous Invoice'),
                ('multiple_invoice', 'Multiple Invoice'),
                ('cheque_adjustment', 'Cheque Adjustment')]

    batch_payment_id = fields.Many2one('batch.payment', string='Batch Payment Reference')
    bank_id = fields.Many2one('bank_info.all_bank', string="Bank")
    in_treatment_state = fields.Boolean(string="In Treatment State")
    treatment_id = fields.Many2one('batch.payment.test', string="Cheque Treatment")
    vendor_collection_reference = fields.Selection([
                ('previous_invoice', 'Previous Invoice'),
                ('multiple_invoice', 'Multiple Invoice')], string="Collection Reference", store=False)
    collection_reference = fields.Selection([
                ('advance_collection', 'Advance Collection'),
                ('previous_invoice', 'Previous Invoice'),
                ('multiple_invoice', 'Multiple Invoice'),
                ('cheque_adjustment', 'Cheque Adjustment')], string="Collection Reference")

    invoice_start_date = fields.Date(string="Invoice Start Date", default=fields.Date.today, store=False)
    invoice_end_date = fields.Date(string="Invoice End Date", default=fields.Date.today, store=False)
    payment_invoice_ids = fields.Many2many('account.move', 'invoice_wise_account_payment_rel', 'payment_id',
                                           'invoice_id', string="Multiple Invoice Reference")
    # domain="[('partner_id', '=', partner_id), ('state', '=', 'posted'), ('invoice_payment_state', '=', 'not_paid'), "
    #        "('date', '<=', invoice_end_date), ('date', '>=', invoice_start_date), ('type', '=', 'out_invoice')]")
    # domain=_get_payment_invoice_ids_domain)
    draft_account_move_id = fields.Many2one('account.move', string="Draft Account Move ID")
    bank_issue_account_move_id = fields.Many2one('account.move', string="Bank Issue Account Move")
    dishonor_balance_adjust_amt = fields.Float(string="Dishonor Balance Adjustment", default=0.0)
    dishonor_collection_ids = fields.Many2many('account.payment', 'account_payment_dishonor_collection_rel',
                                               'dishonor_id', 'collection_id', string='Dishonor Collections')
    # domain="[('state', '=', 'dishonored'), ('dishonor_balance_adjust_amt', '<', 'amount'), ('partner_id', '=', partner_id)]")
    # dishonor_collection_ids = fields.Many2one('account.payment', string='Dishonor Collections',
    #                                            domain="[('state', '=', 'dishonored'), ('dishonor_balance_adjust_amt', '<', amount), ('partner_id', '=', partner_id)]")
    total_due = fields.Float(string="Total Due", store=False)
    tt_sent_journal_id = fields.Many2one('account.journal', string="TT Sent Journal ID",
                                         domain="[('type', '=', 'bank')]")
    not_respone_by_effective_date = fields.Boolean(string="Not response in duration of effective date")
    cih_date = fields.Date("Cheque In Hand Date", default=fields.Date.today)

    # payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', required=False,
    #                                     states={'draft': [('readonly', False)]},
    #                                     help="Manual: Get paid by cash, check or any other method outside of Odoo.\n" \
    #                                          "Electronic: Get paid automatically through a payment acquirer by requesting a transaction on a card saved by the customer when buying or subscribing online (payment token).\n" \
    #                                          "Check: Pay bill by check and print it from Odoo.\n" \
    #                                          "Batch Deposit: Encase several customer checks at once by generating a batch deposit to submit to your bank. When encoding the bank statement in Odoo, you are suggested to reconcile the transaction with the batch deposit.To enable batch deposit, module account_batch_payment must be installed.\n" \
    #                                          "SEPA Credit Transfer: Pay bill from a SEPA Credit Transfer file you submit to your bank. To enable sepa credit transfer, module account_sepa must be installed ")

    payment_method_code = fields.Char("Payment Method Code")
    # dishonor_
    company_id_new = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company.id)

    initial_create_status = fields.Boolean("Initial Create Status", default=False)

    state = fields.Selection([
        ('init', 'Initial'),
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('dishonored', 'Dishonored'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('posted', 'Validated'),
        ('reconciled', 'Reconciled'),
        ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status", tracking=4)

    @api.onchange('vendor_collection_reference')
    def _onchange_vendor_collection_reference(self):
        self.collection_reference = self.vendor_collection_reference
    #     if self.payment_type == 'outbound':
    #         self.collection_reference.selection_add([
    #             ('previous_invoice', 'Previous Invoice'),
    #             ('multiple_invoice', 'Multiple Invoice')])
    #     else:
    #         self.collection_reference.selection_add([
    #             ('advance_collection', 'Advance Collection'),
    #             ('previous_invoice', 'Previous Invoice'),
    #             ('multiple_invoice', 'Multiple Invoice'),
    #             ('cheque_adjustment', 'Cheque Adjustment')])

    @api.model
    def dishonor_scheduling(self):
        dishonor_payment_list = self.env['account.payment'].search(
            [('state', '=', 'waiting_for_approval'), ('effective_date', '=', (date.today() - timedelta(3)))])
        for dishonor_payment in dishonor_payment_list:
            self.env['cheque.treatment'].dishonor_payment(dishonor_payment)
            dishonor_payment.not_respone_by_effective_date = True

    @api.onchange('payment_method_id')
    def onchange_payment_method_id(self):
        self.payment_method_code = self.payment_method_id.code

    @api.onchange('amount')
    def onchange_amount(self):
        if self.collection_reference == 'cheque_adjustment':
            if self.payment_method_id.code != 'manual':
                raise ValidationError(_("Please Select Cash Payment Method for Cheque Adjustment Collection"))
                return False

    def name_get(self):
        result = []
        for payment_line in self:
            name = ""
            if payment_line.cheque_reference:
                name = payment_line.cheque_reference + ' - '
            if payment_line.name:
                name += payment_line.name
            if payment_line.amount:
                name += 'Amount = (' + str(payment_line.amount) + ' '
                if payment_line.currency_id:
                    name += str(payment_line.currency_id.name)
                name += ' )'
            result.append((payment_line.id, name))
        return result

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.company_id_new = self.company_id

    @api.onchange('cheque_reference')
    def _onchange_cheque_reference(self):
        exists = False
        for record in self:
            if record.cheque_reference:
                domain = [('cheque_reference', '=', record.cheque_reference),
                          ('company_id', '=', self.env.user.company_id.id)]
                exists = super(AccountBatchPaymentInherit, self).search(domain, limit=100).name_get()
            if exists:
                raise UserError('Cheque No "' + record.cheque_reference + '" is already in stored!')

    def _get_invoce_type(self):
        invoice_type = 'out_invoice'
        if self.payment_type == 'outbound':
            invoice_type = 'in_invoice'
        return invoice_type

    def _get_invoice_items(self):
        invoice_type = self._get_invoce_type()
        query = """                        
                            select am.id from account_move am
                            left join invoice_wise_account_payment_rel amr on am.id = amr.invoice_id
                            left join account_payment ap on ap.id = amr.payment_id
                            where am.type = '{}' and am.partner_id = {}
                            and am.state = 'posted'
                            and invoice_payment_state = 'not_paid'
                            and date::date <= '{}'::date and date::date >='{}'::date
                            and case 
                                when (COALESCE(am.amount_residual, 0) - ( select COALESCE(sum(amount), 0) from account_payment ext_ap where 
                                        ext_ap.id in (select payment_id from invoice_wise_account_payment_rel ipr where ipr.invoice_id = amr.invoice_id) and
                                        ext_ap.collection_reference = 'multiple_invoice' and ext_ap.state in ('draft', 'sent', 'waiting_for_approval')
                                        and (ext_ap.initial_create_status is null or ext_ap.initial_create_status = false))) <= 0
                                    then 
                                        false
                                    else true
                                end
                            group by am.id
                            order by am.id asc""".format(invoice_type, self.partner_id.id, self.invoice_end_date,
                                                         self.invoice_start_date)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        return [x for xs in query_result for x in xs]

    @api.onchange('invoice_end_date', 'invoice_start_date')
    def _onchange_invoice_date(self):
        invoice_item_ids = self._get_invoice_items()
        return {'domain': {'payment_invoice_ids': [('id', 'in', invoice_item_ids)]}}

    @api.onchange('collection_reference')
    def _onchange_collection_reference(self):
        invoice_type = self._get_invoce_type()
        if self.collection_reference == 'previous_invoice':
            if not self.partner_id:
                raise ValidationError(_("Please Select Partner"))
                return False

            query = """                        
                                    select am.id from account_move am 
                                    where type = '{}' and partner_id = {}
                                    and state = 'posted' 
                                    and invoice_payment_state = 'not_paid'
                                    order by id asc""".format(invoice_type, self.partner_id.id)

            self._cr.execute(query=query)
            exist_challan = self._cr.fetchall()
            if not exist_challan:
                self.env.user.notify_warning(
                    message='Partner has not any Previous Challan. Your Paid amount will be in Advance Payment')

        if self.collection_reference == 'multiple_invoice':
            invoice_item_ids = self._get_invoice_items()
            return {'domain': {'payment_invoice_ids': [('id', 'in', invoice_item_ids)]}}

        if self.collection_reference == 'cheque_adjustment':
            if self.partner_id:
                query = "select id from account_payment where dishonor_balance_adjust_amt < amount and state = 'dishonored' and partner_id = {} and company_id_new = {}".format(
                    self.partner_id.id, self.env.company.id)
                self._cr.execute(query=query)
                dishonor_cheque_ids = [item[0] for item in self._cr.fetchall()]
                # cash_payment_methods = self.env['account.payment.method'].search([('code', '=', 'manual'), ('payment_type', '=', 'outbound')])
                return {'domain': {'payment_method_id': [('code', '=', 'manual'), ('payment_type', '=', 'outbound')],
                                   'dishonor_collection_ids': [('id', 'in', dishonor_cheque_ids)]}}
            else:
                raise ValidationError(_("Please Select Partner"))
                return False
        else:
            if self.journal_id:
                if self.journal_id.currency_id:
                    self.currency_id = self.journal_id.currency_id

                # Set default payment method (we consider the first to be the default one)
                payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
                # payment_methods = self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
                payment_methods_list = payment_methods.ids

                default_payment_method_id = self.env.context.get('default_payment_method_id')
                if default_payment_method_id:
                    # Ensure the domain will accept the provided default value
                    payment_methods_list.append(default_payment_method_id)
                else:
                    self.payment_method_id = payment_methods and payment_methods[0] or False

                # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
                payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'

                user_id = self.env.user.id
                user = self.env['res.users'].search([('id', '=', user_id)], limit=1)
                res_groups = self.env['res.groups'].search([('name', '=', 'TT Collector')], limit=1)
                tt_collector = False
                if user:
                    for grp_id in user.groups_id:
                        if grp_id.id == res_groups.id:
                            tt_collector = True

                if tt_collector:
                    domain = {
                        'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods_list)]}
                else:
                    domain = {
                        'payment_method_id': [('payment_type', '=', payment_type), ('code', '!=', 'tt'),
                                              ('id', 'in', payment_methods_list)]}

                if self.env.context.get('active_model') == 'account.move':
                    active_ids = self._context.get('active_ids')
                    invoices = self.env['account.move'].browse(active_ids)
                    self.amount = abs(
                        self._compute_payment_amount(invoices, self.currency_id, self.journal_id, self.payment_date))

                return {'domain': domain}
            return {}


class AccountBatchPayment(models.Model):
    _name = "batch.payment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Batch Payments"

    name = fields.Char(string="Transaction No", readOnly=True)
    batch_payment_line = fields.One2many('account.payment', 'batch_payment_id', string='Batch Payment Lines')
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', required=True, readonly=True, states={'initial': [('readonly', False)]})
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], tracking=True, readonly=True,
                                    states={'initial': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True, readonly=True,
                                 states={'initial': [('readonly', False)]},
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    payment_date = fields.Date(string='Date', default=fields.Date.today, required=True, readonly=True,
                               states={'initial': [('readonly', False)]}, copy=False, tracking=True)
    branch_id = fields.Many2one('res.branch', string="Branch", required=True,
                                default=lambda self: self.env.user.branch_id)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.company.id)

    dishonor_cheque_list = fields.Many2many('account.payment', 'account_payment_dishonor_rel', 'line_id', 'dishonor_id',
                                            store=False, string="Dishonor Cheques")

    draft_journal_id = fields.Integer("Draft Journal ID", default=lambda self: self.load_draft_journal_id())
    state = fields.Selection(
        [('initial', 'Initial'), ('processing', 'Processing'), ('dishonor', 'Dishonor'), ('approve', 'Approve'),
         ('finished', 'Finished')], readonly=True, default='initial', copy=False, string="Status")
    entry_by = fields.Many2one('res.users', string="Entry By")
    collected_by = fields.Many2one('res.users', string="Collected By", default=lambda self: self.env.user.id)
    approved_by = fields.Many2one('res.users', string="Approve By")
    approved_date = fields.Date(string='Approve Date')

    def _check_settings_Validation(self):
        # for rec in self:
        user_company_id = self.env.user.company_id.id
        saleotherexpense = self.env['saleotherexpense']
        fields_get = saleotherexpense.fields_get()
        if 'cheque_in_hand_account_id' in fields_get.keys():
            company_setting_existORnot = self.env['saleotherexpense'].search([('company_id', '=', user_company_id)])
            if company_setting_existORnot:
                if company_setting_existORnot.cheque_in_hand_account_id:
                    print("write your code here")
                else:
                    raise ValidationError(_('''Check in hand account is not set for this company!!!'''))
                    return False
            else:
                raise ValidationError(_('''Journal settings required for this company!!!'''))
                return False
        else:
            raise ValidationError(_('''Update 'sale_extra_cost' module, Cheque in hand doesn't exists!!!'''))
            return False
        return True

    @api.model
    def load_draft_journal_id(self):
        if not self._check_settings_Validation():
            return False
        query = """
                select id from account_journal where default_credit_account_id = 
                    (select cheque_in_hand_account_id from saleotherexpense where company_id = {} limit 1) limit 1
                    """.format(self.env.user.company_id.id)
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        if query_result:
            return query_result[0][0]

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            return {'domain': {'branch_id': [('company_id', '=', self.company_id.id)]}}

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for line in self.batch_payment_line:
            line.partner_id = self.partner_id

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        for item in self:
            pay_type = item.payment_type
            print(item.batch_payment_line)
            for line in item.batch_payment_line:
                line.payment_type = pay_type

    @api.onchange('batch_payment_line')
    def onchange_batch_payment_line(self):
        list = [(5, 0, 0)]
        for payment_line in self.batch_payment_line:
            if payment_line.dishonor_collection_ids:
                for item in payment_line.dishonor_collection_ids:
                    list.append((0, 0, {
                        'id': item.id,
                        'payment_type': item.payment_type,
                        'payment_date': item.payment_date,
                        'name': item.name,
                        'payment_method_id': item.payment_method_id,
                        'partner_id': item.partner_id,
                        'amount': item.amount,
                        'state': item.state,
                        'company_id': item.company_id,
                        'cheque_reference': item.cheque_reference,
                        'dishonor_balance_adjust_amt': item.dishonor_balance_adjust_amt,
                        'total_due': item.amount - item.dishonor_balance_adjust_amt,
                    }))
                self.dishonor_cheque_list = list

    @api.model
    def create(self, vals):
        upd_vals = vals.copy()
        if upd_vals.get("name", "/") == "/":
            upd_vals["name"] = self.env["ir.sequence"].next_by_code("batch.payment.no")
        if 'batch_payment_line' in vals.keys():
            if vals['batch_payment_line']:
                for line in vals['batch_payment_line']:
                    line[2]['initial_create_status'] = True

        return super().create(upd_vals)

    def btn_dishonor_all(self):
        for record in self:
            record.state = 'dishonor'

    def check_validation(self, payment_info):
        status = False
        message = ""
        if not payment_info.collection_reference:
            message += "Collection Reference should not be empty\n"
            status = True

        if payment_info.collection_reference == 'cheque_adjustment':
            if payment_info.payment_method_id.code != 'manual':
                message += "Payment Method should be Cash Type for Cheque Adjustment Collection\n"
                status = True

        if payment_info.collection_reference == 'cheque_adjustment':
            if payment_info.payment_method_id.code != 'manual':
                message += "Payment Method should be Cash Type for Cheque Adjustment Collection\n"
                status = True

        if payment_info.collection_reference == 'multiple_invoice':
            if not payment_info.payment_invoice_ids:
                message += "Invoice can not be empty in Collection Reference of Multiple Invoice\n"
                status = True

        if payment_info.amount < 1:
            message += "Amount should be greater than 0\n"
            status = True

        if payment_info.payment_method_id.code in ['check_in', 'pdc']:
            if not payment_info.effective_date:
                message += "Effective Date should not be empty\n"
                status = True

        if payment_info.payment_method_id.code in ['check_in', 'pdc', 'tt']:
            if not payment_info.bank_id:
                message += "Bank should not be empty\n"
                status = True

            if not payment_info.cheque_reference:
                message += "Cheque Reference should not be empty\n"
                status = True

        if payment_info.collection_reference == 'cheque_adjustment':
            if len(payment_info.dishonor_collection_ids) > 0:
                dishonor_amt = 0
                for dishonor_cheq in payment_info.dishonor_collection_ids:
                    dishonor_amt += (dishonor_cheq.amount - dishonor_cheq.dishonor_balance_adjust_amt)

                if dishonor_amt < payment_info.amount:
                    message += "Collection amount cannot be greater than total dishonor cheque's amount\n"
                    status = True
            else:
                message += "Dishonor Collection list should be empty\n"
                status = True

        if status:
            return message
        return status

    def _get_journal_id_by_query(self, query):
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        if query_result:
            journal_id = query_result[0][0]
        else:
            raise UserError(
                _("Journal not found\nPlease, select journal/ configure journal by Company"))
        return journal_id

    def set_journal_id(self, line_details):
        if not self._check_settings_Validation():
            return False
        if line_details.payment_method_id.code == 'manual':
            query = """
                                    select id from account_journal where type = 'cash' and company_id = {} limit 1
                                        """.format(self.env.user.company_id.id)
            line_details.journal_id = self._get_journal_id_by_query(query)
        elif line_details.payment_method_id.code == 'tt':
            if line_details.tt_sent_journal_id:
                line_details.journal_id = line_details.tt_sent_journal_id
            else:
                raise ValidationError(_("TT sent journal cannot be empty for TT colection.\n Select TT sent Journal"))
        else:
            query = """
                                    select id from account_journal where default_credit_account_id = 
                                        (select cheque_in_hand_account_id from saleotherexpense where company_id = {} limit 1) limit 1
                                        """.format(self.env.user.company_id.id)
            line_details.journal_id = self._get_journal_id_by_query(query)
        return line_details

    def btn_submit_for_approval(self):
        if not self._check_settings_Validation():
            return False

        if len(self.batch_payment_line) > 0:
            self.state = 'processing'
            self.entry_by = self.env.user.id
            for line_details in self.batch_payment_line:
                line_details = self.set_journal_id(line_details)
                validation_message = self.check_validation(line_details)
                if not validation_message:
                    payment_type_dc = {'payment_type': self.payment_type}
                    state_dc = {'state': 'init'}
                    partner_type_dc = {'partner_type': self.partner_type}
                    partner_id_dc = {'partner_id': self.partner_id}
                    branch_id_dc = {'branch_id': self.branch_id}
                    line_details.update(payment_type_dc)
                    line_details.update(state_dc)
                    line_details.update(partner_type_dc)
                    line_details.update(partner_id_dc)
                    line_details.update(branch_id_dc)
                else:
                    raise ValidationError(_(validation_message))
                    return False
        else:
            raise ValidationError(
                _("Add at least one Payment Information"))
            return False

    def update_invoice_residual_amount_for_multiple_reference_typ_collection(self, given_invoice_ids,
                                                                             increase_or_decrease):
        if given_invoice_ids:
            for invoice_id in given_invoice_ids:
                update_query = """update account_move set amount_residual = COALESCE(amount_residual, 0) {} COALESCE((
                                    select sum(ap.amount) from invoice_wise_account_payment_rel amr
                                    inner join account_payment ap on ap.id = amr.payment_id
                                    where amr.invoice_id = {} and ap.state in ('draft', 'sent', 'waiting_for_approval')
                                    and ap.collection_reference = 'multiple_invoice'
                                    and (ap.initial_create_status is null or ap.initial_create_status = false)
                                    group by amr.payment_id
                                ), 0) where id = {}""".format(increase_or_decrease, invoice_id, invoice_id)
                self._cr.execute(query=update_query)

                update_line_query = """update account_move_line set amount_residual = COALESCE(amount_residual, 0) {} COALESCE((
                                    select sum(ap.amount) from invoice_wise_account_payment_rel amr
                                    inner join account_payment ap on ap.id = amr.payment_id
                                    where amr.invoice_id = {} and ap.state in ('draft', 'sent', 'waiting_for_approval')
                                    and ap.collection_reference = 'multiple_invoice'
                                    and (ap.initial_create_status is null or ap.initial_create_status = false)
                                    group by amr.payment_id
                                ), 0) where move_id = {} and account_internal_type = 'receivable'""".format(
                    increase_or_decrease, invoice_id, invoice_id)
                self._cr.execute(query=update_line_query)
                self._cr.commit()

    def btn_approve(self):
        for record in self:
            record.state = 'approve'
            record.approved_by = self.env.user.id
            record.approved_date = date.today()

        for payment_line in self.batch_payment_line:
            payment_line.initial_create_status = False
            # if payment_line.state == 'waiting_for_approval':
            AccountMove = self.env['account.move'].with_context(default_type='entry')
            for rec in payment_line:
                payment_line.cih_date = date.today()
                # payment_line.honor_date = self.payment_date
                payment_line.honor_date = payment_line.effective_date

                if any(inv.state != 'posted' for inv in rec.invoice_ids):
                    raise ValidationError(
                        _("The payment cannot be processed because the invoice is not open!"))

                # keep the name in case of a payment reset to draft
                if not rec.name:
                    # Use the right sequence to set the name
                    if rec.payment_type == 'transfer':
                        sequence_code = 'account.payment.transfer'
                    else:
                        if rec.partner_type == 'customer':
                            if rec.payment_type == 'inbound':
                                sequence_code = 'account.payment.customer.invoice'
                            if rec.payment_type == 'outbound':
                                sequence_code = 'account.payment.customer.refund'
                        if rec.partner_type == 'supplier':
                            if rec.payment_type == 'inbound':
                                sequence_code = 'account.payment.supplier.refund'
                            if rec.payment_type == 'outbound':
                                sequence_code = 'account.payment.supplier.invoice'
                    rec.name = self.env['ir.sequence'].next_by_code(sequence_code,
                                                                    sequence_date=rec.payment_date)
                    if not rec.name and rec.payment_type != 'transfer':
                        raise UserError(
                            _("You have to define a sequence for %s in your company.") % (sequence_code,))

                    given_invoice_ids = self.get_given_invoices(rec)
                    # Has update residual_amount for avoiding multiple_reference invoice value

                    rec.update({
                        'invoice_ids': [(6, 0, given_invoice_ids)],
                    })

                    # moves.date = rec.effective_date
                    moves = AccountMove.create(rec._prepare_payment_moves())

                    for line in moves.invoice_line_ids:
                        line.collection_date = self.payment_date
                    if rec.effective_date:
                        moves.date = rec.effective_date
                    else:
                        moves.date = self.payment_date
                        # moves.date = datetime.now()

                    if (rec.payment_method_id.code in ['tt', 'manual']) or (rec.payment_type == 'outbound'):
                        if (payment_line.collection_reference != 'multiple_invoice') and (
                                rec.payment_type == 'inbound'):
                            self.update_invoice_residual_amount_for_multiple_reference_typ_collection(given_invoice_ids,
                                                                                                      '-')
                        moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

                        # Update the state / move before performing any reconciliation.
                        move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
                        rec.write({'state': 'posted', 'move_name': move_name})

                        if rec.payment_type in ('inbound', 'outbound'):
                            # ==== 'inbound' / 'outbound' ====
                            if rec.invoice_ids:
                                (moves[0] + rec.invoice_ids).line_ids \
                                    .filtered(
                                    lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
                                    .reconcile()
                        elif rec.payment_type == 'transfer':
                            # ==== 'transfer' ====
                            moves.mapped('line_ids') \
                                .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                                .reconcile()
                        if rec.collection_reference == 'cheque_adjustment':
                            res_amt = rec.amount
                            for dishonor_chq in rec.dishonor_collection_ids:
                                if dishonor_chq.amount < res_amt:
                                    res_amt -= (dishonor_chq.amount - dishonor_chq.dishonor_balance_adjust_amt)
                                    dishonor_chq.dishonor_balance_adjust_amt += (
                                            dishonor_chq.amount - dishonor_chq.dishonor_balance_adjust_amt)
                                else:
                                    dishonor_chq.dishonor_balance_adjust_amt += res_amt
                                    res_amt -= res_amt
                                    # rec.dishonor_balance_adjust_amt -=

                        if (payment_line.collection_reference != 'multiple_invoice') and (
                                rec.payment_type == 'inbound'):
                            self.update_invoice_residual_amount_for_multiple_reference_typ_collection(given_invoice_ids,
                                                                                                      '+')
                    # moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
                    else:
                        # Update the state / move before performing any reconciliation.
                        for move_line in moves.line_ids:
                            move_line.ref = "Cheque Collection"

                        move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
                        rec.write({'state': 'draft', 'move_name': move_name, 'draft_account_move_id': moves.id})
                        #
                        # if rec.payment_type in ('inbound', 'outbound'):
                        #     # ==== 'inbound' / 'outbound' ====
                        #     if rec.invoice_ids:
                        #         (moves[0] + rec.invoice_ids).line_ids \
                        #             .filtered(
                        #             lambda
                        #                 line: not line.reconciled and line.account_id == rec.destination_account_id) \
                        #             .reconcile()
                        # elif rec.payment_type == 'transfer':
                        #     # ==== 'transfer' ====
                        #     moves.mapped('line_ids') \
                        #         .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                        #         .reconcile()

        for payment_line in self.batch_payment_line:
            if payment_line.state == 'cancelled':
                payment_line.state = 'draft'

    def get_given_invoices(self, batch_payment):
        invoice_type = 'out_invoice'
        if self.payment_type == 'outbound':
            invoice_type = 'in_invoice'

        given_invoice_ids = []
        if batch_payment.collection_reference == 'multiple_invoice':
            for given_invoice in batch_payment.payment_invoice_ids:
                given_invoice_ids.append(given_invoice.id)

        elif batch_payment.collection_reference == 'previous_invoice':
            query = """                        
                        select am.id from account_move am
                        left join invoice_wise_account_payment_rel amr on am.id = amr.invoice_id
                        left join account_payment ap on ap.id = amr.payment_id
                        where am.type = '{}' and am.partner_id = {}
                        and am.state = 'posted'
                        and invoice_payment_state = 'not_paid'
                        and case 
                            when (COALESCE(am.amount_residual, 0) - ( select COALESCE(sum(amount), 0) from account_payment ext_ap where 
                                    ext_ap.id in (select payment_id from invoice_wise_account_payment_rel ipr where ipr.invoice_id = amr.invoice_id) and
                                    ext_ap.collection_reference = 'multiple_invoice' and ext_ap.state in ('draft', 'sent', 'waiting_for_approval')
                                    and (ext_ap.initial_create_status is null or ext_ap.initial_create_status = false))) <= 0
                                then 
                                    false
                                else true
                            end
                        group by am.id
                        order by am.id asc""".format(invoice_type, batch_payment.partner_id.id)
            self._cr.execute(query=query)
            query_result = self._cr.fetchall()

            if query_result:
                for given_invoice in query_result:
                    if given_invoice:
                        given_invoice_ids.append(given_invoice[0])

        elif batch_payment.collection_reference == 'cheque_adjustment':
            for dishonor_cheque in batch_payment.dishonor_collection_ids:
                for invoices in dishonor_cheque.payment_invoice_ids:
                    given_invoice_ids.append(invoices.id)

        return given_invoice_ids


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    collection_date = fields.Date(string="collection Date")
