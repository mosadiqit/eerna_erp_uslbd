from odoo import http
from odoo.http import request, Response
from ..main import validate_token
import json

# import firebase_admin
# from firebase_admin import credentials, messaging


class PurchaseListAPI(http.Controller):
    @validate_token
    @http.route('/purchase_list', auth='none', type='http', website=True)
    def purchase_pending_list(self, **vals):
        user = request.env.user
        user_id = user.id
        type = vals['purchase_type']
        if type == 'pending':
            all_prchase = request.env['purchase.order'].search([('state', '=', 'waiting_for_approval')])
            print(all_prchase, user_id)
            purchase_list = list()
            for purchase in all_prchase:
                print('approval line ids = ',purchase.approval_line_ids)
                for approval_line in purchase.approval_line_ids:
                    print('approval line status = ', approval_line.user, approval_line.status)
                    if approval_line.user.id == user_id and approval_line.status == 'waiting':
                        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        url = base_url + '/web#id={}&action=281&model=purchase.order&view_type=form&cids=&menu_id=167'.format(purchase.id)
                        vals = {
                            'user' : approval_line.user.name,
                            'name': purchase.name,
                            'vendor_id' : purchase.partner_id.id,
                            'vendor' : purchase.partner_id.name,
                            'create_uid' : purchase.create_uid.id,
                            'created_by' : purchase.create_uid.name,
                            'status' : approval_line.status,
                            'date': str(purchase.date_order),
                            'url': url,
                        }
                        purchase_list.append(vals)
        elif type == 'approved':
            all_prchase = request.env['purchase.order'].search([('state', 'in', ('purchase', 'waiting_for_approval'))])
            print(all_prchase, user_id)
            purchase_list = list()
            for purchase in all_prchase:
                print('approval line ids = ', purchase.approval_line_ids)
                for approval_line in purchase.approval_line_ids:
                    print('approval line status = ', approval_line.user, approval_line.status)
                    if approval_line.user.id == user_id and approval_line.status == 'approved':
                        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        url = base_url + '/web#id={}&action=281&model=purchase.order&view_type=form&cids=&menu_id=167'.format(purchase.id)
                        vals = {
                            'user': approval_line.user.name,
                            'name': purchase.name,
                            'vendor_id': purchase.partner_id.id,
                            'vendor': purchase.partner_id.name,
                            'create_uid': purchase.create_uid.id,
                            'created_by': purchase.create_uid.name,
                            'status': approval_line.status,
                            'date': str(purchase.date_order),
                            'url': url,
                        }
                        purchase_list.append(vals)
        elif type == 'canceled':
            all_prchase = request.env['purchase.order'].search([('state', '=', 'cancel')])
            print(all_prchase, user_id)
            purchase_list = list()
            for purchase in all_prchase:
                print('approval line ids = ', purchase.approval_line_ids)
                for approval_line in purchase.approval_line_ids:
                    print('approval line status = ', approval_line.user, approval_line.status)
                    if approval_line.user.id == user_id and approval_line.status == 'not_approved':
                        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        url = base_url + '/web#id={}&action=281&model=purchase.order&view_type=form&cids=&menu_id=167'.format(purchase.id)
                        vals = {
                            'user': approval_line.user.name,
                            'name': purchase.name,
                            'vendor_id': purchase.partner_id.id,
                            'vendor': purchase.partner_id.name,
                            'create_uid': purchase.create_uid.id,
                            'created_by': purchase.create_uid.name,
                            'status': approval_line.status,
                            'date': str(purchase.date_order),
                            'url': url,
                        }
                        purchase_list.append(vals)
        return Response(json.dumps({'status' : 'success', 'purchase list': purchase_list}), content_type='application/json;charset=utf-8', status=200)


    @validate_token
    @http.route('/approve_purchase', auth='none', type='json', methods=['POST'], csrf=False)
    def purchase_approve_request(self):
        user = request.env.user
        user_id = user.id
        purchase_name = request.jsonrequest['purchase_name']
        print(purchase_name)
        purchase = request.env['purchase.order'].search([('name', '=', str(purchase_name))])
        if purchase.state != 'purchase':
            for item in purchase.approval_line_ids:
                if item.user.id == user_id and item.status == 'waiting':
                    purchase.confirm_approval()
                    return {'message' : 'Successfully approved'}
                elif item.user.id == user_id and item.status == 'approved':
                    return {'message' : 'Already approved'}
        else:
            return {'message' : 'Already approved'}



    @validate_token
    @http.route('/cancel_purchase', auth='none', type='json', methods=['POST'], csrf=False)
    def purchase_cancel_request(self):
        user = request.env.user
        user_id = user.id
        purchase_name = request.jsonrequest['purchase_name']
        print(purchase_name)
        purchase = request.env['purchase.order'].search([('name', '=', str(purchase_name))])
        for item in purchase.approval_line_ids:
            if item.user.id == user_id and item.status == 'waiting':
                purchase.reject_order()
                return {'message' : 'Purchase Canceled successfully'}
        return {'message' : 'Purchase cannot be Canceled'}

    @validate_token
    @http.route('/update_fcm_token', auth='none', type='json', methods=['POST'], csrf=False)
    def update_fcm_token(self):
        user = request.env.user
        token = request.jsonrequest['token']
        print('old_token = ', user.fcm_token)
        user.write({'fcm_token' : token})
        print('new_token = ', user.fcm_token)