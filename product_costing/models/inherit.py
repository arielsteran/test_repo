# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from dateutil.relativedelta import relativedelta


class ProductCategoryInherited(models.Model):
    _inherit = 'product.category'

    suggested_margin = fields.Float(
        store=True,
        index=True,
        required=True,
        help='Ingrese el márgen sugerido que tendrá la categoría de producto.',
        string="Márgen Sugerido"
    )
    user_ids = fields.Many2many(
        'res.users',
        'product_category_user_rel',
        'product_category_id',
        'user_id',
        ondelete="cascade",
        store=True,
        index=True,
        help='Aquí van los usuarios que serán usados como compradores para las líneas de pedidos de ventas.',
        string="Usuario"
    )


class SaleOrderInherited(models.Model):
    _inherit = 'sale.order'

    has_local_shipping = fields.Boolean(
        default=False,
        index=True,
        store=True,
        help='Marque si el pedido de venta tiene flete local o no.',
        string="Tiene Flete Local"
    )


class ResUsersInherited(models.Model):
    _inherit = 'res.users'

    by_filter = fields.Selection(
        [
            ('1', 'Categoría de Producto'), ('2', 'Producto')
        ],
        store=True,
        index=True,
        default="1",
        required=True,
        help='Seleccione la especificación del comprador.',
        string="Comprador por"
    )
    product_category_ids = fields.Many2many(
        'product.category',
        'product_category_user_rel',
        'user_id',
        'product_category_id',
        ondelete="cascade",
        store=True,
        index=True,
        help='Ingrese las categorías de producto que serán las que use específicamente en usuario seleccionado.',
        string="Categoría de Producto"
    )


class SaleOrderLineInherited(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('supplier_cost_ids', 'company_id')
    def _compute_res_config(self):
        for record in self:
            config = record.env['res.config.settings'] \
                .search(
                [('company_id', '=', record.env.company.id or record.company_id.id)], order='create_date desc', limit=1
            )
            if config:
                record['internal_shipping_us'] = config.internal_shipping_us
                record['internal_shipping'] = config.internal_shipping
                record['air_cost'] = config.air_cost
                record['insurance_cost'] = config.insurance_cost
                record['maritime_cost'] = config.maritime_cost
                record['maritime_insurance_cost'] = config.maritime_insurance_cost
            else:
                company = record.company_id or record.env.company
                record['internal_shipping_us'] = company.internal_shipping_us
                record['internal_shipping'] = company.internal_shipping
                record['air_cost'] = company.air_cost
                record['insurance_cost'] = company.insurance_cost
                record['maritime_cost'] = company.maritime_cost
                record['maritime_insurance_cost'] = company.maritime_insurance_cost

    @api.depends('supplier_cost_ids', 'internal_shipping_us', 'internal_shipping', 'insurance_cost',
                 'air_cost', 'maritime_cost', 'maritime_insurance_cost', 'company_id')
    def _set_res_config(self):
        for record in self:
            key_values = record.read(['internal_shipping_us', 'internal_shipping', 'insurance_cost',
                                      'air_cost', 'maritime_cost', 'maritime_insurance_cost'])[0]
            vals = [key_values[key] for key in key_values]
            if not all(vals):
                company = record.company_id or record.env.company
                record['internal_shipping_us'] = company.internal_shipping_us
                record['internal_shipping'] = company.internal_shipping
                record['air_cost'] = company.air_cost
                record['insurance_cost'] = company.insurance_cost
                record['maritime_cost'] = company.maritime_cost
                record['maritime_insurance_cost'] = company.maritime_insurance_cost

    to_quote = fields.Boolean(
        default=False,
        index=True,
        store=True,
        help='Aquí va marcado si la línea de pedido de venta está por costear o no.',
        string="Costear"
    )
    quoted = fields.Boolean(
        default=False,
        index=True,
        store=True,
        help='Indica si línea de pedido fue costeada o no.',
        string="Costeado"
    )
    has_local_shipping = fields.Boolean(
        default=False,
        index=True,
        store=True,
        help='Marque si el pedido de venta tiene flete local o no.',
        string="Tiene Flete Local"
    )
    shipping_way = fields.Selection(
        [
            ('air', 'Aéreo'), ('maritime', 'Marítimo')
        ],
        store=True,
        index=True,
        help='Selecciona la forma de embarque que se usará con el producto.',
        string="Forma de Embarque"
    )
    supplier_id = fields.Many2one(
        'res.partner',
        ondelete="cascade",
        index=True,
        store=True,
        help='Ingrese el contacto que provee el producto de la línea.',
        string="Proveedor"
    )
    cost = fields.Float(
        index=True,
        store=True,
        help='Aquí va el monto del costo del producto según proveedor seleccionado.',
        string="Costo"
    )
    other_cost = fields.Float(
        index=True,
        store=True,
        help='Aquí va el monto de los otros costos del producto según proveedor seleccionado.',
        string="Otros costos"
    )
    suggested_margin = fields.Float(
        store=True,
        index=True,
        help='Aquí va el márgen sugerido que tendrá la categoría de producto.',
        string="Márgen Sugerido"
    )
    suggested_price = fields.Float(
        store=True,
        index=True,
        compute="compute_sale_suggested_price_quetzal",
        help='Aquí va el precio sugerido según el porcentaje de márgen.',
        string="Precio Sugerido"
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        ondelete="cascade",
        store=True,
        index=True,
        help='Aquí va la orden de compra.',
        string="Orden de Compra"
    )
    state_purchase_order = fields.Selection(
        [
            ('draft', 'Petición presupuesto'),
            ('sent', 'Petición de cotización enviada'),
            ('to approve', 'Para aprobar'),
            ('purchase', 'Pedido de compra'),
            ('done', 'Bloqueado'),
            ('cancel', 'Cancelado')
        ],
        store=True,
        index=True,
        related='purchase_order_id.state',
        help='Aquí va el estado de la orden de compra.',
        string="Estado de OC"
    )
    historical_purchase_order_ids = fields.One2many(
        'purchase.order.line',
        'sale_line_id',
        ondelete="cascade",
        store=True,
        index=True,
        help='Listado del historial de compra del producto.',
        string="Historial de Compra"
    )
    buyer_id = fields.Many2one(
        'res.users',
        ondelete="cascade",
        store=True,
        index=True,
        help='Ingresar el comprador del producto de la línea de pedido',
        string="Comprador"
    )
    supplier_cost_ids = fields.One2many(
        'product_costing.supplier_cost',
        'sale_order_line_id',
        ondelete="cascade",
        store=True,
        index=True,
        help='Listado de los proveedores del producto para costeo.',
        string="Proveedores para costeo"
    )
    costing_date = fields.Date(
        store=True,
        index=True,
        help='Aquí va la fecha de costeo del producto de la línea de pedido',
        string="Fecha de Costeo"
    )
    purchase_requisition_id = fields.Many2one(
        'purchase.requisition',
        ondelete="cascade",
        store=True,
        index=True,
        help='Aquí va el acuerdo de compra creado para la línea de pedido de venta.',
        string="Acuerdo de Compra"
    )
    maritime_cost = fields.Float(
        digits=(6, 5),
        store=True,
        compute="_compute_res_config",
        inverse='_set_res_config',
        help='Ingrese el costo marítimo  para flete que será tomado en cuenta de forma general.',
        string="Flete Marítimo x lb."
    )
    air_cost = fields.Float(
        digits=(6, 5),
        store=True,
        compute="_compute_res_config",
        inverse='_set_res_config',
        help='Ingrese el costo aéreo para flete que será tomado en cuenta de forma general.',
        string="Flete Aéreo x lb."
    )
    internal_shipping_us = fields.Float(
        digits=(6, 5),
        store=True,
        compute="_compute_res_config",
        inverse='_set_res_config',
        help='Ingrese el flete interno en Estado Unidos que será tomado en cuenta de forma general.',
        string="Flete Interno EE.UU. x lb."
    )
    internal_shipping = fields.Float(
        digits=(6, 5),
        store=True,
        compute="_compute_res_config",
        inverse='_set_res_config',
        help='Ingrese el flete interno que será tomado en cuenta de forma general.',
        string="Flete Interno x lb."
    )

    insurance_cost = fields.Float(
        digits=(6, 5),
        store=True,
        compute="_compute_res_config",
        inverse='_set_res_config',
        help='Ingrese el costo aéreo de seguro que será tomado en cuenta de forma general.',
        string="Seguro Aéreo x lb."
    )
    maritime_insurance_cost = fields.Float(
        digits=(6, 5),
        store=True,
        compute="_compute_res_config",
        inverse='_set_res_config',
        help='Ingrese el costo marítimo de seguro que será tomado en cuenta de forma general.',
        string="Seguro Marítimo x lb."
    )
    special_purchase = fields.Boolean(
        default=False,
        index=True,
        store=True,
        help='Al estar seleccionado el cálculo del precio sugerido cambia, '
             'siendo clave la cantidad de unidades solicitadas.',
        string="Compra Especial"
    )
    days = fields.Integer(
        store=True,
        index=True,
        default=0,
        help='Tiempo de espera en días entre la confirmación del pedido de compra y la recepción '
             'de los productos en su almacén. Útil para el planificador, siendo solo informativo.',
        string="Días de entrega"
    )
    dai = fields.Float(
        store=True,
        index=True,
        help='Valor arancelario calculado según el proveedor.',
        string="DAI"
    )

    # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta
    def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
        self.ensure_one()

        product_quantity = self.product_uom_qty
        if quantity:
            product_quantity = quantity

        purchase_qty_uom = self.product_uom._compute_quantity(product_quantity, self.product_id.uom_po_id)

        if self.to_quote:
            if self.supplier_id:
                supplierinfo = self.supplier_cost_ids.filtered(
                    lambda vendor: vendor.name == self.supplier_id and vendor.quote_supplier)
            else:
                raise UserError(
                    _("No se ha checho el costeo para el producto - %s. Por favor espere a que sea costeado "
                      "o proceda a desactivar el costeo.") % (
                        self.product_id.display_name,))
        else:
            supplierinfo = self.product_id._select_seller(
                partner_id=purchase_order.partner_id,
                quantity=purchase_qty_uom,
                date=purchase_order.date_order and purchase_order.date_order.date(),
                uom_id=self.product_id.uom_po_id
            )
        fpos = purchase_order.fiscal_position_id
        taxes = fpos.map_tax(self.product_id.supplier_taxes_id) if fpos else self.product_id.supplier_taxes_id
        if taxes:
            taxes = taxes.filtered(lambda t: t.company_id.id == self.company_id.id)

        price_unit = 0.0
        if supplierinfo:
            if self.to_quote:
                price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(supplierinfo.cost,
                                                                                            self.product_id.supplier_taxes_id,
                                                                                            taxes, self.company_id)
            else:
                price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(supplierinfo.price,
                                                                                            self.product_id.supplier_taxes_id,
                                                                                            taxes, self.company_id)
            if purchase_order.currency_id and supplierinfo.currency_id != purchase_order.currency_id:
                price_unit = supplierinfo.currency_id.compute(price_unit, purchase_order.currency_id)

        product_in_supplier_lang = self.product_id.with_context(
            lang=supplierinfo.name.lang,
            partner_id=supplierinfo.name.id,
        )
        name = '[%s] %s' % (self.product_id.x_code, product_in_supplier_lang.display_name)
        if product_in_supplier_lang.description_purchase:
            name += '\n' + product_in_supplier_lang.description_purchase

        return {
            'name': '[%s] %s' % (
                self.product_id.x_code, self.name) if self.product_id.x_code else self.name,
            'product_qty': purchase_qty_uom,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': fields.Date.from_string(purchase_order.date_order) + relativedelta(
                days=int(supplierinfo.delay)),
            'taxes_id': [(6, 0, taxes.ids)],
            'order_id': purchase_order.id,
            'sale_line_id': self.id,
        }

    # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta

    # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta
    def _purchase_service_create(self, quantity=False):
        PurchaseOrder = self.env['purchase.order']
        supplier_po_map = {}
        sale_line_purchase_map = {}
        for line in self:
            line = line.with_context(force_company=line.company_id.id)
            if line.to_quote:
                if line.supplier_id:
                    suppliers = line.supplier_cost_ids.filtered(
                        lambda vendor: vendor.name == line.supplier_id and vendor.quote_supplier)
                else:
                    raise UserError(
                        _("No se ha checho el costeo para el producto - %s. Por favor espere a que sea costeado "
                          "o proceda a desactivar el costeo.") % (
                            line.product_id.display_name,))
            else:
                suppliers = line.product_id.seller_ids.filtered(
                    lambda vendor: (not vendor.company_id or vendor.company_id == line.company_id) and (
                            not vendor.product_id or vendor.product_id == line.product_id))

            if not suppliers:
                raise UserError(
                    _("No hay proveedor(es) asociados al producto - %s. "
                      "Por favor defina un proveedor para el producto.") % (
                        line.product_id.display_name,))

            supplierinfo = suppliers[0]
            partner_supplier = supplierinfo.name

            purchase_order = supplier_po_map.get(partner_supplier.id)
            if not purchase_order:
                purchase_order = PurchaseOrder.search([
                    ('partner_id', '=', partner_supplier.id),
                    ('state', '=', 'draft'),
                    ('company_id', '=', line.company_id.id),
                ], limit=1)
            if not purchase_order:
                values = line._purchase_service_prepare_order_values(supplierinfo)
                purchase_order = PurchaseOrder.create(values)
            else:
                so_name = line.order_id.name
                origins = []
                if purchase_order.origin:
                    origins = purchase_order.origin.split(', ') + origins
                if so_name not in origins:
                    origins += [so_name]
                    purchase_order.write({
                        'origin': ', '.join(origins)
                    })
            supplier_po_map[partner_supplier.id] = purchase_order

            values = line._purchase_service_prepare_line_values(purchase_order, quantity=quantity)
            purchase_line = line.env['purchase.order.line'].create(values)

            sale_line_purchase_map.setdefault(line, line.env['purchase.order.line'])
            sale_line_purchase_map[line] |= purchase_line
        return sale_line_purchase_map

    # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta

    # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta
    def _purchase_service_generation(self):
        sale_line_purchase_map = {}
        for line in self:
            if not line.purchase_line_count:
                result = line._purchase_service_create()
                sale_line_purchase_map.update(result)
        return sale_line_purchase_map

    # codigo exclusivo para crear Orden de Compra al confirmar Pedido de Venta

    def action_detail_costing(self):
        view = self.env.ref('product_costing.view_form_sale_order_line_costing')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'sale.order.line',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'target': 'new',
            'domain': [('id', '=', self.id)]
        }

    def action_purchase_requisition(self):
        view = self.env.ref('purchase_requisition.view_purchase_requisition_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Acuerdo de Compra para ' + self.order_id.name + ' - ' + self.name,
            'res_model': 'purchase.requisition',
            'view_mode': 'form',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'context': {'default_sale_order_line_id': self.id, 'default_vendor_id': self.supplier_id.id,
                        'default_line_ids': [[0, 'virtual_138',
                                              {'product_id': self.product_id.id, 'product_qty': self.product_uom_qty,
                                               'product_uom_id': 1, 'schedule_date': False,
                                               'account_analytic_id': False, 'price_unit': 0}]]
                        },
            # 'flags': {'initial_mode': 'edit'},
            'target': 'new',
        }

    def action_send_message_salesman(self):
        self.quoted = True
        self.costing_date = fields.Datetime.now()
        sale_order = self.env['sale.order'].search([('id', '=', self.order_id.id)])
        responsible_person = sale_order.user_id.name
        display_msg = """Estimad@ """ + responsible_person + """,
                           <br/>
                           el costeo de la línea de pedido """ + """<b>""" + self.name + """</b>""" + """ ha sido 
                           hecho ya. <br/>"""
        quoted_lines = 0
        no_to_quote_line = 0
        without_quoted_lines = 0
        no_lines = []
        for line in sale_order.order_line:
            if line.to_quote and line.quoted:
                quoted_lines += 1
            elif not line.to_quote:
                no_to_quote_line += 1
            else:
                without_quoted_lines += 1
                no_lines.append(line.name)
        if quoted_lines == len(sale_order.order_line) or (quoted_lines + no_to_quote_line) == len(
                sale_order.order_line):
            display_msg += """<b>Por favor proceder a Enviar Cotización.</b> <br/>"""
        elif without_quoted_lines:
            display_msg += """<b>Faltan por costear """ + str(without_quoted_lines) + """ línea(s) del pedido.</b> <br/>
                              """ + str(no_lines) + """ <br/> """
        followers = sale_order.message_partner_ids.ids
        channels = sale_order.message_channel_ids.ids
        sale_order.message_post(body=display_msg, message_type='notification', subject="Costeo",
                                partner_ids=followers, channel_ids=channels, starred=True)

    @api.onchange('supplier_cost_ids')
    def _onchange_supplier_cost_ids(self):
        if self.supplier_cost_ids:
            suppliers_selected = [supplier for supplier in self.supplier_cost_ids if supplier.quote_supplier]
            if not suppliers_selected or len(suppliers_selected) > 1:
                self.supplier_id = False
                self.cost = 0.00
                self.shipping_way = False
                self.has_local_shipping = False
                self.suggested_margin = 0.00
                self.other_cost = 0.00
                self.suggested_price = 0.00
                self.dai = 0.0
                self.days = 0
            else:
                rate = self.env.company.rate
                self.supplier_id = suppliers_selected[0].name
                self.cost = suppliers_selected[0].cost
                self.shipping_way = suppliers_selected[0].shipping_way
                self.has_local_shipping = suppliers_selected[0].has_local_shipping
                self.suggested_margin = suppliers_selected[0].suggested_margin
                self.other_cost = \
                    suppliers_selected[0].us_shipping + suppliers_selected[0].export_shipping + \
                    suppliers_selected[0].insurance_cost + suppliers_selected[0].local_shipping
                self.suggested_price = suppliers_selected[0].sale_suggested_price * rate
                self.dai = suppliers_selected[0].dai
                self.days = suppliers_selected[0].days

    #  CODIGO PARA QUETZALIZAR LOS MONTOS DE PRECIO SUGERIDO EN VENTAS
    @api.model
    @api.depends('suggested_price', 'order_id')
    def compute_sale_suggested_price_quetzal(self):
        for rec in self:
            rate = rec.env.company.rate
            rec.suggested_price = rec.suggested_price * rate

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            buyer_id = self.product_id.categ_id.user_ids
            purchase_order_ids = self.env['purchase.order.line'] \
                .search([('product_id', '=', self.product_id.id), ('state', 'in', ['purchase', 'done'])]).ids
            self.buyer_id = buyer_id[0].id if buyer_id else False
            self.historical_purchase_order_ids = purchase_order_ids

    @api.onchange('to_quote')
    def _onchange_to_quote(self):
        if self.product_id:
            buyer_id = self.product_id.categ_id.user_ids
            self.buyer_id = buyer_id[0].id if buyer_id else False

    @api.onchange('special_purchase')
    def _onchange_special_purchase(self):
        for supplier in self.supplier_cost_ids:
            supplier['special_purchase'] = self.special_purchase


class PurchaseRequisitionInherited(models.Model):
    _inherit = 'purchase.requisition'

    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        ondelete="cascade",
        store=True,
        index=True,
        help='Aquí va la línea de pedido de venta',
        string="Línea de pedido de venta"
    )


class PurchaseOrderInherited(models.Model):
    _inherit = 'purchase.order'

    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        ondelete="cascade",
        store=True,
        index=True,
        help='Aquí va la línea de pedido de venta',
        string="Línea de pedido de venta"
    )


class PurchaseOrderLineInherited(models.Model):
    _inherit = 'purchase.order.line'

    supplier_id = fields.Many2one(
        'res.partner',
        ondelete="cascade",
        index=True,
        store=True,
        related='order_id.partner_id',
        help='Aquí va el contacto que provee el producto de la línea de pedido de compra.',
        string="Proveedor"
    )
    date_approve = fields.Datetime(
        index=True,
        store=True,
        related='order_id.date_approve',
        help='Aquí va la fecha y hora de la confirmación del pedido de compra.',
        string="Fecha y Hora de Comfirmación"
    )


class ResCompanyInherited(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    suggested_margin = fields.Float(
        store=True,
        index=True,
        help='Ingrese el márgen sugerido como porcentaje que tendrá según el proveedor.',
        string="Márgen Sugerido"
    )
    maritime_cost = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        help='Ingrese el costo marítimo para flete que será tomado en cuenta de forma general.',
        string="Flete Marítimo x lb."
    )
    maritime_insurance_cost = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        help='Ingrese el costo marítimo para seguro que será tomado en cuenta de forma general.',
        string="Seguro Marítimo x lb."
    )
    air_cost = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        help='Ingrese el costo aéreo para flete que será tomado en cuenta de forma general.',
        string="Flete Aéreo x lb."
    )
    internal_shipping_us = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        help='Ingrese el flete interno en Estado Unidos que será tomado en cuenta de forma general.',
        string="Flete Interno EE.UU. x lb."
    )
    internal_shipping = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        help='Ingrese el flete interno que será tomado en cuenta de forma general.',
        string="Flete Interno x lb."
    )
    insurance_cost = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        help='Ingrese el costo aéreo de seguro que será tomado en cuenta de forma general.',
        string="Seguro Aéreo x lb."
    )
    rate = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        help='Ingrese la tasa de cambio para compras que será tomada en cuenta de forma general.',
        string="Tasa de Cambio"
    )

    @api.constrains('suggested_margin')
    def check_suggested_margin(self):
        if self.suggested_margin > 0.99 or not self.suggested_margin:
            raise UserError('El margen sugerido debe ser mayor 0 y menor a 0.99')


class ResConfigSettingsInherited(models.TransientModel):
    _inherit = 'res.config.settings'

    suggested_margin = fields.Float(
        store=True,
        index=True,
        related="company_id.suggested_margin",
        readonly=False,
        help='Ingrese el márgen sugerido como porcentaje que tendrá según el proveedor.',
        string="Márgen Sugerido"
    )
    maritime_cost = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        related="company_id.maritime_cost",
        readonly=False,
        help='Ingrese el costo marítimo para flete que será tomado en cuenta de forma general.',
        string="Flete Marítimo x lb."
    )
    maritime_insurance_cost = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        related="company_id.maritime_insurance_cost",
        readonly=False,
        help='Ingrese el costo marítimo para seguro que será tomado en cuenta de forma general.',
        string="Seguro Marítimo x lb."
    )
    air_cost = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        related="company_id.air_cost",
        readonly=False,
        help='Ingrese el costo aéreo para flete que será tomado en cuenta de forma general.',
        string="Flete Aéreo x lb."
    )
    internal_shipping_us = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        related="company_id.internal_shipping_us",
        readonly=False,
        help='Ingrese el flete interno en Estado Unidos que será tomado en cuenta de forma general.',
        string="Flete Interno EE.UU. x lb."
    )
    internal_shipping = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        related="company_id.internal_shipping",
        readonly=False,
        help='Ingrese el flete interno que será tomado en cuenta de forma general.',
        string="Flete Interno x lb."
    )
    insurance_cost = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        related="company_id.insurance_cost",
        readonly=False,
        help='Ingrese el costo aéreo de seguro que será tomado en cuenta de forma general.',
        string="Seguro Aéreo x lb."
    )
    rate = fields.Float(
        store=True,
        index=True,
        digits=(6, 5),
        related="company_id.rate",
        readonly=False,
        help='Ingrese la tasa de cambio para compras que será tomada en cuenta de forma general.',
        string="Tasa de Cambio"
    )

    @api.constrains('suggested_margin')
    def check_suggested_margin(self):
        if self.suggested_margin > 0.99 or not self.suggested_margin:
            raise UserError('El margen sugerido debe ser mayor 0 y menor a 0.99')


class ProductProductInherited(models.Model):
    _inherit = 'product.template'

    def _compute_weight_uom_name(self):
        for record in self:
            record.weight_uom_name = 'lbs'

    def name_get(self):
        return [(product.id, '[%s] %s' % (product.x_code, product.name))
                for product in self]

    volumetric = fields.Float(
        store=True,
        index=True,
        help='Ingrese el peso volumétrico que será tomado en cuenta en los costeos.',
        string="Peso Volumétrico"
    )
    volumetric_uom_name = fields.Char(
        store=True,
        index=True,
        readonly=True,
        default="lbs",
        help='Es la unidad de medidad de peso volumétrico que será tomado en cuenta en los costeos.',
        string="Unidad de medida Peso Volumétrico"
    )
    weight_uom_name = fields.Char(
        compute="_compute_weight_uom_name",
        default="lbs",
        help='Es la unidad de medidad de peso que será tomado en cuenta en los costeos.',
        string="Unidad de medida Peso"
    )


class ProductInherited(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        return [(product.id, '[%s] %s' % (product.x_code, product.name))
                for product in self]
