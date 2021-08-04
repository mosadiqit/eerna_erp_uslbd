from odoo import http


class MultilevelApproval(http.Controller):
    @http.route('/purchase_approval_dashboard', auth='user', type='json')
    def approval_banner(self):
        return {
            'html': """
                                  <div>
                                      <center><h1><font color="green" style="FONT-FAMILY: 'Times New Roman';">Approval Status Dashboard</font></h1></center>
                                  </div> """
        }