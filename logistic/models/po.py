# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PO(models.Model):
    _name = 'logistic.po'
    _description = 'Órdenes de Compra'

    name = fields.Many2one(comodel_name="purchase.order", string="PO", readonly=True)
    """Revisar fallo de campos related"""
    # state = fields.Selection(
    #     related="name.state",
    #     help="Campo para indicar el estado de la Orden de Compra de la línea.",
    #     string="Estado PO"
    # )
    """Revisar fallo de campos related"""
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Transferencia (Entrada) de Inventario")
    delivery_date = fields.Char(string="Delivery Date")
    merchandise_state = fields.Selection(
        selection=[
            ('complete', 'Completa'), ('incomplete', 'Incompleta')
        ],
        default="complete",
        help="Campo útil para indicar si la mercadería obtenida "
             "en Miami tiene la cantidad indicada en la documentación.",
        string="Mercadería"
    )
    so_id = fields.Char(string="SO", readonly=True)
    """Revisar fallo de campos related"""
    # so_state = fields.Selection(
    #     related="so_id.state",
    #     help="Campo para indicar el estado de la Orden de Venta de la línea.",
    #     string="Estado SO"
    # )
    # supplier_id = fields.Many2one(comodel_name="res.partner", related="name.partner_id", string="Proveedor")
    """Revisar fallo de campos related"""
    wr_id = fields.Many2one(comodel_name="logistic.wr", string="WR")
    conmer_id = fields.Many2one(
        comodel_name="logistic.conmer",
        help="Campo útil para identificar a qué CONMER pertecene el WR.", string="Conmer"
    )


    @api.onchange("picking_id")
    def compute_po(self):
        self.name = self.picking_id.purchase_id.id
        self.so_id = self.picking_id.purchase_id.origin
        self.delivery_date = str(self.picking_id.purchase_id.date_approve)
"""
    @api.onchange("name")
    def compute_data1(self):
        self.picking_id = self.name.picking_ids.id
        self.so_id = self.picking_id.purchase_id.origin
        self.delivery_date = str(self.picking_id.purchase_id.date_approve)
"""


                
                
