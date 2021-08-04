{
    'name': 'GTS EASY SWITCH BRANCH',
    'description': "",
    'version': '1.0.1',
    'category': '',
    'author': 'Geo Technosoft Pvt Ltd.',
    'website' : 'https://www.geotechnosoft.com',
    'summary': '',
    'license': 'AGPL-3',
    'depends': ['web','gts_branch_management'],

    "data": [
        'views/branch_template_view.xml'

    ],
    'qweb': [
        "static/src/xml/branch.xml",
    ],

    "auto_install": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
