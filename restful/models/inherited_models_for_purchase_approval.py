from odoo import models, fields
# import firebase_admin
# from firebase_admin import credentials, messaging
#
#
# class PurchaseOrderInherit(models.Model):
#     _inherit = 'purchase.order'
#
#     def submit_for_approval(self):
#         res = super(PurchaseOrderInherit, self).submit_for_approval()
#         print('in the gardem.......')
#         approval_ids = self.approval_line_ids
#         for item in approval_ids:
#             print('user = ',item.user.name, item.user.id)
#
#         # Send Push Notification
#         cred = credentials.Certificate("/home/alamin/Documents/ODOO/eerna-erp/custom_module/restful/controllers/approval/serviceAccountKey.json")
#         firebase = firebase_admin.initialize_app(cred)
#         print('firebase = ', firebase)
#
#         purchase_approver_group = self.env.ref('usl_purchase_multilevel_approval.group_purchase_approval_settings')
#         user = purchase_approver_group.users[0]
#         reg_tokens = [str(user.fcm_token)]
#         # reg_tokens = ['eVDs1YViQAmSpYawbuf0K8:APA91bF_1hN3X02-mkBWbdaO3IgJGf4wplbShulZ-0Dvm9Skzp84i0BmvKRAFH2lw2M4KfMrXxaptHKgsmZFHRSYPud9Wq6thRMshhUpBfsJC72S7doT89p7WqBISwmVEkLNUC6AyWI7']
#         msg = 'Purchase order "{}" created by "{}" is waiting for your approval. Please open Uni Manager app to approve purchase request.'.format(self.name, self.create_uid.name)
#         title = 'Purchase order approval required'
#
#         message = messaging.MulticastMessage(
#             notification=messaging.Notification(
#                 title=title,
#                 body=msg
#             ),
#             data = {
#                 'name' : self.name,
#                 'created_by' : self.create_uid.name,
#                 'title' : title,
#                 'message' : msg
#             },
#             tokens=reg_tokens
#         )
#         messaging.send_multicast(message)
#         firebase_admin.delete_app(firebase)
#         return res


class res_users(models.Model):
    _inherit = 'res.users'

    fcm_token = fields.Char()
