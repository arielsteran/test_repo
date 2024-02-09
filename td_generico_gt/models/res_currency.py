# -*- coding: utf-8 -*-

from odoo import models, fields


# Language support for num2words
# English = en , French = fr ,Spanish = es , German = de , Lithuanian = lt , Latvian = lv , Polish = pl ,Russian='ru'
# Norwegian = no ,Danish='dk',Portuguese = pt_BR , Arabic = ar ,Italian = it ,Hebrew = he,Indonesian - id
# Turkish -tr,Dutch - nl, Ukrainian - uk ,Slovenian -

# Thai - th, Czech - cz

class ResCurrency(models.Model):
    _inherit = 'res.currency'
    _name = 'res.currency'

    amount_separator = fields.Char("Unit/Subunit Seperator Text")
    close_financial_text = fields.Char("Close Financial Text")
