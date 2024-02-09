# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Merchandise(models.Model):
    _name = 'logistic.merchandise'
    _description = 'Mercadería'

    name = fields.Char(
        help="Campo a ser llenado en Miami, "
             "indicando la descripción de producto, para que Compras ingrese el respectivo producto.",
        string="Producto/Descripción"
    )
    separate_wr = fields.Boolean(
        help="Si desea que el WR sea separado en otro WR, seleccione esta casilla y el botón SEPARAR WR",
        string="Separar WR"
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Variante de Producto"
    )
    product_template_id = fields.Many2one(
        comodel_name="product.template",
        related="product_id.product_tmpl_id",
        string="Plantilla de Producto"
    )
    qty = fields.Float(
        string="Cantidad"
    )
    price_unit = fields.Float(
        help="Campo útil para ingresar el precio unitario del producto de la línea.",
        string="Precio UND"
    )
    wr_id = fields.Many2one(
        comodel_name="logistic.wr",
        string="WR  #"
    )
    alert_id = fields.Many2one(
        comodel_name="logistic.alert",
        string="Alerta"
    )
    child_wr_id = fields.Many2one(
        comodel_name="logistic.wr",
        help="Campo útil únicamente para mercadería que proviene de un WR separado",
        string="WR/S"
    )


    amount = fields.Float(
        help="campo util que muestra el total del producto con el dai, valor y cantidad.",
        string="Total"
    )
    total_amount = fields.Float(
        help="suma de todos los montos",
        string="Monto Total."
    )
    factor = fields.Float(
        string="Factor",
        default=1.75
    )
    po_lines_ids = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Relacion con Orden de compra",
        inverse_name="merchandise_ids"
    )
    default_code = fields.Char(
        string="No. Parte",
        help="numero de parte del producto."
    )
    bool_create_so_form_alert = fields.Boolean(
        string="SOL"
    )
    bool_true_so_created = fields.Boolean(
        string="CSO"
    )

    bool_create_po_form_alert = fields.Boolean(
        string="POL"
    )
    bool_true_po_created = fields.Boolean(
        string="CPO"
    )
    real_price = fields.Float(
        string="precio real"
    )

    transport_type = fields.Selection(
        selection=[
            ('maritime', 'Marítimo'),
            ('air', 'Aéreo'),
            ('courier', 'Courier'), ('land', 'Terrestre')
        ],
        default="maritime",
        string="Transporte", tracking=True
    )

    """
    campo para obtener el dai del producto
    """
    product_dai = fields.Many2many(
        comodel_name="account.tax",
        string="Dai Producto",
    )

    company_id_location = fields.Many2one(
        comodel_name="res.company",
        string="Empresa Destino",
        help="Campo de la empresa que sera el proveedor y donde se genere el po"
    )

    polici = fields.Char(
        help="campo para relazionar poliza con mercaderia",
        string="Poliza",
    )

    @api.onchange("product_dai")
    def compute_dai_for_product(self):
        #self.po_lines_ids.sudo().sale_line_id.sudo().product_template_id.sudo().supplier_taxes_id = self.product_dai
        product = self.env["product.product"].search([("id", "=", self.product_id.id)])
        product.supplier_taxes_id = self.product_dai
        factor_compute = 1.75
        for taxes in self.product_dai:
            if taxes.amount_type == "fixed":
                factor_compute = taxes.logistic_factor
        self.factor = factor_compute
        self.price_unit = self.real_price * self.factor
        self.amount = self.price_unit * self.qty




    @api.onchange("qty","price_unit", )
    def compute_amount(self):
        self.amount = self.qty * self.price_unit

    @api.onchange("factor",  "real_price")
    def compute_price_unit(self):
        self.price_unit = self.real_price * self.factor


class AccountTax(models.Model):
    _name = "account.tax"
    _inherit = "account.tax"

    logistic_factor = fields.Float(string="Factor logistica")
    logistic_value_dai = fields.Float(string="% dai logistica")
