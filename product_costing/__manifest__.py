# -*- coding: utf-8 -*-
{
    'name': "product_costing",

    'summary': """
        Costeo de Productos para Ventas""",

    'description': """
        Costear los productos ingresados en ventas, para evaluar los costeos por proveedores. Y revisar los margenes de precios.
    """,

    'author': "Inteligos Gt",
    'website': "http://www.inteligos.gt",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase', 'sale_purchase', 'purchase_requisition', 'eq_sale_delivery_date'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/buyer_users_views.xml',
        'views/historical_purchase_order_views.xml',
        'views/inherit_product_template_views.xml',
        'views/inherit_res_config_settings_suggested_margin_views.xml',
        'views/inherit_sale_order_views.xml',
        'views/sale_order_line_costing_views.xml',
        'views/supplier_cost_views.xml',
        'views/inherit_res_company_view.xml',
    ],
}
