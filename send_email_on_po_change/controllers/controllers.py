# -*- coding: utf-8 -*-
# from odoo import http


# class SendEmailOnPoChange(http.Controller):
#     @http.route('/send_email_on_po_change/send_email_on_po_change/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/send_email_on_po_change/send_email_on_po_change/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('send_email_on_po_change.listing', {
#             'root': '/send_email_on_po_change/send_email_on_po_change',
#             'objects': http.request.env['send_email_on_po_change.send_email_on_po_change'].search([]),
#         })

#     @http.route('/send_email_on_po_change/send_email_on_po_change/objects/<model("send_email_on_po_change.send_email_on_po_change"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('send_email_on_po_change.object', {
#             'object': obj
#         })
