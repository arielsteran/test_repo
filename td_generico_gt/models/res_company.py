
from odoo import fields, models


class ResCompanyInherit(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    duplicate_nit = fields.Boolean(
        store=True,
        index=True,
        string="¿Existiran NITs duplicados?",
    )
    payment_day = fields.Integer(
        default=4,
        store=True,
        index=True,
        string="Día de pago"
    )
