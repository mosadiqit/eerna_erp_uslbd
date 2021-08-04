from odoo import api, models, _, fields


class AccountCommonJournalInherit(models.TransientModel):
    _inherit = "account.common.report"

    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='all')