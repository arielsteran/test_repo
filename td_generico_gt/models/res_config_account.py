
from odoo import fields, models


class ResConfigAccount(models.TransientModel):
    _name = "res.config.settings"
    _inherit = "res.config.settings"

    duplicate_nit = fields.Boolean(
        store=True,
        index=True,
        related="company_id.duplicate_nit",
        readonly=False,
        string="¿Existiran NITs duplicados?",
    )
    payment_day = fields.Integer(
        store=True,
        index=True,
        related="company_id.payment_day",
        readonly=False,
        string="Día de pago",
    )
