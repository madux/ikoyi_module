from odoo import api, fields, models, _ 
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare

class StockInventoryLine(models.Model):
    _inherit = "stock.inventory"
 
    @api.multi
    def get_current_stock(self):
        total_qty = 0.0
        stock_quant = self.env['stock.quant']
        for rec in self.line_ids:
            if rec.product_id:
                search_quanty = stock_quant.search([
                    ('location_id', '=', rec.location_id.id),
                    ('product_id', '=', rec.product_id.id)
                    ])
                if search_quanty:

                    for rey in search_quanty:
                        total_qty += rey.qty
                else:
                    raise ValidationError('No product found in the selected location')
                rec.current_stock_qty = total_qty
            

            else:
                raise ValidationError('Please Select a Product')

    def open_breakage_form(self):
        pass 
        # resp = {
        #     'name': 'Inventory Breakage and Spoilage',
        #     'res_model': 'breakage.spoilage',
        #     'view_type': 'form',
        #     'view_mode': 'form', 
        #     'target': 'current',
        #     'type': 'ir.actions.act_window',
        #     'context': {
        #         'default_lines' : [(0, 0, self.get_product_lines())],
        #     },

        # }

    def get_product_lines(self):
        vals = {}
        for line in self.line_ids:
            vals = {'product_id': line.product_id.id,
            }
        # return [(0, 0, vals)]
        return vals
     


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"
   
    is_breakage = fields.Boolean('Breakage', default=False)
    current_stock_qty = fields.Float(string="Current Qty")
    inventory_fixed_id = fields.Many2one('cost.fixed.asset.move',string='Cost move ID')

 