# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import ValidationError


class SeparateWRWiz(models.TransientModel):
    _name = 'logistic.separate_wr_wiz'
    _transient = True
    _description = 'Separar WR Wizard'

    transport_type = fields.Selection(
        selection=[
            ('maritime', 'Marítimo'), ('air', 'Aéreo'),
            ('courier', 'Courier')
        ],
        default="maritime",
        required=True,
        string="Transporte"
    )
    wr_id = fields.Many2one(comodel_name="logistic.wr", string="WR")

    """Revisar que cuando se cree un WR hijo, proveniente de un WR separado, 
    la mercadería en cuestion quede enlazado al WR separado y al WR hijo, 
    tal como la lógica que coloqué en las dos líneas finales de esta funcion"""
    def action_confirm_separate(self):
        merchandise_to_separate = self.wr_id.merchandise_ids.filtered(lambda m: m['separate_wr'])
        print(merchandise_to_separate, 'seleccionada')
        values_wr = self.wr_id.prepare_wr_values()
        values_wr['merchandise_ids'] = merchandise_to_separate.ids
        values_wr['transport_type'] = self.transport_type
        print(values_wr, 'valores')
        child_wr = self.env['logistic.wr'].create(values_wr)
        print(child_wr, 'que se creo')
        if not self.wr_id.is_separated:
            self.wr_id.is_separated = True
        for merchandise in merchandise_to_separate:
            print('GENERAR separacion de WR')
            merchandise.child_wr_id = child_wr.id
            merchandise.wr_id = self.wr_id.id
