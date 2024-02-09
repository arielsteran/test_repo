# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SupplierCost(models.Model):
    _name = 'product_costing.supplier_cost'
    _description = 'Proveedor de costeo por Línea de Pedido de Venta'

    def _get_default_res_config_suggested_margin(self):
        res = self.env['res.config.settings']\
            .search([('company_id', '=', self.env.company.id)], order='create_date desc', limit=1)

        if res:
            return res.suggested_margin
        else:
            return self.env.company.suggested_margin

    quote_supplier = fields.Boolean(
        default=False,
        index=True,
        store=True,
        help='Marque si desea este proveedor para costear el producto de la línea de pedido de venta.',
        string="Cotizar Proveedor"
    )
    name = fields.Many2one(
        'res.partner',
        ondelete="cascade",
        index=True,
        store=True,
        required=True,
        help='Ingrese el contacto que provee el producto de la línea de pedido de venta.',
        string="Proveedor"
    )
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        ondelete="cascade",
        store=True,
        index=True,
        help='Aquí va la línea de pedido que será en la que el proveedor fue seleccionado.',
        string="Línea de Pedido"
    )
    cost = fields.Float(
        index=True,
        store=True,
        digits=(6, 5),
        help='Ingrese el costo del producto según el proveedor.',
        string="Costo"
    )
    shipping_way = fields.Selection(
        [
            ('air', 'Aéreo'), ('maritime', 'Marítimo')
        ],
        store=True,
        index=True,
        required=True,
        help='Selecciona la forma de embarque que se usará con el producto según el proveedor.',
        string="Forma de embarque"
    )
    has_local_shipping = fields.Boolean(
        default=False,
        index=True,
        store=True,
        help='Marque si incluye flete interno, según el proveedor, para que Odoo le muestre el campo indicado.',
        string="Tiene Flete Interno"
    )
    local_shipping = fields.Float(
        index=True,
        store=True,
        digits=(6, 5),
        required_if_has_local_shipping=True,
        help='Al marcar que incluye flete interno, este campo se mostrará '
             'para ser llenado con el valor establecido.',
        string="Flete Interno"
    )
    us_shipping = fields.Float(
        index=True,
        store=True,
        digits=(6, 5),
        help='Al marcar que se incluyen otros costos, este campo '
             'puede ser llenado de ser el caso, con el valor de costo flete de Estados Unidos.',
        string="Flete EE.UU."
    )
    export_shipping = fields.Float(
        index=True,
        store=True,
        digits=(6, 5),
        help='Al marcar que se incluyen otros costos, este campo '
             'puede ser llenado de ser el caso, con el valor de costo flete de exportación.',
        string="Flete exportación"
    )
    insurance_cost = fields.Float(
        index=True,
        store=True,
        digits=(6, 5),
        help='Al marcar que se incluyen otros costos, este campo '
             'puede ser llenado de ser el caso, con el valor de costo del seguro.',
        string="Seguro"
    )
    suggested_margin = fields.Float(
        store=True,
        index=True,
        required=True,
        default=lambda self: self._get_default_res_config_suggested_margin(),
        digits=(1, 2),
        help='Ingrese el márgen sugerido entre 0.00 y 1.00 que tendrá según el proveedor.',
        string="Márgen Sugerido"
    )
    sale_suggested_price = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        help='Aquí va el precio de venta sugerido según el porcentaje de márgen.',
        string="Precio Sugerido"
    )
    delay = fields.Integer(
        store=True,
        index=True,
        default=0,
        help='Tiempo de espera en días entre la confirmación del pedido de compra y la recepción '
             'de los productos en su almacén. Usado por el planificador '
             'para el cálculo automático de la planificación de pedidos de compra.',
        string="Tiempo inicial entrega"
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='name.company_id.currency_id',
        readonly=True,
        string="Moneda"
    )
    user_id = fields.Many2one(
        'res.users',
        ondelete="cascade",
        store=True,
        index=True,
        help='Ingrese el usuario que estará en la línea de pedido según proveedor.',
        string="Usuario"
    )
    days = fields.Integer(
        store=True,
        index=True,
        default=0,
        help='Tiempo de espera en días entre la confirmación del pedido de compra y la recepción '
             'de los productos en su almacén. Útil para el planificador, siendo solo informativo.',
        string="Días"
    )
    dai = fields.Float(
        store=True,
        index=True,
        help='Valor arancelario calculado según el proveedor.',
        string="DAI"
    )
    special_purchase = fields.Boolean(
        help='Al estar seleccionado el cálculo del precio sugerido cambia, '
             'siendo clave la cantidad de unidades solicitadas.',
        string="Compra Especial"
    )

    @api.onchange('cost', 'local_shipping', 'us_shipping', 'export_shipping', 'insurance_cost',
                  'suggested_margin', 'shipping_way', 'dai')
    def _onchange_costs(self):
        w = self.sale_order_line_id.product_template_id.weight  # value PESO p.template
        v = self.sale_order_line_id.product_template_id.volumetric  # value PESO VOLUMETRICO p.template
        if w >= v:  # Si peso es mayor o igual a p-volumetrico
            weight = w  # var PESO almacena el value PESO p.template
        else:  # Caso contrario
            weight = v  # var PESO almacena el value PESO VOLUMETRICO p.template
        if self.special_purchase:  # Si es compra especial
            """Calcular CIF price como la suma del costo 
            más la operación de sumar el Flete de USA con el costo de exportación 
            y al resultado dividirlo entre la cantidad de unidades de la línea del pedido de venta."""
            cif_price = self.cost + (
                        (self.us_shipping + self.export_shipping) / self.sale_order_line_id.product_uom_qty)
        else:  # Caso contrario
            """valor % de flete interno USA x lb configurado en la config."""
            config_shipping_us = self.sale_order_line_id.internal_shipping_us
            """Calcular el flete interno USA unitario con la operación 
            de multiplicar var PESO y el % para flete interno USA x lb."""
            self.us_shipping = weight * config_shipping_us
            """Calcular el FOB price con la suma entre el flete USA y el costo ingresado en el costeo."""
            fob_price = self.us_shipping + self.cost
            config_customs_cost = 0.0  # var FORMA DE COSTO FLETE (Aereo, Maritimo) para % según cada caso
            config_insurance_cost = 0.0  # var FORMA DE COSTO SEGURO (Aereo, Maritimo) para % según cada caso
            if self.shipping_way == 'air':  # Si la forma de envío es Aéreo
                """ Obtener el valor % para el costo aéreo para flete ingresado en config."""
                config_customs_cost = self.sale_order_line_id.air_cost
                """ Obtener el valor % para el costo aéreo para seguro ingresado en config."""
                config_insurance_cost = self.sale_order_line_id.insurance_cost
            elif self.shipping_way == 'maritime':  # Si la forma de envío es Marítimo
                """Obtener valor % para el costo marítimo para flete ingresado en config."""
                config_customs_cost = self.sale_order_line_id.maritime_cost
                """ Obtener el valor % para el costo marítimo para seguro ingresado en config."""
                config_insurance_cost = self.sale_order_line_id.maritime_insurance_cost
            """Calcular el costo de exportación con la operación 
            de multiplicar la var PESO y el valor % de var FORMA DE COSTO."""
            self.export_shipping = weight * config_customs_cost
            """Calcular el costo de seguro con la operación de 
            multiplicar FOB price y el valor % para el costo de seguro ingresado desde la configuración."""
            self.insurance_cost = fob_price * config_insurance_cost
            """Calcular CIF price como la suma de FOB price más el costo de exportación y el costo de seguro."""
            cif_price = fob_price + self.export_shipping + self.insurance_cost
        """Obtener impuesto DAI configurado en el producto."""
        dai_tax = self.sale_order_line_id.product_id.supplier_taxes_id \
            .filtered(lambda t: t['group_type'] == 'dai')
        """Calcular impuesto DAI para el CIF price si exite el impuesto en el producto, caso contrario, valor es 0.0."""
        self.dai = cif_price * (dai_tax.amount / 100) if dai_tax else 0.0
        """Calcular CIF price más el monto del impuesto DAI."""
        cif_price_plus_dai = cif_price + self.dai
        """Calculo del IVA a CIF price más el monto del impuesto DAI."""
        iva = cif_price_plus_dai * 0.12
        """Calcular precio internado GT con la operación de sumar CIF price más el monto del impuesto DAI 
        y a su vez sumarle el IVA calculado anteriormente."""
        internal_price_gt = cif_price_plus_dai + iva
        """ Obtener el valor % para el costo flete interno ingresado en config."""
        config_internal_shipping = self.sale_order_line_id.internal_shipping
        """Calcular el costo de flete local con la operación de 
        multiplicar var PESO con el valor % del costo interno."""
        self.local_shipping = weight * config_internal_shipping
        """Calcular precio unitario puesto en ingenio con la 
        suma de el precio internado GT y y el costo del flete local."""
        price_unit_free = internal_price_gt + self.local_shipping
        """Calcular precio de venta sugerido, según qué ingresen en costo (Dólares o Quetzáles), 
        con la multiplicación de el precio unitario en ingenio y el precio sugerido, 
        ya sea configurado o ingresado manualmente en el costeo"""
        sale_suggested_price_dollar = price_unit_free / self.suggested_margin
        """Asignar precio sugerido que fue calculado previamente."""
        self.sale_suggested_price = sale_suggested_price_dollar

    @api.constrains('suggested_margin')
    def check_suggested_margin(self):
        if self.suggested_margin > 0.99 or not self.suggested_margin:
            raise UserError('El margen sugerido debe ser mayor 0 y menor a 0.99')
