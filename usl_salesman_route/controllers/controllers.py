# -*- coding: utf-8 -*-
from odoo import http
from odoo.tools import date_utils
from ...restful.controllers.main import validate_token

from odoo.addons.restful.common import invalid_response, valid_response
from odoo.exceptions import AccessError, AccessDenied
import werkzeug
from odoo.http import HttpRequest, Root, SessionExpiredException, request, Response, WebRequest
import json
import logging
from odoo.http import Controller, route, JsonRequest
from dateutil import parser

_logger = logging.getLogger(__name__)


def _json_response(self, result=None, error=None):
    response = {
        'status': True,
        'message': ''
    }
    if error is not None:
        response['error'] = error
    if result is not None:
        response['result'] = result

    mime = 'application/json'
    body = json.dumps(response, default=date_utils.json_default)

    return Response(
        body, status=error and error.pop('http_status', 200) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )


setattr(JsonRequest, '_json_response', _json_response)


def get_user_from_access_token(request=None, token=None):
    access_token = token
    token_user = request.env['api.access_token'].search([("token", '=', access_token)])
    employee = request.env['hr.employee'].sudo().search(
        [('user_id', '=', token_user.user_id.id), ('company_id', '=', token_user.user_id.company_id.id)])
    # print(employee)

    return employee


def get_user_id_from(request=None, token=None):
    query = """select user_id from api_access_token where token = '{}'""".format(token)
    request._cr.execute(query)
    result = request._cr.fetchall()
    print(result[0][0])
    return result


def value_or_replace_none(value=None):
    if value:
        return value
    return ""


class UslSalesmanRoute(http.Controller):
    @http.route('/routedates', methods=["GET"], type="http", auth="none")
    @validate_token
    def get_route_data(self, **kwargs):
        token = request.httprequest.headers.get("access_token")
        employee = get_user_from_access_token(request, token)
        responce_result = dict()
        responce_result['status'] = True
        responce_result['message'] = ""
        responce_result['routeDates'] = list()
        if employee:
            route_dest = request.env['salesman.route_distributions_line'].search([('salesman', '=', employee.id)])
            if route_dest:
                date_set = set()

                for single_dest in route_dest:

                    val = dict()
                    print(single_dest.route_distribution.route_distribution_date)
                    dates = '{0.day}/{0.month}/{0.year}'.format(single_dest.route_distribution.route_distribution_date)
                    print(dates)
                    if dates not in date_set:
                        # date_set.add(dates)
                        val['date'] = dates,
                        val['routes'] = list()
                        for route in single_dest.routes:
                            route_val = {
                                'id': route.route_id,
                                'route_name': route.route_name
                            }
                            val['routes'].append(route_val)
                        responce_result['routeDates'].append(val)
                print(responce_result)

        return Response(json.dumps(responce_result), content_type='application/json;charset=utf-8', status=200)


    @http.route('/visit', methods=["POST"], type="json", auth="none", csrf=False)
    @validate_token
    def post_visit(self):
        print(request.jsonrequest)

        val = {
            'store_id': request.jsonrequest['store_id'],
            'visit_start': request.jsonrequest['visit_started'],
            'end_date': request.jsonrequest['visit_end'],
            'time_durations': request.jsonrequest['visit_duration'],
            'visit_status': request.jsonrequest['visit_status'],
            'is_ordered': request.jsonrequest['is_ordered'],
            'has_task': request.jsonrequest['has_task'],
            'is_task_completed': request.jsonrequest['is_task_completed'],
            'is_delivery_completed': request.jsonrequest['is_delivery_completed'],
            'reason': request.jsonrequest['reason'],
            'remarks': request.jsonrequest['remarks'],
            'user_id': request.env.user.id,
        }
        # print(val)

        resource = request.env['salesman.shop_visiting_history'].sudo().create(val)
        # print('resource : ', resource)
        data = resource.read()
        # print(data)
        lit = list()
        lit.append(val)
        if resource:
            return lit

        return {'error': 'please try again'}

    @http.route('/visits', methods=["GET"], type="http", auth="none", csrf=False)
    @validate_token
    def get_visits(self, **kwargs):

        response = dict()
        response['success'] = True
        response['message'] = ""
        response['visits'] = list()
        user_id = request.env.user.id

        limit = kwargs.get('limit')
        if limit:
            limit = int(limit)

        start_date = kwargs.get('start_date')

        end_date = kwargs.get('end_date')

        page = kwargs.get('page')
        if page:
            page = int(page)
        ofset = kwargs.get('offset')
        if page and limit:
            ofset = (page - 1) * limit
        if start_date and end_date:
            start_date = parser.parse(start_date)
            end_date = parser.parse(end_date)
            domain = [('user_id', '=', user_id), ('create_date', '>=', start_date), ('create_date', '<=', end_date)]
        elif start_date:
            start_date = parser.parse(start_date)
            domain = [('user_id', '=', user_id), ('create_date', '>=', start_date)]
        elif end_date:
            end_date = parser.parse(end_date)
            domain = [('user_id', '=', user_id), ('create_date', '<=', end_date)]
        print(domain)
        # domain =[('user_id', '=', user_id)]

        if user_id:
            respons = request.env['salesman.shop_visiting_history'].sudo().search_read(domain=domain, limit=limit,
                                                                                       offset=ofset)

            if respons:
                print()
                response['visits'] = respons
        return Response(json.dumps(response, default=date_utils.json_default),
                        content_type='application/json;charset=utf-8', status=200)

    @http.route('/routes-customers', methods=["GET"], type="http", auth="none", csrf=False)
    @validate_token
    def get_route_customers(self, **kwargs):
        response = dict()
        response['success'] = True
        response['message'] = ""
        response['customers'] = list()
        # print(kwargs)
        routes = kwargs.get('routes')
        user_id = request.env.user.id
        # print('user id : ', user_id)
        token = request.httprequest.headers.get("access_token")

        employee = get_user_from_access_token(request, token)
        if routes:
            routes = eval(routes)
        else:
            rotuess = request.env['salesman.route'].sudo().search([])
            routes = list()
            for route in rotuess:
                routes.append(route.route_id)

        # print(type(routes))
        domain = [('salesman', '=', employee.id)]
        # print(domain)
        respons = request.env['salesman.route_distributions_line'].sudo().search(domain)
        # print(respons)
        #
        # print(respons.shops)

        if respons:
            for single_object in respons:
                for shop in single_object.shops:
                    rout = request.env['salesman.route'].sudo().search([('shops', '=', shop.id)])
                    for ro in rout:
                        # print(ro)
                        if ro.route_id in routes:
                            # print('come here')
                            val = {
                                'id': shop.id,
                                'customer_name': value_or_replace_none(shop.name),
                                'shop_name': value_or_replace_none(shop.shop_name),
                                'lat': value_or_replace_none(shop.partner_latitude),
                                'lon': value_or_replace_none(shop.partner_longitude),
                                'shop_address': str(shop.contact_address).replace('\n', ','),
                                'route_id': value_or_replace_none(rout.route_id),
                                'route_name': value_or_replace_none(rout.route_name),
                                'route_sequence': value_or_replace_none(rout.id),
                                'customer_email': value_or_replace_none(shop.email),
                                'profile_image': str(value_or_replace_none(shop.image_1920))

                            }
                            response['customers'].append(val)

            # print(response)
        #     =respons
        return Response(json.dumps(response, default=date_utils.json_default),
                        content_type='application/json;charset=utf-8', status=200)

#     @http.route('/usl_salesman_route/usl_salesman_route/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"
# 'user_id', '=', user_id
# "Aug 28 1999 12:00AM"

#     @http.route('/usl_salesman_route/usl_salesman_route/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_salesman_route.listing', {
#             'root': '/usl_salesman_route/usl_salesman_route',
#             'objects': http.request.env['usl_salesman_route.usl_salesman_route'].search([]),
#         })

#     @http.route('/usl_salesman_route/usl_salesman_route/objects/<model("usl_salesman_route.usl_salesman_route"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_salesman_route.object', {
#             'object': obj
#         })
