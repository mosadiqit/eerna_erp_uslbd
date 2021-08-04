import json
from odoo.exceptions import AccessError
from odoo.http import request, Response
from ..main import validate_token
from odoo import http, _
from .. import main
import datetime
import pytz

class AddOutstanding(http.Controller):
    @validate_token
    @http.route('/add_outstanding', methods=['post'], auth='none', csrf=False, type='json')
    def add_outstanding(self):
        if not request.jsonrequest['invoice_name'] and not request.jsonrequest['outstanding']:
            return {'message' : 'value is missing.'}
        else:
            invoice = request.env['account.move'].search([('name', '=', str(request.jsonrequest['invoice_name']))])
            outstanding_line = request.env['account.move.line'].search([('move_name', '=', str(request.jsonrequest['outstanding'])), ('account_internal_type', '=', 'receivable')])

            obj = invoice.js_assign_outstanding_line(outstanding_line.id)
            return {'msg' : 'outstanding successfully added...'}