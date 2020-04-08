##############################################################################
#
#    Maach Media. Ltd.
#    Copyright (C) 2019-TODAY Maach Media .
#    Maintainer: Maach Media sperality@gmail.com
#
#############################################################################

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
     
    # @api.multi
    # def action_invoice_open(self):
    #     res = super(AccountInvoice, self).action_invoice_open()
    #     if self.type == "in_invoice":
    #         pur_obj = self.env['payment.schedule.ikoyi'].search([('purchase_id', '=', self.purchase_id.id), ('state', '=', "draft")], limit=1)
    #         if pur_obj:
    #             pur_obj.write({'state': 'account_payable'})
    #         else:
    #             raise ValidationError('No schedule found')  
    #             # pass
    #     return res

    # def button_create_vendor_bill(self, ): # draft,
    #     resp = {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Purchase Reference'),
    #         'res_model': 'purchase.order',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'view_id': view_id,
    #         'context': {'default_purchase_id': self.ikoyi_ref.purchase_order_id.id,
    #                     'default_partner_id': self.name.id,
    #                     'default_branch_id': self.env.user.branch_id.id
    #                     },
    #         'target': 'new',
    #         # 'res_id': self.ikoyi_ref.purchase_order_id 
    #     }
    #     return resp