from odoo import http
from odoo.addons.restful.common import invalid_response, valid_response
from odoo.exceptions import AccessError, AccessDenied
import werkzeug
from odoo.http import request
import json



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


class LoginApi(http.Controller):
    @http.route('/login', methods=["GET"], type="http", auth="none")
    def user_login(self, **post):

        print(post)
        _token = request.env["api.access_token"]
        print(_token)
        params = ["db", "login", "password", "fcm_token"]
        params = {key: post.get(key) for key in params if post.get(key)}
        db, username, password, fcm_token = (
            params.get("db"),
            post.get("login"),
            post.get("password"),
            post.get("fcm_token"),
        )
        print(db, username, password)
        _credentials_includes_in_body = all([db, username, password, fcm_token])
        if not _credentials_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            print('headers = ', headers)
            db = headers.get("db")
            username = headers.get("login")
            password = headers.get("password")
            password = headers.get("fcm_token")
            _credentials_includes_in_headers = all([db, username, password])
            if not _credentials_includes_in_headers:
                # Empty 'db' or 'username' or 'password:
                return invalid_response(
                    "missing error", "either of the following are missing [db, username,password,fcm_token]", 403,
                )
        # Login in odoo database:
        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return invalid_response("Access error", "Error: %s" % aee.name)
        except AccessDenied as ade:
            return invalid_response("Access denied", "Login, password or db invalid")
        except Exception as e:
            # Invalid database:
            info = "The database name is not valid {}".format((e))
            error = "invalid_database"
            _logger.error(info)
            return invalid_response("wrong database name", error, 403)

        uid = request.session.uid
        # odoo login failed:
        if not uid:
            info = "authentication failed"
            error = "authentication failed"
            _logger.error(info)
            return invalid_response(401, error, info)
        # Set user's FCM token
        login_user = request.env['res.users'].search([('id', '=', int(uid))])
        login_user.sudo().write({'fcm_token': str(fcm_token)})
        # Generate tokens
        access_token = _token.find_one_or_create_token(user_id=uid, create=True)
        employee = get_user_from_access_token(request, access_token)
        # print(str(employee.image_1920))
        user_dict = dict()
        user_dict['user_id'] = uid
        if employee.job_id:
            user_dict['position'] = employee.job_id.name
        else:
            user_dict['position'] = ''
        if employee.barcode:
            user_dict['employee_id'] = employee.barcode
        else:
            user_dict['employee_id'] = ''
        if employee.name:
            user_dict['name'] = employee.name
        else:
            user_dict['name'] = ''
        if employee.work_email:
            user_dict['email'] = employee.work_email
        else:
            user_dict['email'] = ''

        if employee.birthday:
            user_dict['dob'] = employee.birthday
        else:
            user_dict['dob'] = ''

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if employee.image_1920:
            image_url = base_url + '/web/content/hr.employee/{}/image_1920'.format(employee.id)
            user_dict['profile_image'] = image_url
        else:
            user_dict['profile_image'] = ''

        response = {
            'status': True,
            'message': "User has been logged in successfully",
            'user': user_dict,
            'access_token': access_token,

        }

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(response),
        )