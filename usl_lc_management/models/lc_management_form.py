from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from num2words import num2words


class LcManagementForm(models.Model):
    _name = 'usl.lc.management'
    _description = 'LcManagementForm'
    _rec_name = 'lc_no'
    _sql_constraints = [('lc_no_unique', 'unique(lc_no)', 'A L/C NO. must have to be unique.')]

    @api.onchange('draft_amount')
    def int2words(self):
        number = self.draft_amount
        self.draft_amount_in_word = num2words(number, lang='en').title()

    @api.model
    def create(self, vals):
        # print('come crete')
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('usl.lc.sequence') or _('New')
        result = super(LcManagementForm, self).create(vals)
        return result

    def write(self, vals):
        flag = True
        if 'draft_amount' in vals.keys():
            for rec in self:
                if rec.draft_amount > vals.get('draft_amount'):
                    flag = False
                    break
        if flag:
            result = super(LcManagementForm, self).write(vals)
            return result
        else:
            raise ValidationError("Invalid LC Amount.")


    name_seq = fields.Char(string='LC serial', required=True, copy=False, readonly=True,
                           index=True, default=lambda self: _('New'))


    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.currency_set())

    def currency_set(self):
        return self.env['res.currency'].search([('name', 'ilike', 'USD')]).id


    bank_name = fields.Many2one('res.partner', string='Bank Name', required=True)
    bank_state = fields.Char(string='Address state', related='bank_name.street')
    bank_state2 = fields.Char(string='Address state2', related='bank_name.street2')
    bank_city = fields.Char(string='Address City', related='bank_name.city')
    bank_country = fields.Char(string='Address Country', related='bank_name.country_id.name')
    stamp = fields.Binary(string='STAMP')
    lc_no = fields.Char(string='L/C NO.')
    date = fields.Date(string='Date')
    is_mail = fields.Boolean(string='Mail/Airmail', default=False)
    is_teletransmission_in_full = fields.Boolean(string=' Teletransmission in full', default=False)
    is_teletransmission_in = fields.Boolean(string=' Teletransmission in ', default=False)
    is_swift = fields.Boolean(string='Swift', default=False)

    beneficiary_name = fields.Many2one('res.partner', string='Beneficiary\'s Name')
    beneficiary_state = fields.Char(string='Address state', related='beneficiary_name.street')
    beneficiary_state2 = fields.Char(string='Address state2', related='beneficiary_name.street2')
    beneficiary_city = fields.Char(string='Address City', related='beneficiary_name.city')
    beneficiary_country = fields.Char(string='Address Country', related='beneficiary_name.country_id.name')

    openers_name = fields.Many2one('res.partner', string='Opener\'s Name')
    openers_state = fields.Char(string='Address state', related='openers_name.street')
    openers_state2 = fields.Char(string='Address state2', related='openers_name.street2')
    openers_city = fields.Char(string='Address City', related='openers_name.city')
    openers_country = fields.Char(string='Address Country', related='openers_name.country_id.name')
    draft_amount = fields.Monetary(string='Draft amount')
    draft_amount_in_word = fields.Char(string='In words')
    is_at_sight = fields.Boolean(string='At sight', default=False)
    days_da_or_dp = fields.Char(string='days DA/DP')
    is_cif = fields.Boolean(string='CIF', default=False)
    is_fob = fields.Boolean(string='FOB', default=False)
    is_cfr = fields.Boolean(string='C F R', default=False)
    is_us = fields.Boolean(string='Us', default=False)
    is_them = fields.Boolean(string='Them', default=False)
    country_of_origin = fields.Many2one('res.country', string='Country of origin')
    utilities = fields.Text(string='Please specify commodities, price, quantity, indent no, etc.')
    is_commercial_invoice_in_sixtuplicate = fields.Boolean(string='Commercial Invoice in sixtuplicate', default=False)
    is_custom_invoice_in_duplicate = fields.Boolean(string='Special custom invoice in duplicate', default=False)
    bangladesh_bank_reg_no = fields.Char(string='Bangladesh Bank Registration No.')
    import_licence = fields.Char(string='Import Licence/LCAF No.')
    hs_code = fields.Many2many('other.tax.info', string='H.S. code')
    irc_no = fields.Char(string='IRC. No.')
    is_others_doc = fields.Boolean(string='Other documents', default=False)
    other_documents = fields.Text(string='Other documents(name of the issuer)')
    is_clean_bill_landing = fields.Boolean(string='Full set of clean on board bills of landing ', default=False)
    is_airway_bill = fields.Boolean(string='Airway Bill', default=False)
    is_post_parcel = fields.Boolean(string="Post parcel", default=False)
    is_rel_to_shipment = fields.Boolean(string='Relating to shipment', default=False)
    is_tr = fields.Boolean(string='T/R', default=False)
    is_rr = fields.Boolean(string='R/R', default=False)
    shipping_address = fields.Text(string='From')
    destination_address = fields.Text(string='To')
    insurance_cover_note_policy = fields.Char(string='Insurance cover note/policy no.')
    insurance_date = fields.Char(string='Date')
    insurance_amount = fields.Monetary(string='Amount Tk.')

    name_of_insurance_company = fields.Many2one('res.partner')
    insurance_company_state = fields.Char(string='Address state', related='name_of_insurance_company.street')
    insurance_company_state2 = fields.Char(string='Address state2', related='name_of_insurance_company.street2')
    insurance_company_city = fields.Char(string='Address City', related='name_of_insurance_company.city')
    insurance_company_country = fields.Char(string='Address Country',
                                            related='name_of_insurance_company.country_id.name')
    is_part_shipment = fields.Boolean(string='Part shipment', default=False)
    is_part_allowed = fields.Boolean(string='Allowed', default=False)
    is_part_prohibited = fields.Boolean(string='Prohibited', default=False)

    is_tran_shipment = fields.Boolean(string='Transhipment', default=False)
    is_tran_allowed = fields.Boolean(string='Allowed', default=False)
    is_tran_prohibited = fields.Boolean(string='Prohibited', default=False)
    last_date_of_shipment = fields.Date(string='Last date of shipment')
    last_date_of_negotiation = fields.Date(string='Last date of negotiation')
    terms_and_conditions = fields.Text(string='Terms and Conditions')

    reserved_amount=fields.Integer(default=0.0)
    remaining_amount=fields.Integer(default=0.0)

    @api.onchange('draft_amount')
    def _get_amount(self):
        for rec in self:
            rec.remaining_amount=rec.draft_amount



