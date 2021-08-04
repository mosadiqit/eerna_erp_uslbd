# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2016 ePillars Systems (<http://epillars.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Web Slider Widget',
    'version': '1.0',
    'category': 'Extra Tools',
    'summary': 'Display attractive range sliders for number selection in form view',
    'description': """ 
    
Web Slider Widget
=================
Add slider to char or int fields. For 2 way range, sliders, the field must be
of char type.

Usage
--------------

widget="slider" in Form View


Options
--------------

Use options as illustrated in the examples to define additional options for the widget

* color: Supports hex-code,names and rgb() values
* range: 'min' for Fixed Minimum, 'max' for Fixed Maximum, 
        'range' for both min and max sliders
        Note: For 'range' values, the values are stored in the database in the format 'lower value,upper value'.
* text_before: Define the string to be displayed before the value e.g. '$','USD' etc.
* separator: Define the separator string e.g. ' - ', ' to ' etc.
* text_after: Define the string to be displayed after the value e.g. 'sq. ft.' etc.
* min_val: The minimum acceptable value for the slider. 0 by default
* max_val: The maximum acceptable value for the slider. 500 by default
* step: The increments for the slider. 1 by default
* orientation: 'horizontal' or 'vertical'. It is horizontal by default.

Examples
--------------

<group>
    <field name="bedrooms" string="Bedrooms" 
            widget="slider" options="{'color':'black','max_val':7,'min_val':1}" />
    
    <field name="area" 
            string="Built-up Area" 
            widget="slider" 
            options="{'step':50,'color':'red','range':'min','text_after':' sq. ft.','max_val':10000}" />
    
    <field name="price" 
            string="Price Range"  widget="slider" 
            options="{'color':'purple','range':'range','text_before':'$ ','min_val':10000,'separator':' - $ ','max_val':80000,'step':1000}" />
</group>
<group>
    <field name="floor" string="Floor No." widget="slider" options="{'orientation':'vertical','range':'max','max_val':100}"/>                                            
</group>

Notes
--------------

Before setting the widget, avoid garbage values in the field to avoid errors.
                    
                    """,
    'author': 'ePillars Systems',
    'website': 'http://www.epillars.com',
    'depends': ['base','web'],
    'data':[
            "views/slider_view.xml",
            ],
    'qweb':["static/src/xml/slider.xml"],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
   # 'price':1.00,
   # 'currency':'EUR',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
