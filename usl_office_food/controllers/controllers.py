# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request, Response
from ...restful.controllers.main import validate_token
import datetime
import json

class EmployeeEat(http.Controller):
    @http.route('/employee_eat/kiosk_keepalive', auth='user', type='json')
    def kiosk_keepalive(self):
        request.httprequest.session.modified = True
        return {}

class LunchController(http.Controller):
    @validate_token
    @http.route('/food_list', type='http', auth='none')
    def food_list(self, **vals):
        foods = request.env['lunch.product'].search([])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        food_list = list()
        for item in foods:
            image_url = base_url + '/web/content/lunch.product/{}/image_1920'.format(item.id)
            vals = {
                'product_id' : item.id,
                'product_name' : item.name,
                'product_categ' : item.category_id.name,
                'product_description' : item.description,
                'price' : item.price,
                'is_new' : True if item.new_until and item.new_until >= datetime.date.today() else False,
                'image' : image_url if item.image_1920 else ""
            }
            food_list.append(vals)
        return Response(json.dumps({'food_list' : food_list}), content_type='application/json')

    @validate_token
    @http.route('/category_wise_food_list', type='http', auth='none')
    def categ_food_list(self, **vals):
        categories = request.env['lunch.product.category'].search([])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        category_list = list()
        for category in categories:
            foods = request.env['lunch.product'].search([('category_id', '=', category.id)])
            food_list = list()
            for item in foods:
                image_url = base_url + '/web/content/lunch.product/{}/image_1920'.format(item.id)
                vals = {
                    'product_id': item.id,
                    'product_name': item.name,
                    'product_categ': item.category_id.name,
                    'product_description': item.description,
                    'price': item.price,
                    'is_new': True if item.new_until and item.new_until >= datetime.date.today() else False,
                    'image' : image_url if item.image_1920 else "",
                }
                food_list.append(vals)
            categ_vals = {
                'category_id' : category.id,
                'category_name' : category.name,
                'food_list' : food_list,
            }
            category_list.append(categ_vals)
        return Response(json.dumps({'category_list': category_list}), content_type='application/json')
