# Copyright (C) 2018 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class ForeignPurchaseOrder(models.Model):
    _name = "foreign.purchase.order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Foreign Purchase Order"

    invoice_ids = fields.Many2many('account.move', compute="_compute_invoice", string='Bills', copy=False, store=True)
    partner_ref = fields.Char('Vendor Reference', copy=False,
                              help="Reference of the sales order or bid sent by the vendor. "
                                   "It's used to do the matching when you receive the "
                                   "products as this reference is usually written on the "
                                   "delivery order sent by your vendor.")
    # invoice_count = fields.Integer(compute="_compute_invoice", string='Bill Count', copy=False, default=0, store=True)
    invoice_count = fields.Integer( string='Bill Count',compute="_compute_invoice")
    dest_address_id = fields.Many2one('res.partner',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                      string='Drop Ship Address',
                                      help="Put an address if you want to deliver directly from the vendor to the customer. "
                                           "Otherwise, keep empty to deliver to your own company.")
    # @api.onchange('invoice_ids.invoice_line_ids')
    # def fpo_invoice_qty_update(self):
    #     print(self)

    def button_approve(self, force=False):
        self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        return {}
    # @api.depends('name')
    def _compute_invoice(self):
        if self.name:
            count= self.env['account.move'].search_count([('invoice_origin','=',self.name),('type','=','in_invoice')])
            self.invoice_count=count

    # def action_pre_shipment(self):
    #     self.state='pre-shipment'

    def action_draft(self):
        self.state='draft'
    def action_shipment(self):
        self.button_approve_svl()
        self._cr.commit()
        # move_id = self.env['stock.move'].search([('origin', '=', self.name)])
        # query_move = """update stock_move set state = 'done' where id in {}""".format(
        #     str(tuple(move_id.ids)).replace(',)', ')'))
        # self._cr.execute(query=query_move)
        # query_move_line = """update stock_move_line set qty_done = product_qty,product_qty=0,product_uom_qty=0, state='done', location_dest_id = '72' where move_id in {}""".format(
        #     str(tuple(move_id.ids)).replace(',)', ')'))
        # self._cr.execute(query=query_move_line)

        for rec in self:
            for line in rec.line_ids:
                if line.price_unit !=line.bank_payment+line.local_payment:
                    raise ValidationError("Unit price and Summation of Bank Payment, Local Payment should be equal")
                if line.price_unit == line.bank_payment + line.local_payment:
                    line.remaining_bank_payment=line.bank_payment
        # self.picking_ids.button_validate_foreign(self.name)
        self.state = 'shipment'






    def action_view_relavent_invoice(self):
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('invoice_origin','=',self.name),('type','=','in_invoice')],
            # 'context': {'search_default_group_by_payment_method': 1}
        }

    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        # if self.line_ids.original_uom_qty >self.line_ids.invoiced_uom_qty:
        active_model = self._name
        default_currency_id = self.env.ref('base.main_company').currency_id.id
        bank_rate = self.env['res.currency.rate'].search([('currency_id', '=', default_currency_id)]).rate
        local_rate = self.env.ref('base.main_company').currency_id.local_currency
        if active_model == 'foreign.purchase.order':
            stock_move = self.env['stock.move']
            get_stock_move = self.env['stock.move'].search([('origin', '=', self.name)])
            for line in self.line_ids:
                for row in get_stock_move:
                    if line.product_id.product_tmpl_id.name == row.name:
                        row.price_unit = (line.bank_payment * bank_rate) + (local_rate * line.local_payment)
        action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        create_bill = self.env.context.get('create_bill', False)
        # override the context to get rid of the default filtering
        result['context'] = {
            'default_type': 'in_invoice',
            'default_company_id': self.company_id.id,
            'default_foreign_purchase_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_flag': True
        }
        # Invoice_ids may be filtered depending on the user. To ensure we get all
        # invoices related to the purchase order, we read them in sudo to fill the
        # cache.
        self.sudo()._read(['invoice_ids'])
        # choose the view_mode accordingly
        if len(self.invoice_ids) > 1 and not create_bill:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        else:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                result['views'] = form_view
            # Do not set an invoice_id if we want to create a new bill.
            if not create_bill:
                result['res_id'] = self.invoice_ids.id or False
        result['context']['default_invoice_origin'] = self.name
        result['context']['default_ref'] = self.partner_ref
        return result
        # else:
        #     raise UserError(_("Nothing to Invoice"))

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    @api.model
    def _default_company(self):
        return self.env.user.company_id

    @api.depends("line_ids.price_total")
    def _compute_amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update(
                {
                    "amount_untaxed": order.currency_id.round(amount_untaxed),
                    "amount_tax": order.currency_id.round(amount_tax),
                    "amount_total": amount_untaxed + amount_tax,
                }
            )

    name = fields.Char(default="Draft", readonly=True)
    primary_partner_id = fields.Many2one(
        "res.partner",
        string="Primary Vendor",
        track_visibility="always"

    )
    same_partner = fields.Boolean(string="Same Vendor", default=False)
    partner_id = fields.Many2one(
        "res.partner",
        string="Secondary Vendor",
        track_visibility="always",
        store=True

    )

    @api.onchange("same_partner")
    def _get_secondary_vendor(self):
        if self.same_partner == True:
            self.partner_id = self.primary_partner_id
        else:
            self.partner_id = None

    line_ids = fields.One2many(
        "foreign.purchase.order.line",
        "order_id",
        string="Order lines",
        track_visibility="always",
        copy=True,
    )

    line_count = fields.Integer(
        string="Purchase Blanket Order Line count",
        compute="_compute_line_count",
        readonly=True,
    )
    product_id = fields.Many2one(
        "product.product", related="line_ids.product_id", string="Product",
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.currency_set(),
    )
    def currency_set(self):
        return self.env['res.currency'].search([('name','ilike','USD')]).id
    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Payment Terms",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    confirmed = fields.Boolean(copy=False)
    # state = fields.Selection(
    #     selection=[
    #         ("draft", "Draft"),
    #         ("open", "Open"),
    #         ("done", "Done"),
    #         ("expired", "Expired"),
    #     ],
    #     compute="_compute_state",
    #     store=True,
    #     copy=False,
    #     track_visibility="always",
    # )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed","Confirm Order"),
            ("pre-shipment", "Pre-Shipment"),
            ("shipment", "Shipment"),
            # ('invoice','C/I'),
            ("done", "Done"),
            ("expired", "Expired"),
        ],
        # compute="_compute_state",
        default = 'draft',
        store=True,
        copy=False,
        track_visibility="always",
    )
    # validity_date = fields.Date(
    #     readonly=True,
    #     states={"draft": [("readonly", False)]},
    #     track_visibility="always",
    #     help="Date until which the blanket order will be valid, after this "
    #     "date the blanket order will be marked as expired",
    # )
    date_start = fields.Datetime(
        readonly=True,
        required=True,
        string="Start Date",
        default=fields.Datetime.now,
        states={"draft": [("readonly", False)]},
        help="Blanket Order starting date.",
    )

    note = fields.Text(readonly=True, states={"draft": [("readonly", False)]})
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        readonly=True,
        default=lambda self: self.env.uid,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=_default_company,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    # purchase_count = fields.Integer(compute="_compute_purchase_count")

    fiscal_position_id = fields.Many2one(
        "account.fiscal.position", string="Fiscal Position"
    )

    amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        store=True,
        readonly=True,
        compute="_compute_amount_all",
        track_visibility="always",
    )
    amount_tax = fields.Monetary(
        string="Taxes", store=True, readonly=True, compute="_compute_amount_all"
    )
    amount_total = fields.Monetary(
        string="Total", store=True, readonly=True, compute="_compute_amount_all"
    )

    # Fields use to filter in tree view
    original_uom_qty = fields.Float(
        string="Quantity",
        # compute="_compute_uom_qty",
        search="_search_original_uom_qty",
    )
    ordered_uom_qty = fields.Float(
        string="Ordered quantity",
        # compute="_compute_uom_qty",
        search="_search_ordered_uom_qty",
    )
    invoiced_uom_qty = fields.Float(
        string="Invoiced quantity",
        readonly=True,
        # compute="_compute_uom_qty",
        search="_search_invoiced_uom_qty",
    )
    # remaining_uom_qty = fields.Float(
    #     string="Remaining quantity",
    #     readonly=True,
    #     # compute="_compute_uom_qty",
    #     search="_search_remaining_uom_qty",
    # )
    received_uom_qty = fields.Float(
        string="Received quantity",
        readonly=True,
        # compute="_compute_uom_qty",
        search="_search_received_uom_qty",
    )

    def _get_purchase_orders(self):
        return self
        # return self.mapped("line_ids.purchase_lines.")

    @api.depends("line_ids")
    def _compute_line_count(self):
        self.line_count = len(self.mapped("line_ids"))

    def _compute_purchase_count(self):
        for blanket_order in self:
            blanket_order.purchase_count = len(blanket_order._get_purchase_orders())

    @api.depends(
        "line_ids.remaining_uom_qty",  "confirmed",
    )
    def _compute_state(self):
        today = fields.Date.today()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for order in self:
            if not order.confirmed:
                order.state = "draft"
            # elif order.validity_date <= today:
            #     order.state = "expired"
            elif float_is_zero(
                sum(order.line_ids.mapped("remaining_uom_qty")),
                precision_digits=precision,
            ):
                order.state = "done"
            else:
                order.state = "open"

    # def _compute_uom_qty(self):
    #     for bo in self:
    #         bo.original_uom_qty = sum(bo.mapped("line_ids.original_uom_qty"))
    #         bo.ordered_uom_qty = sum(bo.mapped("line_ids.ordered_uom_qty"))
    #         bo.invoiced_uom_qty = sum(bo.mapped("line_ids.invoiced_uom_qty"))
    #         bo.received_uom_qty = sum(bo.mapped("line_ids.received_uom_qty"))
    #         bo.remaining_uom_qty = sum(bo.mapped("line_ids.remaining_uom_qty"))

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Payment term
        """
        if not self.partner_id:
            self.payment_term_id = False
            self.fiscal_position_id = False
            return

        self.payment_term_id = (
            self.partner_id.property_supplier_payment_term_id
            and self.partner_id.property_supplier_payment_term_id.id
            or False
        )

        self.fiscal_position_id = (
            self.env["account.fiscal.position"]
            .with_context(company_id=self.company_id.id)
            .get_fiscal_position(self.partner_id.id)
        )

        # self.currency_id = (
        #     self.partner_id.property_purchase_currency_id.id
        #     or self.env.user.company_id.currency_id.id
        # )

        if self.partner_id.user_id:
            self.user_id = self.partner_id.user_id.id

    def unlink(self):
        for order in self:
            if order.state not in ("draft", "cancel"):
                raise UserError(
                    _(
                        "You can not delete an open blanket order! "
                        "Try to cancel it before."
                    )
                )
        return super().unlink()

    def copy_data(self, default=None):
        if default is None:
            default = {}
        default.update(self.default_get(["name", "confirmed"]))
        return super().copy_data(default)

    def _validate(self):
        try:
            today = fields.Date.today()
            for order in self:
                # assert order.validity_date, _("Validity date is mandatory")
                # assert order.validity_date > today, _(
                #     "Validity date must be in the future"
                # )
                assert order.partner_id, _("Partner is mandatory")
                assert len(order.line_ids) > 0, _("Must have some lines")
                order.line_ids._validate()
        except AssertionError as e:
            raise UserError(e)

    def set_to_draft(self):
        for order in self:
            order.write({"state": "draft"})
        return True

    def action_confirm(self):
        # self._validate()
        for order in self:
            sequence_obj = self.env["ir.sequence"]
            if order.company_id:
                sequence_obj = sequence_obj.with_context(
                    force_company=order.company_id.id
                )
            name = sequence_obj.next_by_code("foreign.purchase.order")
            self.state = 'confirmed'
            self.name=name
            self.button_approve()
            # self.button_approve_svl()
            # self.picking_ids.button_validate_forign(order.picking_ids,order.name)
            # order.write({"confirmed": True, "name": name})
        return True



    def action_pre_shipment(self):
        self.state="pre-shipment"

        # move_id = self.env['stock.move'].search([('origin','=',self.name)])
        # query_move = """update stock_move set state = 'done' where id in {}""".format(str(tuple(move_id.ids)).replace(',)', ')'))
        # self._cr.execute(query=query_move)
        # query_move_line = """update stock_move_line set qty_done = product_qty,product_qty=0,product_uom_qty=0, state='done', location_dest_id = '72' where move_id in {}""".format(str(tuple(move_id.ids)).replace(',)', ')'))
        # self._cr.execute(query=query_move_line)
        # self.picking_ids.button_validate_foreign(self.name)
        for rec in self:
            for line in rec.line_ids:
                line.bank_payment=line.price_unit
                line.remaining_bank_payment = line.price_unit




    def action_cancel(self):
        for order in self:
            if order.purchase_count > 0:
                for po in order._get_purchase_orders():
                    if po.state not in ("cancel"):
                        raise UserError(
                            _(
                                "You can not delete a blanket order with opened "
                                "purchase orders! "
                                "Try to cancel them before."
                            )
                        )
            order.write({"state": "expired"})
        return True

    def action_view_purchase_orders(self):
        purchase_orders = self._get_purchase_orders()
        action = self.env.ref("purchase.purchase_rfq").read()[0]
        if len(purchase_orders) > 0:
            action["domain"] = [("id", "in", purchase_orders.ids)]
            action["context"] = [("id", "in", purchase_orders.ids)]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    # def action_view_purchase_blanket_order_line(self):
    #     action = self.env.ref(
    #         "foreign.purchase.order" ".act_open_foreign_purchase_order_lines_view_tree"
    #     ).read()[0]
    #     lines = self.mapped("line_ids")
    #     if len(lines) > 0:
    #         action["domain"] = [("id", "in", lines.ids)]
    #     return action

    @api.model
    def expire_orders(self):
        today = fields.Date.today()
        expired_orders = self.search(
            [("state", "=", "open")]
        )
        # expired_orders.modified(["validity_date"])
        expired_orders.recompute()

    @api.model
    def _search_original_uom_qty(self, operator, value):
        bo_line_obj = self.env["foreign.purchase.order.line"]
        res = []
        bo_lines = bo_line_obj.search([("original_uom_qty", operator, value)])
        order_ids = bo_lines.mapped("order_id")
        res.append(("id", "in", order_ids.ids))
        return res

    @api.model
    def _search_ordered_uom_qty(self, operator, value):
        bo_line_obj = self.env["foreign.purchase.order.line"]
        res = []
        bo_lines = bo_line_obj.search([("ordered_uom_qty", operator, value)])
        order_ids = bo_lines.mapped("order_id")
        res.append(("id", "in", order_ids.ids))
        return res

    @api.model
    def _search_invoiced_uom_qty(self, operator, value):
        bo_line_obj = self.env["foreign.purchase.order.line"]
        res = []
        bo_lines = bo_line_obj.search([("invoiced_uom_qty", operator, value)])
        order_ids = bo_lines.mapped("order_id")
        res.append(("id", "in", order_ids.ids))
        return res

    @api.model
    def _search_received_uom_qty(self, operator, value):
        bo_line_obj = self.env["foreign.purchase.order.line"]
        res = []
        bo_lines = bo_line_obj.search([("received_uom_qty", operator, value)])
        order_ids = bo_lines.mapped("order_id")
        res.append(("id", "in", order_ids.ids))
        return res

    @api.model
    def _search_remaining_uom_qty(self, operator, value):
        bo_line_obj = self.env["foreign.purchase.order.line"]
        res = []
        bo_lines = bo_line_obj.search([("remaining_uom_qty", operator, value)])
        order_ids = bo_lines.mapped("order_id")
        res.append(("id", "in", order_ids.ids))
        return


class ForeignPurchaseOrderLine(models.Model):
    _name = "foreign.purchase.order.line"
    _description = "Foreign Purchase Order Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    invoice_lines = fields.One2many('account.move.line', 'foreign_purchase_line_id', string="Bill Lines", readonly=True,
                                    copy=False)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    qty_received_method = fields.Selection([('manual', 'Manual')], string="Received Qty Method",
                                           compute='_compute_qty_received_method', store=True,
                                           help="According to product configuration, the recieved quantity can be automatically computed by mechanism :\n"
                                                "  - Manual: the quantity is set manually on the line\n"
                                                "  - Stock Moves: the quantity comes from confirmed pickings\n")
    shipment_route=fields.Selection([
        ('by_lc','By Lc'),
        ('by_direct','By Direct')
    ],string='Shipping Route')

    incoterms = fields.Selection([
        ('by_air','By Air'),
        ('by_sea','By Sea')
    ], 'Incoterms')

    destination_port=fields.Many2one('usl.port', string="Port Of Destination")



    @api.onchange('local_payment')
    def check_local_amount(self):
        for rec in self:
            if rec.bank_payment + rec.local_payment != rec.price_unit:
                return {
                    'warning': {
                        'title': 'Warning!',
                        'message': "Unit price and Summation of Bank Payment, Local Payment should be equal"}
                }
                # raise ValidationError("Unit price and Summation of Bank Payment, Local Payment should be equal")

    @api.onchange('bank_payment')
    def check_bank_amount(self):
        for rec in self:
            if rec.bank_payment==0:
                # query=self.env['usl.lc.management'].search(['lc_no','=','Direct'])
                return {'domain':{'lc_number':[('lc_no','=','Direct')]}}

            if rec.bank_payment + rec.local_payment != rec.price_unit:
                return {
                    'warning': {
                        'title': 'Warning!',
                        'message': "Unit price and Summation of Bank Payment, Local Payment should be equal"}
                }
            if rec.bank_payment + rec.local_payment == rec.price_unit:
                rec.remaining_bank_payment = rec.bank_payment

                # raise ValidationError("Unit price and Summation of Bank Payment, Local Payment should be equal")

    # @api.constrains('bank_payment', 'local_payment')
    # def check_bank_amount_(self):
    #     if self.bank_payment + self.local_payment != self.price_unit:
    #         raise ValidationError("Unit price and Summation of Bank Payment, Local Payment should be equal")

    @api.onchange('shipment_route')
    def _get_incomterms(self):
        for rec in self:
            if rec.shipment_route != False:
                if rec.shipment_route == 'by_lc':
                    rec.incoterms = 'by_sea'
                else:
                    rec.incoterms = 'by_air'



    @api.model
    def get_custom_dropdown(self):
        result = []
        result.append((1, 'BY LC'))
        result.append((2, 'BY DIRECT'))
        self.shipment_route=result

    @api.depends('product_id')
    def _compute_qty_received_method(self):
        for line in self:
            if line.product_id and line.product_id.type in ['consu', 'service']:
                line.qty_received_method = 'manual'
            else:
                line.qty_received_method = False


    @api.depends("original_uom_qty", "price_unit", "taxes_id")
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(
                line.price_unit,
                line.order_id.currency_id,
                line.original_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_id,
            )
            line.update(
                {
                    "price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                }
            )

    name = fields.Char("Description", track_visibility="onchange")

    sequence = fields.Integer()
    order_id = fields.Many2one(
        "foreign.purchase.order", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        domain=[("purchase_ok", "=", True)],
    )
    product_uom = fields.Many2one("uom.uom", string="Unit of Measure", required=True)
    price_unit = fields.Float(string="Unit Price", required=True, digits=("Product Price"))
    taxes_id = fields.Many2many(
        "account.tax",
        string="Taxes",
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    # date_schedule = fields.Date(string="Scheduled Date")
    original_uom_qty = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
        digits=("Product Unit of Measure"),
    )
    ordered_uom_qty = fields.Float(
        string="Ordered quantity",
        # compute="_compute_quantities",
        store=True,
        digits=("Product Unit of Measure"),
    )
    invoiced_uom_qty =fields.Float(compute='_compute_qty_invoiced', string="Invoiced quantity", digits='Product Unit of Measure', store=True)
    #     fields.Float(
    #     string="Invoiced quantity",
    #     compute="_compute_quantities",
    #     store=True,
    #     digits=("Product Unit of Measure"),
    # )
    remaining_uom_qty = fields.Float(
        string="Remaining quantity",
        # compute="_compute_qty_invoiced",
        store=True,
        digits=("Product Unit of Measure"),
    )
    remaining_qty = fields.Float(
        string="Remaining quantity in base UoM",
        # compute="_compute_qty_invoiced",
        store=True,
        digits=("Product Unit of Measure"),
    )
    received_uom_qty = fields.Float(
        string="Received quantity",
        # compute="_compute_qty_invoiced",
        store=True,
        digits=("Product Unit of Measure"),
    )
    # purchase_lines = fields.One2many(
    #     comodel_name="account.move.line",
    #     inverse_name="purchase_order_line",
    #     string="Purchase Order Lines",
    #     readonly=True,
    #     copy=False,
    # )
    company_id = fields.Many2one(
        "res.company", related="order_id.company_id", store=True, readonly=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="order_id.currency_id", readonly=True
    )
    partner_id = fields.Many2one(
        related="order_id.partner_id", string="Vendor"
    )
    user_id = fields.Many2one(
        related="order_id.user_id", string="Responsible", readonly=True
    )
    payment_term_id = fields.Many2one(
        related="order_id.payment_term_id", string="Payment Terms", readonly=True
    )

    price_subtotal = fields.Monetary(
        compute="_compute_amount", string="Subtotal", store=True
    )
    price_total = fields.Monetary(compute="_compute_amount", string="Total", store=True)
    price_tax = fields.Float(compute="_compute_amount", string="Tax", store=True)

    production_complete_date = fields.Date(
        # readonly=True,
        # required=True,
        string="Production Complete Date",
        # default=fields.Datetime.now,
        # states={"draft": [("readonly", False)]},
        help="Foreign Purchase Order Production Complete date.",
    )

    handover_date = fields.Date(
        # readonly=True,
        # required=True,
        string="Handover Date",
        # default=fields.Datetime.now,
        # states={"draft": [("readonly", False)]},
        help="Foreign Purchase Order Handover date.",
    )
    expected_shipment_date = fields.Date(
        # readonly=True,
        # required=True,
        string="Expected Shipment Date",
        # default=fields.Datetime.now,
        # states={"draft": [("readonly", False)]},
        help="Foreign Purchase Order Expected Shipment date.",
    )
    planed_arrival_date_warehouse = fields.Date(
        # readonly=True,
        # required=True,
        string="Planed Arrival Date Warehouse",
        # default=fields.Datetime.now,
        # states={"draft": [("readonly", False)]},
        help="Foreign Purchase Order Arrival date.",
    )
    bank_payment = fields.Float(string='Bank Payment')
    remaining_bank_payment=fields.Float()
    local_payment = fields.Float(string='Local Payment')
    # total = fields.Monetary(string='Total', compute='_get_total', store=True)
    # commercial_inv=fields.Many2one('account.move',string='C/I No')
    productional_inv=fields.Char(string='P/I No')
    bill_no=fields.Char(string='B/L No')
    bill_date=fields.Date(
        # readonly=True,
        # required=True,
        string="Bill Date",
        default=fields.Datetime.now,
        # states={"draft": [("readonly", False)]},
        help="Foreign Purchase Bill date.",
    )

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    lc_number=fields.Many2many('usl.lc.management','foreign_purchase_lc_rel',string="L/C No")

    # @api.onchange('order_id.state')
    # def suggest_bank_payment(self):
    #     for rec in self:
    #         rec.bank_payment=rec.price_unit

    def write(self,vals):
        if 'bank_payment' in vals and 'local_payment' not in vals:
            price_unit=self.price_unit
            total_bank_local=vals['bank_payment']
            if price_unit!=total_bank_local:
                raise ValidationError(_("Price unit and sum of bank & local payment is not equal for product: (%s), Please fix it for further operation!!!"%(self.product_id.product_tmpl_id.name)))
            else:
                res = super(ForeignPurchaseOrderLine, self).write(vals)
            # print('*********')
        if 'local_payment' in vals and 'bank_payment' not in vals:
            price_unit=self.price_unit
            total_bank_local=vals['local_payment']
            if price_unit!=total_bank_local:
                raise ValidationError(_("Price unit and sum of bank & local payment is not equal for product: (%s), Please fix it for further operation!!!"%(self.product_id.product_tmpl_id.name)))
            else:
                res = super(ForeignPurchaseOrderLine, self).write(vals)
        if 'bank_payment' in vals and 'local_payment' in vals:
            price_unit = self.price_unit
            total_bank_local = vals['bank_payment']+vals['local_payment']
            if price_unit != total_bank_local:
                raise ValidationError(
                    _("Price unit and sum of bank & local payment is not equal for product: (%s), Please fix it for further operation!!!" % (
                        self.product_id.product_tmpl_id.name)))
            else:
                res = super(ForeignPurchaseOrderLine, self).write(vals)
        if 'lc_number' in vals:
            # query="select sum(remaining_amount) from usl_lc_management where id in {}".format(tuple(vals['lc_number'][0][2]))
            # self._cr.execute(query=query)
            # get_lc_details=self._cr.fetchone()
            # for rec in self:
            #     for
            # if get_lc_details[0]>
            # print(self.lc_number.ids)
            # # if len(self.lc_number.ids)>0:
            # #     for lc in self.lc_number.ids:
            # #         get_purchase_wise_lc_history="select * from purchase_wise_lc_history where lc_id={}".format(lc)
            # #         remaining_bank_payment=lc.remaining_bank_payment+(get_purchase_wise_lc_history./lc.)
            # print(vals['lc_number'][0][2])
            # if len(vals['lc_number'][0][2])>0:
            #     # for model in self.lc_number.ids:
            #     #     for val in vals['lc_number'][0][2]:
            #     #         if model==val:
            #
            #     for rec in self:
            #         total_lc=0
            #         flag=False
            #         for lc in vals['lc_number'][0][2]:
            #             get_lc = self.env['usl.lc.management'].browse(lc)
            #             total_lc+=get_lc.remaining_amount
            #             # if len(rec.lc_number.ids) > len(vals['lc_number'][0][2]):
            #         if rec.invoiced_uom_qty == 0:
            #             if total_lc>=rec.remaining_bank_payment*rec.original_uom_qty:
            #                 # flag=True
            #
            #                 for lc in vals['lc_number'][0][2]:
            #                     get_lc=self.env['usl.lc.management'].browse(lc)
            #                     print(get_lc)
            #                     # if rec.invoiced_uom_qty==0:
            #                     if get_lc.remaining_amount<rec.remaining_bank_payment*rec.original_uom_qty:
            #                         reserved_amount=get_lc.remaining_amount
            #                         remaining_amount=0
            #                         query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
            #                             reserved_amount, remaining_amount, get_lc.lc_no)
            #                         print(query)
            #                         self._cr.execute(query=query)
            #
            #                         remaining_bank_payment= ((rec.remaining_bank_payment*rec.original_uom_qty) - reserved_amount)/rec.original_uom_qty
            #                         query = "update foreign_purchase_order_line set remaining_bank_payment={} where id='{}'".format(
            #                            remaining_bank_payment, rec.id)
            #                         print(query)
            #                         self._cr.execute(query=query)
            #
            #                         query="select max(id) from purchase_wise_lc_history"
            #                         self._cr.execute(query=query)
            #                         id=self._cr.fetchone()
            #                         max_id=0
            #                         if id[0]==None:
            #                             max_id=1
            #                         else:
            #                             max_id=id[0]+1
            #                         query="insert into purchase_wise_lc_history values({},{},{},{},{})".format(max_id,rec.order_id.id,rec.id,lc,float(reserved_amount))
            #                         print(query)
            #                         self._cr.execute(query=query)
            #                         self._cr.commit()
            #
            #
            #                     if get_lc.remaining_amount == rec.remaining_bank_payment*rec.original_uom_qty:
            #                         reserved_amount = rec.remaining_bank_payment*rec.original_uom_qty
            #                         remaining_amount = 0
            #                         query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
            #                             reserved_amount, remaining_amount, get_lc.lc_no)
            #                         print(query)
            #                         self._cr.execute(query=query)
            #                         remaining_bank_payment = ((rec.remaining_bank_payment * rec.original_uom_qty) - reserved_amount) / rec.original_uom_qty
            #                         query = "update foreign_purchase_order_line set remaining_bank_payment={} where id='{}'".format(
            #                             remaining_bank_payment , rec.id)
            #                         print(query)
            #                         self._cr.execute(query=query)
            #                         query = "select max(id) from purchase_wise_lc_history"
            #                         self._cr.execute(query=query)
            #                         id = self._cr.fetchone()
            #                         max_id = 0
            #                         if id[0] == None:
            #                             max_id = 1
            #                         else:
            #                             max_id = id[0] + 1
            #                         query = "insert into purchase_wise_lc_history values({},{},{},{},{})".format(max_id,rec.order_id.id,rec.id,lc,float(reserved_amount))
            #                         print(query)
            #                         self._cr.execute(query=query)
            #                         self._cr.commit()
            #                         break
            #
            #                     if get_lc.remaining_amount > rec.remaining_bank_payment*rec.original_uom_qty:
            #                         reserved_amount = rec.remaining_bank_payment*rec.original_uom_qty
            #                         remaining_amount = get_lc.remaining_amount-reserved_amount
            #                         query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
            #                             reserved_amount, remaining_amount, get_lc.lc_no)
            #                         print(query)
            #                         self._cr.execute(query=query)
            #                         remaining_bank_payment = ((rec.remaining_bank_payment * rec.original_uom_qty) - reserved_amount) / rec.original_uom_qty
            #                         query = "update foreign_purchase_order_line set remaining_bank_payment={} where id='{}'".format(
            #                             remaining_bank_payment , rec.id)
            #                         print(query)
            #                         self._cr.execute(query=query)
            #                         query = "select max(id) from purchase_wise_lc_history"
            #                         self._cr.execute(query=query)
            #                         id = self._cr.fetchone()
            #                         max_id = 0
            #                         if id[0] == None:
            #                             max_id = 1
            #                         else:
            #                             max_id = id[0] + 1
            #                         query = "insert into purchase_wise_lc_history values({},{},{},{},{})".format(max_id,rec.order_id.id,rec.id,lc,float(reserved_amount))
            #                         print(query)
            #                         self._cr.execute(query=query)
            #                         self._cr.commit()
            #                         break
            #             else:
            #                 error_msg = "Insufficient LC Amount"
            #                 # raise ValidationError(error_msg)
            #                 return {
            #                     'warning': {
            #                         'title': 'Warning!',
            #                         'message': error_msg}
            #                 }





            #if after save remove both "LC"
            # else:
                # for rec in self:
                #     bank_payment=rec.bank_payment
                #     for lc in rec.lc_number.ids:
                #         get_lc = self.env['usl.lc.management'].browse(lc)
                #         if bank_payment<get_lc.draft_amount:
                #
                    # for lc in rec.lc_number.ids:
                    #     get_lc = self.env['usl.lc.management'].browse(lc)
                    #     print(get_lc)
                    #     if get_lc.reserved_amount>rec.bank_payment:
                    #         reserved_amount=get_lc.reserved_amount-rec.bank_payment
                    #     else:
                    #         reserved_amount=0
                    #     # reserved_amount = get_lc.re,
                    #     remaining_amount = get_lc.draft_amount - reserved_amount
                    #     print(reserved_amount)
                    #     query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
                    #         reserved_amount, remaining_amount, get_lc.lc_no)
                    #     print(query)
                    #     self._cr.execute(query=query)
                    # print(rec.lc_number.ids)
            res = super(ForeignPurchaseOrderLine, self).write(vals)
        else:
            res=super(ForeignPurchaseOrderLine,self).write(vals)
            return res
        # print(self)

    @api.onchange('lc_number')
    def check_amount_satisfied_with_bank_payment(self):
        for rec in self:
            if len(rec.ids) > 0:
                flag = 0
                for lc_no in rec.lc_number:
                    if lc_no.lc_no == 'Direct':
                        flag = 1

                if flag == 0:
                    get_po_id = self.env['foreign.purchase.order.line'].search([('id', '=', rec.ids[0])]).order_id.id
                    if len(rec.lc_number) > 0:
                        get_exists_all_p_w_lc_h = self.env['purchase.wise.lc.history'].search_count(
                            [('po_line_id', '=', rec.ids[0])])
                        if len(rec.lc_number) > get_exists_all_p_w_lc_h:
                            for lc_id in rec.lc_number.ids:
                                get_exists_in_p_w_lc_h = self.env['purchase.wise.lc.history'].search(
                                    [('po_line_id', '=', rec.ids[0]), ('lc_id', '=', lc_id)])

                                print(get_exists_in_p_w_lc_h)
                                if not get_exists_in_p_w_lc_h:
                                    lc_details = self.env['usl.lc.management'].search([('id', '=', lc_id)])
                                    lc_remaining_amount = lc_details.remaining_amount
                                    lc_reserved_amount = lc_details.reserved_amount
                                    po_line_qty = rec.original_uom_qty
                                    remaining_bank_payment = rec.remaining_bank_payment * po_line_qty
                                    # if lc_remaining_amount<(remaining_bank_payment*rec.original_uom_qty):

                                    # else:
                                    # remaining_bank_payment_after_lc=0
                                    if remaining_bank_payment != 0:
                                        if lc_remaining_amount < remaining_bank_payment:
                                            remaining_bank_payment_after_lc = remaining_bank_payment - (
                                                    lc_remaining_amount / rec.original_uom_qty)
                                            # update foreign_purchase_order_line
                                            query = """update foreign_purchase_order_line set remaining_bank_payment={} where id={}""".format(
                                                remaining_bank_payment_after_lc, rec.ids[0])
                                            self._cr.execute(query=query)
                                            self._cr.commit()

                                            # Update usl_lc_management
                                            query = "update usl_lc_management set remaining_amount={},reserved_amount={} where id={}".format(
                                                lc_details.remaining_amount - (
                                                            remaining_bank_payment_after_lc * po_line_qty),
                                                lc_remaining_amount + (remaining_bank_payment_after_lc * po_line_qty),
                                                lc_id)
                                            self._cr.execute(query=query)
                                            self._cr.commit()

                                            # Create in purchase_wise_lc_history
                                            purchase_wise_lc_history = self.env['purchase.wise.lc.history']
                                            val_list = [{
                                                'po_id': get_po_id,
                                                'po_line_id': rec.ids[0],
                                                'lc_id': lc_id,
                                                'taking_amount_from_lc': float(lc_remaining_amount)
                                            }]
                                            purchase_wise_lc_history.sudo().create(val_list)

                                            # Create foreign_purchase_lc_rel
                                            query = "insert into foreign_purchase_lc_rel values({},{})".format(
                                                rec.ids[0], lc_id)
                                            self._cr.execute(query=query)
                                            self._cr.commit()

                                            error_msg = "Insufficient LC Amount, L/C No : %s " % lc_details.lc_no
                                            return {
                                                'warning': {
                                                    'title': 'Warning!',
                                                    'message': error_msg}
                                            }
                                        else:
                                            remaining_bank_payment_after_lc = 0
                                            # update foreign_purchase_order_line
                                            query = """update foreign_purchase_order_line set remaining_bank_payment={} where id={}""".format(
                                                remaining_bank_payment_after_lc, rec.ids[0])
                                            self._cr.execute(query=query)
                                            self._cr.commit()

                                            # Update usl_lc_management
                                            query = "update usl_lc_management set remaining_amount={},reserved_amount={} where id={}".format(
                                                lc_details.remaining_amount - remaining_bank_payment,
                                                lc_details.reserved_amount + remaining_bank_payment, lc_id)
                                            self._cr.execute(query=query)
                                            self._cr.commit()

                                            # Create in purchase_wise_lc_history
                                            purchase_wise_lc_history = self.env['purchase.wise.lc.history']
                                            val_list = [{
                                                'po_id': get_po_id,
                                                'po_line_id': rec.ids[0],
                                                'lc_id': lc_id,
                                                'taking_amount_from_lc': float(remaining_bank_payment)
                                            }]
                                            purchase_wise_lc_history.sudo().create(val_list)

                                            # Create foreign_purchase_lc_rel
                                            query = "insert into foreign_purchase_lc_rel values({},{})".format(
                                                rec.ids[0],
                                                lc_id)
                                            self._cr.execute(query=query)
                                            self._cr.commit()
                                    else:
                                        raise ValidationError(
                                            _("Product bank payment already satisfied!!!."))


                                else:
                                    continue

                        if len(rec.lc_number) < get_exists_all_p_w_lc_h:
                            get_deleted_relational_data = self.env['purchase.wise.lc.history'].search(
                                [('lc_id', 'not in', tuple(rec.lc_number.ids)), ('po_line_id', '=', rec.ids[0])])
                            lc_details = self.env['usl.lc.management'].search(
                                [('id', '=', get_deleted_relational_data.lc_id)])
                            # update purchase_order_line
                            po_line_qty = rec.original_uom_qty
                            remaining_bank_payment = rec.remaining_bank_payment + (
                                        get_deleted_relational_data.taking_amount_from_lc / po_line_qty)
                            query = """update foreign_purchase_order_line set remaining_bank_payment={} where id={}""".format(
                                remaining_bank_payment, rec.ids[0])
                            self._cr.execute(query=query)
                            self._cr.commit()

                            # delete foreign_purchase_lc_rel
                            query = " delete from foreign_purchase_lc_rel where foreign_purchase_order_line_id={} and usl_lc_management_id={}".format(
                                rec.ids[0],
                                get_deleted_relational_data.lc_id)
                            self._cr.execute(query=query)
                            self._cr.commit()

                            # Update usl_lc_management
                            query = "update usl_lc_management set remaining_amount={},reserved_amount={} where id={}".format(
                                lc_details.remaining_amount + get_deleted_relational_data.taking_amount_from_lc,
                                lc_details.reserved_amount - get_deleted_relational_data.taking_amount_from_lc,
                                get_deleted_relational_data.lc_id)
                            self._cr.execute(query=query)
                            self._cr.commit()

                            # delete purchase_wise_lc_history
                            query = """delete from purchase_wise_lc_history where po_line_id={} and lc_id={}""".format(
                                rec.ids[0], get_deleted_relational_data.lc_id)
                            self._cr.execute(query=query)
                            self._cr.commit()

                    if len(rec.lc_number) == 0:
                        query = "select * from purchase_wise_lc_history where po_line_id={}".format(rec.ids[0])
                        self._cr.execute(query=query)
                        get_tracking_data = self._cr.fetchall()
                        if len(get_tracking_data) > 0:
                            for trck_data in get_tracking_data:
                                query = "select * from usl_lc_management where id={}".format(trck_data[4])
                                self._cr.execute(query=query)
                                get_lc_data = self._cr.fetchone()
                                taking_amount_from_lc = trck_data[5]
                                query = "update usl_lc_management set remaining_amount={},reserved_amount={} where id={}".format(
                                    get_lc_data[56] + taking_amount_from_lc,
                                    get_lc_data[51] - taking_amount_from_lc, trck_data[4])
                                self._cr.execute(query=query)
                                self._cr.commit()
                                remaining_bank_payment = taking_amount_from_lc / rec.original_uom_qty
                                query = "update foreign_purchase_order_line set remaining_bank_payment={} where id={}".format(
                                    rec.remaining_bank_payment + remaining_bank_payment, rec.ids[0])
                                self._cr.execute(query=query)
                                query = "delete from foreign_purchase_lc_rel where foreign_purchase_order_line_id={}".format(
                                    rec.ids[0])
                                print(query)
                                self._cr.execute(query=query)
                                query = "delete from purchase_wise_lc_history where po_line_id={} and lc_id={}".format(
                                    rec.ids[0], trck_data[4])
                                print(query)
                                self._cr.execute(query=query)
                                self._cr.commit()
    # @api.onchange('lc_number')
    # def check_amount_satisfied_with_bank_payment(self):
    #
    #     for rec in self:
    #         print(rec.ids)
    #         if len(rec.ids) > 0:
    #             flag=0
    #             for lc_no in rec.lc_number:
    #                 if lc_no.lc_no=='Direct':
    #                     flag=1
    #
    #             if flag==0:
    #                 total_lc=0.0
    #                 for inner_rec in self:
    #                     for inner_lc in inner_rec.lc_number:
    #                         total_lc+=inner_lc.remaining_amount
    #
    #                 print(len(rec.lc_number))
    #
    #                 query="select order_id from foreign_purchase_order_line where id={}".format(rec.ids[0])
    #                 self._cr.execute(query=query)
    #                 get_po_id=self._cr.fetchone()
    #                 print(rec.id)
    #                 lc_remaining_amount=0.0
    #                 if len(rec.lc_number)==0:
    #                     query = "select * from purchase_wise_lc_history where po_line_id={}".format(rec.ids[0])
    #                     self._cr.execute(query=query)
    #                     get_tracking_data = self._cr.fetchall()
    #                     if len(get_tracking_data) > 0:
    #                         for trck_data in get_tracking_data:
    #                             query = "select * from usl_lc_management where id={}".format(trck_data[3])
    #                             self._cr.execute(query=query)
    #                             get_lc_data = self._cr.fetchone()
    #                             taking_amount_from_lc = trck_data[4]
    #                             query = "update usl_lc_management set remaining_amount={},reserved_amount={} where id={}".format(
    #                                 get_lc_data[56] + taking_amount_from_lc,
    #                                 get_lc_data[51] - taking_amount_from_lc,trck_data[3])
    #                             self._cr.execute(query=query)
    #                             # self._cr.commit()
    #                             remaining_bank_payment = taking_amount_from_lc / rec.original_uom_qty
    #                             query = "update foreign_purchase_order_line set remaining_bank_payment={} where id={}".format(
    #                                 rec.remaining_bank_payment + remaining_bank_payment, rec.ids[0])
    #                             self._cr.execute(query=query)
    #                             query = "delete from foreign_purchase_lc_rel where foreign_purchase_order_line_id={}".format(
    #                                 rec.ids[0])
    #                             print(query)
    #                             self._cr.execute(query=query)
    #                             query = "delete from purchase_wise_lc_history where po_line_id={}".format(
    #                                 rec.ids[0])
    #                             print(query)
    #                             self._cr.execute(query=query)
    #                             self._cr.commit()
    #                 if len(rec.lc_number) >0:
    #                     for lc in rec.lc_number:
    #                         print(lc.remaining_amount)
    #                         # print("Hello")
    #                         lc_remaining_amount += lc.remaining_amount
    #                     for lc in rec.lc_number:
    #                         print(lc_remaining_amount)
    #                         print(lc.ids)
    #                         if rec.invoiced_uom_qty==0:
    #
    #                             if (rec.remaining_bank_payment*rec.original_uom_qty)>lc_remaining_amount:
    #                                 # rec.lc_number=rec.lc_number
    #                                 error_msg="Insufficient LC Amount, L/C No : %s "%rec.lc_number.lc_no
    #                                 # raise ValidationError(error_msg)
    #                                 return {
    #                                     'warning': {
    #                                         'title': 'Warning!',
    #                                         'message': error_msg}
    #                                 }
    #                             else:
    #                                 print(rec.ids)
    #                                 # if lc!=None:
    #                                 #     query = "select * from purchase_wise_lc_history where po_line_id={} and lc_id!={}".format(rec.ids[0],lc.ids[0])
    #                                 # else:
    #                                 query = "select * from purchase_wise_lc_history where po_line_id={} and lc_id={}".format(rec.ids[0],lc.ids[0])
    #                                 self._cr.execute(query=query)
    #                                 get_tracking_data = self._cr.fetchall()
    #
    #                                 query = "select * from purchase_wise_lc_history where po_line_id={} ".format(
    #                                     rec.ids[0])
    #                                 self._cr.execute(query=query)
    #                                 get_track_count=self._cr.fetchall()
    #                                 get_tracking_data_for_deleted=[]
    #                                 if len(get_track_count)>len(lc.ids):
    #                                     query = "select * from purchase_wise_lc_history where po_line_id={} and lc_id!={}".format(
    #                                         rec.ids[0], lc.ids[0])
    #                                     self._cr.execute(query=query)
    #                                     get_tracking_data_for_deleted = self._cr.fetchall()
    #
    #                                 if len(get_tracking_data) > 0 :
    #                                     for trck_data in get_tracking_data:
    #
    #                                         # if  trck_data[3]==lc.ids[0]:
    #                                         query = "select * from usl_lc_management where id={}".format(lc.ids[0])
    #                                         self._cr.execute(query=query)
    #                                         get_lc_data = self._cr.fetchone()
    #                                         taking_amount_from_lc = trck_data[4]
    #                                         query = "update usl_lc_management set remaining_amount={},reserved_amount={} where id={}".format(
    #                                             get_lc_data[56] + taking_amount_from_lc,
    #                                             get_lc_data[51] - taking_amount_from_lc,trck_data[3])
    #                                         self._cr.execute(query=query)
    #                                         # self._cr.commit()
    #                                         remaining_bank_payment = taking_amount_from_lc / rec.original_uom_qty
    #                                         query = "update foreign_purchase_order_line set remaining_bank_payment={} where id={}".format(
    #                                             rec.remaining_bank_payment + remaining_bank_payment, rec.ids[0])
    #                                         self._cr.execute(query=query)
    #                                         query = "delete from foreign_purchase_lc_rel where foreign_purchase_order_line_id={}".format(rec.ids[0])
    #
    #                                         print(query)
    #                                         self._cr.execute(query=query)
    #                                         query = "delete from purchase_wise_lc_history where po_line_id={}".format(
    #                                             rec.ids[0])
    #                                         print(query)
    #                                         self._cr.execute(query=query)
    #                                         self._cr.commit()
    #                                 if len(get_tracking_data_for_deleted)>0:
    #                                     for trck_data in get_tracking_data_for_deleted:
    #
    #                                         # if  trck_data[3]==lc.ids[0]:
    #                                         query = "select * from usl_lc_management where id={}".format(trck_data[3])
    #                                         self._cr.execute(query=query)
    #                                         get_lc_data = self._cr.fetchone()
    #                                         taking_amount_from_lc = trck_data[4]
    #                                         query = "update usl_lc_management set remaining_amount={},reserved_amount={} where id={}".format(
    #                                             get_lc_data[56] + taking_amount_from_lc,
    #                                             get_lc_data[51] - taking_amount_from_lc,trck_data[3])
    #                                         self._cr.execute(query=query)
    #                                         # self._cr.commit()
    #                                         remaining_bank_payment = taking_amount_from_lc / rec.original_uom_qty
    #                                         query = "update foreign_purchase_order_line set remaining_bank_payment={} where id={}".format(
    #                                             rec.remaining_bank_payment + remaining_bank_payment, rec.ids[0])
    #                                         self._cr.execute(query=query)
    #                                         query = "delete from foreign_purchase_lc_rel where foreign_purchase_order_line_id={}".format(rec.ids[0])
    #
    #                                         print(query)
    #                                         self._cr.execute(query=query)
    #                                         query = "delete from purchase_wise_lc_history where po_line_id={}".format(
    #                                             rec.ids[0])
    #                                         print(query)
    #                                         self._cr.execute(query=query)
    #                                         self._cr.commit()
    #                                 # **************************************************************************************
    #                                 if lc.remaining_amount < rec.remaining_bank_payment * rec.original_uom_qty:
    #                                     # total_lc=0.0
    #                                     # for inner_rec in self:
    #                                     #     for inner_lc in inner_rec.lc_number:
    #                                     #         total_lc+=inner_lc.remaining_amount
    #                                     # if total_lc<rec.bank_payment:
    #                                     #     error_msg = "Insufficient LC Amount"
    #                                     #     return {
    #                                     #         'warning': {
    #                                     #             'title': 'Warning!',
    #                                     #             'message': error_msg}
    #                                     #     }
    #                                     # else:
    #                                     reserved_amount = lc.remaining_amount
    #                                     remaining_amount = 0
    #                                     query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
    #                                         reserved_amount, remaining_amount, lc.lc_no)
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     remaining_bank_payment = ((
    #                                                                           rec.remaining_bank_payment * rec.original_uom_qty) - reserved_amount) / rec.original_uom_qty
    #                                     query = "update foreign_purchase_order_line set remaining_bank_payment={} where id='{}'".format(
    #                                         remaining_bank_payment, rec.ids[0])
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     query = "select max(id) from purchase_wise_lc_history"
    #                                     self._cr.execute(query=query)
    #                                     id = self._cr.fetchone()
    #                                     max_id = 0
    #                                     if id[0] == None:
    #                                         max_id = 1
    #                                     else:
    #                                         max_id = id[0] + 1
    #                                     query = "insert into purchase_wise_lc_history values({},{},{},{},{})".format(max_id,
    #                                                                                                                  get_po_id[
    #                                                                                                                      0],
    #                                                                                                                  rec.ids[0],
    #                                                                                                                  lc.ids[0],
    #                                                                                                                  float(
    #                                                                                                                      reserved_amount))
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #
    #                                     query = "insert into foreign_purchase_lc_rel values({},{})".format(rec.ids[0],
    #                                                                                                        lc.ids[0])
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     self._cr.commit()
    #                                     # ************************************************************************************
    #                                     # ************************************************************************************
    #                                     # reserved_amount = lc.remaining_amount
    #                                     # remaining_amount = 0
    #                                     # query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
    #                                     #     reserved_amount, remaining_amount, lc.lc_no)
    #                                     # print(query)
    #                                     # self._cr.execute(query=query)
    #                                     #
    #                                     # remaining_bank_payment = ((
    #                                     #                                       rec.remaining_bank_payment * rec.original_uom_qty) - reserved_amount) / rec.original_uom_qty
    #                                     # query = "update foreign_purchase_order_line set remaining_bank_payment={} where id='{}'".format(
    #                                     #     remaining_bank_payment, rec.id)
    #                                     # print(query)
    #                                     # self._cr.execute(query=query)
    #                                     #
    #                                     # query = "select max(id) from purchase_wise_lc_history"
    #                                     # self._cr.execute(query=query)
    #                                     # id = self._cr.fetchone()
    #                                     # max_id = 0
    #                                     # if id[0] == None:
    #                                     #     max_id = 1
    #                                     # else:
    #                                     #     max_id = id[0] + 1
    #                                     # query = "insert into purchase_wise_lc_history values({},{},{},{},{})".format(max_id,
    #                                     #                                                                              rec.order_id.id,
    #                                     #                                                                              rec.id, lc,
    #                                     #                                                                              float(
    #                                     #                                                                                  reserved_amount))
    #                                     # print(query)
    #                                     # self._cr.execute(query=query)
    #                                     # self._cr.commit()
    #                                 if lc.remaining_amount == rec.remaining_bank_payment*rec.original_uom_qty:
    #                                     # total_lc = 0.0
    #                                     # for rec in self:
    #                                     #     for lc in rec.lc_number:
    #                                     #         total_lc += lc.remaining_amount
    #                                     # if total_lc < rec.bank_payment:
    #                                     #     error_msg = "Insufficient LC Amount"
    #                                     #     return {
    #                                     #         'warning': {
    #                                     #             'title': 'Warning!',
    #                                     #             'message': error_msg}
    #                                     #     }
    #                                     # else:
    #                                     reserved_amount = rec.remaining_bank_payment*rec.original_uom_qty
    #                                     remaining_amount = 0
    #                                     query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
    #                                         reserved_amount, remaining_amount, lc.lc_no)
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     remaining_bank_payment = ((
    #                                                                       rec.remaining_bank_payment * rec.original_uom_qty) - reserved_amount) / rec.original_uom_qty
    #                                     query = "update foreign_purchase_order_line set remaining_bank_payment={} where id='{}'".format(
    #                                         remaining_bank_payment, rec.ids[0])
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     query = "select max(id) from purchase_wise_lc_history"
    #                                     self._cr.execute(query=query)
    #                                     id = self._cr.fetchone()
    #                                     max_id = 0
    #                                     if id[0] == None:
    #                                         max_id = 1
    #                                     else:
    #                                         max_id = id[0] + 1
    #                                     query = "insert into purchase_wise_lc_history values({},{},{},{},{})".format(max_id,
    #                                                                                                                  get_po_id[
    #                                                                                                                      0],
    #                                                                                                                  rec.ids[0],
    #                                                                                                                  lc.ids[0],
    #                                                                                                                  float(
    #                                                                                                                      reserved_amount))
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #
    #                                     query = "insert into foreign_purchase_lc_rel values({},{})".format(rec.ids[0],
    #                                                                                                        lc.ids[0])
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     self._cr.commit()
    #
    #                                     # **************************************************************************************************
    #                                     # **************************************************************************************************
    #                                     # reserved_amount = rec.remaining_bank_payment*rec.original_uom_qty
    #                                     # remaining_amount = 0
    #                                     # query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
    #                                     #     reserved_amount, remaining_amount, lc.lc_no)
    #                                     # print(query)
    #                                     # self._cr.execute(query=query)
    #                                     # remaining_bank_payment = ((rec.remaining_bank_payment * rec.original_uom_qty) - reserved_amount) / rec.original_uom_qty
    #                                     # query = "update foreign_purchase_order_line set remaining_bank_payment={} where id='{}'".format(
    #                                     #     remaining_bank_payment , rec.id)
    #                                     # print(query)
    #                                     # self._cr.execute(query=query)
    #                                     # query = "select max(id) from purchase_wise_lc_history"
    #                                     # self._cr.execute(query=query)
    #                                     # id = self._cr.fetchone()
    #                                     # max_id = 0
    #                                     # if id[0] == None:
    #                                     #     max_id = 1
    #                                     # else:
    #                                     #     max_id = id[0] + 1
    #                                     # query = "insert into purchase_wise_lc_history values({},{},{},{},{})".format(max_id,rec.order_id.id,rec.id,lc,float(reserved_amount))
    #                                     # print(query)
    #                                     # self._cr.execute(query=query)
    #                                     # self._cr.commit()
    #                                     # break
    #
    #                                 if lc.remaining_amount > rec.remaining_bank_payment*rec.original_uom_qty:
    #                                     reserved_amount = rec.remaining_bank_payment*rec.original_uom_qty
    #                                     remaining_amount = lc.remaining_amount-reserved_amount
    #                                     query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
    #                                         reserved_amount, remaining_amount, lc.lc_no)
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     remaining_bank_payment = ((rec.remaining_bank_payment * rec.original_uom_qty) - reserved_amount) / rec.original_uom_qty
    #                                     query = "update foreign_purchase_order_line set remaining_bank_payment={} where id='{}'".format(
    #                                         remaining_bank_payment , rec.ids[0])
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     query = "select max(id) from purchase_wise_lc_history"
    #                                     self._cr.execute(query=query)
    #                                     id = self._cr.fetchone()
    #                                     max_id = 0
    #                                     if id[0] == None:
    #                                         max_id = 1
    #                                     else:
    #                                         max_id = id[0] + 1
    #                                     query = "insert into purchase_wise_lc_history values({},{},{},{},{})".format(max_id,get_po_id[0],rec.ids[0],lc.ids[0],float(reserved_amount))
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #
    #                                     query = "insert into foreign_purchase_lc_rel values({},{})".format(rec.ids[0],lc.ids[0])
    #                                     print(query)
    #                                     self._cr.execute(query=query)
    #                                     self._cr.commit()
    #
    #                                 if total_lc < rec.bank_payment * rec.original_uom_qty:
    #                                     error_msg = "Insufficient LC Amount"
    #                                     return {
    #                                         'warning': {
    #                                             'title': 'Warning!',
    #                                             'message': error_msg}
    #                                     }
    #
    #
    #
    #                                 # **************************************************************************************
    #                                 # query="select * from purchase_wise_lc_history where po_line_id={}".format(rec.id)
    #                                 # self._cr.execute(query=query)
    #                                 # get_teacking_data=self._cr.fetchall()
    #                                 # if get_teacking_data!=None:
    #                                 #     for trck_data in get_teacking_data:
    #                                 #         query="select * from usl_lc_management where id={}".format(trck_data.lc_id)
    #                                 #         self._cr.execute(query=query)
    #                                 #         get_lc_data=self._cr.fetchone()
    #                                 #         taking_amount_from_lc=trck_data.taking_amount_from_lc
    #                                 #         query="update usl_lc_management set remaining_amount={},reserved_amount={}".format(get_lc_data.remaining_amount+taking_amount_from_lc,get_lc_data.remaining_amount-taking_amount_from_lc)
    #                                 #         self._cr.execute(query=query)
    #                                 #         self._cr.commit()
    #                                 #         remaining_bank_payment=taking_amount_from_lc/rec.original_uom_qty
    #                                 #         query = "update foreign_purchase_order_line set remaning_bank_payment={} where id={}".format(
    #                                 #             rec.remaining_bank_payment+remaining_bank_payment,rec.id)
    #                                 #         self._cr.execute(query=query)
    #                                 #         self._cr.commit()
    #                         else:
    #                             if (rec.remaining_bank_payment*rec.remaining_uom_qty)>lc_remaining_amount:
    #                                 # rec.lc_number=rec.lc_number
    #                                 error_msg="Insufficient LC Amount, L/C No : %s "%lc.lc_no
    #                                 # raise ValidationError(error_msg)
    #                                 return {
    #                                     'warning': {
    #                                         'title': 'Warning!',
    #                                         'message': error_msg}
    #                                 }
    #
    #                     # else:
    #                     #     reserved_amount = rec.bank_payment ,
    #                     #     remaining_amount = lc.remaining_amount - rec.bank_payment
    #                     #     print(reserved_amount)
    #                     #     query = "update usl_lc_management set reserved_amount={},remaining_amount={} where lc_no='{}'".format(
    #                     #         reserved_amount[0], remaining_amount, lc.lc_no)
    #                     #     print(query)
    #                     #     self._cr.execute(query=query)
    #
    #                         # values={
    #                         #
    #                         #         'reserved_amount':rec.bank_payment,
    #                         #         'remaining_amount':lc.remaining_amount-rec.bank_payment
    #                         #
    #                         # }
    #                         # rec.lc_number.write(values)
    #                     # lc.reserved_amount=rec.price_subtotal*self.env.ref('base.main_company').currency_id.rate
    #                     # lc.remaining_amount=lc.remaining_amount-(rec.price_subtotal*self.env.ref('base.main_company').currency_id.rate)
    #         else:
    #             return None




    @api.onchange('production_complete_date','handover_date','expected_shipment_date','planed_arrival_date_warehouse')
    def date_validation(self):
        current_date=fields.Date.today()
        for rec in self:

            if rec.production_complete_date!=False and rec.production_complete_date<current_date:
                raise ValidationError("Production Complete Date Must be Equal or Greater than Current Date")
            if rec.handover_date!=False and rec.handover_date<current_date:
                raise ValidationError("Handover Date Must be Equal or Greater than Current Date")
            if rec.expected_shipment_date!=False and rec.expected_shipment_date<current_date:
                raise ValidationError("Expected Shipment Date Must be Equal or Greater than Current Date")
            if rec.planed_arrival_date_warehouse!=False and rec.planed_arrival_date_warehouse<current_date:
                raise ValidationError("Planed Arrival Date Warehouse Date Must be Equal or Greater than Current Date")




    def _format_date(self, date):
        # format date following user language
        lang_model = self.env["res.lang"]
        lang = lang_model._lang_get(self.env.user.lang)
        date_format = lang.date_format
        return datetime.strftime(fields.Date.from_string(date), date_format)

    # def name_get(self):
    #     result = []
    #     if self.env.context.get("from_purchase_order"):
    #         for record in self:
    #             res = "[%s]" % record.order_id.name
    #             if record.date_schedule:
    #                 formatted_date = self._format_date(record.date_schedule)
    #                 res += " - {}: {}".format(_("Date Scheduled"), formatted_date)
    #             res += " ({}: {} {})".format(
    #                 _("remaining"), record.remaining_uom_qty, record.product_uom.name,
    #             )
    #             result.append((record.id, res))
    #         return result
    #     return super().name_get()

    def _get_display_price(self, product):

        seller = product._select_seller(
            partner_id=self.order_id.partner_id,
            quantity=self.original_uom_qty,
            date=self.order_id.date_start
            and fields.Date.from_string(self.order_id.date_start),
            uom_id=self.product_uom,
        )

        if not seller:
            return
        price_unit =0
        # price_unit = (
        #     self.env["account.tax"]._fix_tax_included_price_company(
        #         seller.price,
        #         product.supplier_taxes_id,
        #         (),
        #         # self.purchase_lines.taxes_id,
        #         self.company_id,
        #     )
        #     if seller
        #     else 0.0
        # )
        if (
            price_unit
            and seller
            and self.order_id.currency_id
            and seller.currency_id != self.order_id.currency_id
        ):
            price_unit = seller.currency_id.compute(
                price_unit, self.order_id.currency_id
            )

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        return price_unit

    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        if self.product_id:
            name = self.product_id.name
            if not self.product_uom:
                self.product_uom = self.product_id.uom_id.id
            if self.order_id.partner_id and float_is_zero(
                self.price_unit, precision_digits=precision
            ):
                self.price_unit = self._get_display_price(self.product_id)
            if self.product_id.code:
                name = "[{}] {}".format(name, self.product_id.code)
            if self.product_id.description_purchase:
                name += "\n" + self.product_id.description_purchase
            self.name = name

            fpos = self.order_id.fiscal_position_id
            if self.env.uid == SUPERUSER_ID:
                company_id = self.env.user.company_id.id
                self.taxes_id = fpos.map_tax(
                    self.product_id.supplier_taxes_id.filtered(
                        lambda r: r.company_id.id == company_id
                    )
                )
            else:
                self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)


    def _validate(self):
        try:
            for line in self:
                assert line.price_unit > 0.0, _("Price must be greater than zero")
                assert line.original_uom_qty > 0.0, _(
                    "Quantity must be greater than zero"
                )
        except AssertionError as e:
            raise UserError(e)

    def _prepare_account_move_line(self, move):
        self.ensure_one()
        unit_price = self.price_unit
        unit_price_subtotal = 0.0
        # if self.currency_id.name == 'BDT':
        #     unit_price = self.price_unit
        #     unit_price_subtotal = unit_price * self.original_uom_qty
        #
        # if self.currency_id.name == 'USD':
        #     original_rate = self.env['res.currency.rate'].search(
        #         [('currency_id', '=', self.env.ref('base.main_company').currency_id.id)]).rate
        #     unit_price = self.bank_payment * original_rate + self.local_payment * self.env.ref('base.main_company').currency_id.local_currency
        #     unit_price_subtotal = unit_price * self.original_uom_qty

        if self.product_id.purchase_method == 'purchase':
            qty = self.original_uom_qty - self.invoiced_uom_qty
        else:
            qty=self.original_uom_qty-self.invoiced_uom_qty
            # qty = self.qty_received - self.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
            qty = 0.0

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        return {
            'name': '%s: %s' % (self.order_id.name, self.name),
            'move_id': move.id,
            # 'currency_id': currency and currency.id or False,
            'currency_id': self.currency_id,
            'foreign_purchase_line_id': self.id,
            'date_maturity': move.invoice_date_due,
            'product_uom_id': self.product_uom.id,
            'product_id': self.product_id.id,
            'price_unit': unit_price,
            'quantity': qty,
            'partner_id': move.partner_id.id,
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'display_type': self.display_type,
            'bank_payment':self.bank_payment,
            'local_payment':self.local_payment,
            'original_uom_qty':self.original_uom_qty,
            'invoiced_uom_qty':self.invoiced_uom_qty

            # 'po_price':self.po_price,
            # 'total_po':self.total_po,
            # 'total_os':self.total_os

        }

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity')
    def _compute_qty_invoiced(self):
        for line in self:
            qty = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.move_id.state not in ['cancel']:
                    if inv_line.move_id.type == 'in_invoice':
                        qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                    elif inv_line.move_id.type == 'in_refund':
                        qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
            line.invoiced_uom_qty = qty




