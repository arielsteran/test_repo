{
    'name': "Tropicalización para Guatemala",

    'summary': """
        Tropicalización de Inteligos para Guatemala.""",

    'description': """
        Tipos de Documento
        Impuestos
        Datos fiscales en facturas
        Posiciones Fiscales
    """,

    'author': "Inteligos, S.A.",
    'website': "http://www.inteligos.gt",
    'category': 'Localization',
    'version': '0.2',
    'depends': ['base', 'account', 'account_accountant', 'l10n_latam_base',
                'l10n_latam_invoice_document',
                'account_tax_python', 'account_check_printing'],
    'data': [
        'data/l10n_latam.document.type.csv',
        'data/l10n_latam_identification_type_data.xml',
        'data/l10n_gt_chart_data.xml',
        'data/account.account.template.csv',
        'data/l10n_gt_chart_post_data.xml',
        'data/account_tax_group_data.xml',
        'data/account_taxes_data.xml',
        'data/account_fiscal_template.xml',
        'data/res_country_group_data.xml',
        'data/account_chart_template_data.xml',
        'views/account_move_view.xml',
        'views/account_account_view.xml',
        'views/account_payment_view.xml',
        'views/res_currency_view.xml',
        'views/res_partner_view.xml',
        'views/td_generico_invoice_view.xml',
        'views/inherit_res_config_settings_account_views.xml',
        # 'views/invoice_cancel_view.xml',
      ],

}
# -*- coding: utf-8 -*-
