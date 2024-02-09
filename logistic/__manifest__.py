# -*- coding: utf-8 -*-
{
    'name': "logistic",

    'summary': """
       Logística""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Soluciones Ágiles S. A.",
    'website': "http://www.inteligos.gt",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Logística',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'sale', 'sale_purchase', 'product_costing', 'purchase_stock', 'td_generico_gt', 'purchase', 'stock_account'],

    # always loaded
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/main_menu_views.xml',
        'views/po_views.xml',
        'views/wr_views.xml',
        'wizards/separate_wr_wizard.xml',
        'data/sequences.xml',
        'views/alert_view.xml',
        'views/res_config_settings_view.xml',
        'views/account_tax_inherit_view.xml',
        'views/report_wh.xml',
        'views/report_conmer.xml',
        'views/inherit_view_shipping_cost.xml',
        'views/inherit_view_sale_order_lines.xml',
        'views/conmer_views.xml',
        # 'views/po_inherit_view.xml',
        'views/report_alert.xml',
        'views/report_bundle.xml',
        'views/expenses_inherit_views.xml'
        # 'views/inherit_account_move.xml'
    ],
}
