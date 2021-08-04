from odoo.addons.restful.common import invalid_response, valid_response
from odoo.exceptions import AccessError
from odoo.http import request, Response
import werkzeug.wrappers
from json import dumps
from odoo import http
from .. import main
import datetime
import base64
import json


# For Serializing the create dates
def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

class CustomerInfoAPI(http.Controller):

    @main.validate_token
    @http.route('/customers_info', auth='none', type='http')
    def fetch_all_customers(self, **payload):
        try:
            page_no = payload.get('page_no')  # '5'
            if page_no:
                page_no = int(page_no)

            limit = payload.get('limit')
            if limit:
                limit = int(limit)

            offset = 0
            if page_no and limit:
                offset = page_no * limit

            customers = request.env['res.partner'].sudo().search([], offset=offset, limit=limit)
            data = []
            for customer in customers:
                cus_id = customer.id
                cus_name = customer.name if customer.name else ""
                lat = customer.partner_latitude if customer.partner_latitude else ""
                lon = customer.partner_longitude if customer.partner_longitude else ""
                shop_adrs = customer.contact_address if customer.contact_address else ""
                email = customer.email if customer.email else ""
                img = str(customer.image_1920) if customer.image_1920 else ""
                vals = {
                    'id': cus_id,
                    'customer_name': cus_name,
                    'shop_name': cus_name,
                    'lat': lat,
                    'lon': lon,
                    'shop_address': shop_adrs.strip(),
                    'customer_email': email,
                    'profile_image': img,
                }
                data.append(vals)
            response = dict()
            response['success'] = True
            response['message'] = ''
            response['customers'] = data
            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)
        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)

