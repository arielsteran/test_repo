# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError


class account_move_chatter(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "mail.thread", "mail.activity.mixin"]

    name = fields.Char(track_visibility='onchange')
    ref = fields.Char(track_visibility='onchange')
    date = fields.Date(track_visibility='onchange')
    journal_id = fields.Many2one(track_visibility='onchange')
    currency_id = fields.Many2one(track_visibility='onchange')
    state = fields.Selection(track_visibility='onchange')
    partner_id = fields.Many2one(track_visibility='onchange')
    amount = fields.Monetary(compute="set_total_amount", string="Suma total")
    reverse_date = fields.Date(track_visibility='onchange')

    # CAMBIOS PARA ACTUALIZAR EN MODULOS FEL
    def set_total_amount(self):
        for record in self:
            total = sum([line.line_total for line in record.invoice_line_ids])
            record.amount = total
