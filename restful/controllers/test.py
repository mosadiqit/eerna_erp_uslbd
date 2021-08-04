import requests
import json

headers = {'content-type': 'text/plain', 'charset': 'utf-8'}

data = {
    'login': 'admin@gmail.com',
    'password': 'admin',
    'db': 'odoo13'
}
base_url = 'http://127.0.0.1:8069'
req = requests.post(
    '{}/api/auth/token'.format(base_url), data=data, headers=headers)
content = json.loads(req.content.decode('utf-8'))
print(content)
