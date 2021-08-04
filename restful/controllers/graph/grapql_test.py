from odoo.http import request, Response
from odoo import http
import graphene
from . import schema
from .. import main
import json

class GraphqlEndpoint(http.Controller):
    @main.validate_token
    @http.route('/graph_demo', csrf=False, auth='none', methods=['post'], type='json')
    def routeGraphDemo(self):
        sch = graphene.Schema(query=schema.Query)
        print('schema = ',sch)
        print('=====================================================')
        query_str = request.jsonrequest['query']
        res = sch.execute(query_str)
        if res.errors:
            return {'message' : 'something wrong...'}
        res_dict = dict(res.data.items())
        json_res = json.dumps(res_dict, indent=4)
        return Response(json.loads(json_res))