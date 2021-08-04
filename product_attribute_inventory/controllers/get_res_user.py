from odoo import http
from odoo.http import request


class PartnerProvider(http.Controller):

    @http.route(['/odootest/partners'], type='json', auth='user', methods=['POST'])
    def send_users(self, **kwargs):
        print('API working!')
        if len(kwargs) == 0:
           print('all partner returning')
           cr = request.env.cr
           query = """
           SELECT id, name, mobile, city FROM res_partner WHERE active = true
           """
           cr.execute(query)
           partners = cr.dictfetchall()
           return {
               'partners': partners,
           }
        elif len(kwargs) == 1:
           print('One partner returning')
           cr = request.env.cr
           query = """
                       SELECT name, mobile, city FROM res_partner WHERE active = true AND id = %s
                       """ %kwargs['id']  # Assuming that the data from the client contains the id of the partner
           cr.execute(query)
           partner = cr.dictfetchall()
           return {
               'partner': partner,
           }


class RESTAPI(http.Controller):

    @http.route('/api/test-user/', type='json', auth='user')
    def get_user(self):
        print('User API working')
        return {
            'status': 200,
            'response': {
                'data': 'User is authenticated'
            }
        }

    @http.route('/api/test-public/', type='json', auth='public')
    def get_user_public(self):
        print('API working public API')
        return {
            'status': 200,
            'response': {
                'data': 'Working fine public API'
            }
        }
