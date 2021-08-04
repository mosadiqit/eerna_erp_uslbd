import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("/home/alamin/Documents/ODOO/eerna-erp/custom_module/restful/controllers/approval/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

reg_tokens = ['fKwxeavHTROprrkaJXPWiV:APA91bEQVSkDqrHkM9CWMgUxroZN11AIEOAei9FK2SrZdnZxk4xnLHTXluxHaPj8NY9RBVx60CVwavXAPPuJ1dWJq7j5Lz7CxFHkdHihbMtZ-HDid6LjvlHcIGQIrx_F9gIBAhoTjJzS']
title = 'This is a title'
msg = 'message about given title'
dataObject = {
    'key' : 'value'
}
message = messaging.MulticastMessage(
    notification=messaging.Notification(
        title=title,
        body=msg
    ),
    data=dataObject,
    tokens=reg_tokens
)

messaging.send_multicast(message)

