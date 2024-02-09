# -*- coding: utf-8 -*-

from num2words import num2words
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.tools import config


class AccountPaymentInherited(models.Model):
    _inherit = "account.payment"
    _name = "account.payment"

    @api.depends('amount')
    def amount_word(self):
        for record in self:
            language = 'es'
            list_lang = [['en', 'en_US'], ['en', 'en_AU'], ['en', 'en_GB'], ['en', 'en_IN'],
                         ['fr', 'fr_BE'], ['fr', 'fr_CA'], ['fr', 'fr_CH'], ['fr', 'fr_FR'],
                         ['es', 'es_ES'], ['es', 'es_AR'], ['es', 'es_BO'], ['es', 'es_CL'], ['es', 'es_CO'],
                         ['es', 'es_CR'], ['es', 'es_DO'],
                         ['es', 'es_EC'], ['es', 'es_GT'], ['es', 'es_MX'], ['es', 'es_PA'], ['es', 'es_PE'],
                         ['es', 'es_PY'], ['es', 'es_UY'], ['es', 'es_VE'],
                         ['lt', 'lt_LT'], ['lv', 'lv_LV'], ['no', 'nb_NO'], ['pl', 'pl_PL'], ['ru', 'ru_RU'],
                         ['dk', 'da_DK'], ['pt_BR', 'pt_BR'], ['de', 'de_DE'], ['de', 'de_CH'],
                         ['ar', 'ar_SY'], ['it', 'it_IT'], ['he', 'he_IL'], ['id', 'id_ID'], ['tr', 'tr_TR'],
                         ['nl', 'nl_NL'], ['nl', 'nl_BE'], ['uk', 'uk_UA'], ['sl', 'sl_SI'], ['vi_VN', 'vi_VN']]

            #     ['th','th_TH'],['cz','cs_CZ']
            cnt = 0
            for rec in list_lang[cnt:len(list_lang)]:
                if rec[1] == record.partner_id.lang:
                    language = rec[0]
                cnt += 1

            amount_str = str('{:2f}'.format(record.amount))
            amount_str_splt = amount_str.split('.')
            before_point_value = amount_str_splt[0]
            after_point_value = amount_str_splt[1][:2]

            before_amount_words = num2words(int(before_point_value), lang=language)

            amount = before_amount_words

            if record.currency_id and record.currency_id.currency_unit_label:
                amount += ' ' + record.currency_id.currency_unit_label

            if record.currency_id and record.currency_id.amount_separator:
                amount += ' ' + record.currency_id.amount_separator

            if int(after_point_value) > 0:
                amount += ' con ' + str(after_point_value) + '/100.'
            else:
                amount += ' exactos.'

            record.amount_in_words = amount.capitalize()
	
    reference = fields.Char("Referencia")
    amount_in_words = fields.Char(compute='amount_word', string='Monto', readonly=True)
    print_to_report = fields.Boolean(string="Mostrar en reporte", default=True)
    method = fields.Selection(
        [
            ("E", "Efectivo"),
            ("C", "Cheque"),
            ("T", "Transferencia"),
            ("TC", "Tarjeta de Credito"),
            ("DE", "Deposito"),
        ],
        string="Forma de Pago"
    )
    """Campo para ingresar referencia de banco en transferencias de pagos. 
           Campo único, no pueden haber más de un registro con los mismos datos."""
    bank_reference = fields.Char(
        copy=False,
        help="Campo para ingresar referencia de banco en transferencias de pagos. "
             "Campo único, no pueden haber más de un registro con los mismos datos.",
        string="Referencia de banco"
    )
    """Campo para ingresar cuenta contable personalizada de destino. 
        Si no existe valor en el campo, seguirá el curso normal de odoo"""
    custom_destination_account_id = fields.Many2one(
        comodel_name='account.account',
        ondelete="cascade",
        domain="[('is_custom_payment_account', '=', True)]",
        index=True,
        help="Campo útil para ingresar cuenta contable personalizada de destino. "
             "Si no existe valor en el campo, seguirá el curso normal de odoo",
        string="Cuenta contable de destino"
    )

    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        for record in self:
            if record.custom_destination_account_id:
                record.destination_account_id = record.custom_destination_account_id.id
            else:
                super(AccountPaymentInherited, record)._compute_destination_account_id()

    _sql_constraints = [
        ('bank_reference_unique', 'UNIQUE(bank_reference)', 'La referencia de banco ingresada ya existe!')
    ]

    """Actualizacion 22/03/2021 para agregar numero de cheque a nombre de pago"""
    def name_get(self):
        names = []
        for record in self:
            names.append(
                (record.id, '%s %s' % (record.name, '- ' + str(record.check_number) if record.check_number else ''))
            )
        return names
    """Actualizacion 22/03/2021 para agregar numero de cheque a nombre de pago"""

    def month_to_text(self, month):
        return {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }

