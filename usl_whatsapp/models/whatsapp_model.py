from odoo import api, fields, models
import pyautogui as pg
import time
import webbrowser as web


class WhatsappMessage(models.Model):
    _name = 'whatsapp.message'

    user_id = fields.Many2one('res.partner', string="Recipient")
    mobile = fields.Char(related='user_id.mobile', required=True)
    message = fields.Text(string="message", required=True)

    # def write(self, vals):
    #     if vals['message']:
    #         self.send_message()
    #     print('Hello')

    # def send_message(self):
    #     if self.message and self.mobile:
    #         message_string = ''
    #         message = self.message.split(' ')
    #         for msg in message:
    #             message_string = message_string + msg + '%20'
    #         message_string = message_string[:(len(message_string) - 3)]
    #         return {
    #             'type': 'ir.actions.act_url',
    #             'url': "https://api.whatsapp.com/send?phone=" + self.user_id.mobile + "&text=" + message_string,
    #             'target': 'new',
    #             'res_id': self.id,
    #         }
    @api.onchange('message')
    def send_message(self):
        leads = ['+8801753883073','+8801313002662']
        messages = ['Hello','Hello']
        combo = zip(leads, messages)
        first = True
        for lead, message in combo:
            time.sleep(1)
            web.open("https://web.whatsapp.com/send?phone=" + lead + "&text=" + message,new=1)
            if first:
                time.sleep(6)
                first = False
            width, height = pg.size()
            pg.click(width / 2, height / 2)
            time.sleep(6)
            pg.press('enter')
            time.sleep(6)
            pg.hotkey('ctrl', 'w')