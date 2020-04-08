from datetime import datetime, timedelta
import time
from dateutil.relativedelta import relativedelta
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _, SUPERUSER_ID, tools
from odoo.exceptions import ValidationError, UserError

from odoo import http
from odoo.modules import get_module_resource
 

class Ikoyi_Material_Request(models.Model):
    _name = "ik.material.request"
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'ir.attachment']
    _description = "Material Request"
    _order = "id desc"
    
    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'ik.material.request'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'ik.material.request', 'default_res_id': self.id}
        return res

    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/> to Review. ".format(base_url)
        #  base_url += '/web# id=%d&view_type=form&model=%s' % (self.id,
        #  self._name)

        #  self.get_url(self.id, self._name)

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    def default_partner_id(self):
        partner = self.env['res.partner'].browse([0])
        return partner.id 
    
    # USED TO GET LIST OF USERS IN THE GROUP CATEGORY
    # And then append them as followers
    
    def _get_all_followers(self):
        followers = []
        groups = self.env['res.groups']
        store_manager = groups.search([('name', 'ilike', "Store Manager")])
        store_keeper = groups.search([('name', 'ilike', "Store Keeper")])

        procure_manager = groups.search([('name', '=', "Procurement Manager")])
        procurement_officer = groups.search(
            [('name', '=', "Procurement Officer")])
        internal_control = groups.search(
            [('name', '=', "Internal Control Manager")])
        finance = groups.search([('name', '=', "Finance & Admin Manager")])
        chairman = groups.search([('name', '=', "Chairman")])
        vice_chairman = groups.search([('name', '=', "Vice Chairman")])
        general_manager = groups.search([('name', '=', "General Manager")])

        for rec in store_manager:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in store_keeper:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in procure_manager:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in procurement_officer:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in internal_control:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in finance:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in chairman:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in vice_chairman:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in general_manager:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        return followers

    READONLY_STATES = {
        'to approve': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    name = fields.Char(
        'Order Reference',
        required=True,
        index=True,
        copy=False,
        default='')
    
    origin = fields.Char('Source Document', states=READONLY_STATES)
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.currency_id.id)

    order_line = fields.One2many(
        'ik.material.line', 'order_id', string='Material Request Lines', states={
            'cancel': [
                ('readonly', True)], 'done': [
                ('readonly', True)]}, copy=True)

    user_id = fields.Many2one(
        'res.users',
        string="Users",
        default=lambda a: a.env.user.id)

    date_order = fields.Datetime(
        'Order Date',
        required=True,
        states=READONLY_STATES,
        index=True,
        copy=False,
        default=fields.Datetime.now)
    date_planned = fields.Datetime(
        string='Overall Deadline', store=True, index=True)
    users_followers = fields.Many2many(
        'hr.employee',
        string='Add followers',
        required=False,
        default=_get_all_followers)
    branch_id = fields.Many2one(
        'res.branch',
        string="Section",
        default=lambda self: self.env.user.branch_id.id,
        help="Tell Admin to set your branch... (Users-->Preferences-->Allowed Branch)")
    location = fields.Many2one(
        'stock.location',
        'Stock Location',
        help="Go to inventory config, set branch for warehouse and location")
    warehouse = fields.Many2one(
        'stock.warehouse',
        'Warehouse',
        help="Go to inventory config, set branch for warehouse and location")
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string='Purchase Order', copy=False,)

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('store_manager', 'Draft Purchase Order'),
        ('done', 'Manager Approved'),
        ('pm_done', 'PM Approved'),
        ('refuse', 'Refuse'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True,
                             copy=False,
                             default='draft',
                             track_visibility='onchange')

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=_default_employee)
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        default=default_partner_id,
        track_visibility='always')
    notes = fields.Text('Terms and Conditions')
    remarks = fields.Text('Remarks')
    total_amount = fields.Float('Grand Total', compute="get_all_total")

    @api.depends('purchase_order_id')
    def get_po_name(self):
        for rec in self:
            rec.origin = rec.purchase_order_id.name
    @api.one
    @api.depends('order_line')
    def get_all_total(self):
        total = 0.0
        for rec in self:
            for tec in rec.order_line:
                total += tec.total
            rec.total_amount = total
    
    @api.multi
    def unlink(self):
        for holiday in self.filtered(
            lambda holiday: holiday.state not in [
                'draft,refuse,cancel']):
            raise ValidationError(
                _('In order to delete a Request order, you must cancel it first...'))
        return super(Ikoyi_Material_Request, self).unlink()
    
    def copy(self, default=None):
        default = dict(default or {})
        default.update({ 'purchase_order_id': '', })
  
        return super(Ikoyi_Material_Request, self).copy(default)

    @api.multi
    def button_store_to_manager(self): 
        for order in self:
            email_from = order.env.user.email
            group_user_id = self.env.ref(
                'ikoyi_module.inventory_manager_ikoyi').id
            extra = self.employee_id.work_email
            order.mail_sending(email_from, group_user_id, extra)
            order.write({'state': 'store_manager'})
        return True

    @api.multi
    def button_store_manager_approve(self, force=False):  
        email_from = self.env.user.email
        group_user_id = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id 
        extra = self.employee_id.work_email
        self.mail_sending(email_from, group_user_id, extra)
        self.write({'state': 'done'})
        self.procure_btn()

    @api.multi
    def button_draft(self):
        self.write({'state': 'draft'})
        #  return {}

    @api.multi
    def button_refuse(self):
        return self.button_return_request_back()
        #  return {}

    @api.multi
    def button_cancel(self):
        for order in self:
            if order.state not in ['store_manager', 'done']:
                order.write({'state': 'cancel'})
            else:
                raise ValidationError('You can cancel a confirmed request')

    def mail_sending(self, email_from, group_user_id, extra):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (
            self.id, self._name)

        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_emails = group_users.users

            followers = []
            email_to = []
            for group_mail in self.users_followers:
                followers.append(group_mail.work_email)

            for gec in group_emails:
                email_to.append(gec.login)

            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_appends = (', '.join(str(item)for item in followers))
            mail_to = (','.join(str(item2)for item2 in email_to))
            subject = "Material Order Request"
            '''bodyx = "Dear Sir/Madam, </br>We wish to notify you that an MOF request from {} has been sent to you for approval </br>\
             </br>Kindly <a href={}> </b>Click<a/> to Review. </br> </br>Thanks".format(self.employee_id.name, base_url)'''
            bodyx = "Dear Sir/Madam, </br>We wish to notify you that an MOF request from {} has been sent to you for approval </br>\
             </br> {} </br> </br>Thanks".format(self.employee_id.name, self.get_url(self.id, self._name))

            extrax = (', '.join(str(extra)))
            followers.append(extrax)
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_to,
                'email_cc': mail_appends,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    @api.multi
    def procure_btn(self, context=None):
        """
        Method to procure products when they become unavailable in the warehouse
        :param context: Context supplies the needed values including: partner_id, warehouse_id, location_id
        :return:
        """
        purchase_obj = self.env['purchase.order']
        """
        To get the picking type i need to apply a domain where:
             1. warehouse_id = the warehouse_id on the IR,
             2. default_location_dest_id = src_location_id on the IR
        """

        warehouse = self.env['stock.warehouse'].search(
            [('branch_id', '=', self.branch_id.id)])
        location = self.env['stock.location'].search(
            [('branch_id', '=', self.branch_id.id)])

        users = []
        search = self.env['ik.material.request'].search([('id', '=', self.id)])
        for rec in search:
            for tec in rec.users_followers:
                users.append(tec.id)

        warehouse_id = []
        location_id = []
        for i in warehouse:
            warehouse_id.append(i.id)
        for y in location:
            location_id.append(y.id)

        if not (warehouse and location):
            raise ValidationError(
                "Selected Branch must be added to an Warehouse and Location")
        for reck in warehouse_id:
            for tec in location_id:
                domain = [
                    ('code', '=', 'incoming'),
                    ('warehouse_id', '=', reck),
                    ('active', '=', True),
                    ('default_location_dest_id', '=', tec)
                ]

                picking_type_id = self.env['stock.picking.type'].search(domain)
                picking_type_id2 = self.env['stock.picking.type'].search(
                    [('active', '=', True)])[0]
                partner_obj = self.env['res.partner']
                partner_id = 0
                partner_ids = partner_obj.search([('name', '=', 'Default Client')])
                if partner_ids:
                    partner_id = partner_ids.id
                else:
                    partner_create = partner_obj.create({'name': 'Default Client', 'supplier': True}).id
                    partner_id = partner_create

                purchase = purchase_obj.create({
                    'partner_id': partner_id,
                    'date_order': time.strftime("%m/%d/%Y %H:%M:%S"),
                    'picking_type_id': picking_type_id2.id,  
                    'date_planned': time.strftime("%m/%d/%Y %H:%M:%S"),
                    'branch_id': self.branch_id.id,
                    'state': 'pm',
                    'users_followers': [(6, 0, users)]
                })

                pur_search = purchase_obj.search([('id', '=', purchase.id)])
                
                tax = []
                for rex in self.order_line:
                    # tax = [tax for tax in self.rex.taxes_id]
                    for tec in rex.taxes_id:
                        tax.append(tec.id)
                    values = {
                        'order_id': purchase.id,
                        'product_id': rex.product_id.id,
                        'name': rex.name,
                        'product_qty': rex.qty,
                        'price_unit': rex.actual_price,
                        'product_uom': rex.label.id,
                        'name': rex.product_id.name,
                        #  time.strftime("%m/%d/%Y %H:%M:%S"),
                        'date_planned': rex.date_planned,
                        'price_subtotal': rex.total, # rex.actual_price * rex.qty,
                        'price_total': rex.total, #rex.actual_price * rex.qty,
                        'taxes_id': [(6, 0, tax)]

                    }

                    purchase_browse = purchase_obj.browse(purchase.id)
                    purchase_browse.write({'order_line': [(0, 0, values)]})
                    purchase_browse.write({'state': 'pm'})

                return self.write(
                    {'purchase_order_id': purchase_browse.id, 'state': 'done'})

    @api.multi
    def button_return_request_back(self):  #  vis_account,
        users = []
        for rec in self.users_followers:
            users.append(rec.id)
        return {
            'name': 'Return of Request',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'generalreturn.ikoyi',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_inv_memo_record': self.id,
                'default_date': self.date_order,
                'default_purchase_id': self.purchase_order_id.id,
                'default_users_followers': [(6, 0, users)]
            },
        }


class ConstructionMaterial_Line(models.Model):
    _name = 'ik.material.line'
    _description = 'Material Request Line'
    _order = 'id desc'
    _rec_name = "product_id"

    def change_uom(self):
        uom = self.env['product.uom'].search([('name', '=', 'Unit(s)')])
        return uom.id

    def branch_name_compute(self):
        branch = self.order_id.branch_id
        return branch.id

    @api.model
    def _get_context_warehouse(self):
        if 'ware' in self._context:
            return self._context['ware']
        return self.warehouse.id

    def get_context_dateplan(self):
        if 'dplan' in self._context:
            return self._context['dplan']
        return self.date_planned or fields.Datetime.now()

    order_id = fields.Many2one(
        'ik.material.request',
        string='Reference',
        index=True,
        required=True,
        ondelete='cascade')
    warehouse = fields.Many2one(
        'stock.warehouse',
        'Warehouse',
        default=_get_context_warehouse)
    location = fields.Many2one('stock.location', 'Stock Location')

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        change_default=True,
        required=True)
    name = fields.Text(string='Purpose', required=False)
    label = fields.Many2one(
        'product.uom',
        string='UOM',
        default=change_uom,
        required=True)
    taxes_id = fields.Many2many('account.tax', string=u'Taxes')

    qty = fields.Float('Requested Qty', default=1.0, )
    rate = fields.Float(
        'Current Rate',
        readonly=True,
        related='product_id.list_price')
    total = fields.Float('Total', compute='get_total')
    date_planned = fields.Datetime(
        string='Exp. Date',
        default=fields.Datetime.now,
        required=False,
        index=True)
    remaining_qty = fields.Float('Remaining Qty')
    actual_price = fields.Float(
        'Requesting Price',
        default=0.0,
        help="The user will enter the requesting price to buy it")

    branch_id = fields.Many2one(
        'res.branch',
        string="Branch",
        default=lambda self: self.env.user.branch_id.id)
    actual_qty = fields.Float('Stock Qty', compute="Quantity_Moves", store=True)
 
    @api.onchange('location')
    def domain_product_location(self):
        domain = {}
        products = []
        for rec in self:
            stock_location = self.env['stock.location']
            search_location = stock_location.search(
                [('branch_id', '=', rec.branch_id.id)])
            for r in search_location:
                stock_quant = self.env['stock.quant']
                search_quanty = stock_quant.search(
                    [('location_id', '=', r.id)])
                for ref in search_quanty:

                    products.append(ref.product_id.id)
                    domain = {'product_id': [('id', 'in', products)]}
            return {'domain': domain}
    @api.one
    @api.depends('product_id')
    def Quantity_Moves(self):
        diff = 0.0
        # for rec in self:
        stock_location = self.env['stock.location']
        search_location = stock_location.search(
                [('branch_id', '=', self.branch_id.id)])
        for r in search_location:
            stock_quant = self.env['stock.quant']
            search_quanty = stock_quant.search(
                    [('location_id', '=', r.id), ('product_id', '=', self.product_id.id)])
            if search_quanty:
                for rey in search_quanty:
                    diff += rey.qty
        self.actual_qty = diff

    @api.depends('qty', 'actual_price', 'taxes_id')
    def get_total(self):
        totals = 0.0
        taxes = 0.0
        for rec in self:
            if rec.taxes_id:
                for tax in rec.taxes_id:
                    if tax.amount_type == "fixed":
                        taxes += tax.amount
                        totals = (rec.qty * rec.actual_price) + taxes
                    if tax.amount_type == "percent":
                        taxes += tax.amount / 100
                        totals = (rec.qty * rec.actual_price) * taxes + (rec.qty * rec.actual_price)   
            elif not rec.taxes_id:
                totals = rec.qty * rec.actual_price
            rec.total = totals


class Send_GeneralIkoyi_back(models.Model):
    _name = "generalreturn.ikoyi"

    resp = fields.Many2one(
        'res.users',
        'Responsible',
        default=lambda self: self.env.user.id)  #  , default=self.write_uid.id)
    memo_record = fields.Many2one('ikoyi.request', 'Request ID',)
    inv_memo_record = fields.Many2one(
        'ik.material.request', 'Inventory Request ID',)
    reason = fields.Char('Reason', required=True)

    date = fields.Datetime('Date')

    users_followers = fields.Many2many('hr.employee', string='Add followers')
    purchase_id = fields.Many2one('purchase.order', 'PO REF')

    @api.multi
    def post_back(self):
        email_from = self.env.user.email
        # email_to = self.direct_memo_user.work_email

        inv = self.env['ik.material.request']
        ikoyi_request_obj = self.env['ikoyi.request'].search(
            [('id', '=', self.memo_record.id)])
        purchase = self.env['purchase.order'].search(
            [('id', '=', self.purchase_id.id)])
        get_inv = inv.search([('purchase_order_id', '=', self.purchase_id.id)])

        for states in self.inv_memo_record:
            if states.state == "store_manager":
                states.write({'state': 'refuse'})
                self.send_store_officer_mail()

        if get_inv:
            for status in get_inv:
                status.write({'state': 'refuse'})
                self.send_store_manager_mail()
            for pur in purchase:
                pur.write({'state': 'cancel'})

        if ikoyi_request_obj:
            for tec in ikoyi_request_obj:
                tec.write({'state': 'refused'})

                purchases = self.env['purchase.order'].search(
                    [('id', '=', self.purchase_id.id)])
                get_invs = inv.search(
                    [('purchase_order_id', '=', self.purchase_id.id)])
                if purchases:
                    for purs in purchases:
                        purs.write({'state': 'cancel'})
                if get_invs:
                    for invs in get_invs:
                        invs.write({'state': 'refuse'})

        return{'type': 'ir.actions.act_window_close'}

    def mail_sending(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):

        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)
            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            print(all_mails)
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item)for item in all_mails))

            # mail_appends = (', '.join(str(item)for item in append_mails))
            # mail_appends_to = (', '.join(str(item)for item in append_mails_to))
            subject = "Request Refusal"
            bodyxX = "Dear Sir, <br/>A request with MOF reference Number: {} have been refused\
            by {}<br/>for the following reasons:\
            </br><li>{}</li> <br/>\
            Regards".format(self.purchase_id.name, self.env.user.name, self.reason)
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    def send_store_officer_mail(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('purchase.group_purchase_manager').id
        group_user_id = self.env.ref('stock.group_stock_user').id
        group_user_id3 = self.env.ref('ikoyi_module.store_keeper_ikoyi').id

        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been refused\
            by {}<br/>for the following reasons:\
            </br><li>{}</li> <br/>\
            Regards".format(self.inv_memo_record.name, self.env.user.name, self.reason)
        self.mail_sending(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def send_store_manager_mail(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref(
            'ikoyi_module.inventory_manager_ikoyi').id
        group_user_id = self.env.ref('stock.group_stock_manager').id
        group_user_id3 = self.env.ref('ikoyi_module.store_keeper_ikoyi').id

        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been refused\
            by {} for the following reasons:\
            </br><li>{}</li> <br/>\
            Regards".format(self.purchase_id.name, self.env.user.name, self.reason)
        self.mail_sending(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _order = "id desc"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/> to Review. ".format(base_url)
 
    users_followers = fields.Many2many(
        'hr.employee', string='Followers', required=True)
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee(Initiator)',
        default=_default_employee)
    acc_inv = fields.Many2one(
        'account.invoice',
        string='Invoice ID',
        )
    
    state = fields.Selection([
        ('officer', 'Officer'),
        ('pm', 'PM'),
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True, copy=False, default='officer', track_visibility='onchange')
    set_value = fields.Selection([
        ('gen', 'Generate'), ('nogen', 'Non Generate'), ('addgen', 'Done')
    ], string='Status', readonly=False, index=True, copy=False, track_visibility='always')
    state_mode = fields.Selection([('fixed',
                                    'Fixed Asset'),
                                   ('purchase',
                                    'Purchase'),
                                   ('others',
                                    'Other'),
                                   ],
                                  string='Request Mode',
                                  readonly=False,
                                  index=True,
                                  copy=False,
                                  default='purchase',
                                  track_visibility='onchange')

    @api.multi
    def button_request_approval_by_officer(self):
        for rec in self:
            rec.write({'state': 'pm'})

    @api.multi
    def button_refuse(self):
        return self.button_return_request_back()
        #  return {}

    @api.multi
    def button_return_request_back(self):  #  vis_account,
        users = []
        for rec in self.users_followers:
            users.append(rec.id)
        return {
            'name': 'Return of Request',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'generalreturn.ikoyi',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                #  'default_inv_memo_record': self.id,
                'default_date': self.date_order,
                'default_purchase_id': self.id,
                'default_users_followers': [(6, 0, users)]
            },
        }

    def button_confirm_purchase_order(self, record):  #  vis_post
        #  print "# # # # # # # # # # #  "+ str(self.vendor_bill)
        xxxxlo = self.env['ikoyi.request'].search([('id', '=', record.id)])
        if not xxxxlo:
            raise ValidationError('There is no related Request Created.')
        resp = {
            'type': 'ir.actions.act_window',
            'name': _('Request Reference'),
            'res_model': 'ikoyi.request',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id': xxxxlo.id
        }
        return resp

    @api.multi
    def button_request_approval_by_pm(self):
        users = []
        for rec in self.users_followers:
            users.append(rec.id)

        for rex in self:

            values = {
                #  'default_memo_record': self.id,
                'date': rex.date_order,
                'amountfig': rex.amount_total,
                'purchase_order_id': self.id,
                'name': rex.name,
                'branch_id': rex.branch_id.id,
                'users_followers': [(6, 0, users)],  #  self.employee_id.id,
                'employee_id': rex.employee_id.id,
                'state': 'finance_manager_one',
                'set_value': 'gen',
            }
            ikoyi_obj = 'ikoyi.request'
            create_request = self.env['ikoyi.request'].create(values)
            self.send_recieve_account_mail(create_request.id, ikoyi_obj)
        return self.button_confirm_purchase_order(create_request)

    def send_recieve_account_mail(self, id, model):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.account_payable_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.inventory_manager_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.costing_manager_ikoyi').id

        bodyx = "Dear Sir, <br/>A LPO with reference Number: {} have been confirmed for purchase by {} and the goods is yet to be supplied.\
         Please kindly {} <br/>\
        Regards".format(self.name, self.employee_id.name, self.get_url(id, model))
        self.mail_sending(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def mail_sending(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            print(all_mails)
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item)for item in all_mails)) 
            subject = "Procurement Notification"
            bodyxx = "Dear Sir/Madam, </br>We wish to notify you that a request from {} has been sent to you for approval </br> \
            </br>Kindly {} </br> </br>Thanks".format(self.employee_id.name, self.get_url(self.id, self._name))

            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    @api.multi
    def button_confirm(self):  #  state:draft, group:procurement manager
        res = super(PurchaseOrder, self).button_confirm()

        self.action_rfq_send()
        self.create_invoice()
        stocking = self.env['stock.picking'].search(
            [('origin', 'ilike', self.name)], limit=1)
        if stocking:
            stock_model = "stock.picking"
            self.send_recieve_account_mail(stocking.id, stock_model)
        return res

    @api.multi
    def send_account_mail(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_payable_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.costing_manager_ikoyi').id

        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. \
        Please {} <br/>\
        Regards".format(
            self.name,
            self.employee_id.name,
            self.get_url(
                self.id,
                self._name))
        self.mail_sending(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    @api.multi
    def create_invoice(self):  # invoice memoficer
        if self:
            invoice_list = self.create_vendor_bill()
            
    @api.multi
    def create_vendor_bill(self):
        """ Create Customer Invoice for vendors.
        
        """
        invoice_list = []
        #invoice = 0
        for partner in self:
            invoice = self.env['account.invoice'].create({
                'partner_id': partner.partner_id.id,
                'account_id': partner.partner_id.property_account_payable_id.id,#partner.account_id.id,
                'fiscal_position_id': partner.partner_id.property_account_position_id.id,
                'branch_id': self.env.user.branch_id.id,
                'origin': self.name,
                'date_invoice': datetime.today(),
                'type': 'in_invoice', # vendor
                #'type': 'out_invoice', # customer
            })
            for line in self.order_line:
                line_values = {
                    'product_id': line.product_id.id, # partner.product_id.id,
                    'price_unit': line.price_unit,
                    'quantity': line.product_qty,
                    'price_subtotal': line.price_subtotal,
                    'invoice_id': invoice.id,
                    'purchase_id': self.id,
                    'account_id': self.partner_id.property_account_payable_id.id,

                } 
                invoice_line = self.env['account.invoice.line'].new(line_values)
                invoice_line._onchange_product_id()
                line_values = invoice_line._convert_to_write(
                    {name: invoice_line[name] for name in invoice_line._cache}) 
                invoice.write({'invoice_line_ids': [(0, 0, line_values)]})
                invoice_list.append(invoice.id)
            # invoice.compute_taxes()

            self.acc_inv = invoice.id

            find_id = self.env['account.invoice'].search(
                [('id', '=', invoice.id)])
            find_id.action_invoice_open()

        return invoice_list
 
    @api.multi
    def button_print_purchases(self):
        return self.env['report'].get_action(self, 'ikoyi_module.purchase_order_prints')
    
    
class Ikoyi_Memo_Request(models.Model):
    _name = "ikoyi.request"
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'ir.attachment']
    _order = "id desc"
    
    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'ikoyi.request'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'ikoyi.request', 'default_res_id': self.id}
        return res

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char('Request')
    date = fields.Datetime(
        string='Date',
        default=fields.Date.context_today,
        required=True,
        copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee(Initiator)')

    users_followers = fields.Many2many(
        'hr.employee', string='Add followers', required=True)
    branch_id = fields.Many2one('res.branch', string="Branch")
    location = fields.Many2one('stock.location', 'Stock Location')
    warehouse = fields.Many2one('stock.warehouse', 'Warehouse')

    dept_ids = fields.Char(
        string='Department',
        related='employee_id.department_id.name',
        readonly=True,
        store=True)
    description = fields.Char('Note')
    project_id = fields.Many2one('account.analytic.account', 'Project')
    amountfig = fields.Float('Request Amount', store=True)
#  purchase_id
    description_two = fields.Text('Refusal Reasons')
    reason_back = fields.Char('Return Reason')
    file_upload = fields.Binary('File Upload')
    binary_fname = fields.Char('Binary Name')

    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string='Purchase Order')
    status_progress = fields.Float(
        string="Progress(%)",
        compute='_taken_states')
    mof_ref = fields.Many2one(
        'ik.material.request',
        'Material Order Reference',
        compute="get_mof_ref")
 
    state = fields.Selection([
        ('store_officer_one', 'Store Officer'),
        ('store_manager_one', 'Store Manager'),
        ('procurement_manager_one', 'Procurement Manager'),
        ('finance_manager_one', 'F&A Manager'), 
        ('inter_control', 'Internal Control '),
        ('general_manager_one', 'General Manager'),

        ('finance_manager_two', 'F&A Manager'),
        ('procurement_manager_two', 'Procurement Manager'), 
        ('account_payable_one', 'Account Payable'),
        ('accountant', 'Accountant'),
        ('account_payable_two', 'Account Payable'),
        ('finance_manager_three', 'F&A Manager'),
        ('inter_control_two', 'Internal Control '),
        ('general_manager_two', 'General Manager'), 
        ('procurement_state', 'Procurement State'),
        ('good_reject', 'Goods Rejected'),
        ('vice', 'Vice Chairman'),
        ('chair', 'Chairman'),
        ('schedule', 'Payment Requisition'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('refused', 'Refused'),
    ], string='Status', readonly=True, index=True, copy=False, default='store_officer_one', track_visibility='onchange')

    @api.model
    def _needaction_domain_get(self): 
        return [('state', 'in', ['finance_manager_one', 'inter_control',
                                 'general_manager_one', 'account_payable_one', 
                                 'accountant', 'account_payable_two', 'vice', 'chair',
                                 'general_manager_two', 'inter_control_two', 'schedule'])]

    @api.depends('purchase_order_id')
    def get_mof_ref(self):
        mof = self.env['ik.material.request'].search(
            [('purchase_order_id', '=', self.purchase_order_id.id)])
        for tec in mof:
            tec.write({'mof_ref': mof.id})

    @api.multi
    def get_vendor_bills(self):  # verify,
        search_view_ref = self.env.ref(
            'account.view_account_invoice_filter', False)
        form_view_ref = self.env.ref('account.invoice_form', False) 
        tree_view_ref = self.env.ref('account.invoice_tree', False)
        lis = []
        request_ik = self.env['purchase.order'].search([('id', '=', self.purchase_order_id.id )])
        for tec in request_ik:
            lis.append(tec.acc_inv.id)

        return {
            'domain': [('id', '=', lis)],
            'name': 'Invoices',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            # 'views': [(form_view_ref.id, 'form')],
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'search_view_id': search_view_ref and search_view_ref.id,
        } 
    @api.multi
    @api.depends('state')
    #  Depending on any field change (ORM or Form), the function is triggered.
    def _taken_states(self):
        for order in self:
            if order.state == "store_manager_one":
                order.status_progress = 5
            elif order.state == "procurement_manager_one":
                order.status_progress = 25

            elif order.state == "finance_manager_one":
                order.status_progress = 50

            elif order.state == "general_manager_one":
                order.status_progress = 70

            elif order.state == "vice":
                order.status_progress = 75

            elif order.state == "chair":
                order.status_progress = 80

            elif order.state == "refused":
                order.status_progress = 0

            elif order.state == "done":
                order.status_progress = 100

            else:
                order.status_progress = 100 / len(order.state)

    @api.multi
    def button_send_back(self):  #  Send memo back
        users = []
        for rec in self.users_followers:
            users.append(rec.id)

        return {
            'name': 'Reason for Return',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'send.refused.wizardikoyi',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_memo_record': self.id,
                'default_date': self.date,
                #  self.employee_id.id,
                'default_users_followers': [(6, 0, users)]
            },
        }

    @api.multi
    def unlink(self):
        for rec in self.filtered(
            lambda rec: rec.state not in [
                'store_officer_one',
                'cancel',
                'done',
                'refused']):
            raise ValidationError(
                _('You cannot delete a request which is in %s state.') %
                (holiday.state,))
        return super(Send_Request, self).unlink()

    def message_posts(self):
        body = "REFUSAL NOTIFICATION;\n %s" % (self.description_two)
        records = self._get_followers()
        followers = records
        self.message_post(
            body=body,
            subtype='mt_comment',
            message_type='notification',
            partner_ids=followers)

    @api.constrains('users_followers')
    def _check_something(self):
        if not self.users_followers:
            raise ValidationError(
                "You are required to select either Followers")

    def message_posts_back(self):
        body = "RETURN NOTIFICATION;\n %s" % (self.reason_back)
        records = self._get_followers()
        followers = records
        self.message_post(
            body=body,
            subtype='mt_comment',
            message_type='notification',
            partner_ids=followers)

    def write_state_done(self):
        mof = self.env['ik.material.request'].search(
            [('purchase_order_id', '=', self.purchase_order_id.id)])
        mof.write({'state': 'pm_done'})

    def write_state_storeback(self):
        mof = self.env['ik.material.request'].search(
            [('purchase_order_id', '=', self.purchase_order_id.id)])
        mof.write({'state': 'store_manager'})

    def write_state_storerefuse(self):
        mof = self.env['ik.material.request'].search(
            [('purchase_order_id', '=', self.purchase_order_id.id)])
        mof.write({'state': 'refuse'})

    def write_state_storecancel(self):
        mof = self.env['ik.material.request'].search(
            [('purchase_order_id', '=', self.purchase_order_id.id)])
        mof.write({'state': 'cancel'})

    def mail_sending(self, email_from, group_user_id, bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:

            group_users = groups.search([('id', '=', group_user_id)])
            group_emails = group_users.users
            mail_to = []
            append_mails = []
            for mai in group_emails:
                mail_to.append(mai.login)

            for group_mail in self.users_followers:
                append_mails.append(group_mail.work_email)

            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_appends = (', '.join(str(item)for item in append_mails))
            email_to = (', '.join(str(item)for item in mail_to))

            subject = "Request Notification"
            extrax = self.employee_id.work_email 
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': email_to,
                'email_cc': mail_appends,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    @api.multi 
    def button_procurement_manager_send_to_FA(self):
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        extra = self.employee_id.work_email
        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to Review. <br/>\
        Regards".format(self.mof_ref.name, self.employee_id.name)
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'finance_manager_one','description_two':'',})
        #  self.write_state()

    @api.multi 
    def button_fA_send_to_Internal_control(self):
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.audit_boss_ikoyi').id
        extra = self.employee_id.work_email
        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to Review. <br/>\
        Regards".format(self.name, self.employee_id.name, self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'inter_control','description_two':'',})

    def get_url_pur(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>".format(base_url)

    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>. ".format(base_url)

    @api.multi 
    def button_procurement_creates_LPO(self):
        purchase_id = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        #  self.send_mail_to_two()
        purchase_id.write({'state': 'draft','description_two': ''})
        self.write({'state': 'procurement_state'})
        return self.button_confirm_purchase_order()

    @api.multi
    def button_internal_to_conditions(self):  #  state = inter_control
        amount = 50000
        email_from = self.env.user.email
        purchase_id = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        pur_obj = "purchase.order"
        if self.amountfig <= amount:
            self.write({'state': 'procurement_manager_two','description_two':'',})
            group_user_id = self.env.ref(
                'ikoyi_module.procurement_manager_ikoyi').id
            extra = self.employee_id.work_email
            self.button_procurement_creates_LPO()
            bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and a draft LPO is created. \
            Please kindly {} to Review<br/>\
            Regards".format(self.mof_ref.name, self.employee_id.name, self.get_url_pur(purchase_id.id, pur_obj))
            self.mail_sending(email_from, group_user_id, bodyx)

        elif self.amountfig > 50000:
            group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
            extra = self.employee_id.work_email
            bodyx = "Dear Sir, </br>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to Review<br/>\
            Regards".format(self.name, self.employee_id.name, self.get_url(self.id, self._name))
            self.mail_sending(email_from, group_user_id, bodyx)
            self.write({'state': 'general_manager_one','description_two':'',})

    @api.multi
    def button_generalmanager_to_vice_chairman(self):  #  general_manager_one
        amount = 50000
        email_from = self.env.user.email

        if self.amountfig in range(amount, 200001):
            group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
            extra = self.employee_id.work_email
            bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to Review <br/>\
            Regards".format(self.name, self.employee_id.name, self.get_url(self.id, self._name))
            self.mail_sending(email_from, group_user_id, bodyx)
            return self.write({'state': 'procurement_manager_two','description_two':'',})

        elif self.amountfig > 200001:
            group_user_id = self.env.ref('ikoyi_module.vice_chairman_ikoyi').id
            extra = self.employee_id.work_email
            bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to Review <br/>\
            Regards".format(self.mof_ref.name, self.employee_id.name, self.get_url(self.id, self._name))
            self.write({'state': 'vice','description_two':'',})
            return self.mail_sending(email_from, group_user_id, bodyx)
        else:
            # self.write({'state': 'vice'})
            raise ValidationError('Not in figure range')

    @api.multi
    def button_vice_chairman_to_fin_or_chairman(self):  #  vice
        amount = 50000
        email_from = self.env.user.email

        if self.amountfig in range(200001, 500000):
            group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
            extra = self.employee_id.work_email
            bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to review <br/>\
            Regards".format(self.mof_ref.name, self.employee_id.name, self.get_url(self.id, self._name))
            self.mail_sending(email_from, group_user_id, bodyx)
            self.write({'state': 'procurement_manager_two','description_two':'',})

        elif self.amountfig > 500000:
            group_user_id = self.env.ref('ikoyi_module.chairman_ikoyi').id
            extra = self.employee_id.work_email
            bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to review<br/>\
            Regards".format(self.mof_ref.name, self.employee_id.name, self.get_url(self.id, self._name))
            self.mail_sending(email_from, group_user_id, bodyx)
            self.write({'state': 'chair', 'description_two':'',})

    @api.multi
    def button_chair_send_to_FA(self):
        email_from = self.env.user.email
        purchase_id = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        pur_obj = "purchase.order"
        group_user_id = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id
        extra = self.employee_id.work_email
        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been confirmed by {}. You can proceed to Create a LPO. Please kindly {}to review <br/>\
        Regards".format(self.mof_ref.name, self.employee_id.name, self.get_url_pur(purchase_id.id, pur_obj))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'procurement_manager_two','description_two':'',})

    @api.multi
    def button_FA_send_to_procurement(self):  #  procurement_manager_two
        email_from = self.env.user.email
        purchase_id = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        pur_obj = "purchase.order"
        group_user_id = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id
        extra = self.employee_id.work_email
        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {}to review <br/>\
        Regards".format(self.mof_ref.name, self.employee_id.name, self.get_url_pur(purchase_id.id, pur_obj))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'procurement_manager_two','description_two':'',})

    def button_confirm_purchase_order(self): 
        xxxxlo = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        if not xxxxlo:
            raise ValidationError('There is no related PO for this Memo. \
                                 Kindly create a Purchase order for it and try again.')
        resp = {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Reference'),
            'res_model': 'purchase.order',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id': xxxxlo.id
        }
        return resp

    @api.multi
    def button_APO_to_Accountant(self):  #  state account_payable_one
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.accountant_ikoyi').id
        extra = self.employee_id.work_email
        bodyx = "Dear Sir, <br/>A requisition request with reference Number: {} have been sent to account for checking.\
         Kindly {} to view the record..<br/> Regards".format(self.name, self.get_url_pur(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'accountant','description_two':'',})
        self.auto_create_requisition() 

    @api.multi
    def button_Accountant_To_FA(self):  #  state accountant
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        extra = self.employee_id.work_email
        bodyx = "Dear Sir, <br/>A requisition request with reference Number: {} have been checked and approved. You can {} validate\
            . <br/>\
            Regards".format(self.name, self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'finance_manager_three','description_two':'',})

    @api.multi
    def button_FA3_internal(self):  #  finance_manager_three
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.audit_boss_ikoyi').id
        extra = self.employee_id.work_email
        bodyx = "Dear Sir, <br/>A requisition request with reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to Review. <br/>\
        Regards".format(self.name, self.employee_id.name, self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'inter_control_two','description_two':'',})

    @api.multi
    def button_INTERNAL2_GM(self):  #  state inter_control_two
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
        extra = self.employee_id.work_email
        bodyx = "Dear Sir, <br/>A requisition request with reference Number: {} have been raised by {} and is waiting for your approval. Please kindly {} to Review. <br/>\
        Regards".format(self.name, self.employee_id.name, self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'general_manager_two','description_two':'',})

    @api.multi
    def button_GM2_APO2(self):  #  state general_manager_two
        self.send_mail_to_two3()
        self.write({'state': 'schedule'})

    def auto_create_mandate(self):
        schedule = self.env['payment.mandate.ikoyi']
        po_obj = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        po_browse = self.env['purchase.order'].browse(po_obj.id)
        bank_acc = self.env['res.partner.bank'].search(
            [('partner_id', '=', po_browse.partner_id.id)])
        vendor_bank = 0
        vendor_acc = 0
        t = 0
        p = 0
        for tec in bank_acc:
            vendor_acc = tec[0].id  #  tec[0].bank_id.id
            vendor_bank = vendor_acc.bank_id.id
        for line in po_obj.order_line:
            t += line.product_qty
            p += line.price_unit
        account_invoice = self.env['account.invoice'].search(
            [('partner_id', '=', self.purchase_order_id.partner_id.id),('origin','=ilike',self.purchase_order_id.name)])
        for rec in self:
            vals = {}
            for pur in po_obj:
                vals['pay_amount'] = t * p
                vals['date_sche'] = fields.Date.today()
                vals['name'] = pur.partner_id.id or self.env.user.partner_id.id
                vals['select_mode'] = "pur"
                vals['vendor_account'] = vendor_acc
                vals['vendor_bank'] = vendor_bank
                vals['purchase_id'] = pur.id
                vals['product_qty'] = t
                vals['ikoyi_ref'] = self.id 
                vals['state'] = "account_payable"
            pay = schedule.create(vals)
            payment = self.env['payment.mandate.ikoyi'].search(
                [('id', '=', pay.id)])
            inv_list = []
            for inv in account_invoice[0]: 
                inv_list.append(inv.id)
            payment.write({'ikoyi_req_ref': pay.id, 'invoice_ids':[(6, 0, inv_list)]})
            payment.accountpay_accountant()

    @api.multi
    def raise_payment_mandate(self):  #  state general_manager_two
        self.auto_create_mandate()
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.accountant_ikoyi').id

        pay = self.env['payment.mandate.ikoyi'].search(
            [('purchase_id', '=', self.purchase_order_id.id)])
        pay_model = 'payment.mandate.ikoyi' 
        if pay:
            bodyx = "Dear Sir, <br/>A mandate request with purchase reference Number: {} have been sent to accounts for approval. Kindly {} to view. <br/>\
            Regards".format(self.purchase_order_id.name, self.get_url_pur(pay[0].id, pay_model))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            pay.write({'state': 'accountant'})
            self.write({'state': 'done'})
        else:
            raise ValidationError('Not created')

    def auto_create_requisition(self):
        schedule = self.env['payment.schedule.ikoyi']
        po_obj = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        po_browse = self.env['purchase.order'].browse(po_obj.id)
        bank_acc = self.env['res.partner.bank'].search(
            [('partner_id', '=', po_browse.partner_id.id)])
        
        vendor_bank = 0
        vendor_acc = 0
        for tec in bank_acc:
            # vendor_bank= tec[0].id
            vendor_acc = tec[0].id  #  tec[0].bank_id.id
            vendor_bank = vendor_acc.bank_id.id

        t = 0.0
        p = 0.0
        for line in po_obj.order_line:
            t += line.product_qty
            p += line.price_unit

        for rec in self:
            vals = {}
            for pur in po_obj:
                vals['pay_amount'] = t * p
                vals['date_sche'] = fields.Date.today()
                vals['name'] = pur.partner_id.id or self.env.user.partner_id.id
                vals['select_mode'] = "pur"
                vals['vendor_account'] = vendor_acc
                vals['vendor_bank'] = vendor_bank
                vals['purchase_id'] = pur.id
                vals['product_qty'] = t
                vals['ikoyi_ref'] = self.id
                vals['state'] = "account_payable"

            pay = schedule.create(vals)
            payment = self.env['payment.schedule.ikoyi'].search(
                [('id', '=', pay.id)])

            payment.accountpay_accountant()

    def send_mail_to_two3(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.account_payable_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.accountant_ikoyi').id

        payment_schedule = self.env['payment.schedule.ikoyi']
        pay_model = 'payment.schedule.ikoyi'
        pay = payment_schedule.search([('ikoyi_ref', '=', self.id)])
        if pay:
            bodyx = "Dear Sir/Madam, <br/>A request with MOF reference Number: {} have been recieve and inspected by the respective officers\
            <br/>.We also request you {} to view the draft payment schedule for the vendors payment or {} to view the source document (MOF)\
            </br> \
            Regards".format(
                self.name, self.get_url_pur(
                    pay.id, pay_model), self.get_url(
                    self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)

# # # # # # # # # # # # # # # # # #  Mail for Three People # # # # # # # # # # # # # # # # # # # # # # # 
    def mail_sending_for_three(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            print(all_mails)
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item)for item in all_mails)) 
            subject = "MOF Request"
            bodyxx = "Dear Sir/Madam, </br>We wish to notify you that a request from {} has been sent to you for approval </br> </br>Kindly review it. </br> </br>Thanks".format(
                self.employee_id.name)
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

# # # # # # # # # # # # # # #  WORKFLOW FOR REQUESTS ENDS # # # # # #  

    def write_state_draft(self):
        mof = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        mof.write({'state': 'draft'})
# # # # # # # # # # # # # 3 RETURN REJECT  FUNCTIONS # # # # # # # # # 

    @api.multi
    def button_reject_all(self, name): 
        users = []
        for rec in self.users_followers:
            users.append(rec.id)
        return {
            'name': name,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'ikoyirefuse.message',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_memo_record': self.id,
                'default_date': self.date,
                'default_purchase_id': self.purchase_order_id.id,
                'default_users_followers': [(6, 0, users)]
            },
        }
 
    @api.multi
    def button_FA_return_request_back(self): 
        users = []
        for rec in self.users_followers:
            users.append(rec.id)
        return {
            'name': 'Return of Request',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'generalreturn.ikoyi',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_memo_record': self.id,
                'default_date': self.date,
                'default_purchase_id': self.purchase_order_id.id,
                'default_users_followers': [(6, 0, users)]
            },
        }

# # # # # # # #  button reject internal three to financial three # # 

    @api.multi
    def button_refusal_general_account_three(self):  #  internal_control1,
        if not self.reason_back:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note below')
        else:
            self.write({'state': 'finance_manager_three'})
            return self.mail_refusal_internal_account_three()
            print 'Nice'

    @api.multi
    def internal_mail_reject_requistion(self):  #  internal_control1,
        if not self.reason_back:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note below')
        else:
            self.write({'state': 'finance_manager_three'})
            return self.mail_refusal_internal_account_three()
            print 'Nice'

    @api.multi
    def button_reject_internal_for_fA(self):  #  internal_control1,
        if not self.description_two:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note below')
        else:
            self.state = "finance_manager_one"
            return self.mail_refusal_internal_account()
            print 'Nice'

    @api.multi
    def button_reject_general_for_fA(self):  #  internal_control1,
        if not self.description_two:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note below')
        else:
            self.state = "finance_manager_one"
            return self.mail_refusal_general_account()
            print 'Nice'

    @api.multi
    def button_reject_vice_for_general(self):  #  internal_control1,
        if not self.description_two:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note below')
        else:
            self.state = "general_manager_one"
            return self.mail_refusal_vice_general()
            print 'Nice'

    @api.multi
    def button_reject_chair_general(self):  #  internal_control1,
        if not self.description_two:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note below')
        else:
            self.state = "general_manager_one"
            return self.mail_refusal_chair_general()
            print 'Nice'
            
    @api.multi
    def button_refusal_internal_to_fAX(self):  #  internal_control1,
        if not self.reason_back:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note below')
        else:
            self.write({'state': 'finance_manager_three'})
            return self.mail_refusal_internal_account_three()
            print 'Nice'

    def mail_sending_refusal(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            print(all_mails)
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item)for item in all_mails))
            subject = "Request Refusal"
             
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    def mail_refusal_internal_account(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref(
            'ikoyi_module.inventory_manager_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id
        name = 'Internal Control Reason for Refusal'
        bodyx = "<b>{} <b/></br> The Following Request is refused by {} because of the following reasons: </br><li> {}<li/> [SEE FULL REMARKS]".format(
            name, self.env.user.name, self.description_two)
        self.mail_sending_refusal(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def mail_refusal_general_account(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref(
            'ikoyi_module.inventory_manager_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id
        name = 'General Manager Reason for Refusal'
        bodyx = "<b>{} <b/></br> The Following Request is refused by {} because of the following reasons: </br><li> {}<li/> [SEE FULL REMARKS]".format(
            name, self.env.user.name, self.description_two)
        self.mail_sending_refusal(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def mail_refusal_vice_general(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id
        name = 'Vice Chairman Reason for Refusal'
        bodyx = "<b>{} <b/></br> The Following Request is refused by {} because of the following reasons: </br><li> {}<li/> [SEE FULL REMARKS]".format(
            name, self.env.user.name, self.description_two)
        self.mail_sending_refusal(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def mail_refusal_chair_general(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id
        name = 'Chairman Reason for Refusal'
        bodyx = "<b>{} <b/></br> The Following Request is refused by {} because of the following reasons: </br><li> {}<li/> [SEE FULL REMARKS]".format(
            name, self.env.user.name, self.description_two)
        self.mail_sending_refusal(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def mail_refusal_internal_account_three(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.accountant_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.account_payable_ikoyi').id

        name = 'Internal Control Reason for Refusal'
        bodyx = "<b>{} <b/></br> The Following Payment requisiton is refused by {} because of the following reasons: </br><li> {}<li/> [SEE FULL REMARKS]".format(
            name, self.env.user.name, self.description_two)
        self.mail_sending_refusal(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def mail_refusal_general_account_three(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.accountant_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.account_payable_ikoyi').id

        name = 'General Chairman Reason for Refusal'
        bodyx = "<b>{} <b/></br> The Following Payment Requisiton is refused by {} because of the following reasons: </br><li> {}<li/> [SEE FULL REMARKS]".format(
            name, self.env.user.name, self.description_two)
        self.mail_sending_refusal(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)
    

class IkoyiRefuse_Message(models.Model):
    _name = "ikoyirefuse.message"
    
    reason = fields.Char('Reason', required=True)
    date = fields.Datetime('Date') 
    resp = fields.Many2one('res.users', 'Responsible')
    memo_record = fields.Many2one('ikoyi.request', 'Request ID')
    purchase_id = fields.Many2one('purchase.order', 'PO REF')
    users_followers = fields.Many2many(
        'hr.employee', string='Add followers', required=True)

    def write_state(self):
        mof = self.env['ik.material.request'].search(
            [('purchase_order_id', '=', self.purchase_order_id.id)])
        mof.write({'state': 'refused'})

    def write_state_ikoyi_req(self):
        mof = self.env['ikoyi.request'].search(
            [('id', '=', self.memo_record.id)])
        if mof:
            mof.write({'state': 'refused'})

    @api.multi
    def post_refuse(self):
        get_state = self.env['ikoyi.request'].search(
            [('id', '=', self.memo_record.id)])
        reasons = "%s Refused the Request for the PO %s because of the following reason: \n %s." % (
            self.env.user.name, self.reason, self.purchase_id.name)
        get_state.write({'description_two': reasons, 'state': 'refused'}) 
        self.send_refusal_mail()
        self.write_state_ikoyi_req()
        self.write_state()

        return{'type': 'ir.actions.act_window_close'}

    def send_refusal_mail(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref(
            'ikoyi_module.inventory_manager_ikoyi').id
        group_user_id = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id

        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been refused\
        by {}<br/>for the following reasons:\
        </br><li>{}</li> <br/>\
        Regards".format(self.purchase_id.name, self.env.user.name, self.reason)
        self.mail_sending(email_from, group_user_id, group_user_id2, bodyx)

    def mail_sending(self, email_from, group_user_id, group_user_id2, bodyx):

        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:

            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_emails = group_users.users
            group_emails2 = group_users2.users 
            append_mails = []
            append_mails_to = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for followers in order.users_followers:
                append_mails.append(followers.work_email)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_appends = (', '.join(str(item)for item in append_mails))
            mail_appends_to = (', '.join(str(item)for item in append_mails_to))
            subject = "Request Refusal" 
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_appends_to,
                'email_cc': mail_appends,
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)


class Send_MessageIkoyi_back(models.Model):
    _name = "send.back.ikoyi"

    resp = fields.Many2one(
        'res.users',
        'Responsible',
        default=lambda self: self.env.user.id)   
    memo_record = fields.Many2one('ikoyi.request', 'Request ID',) 
    reason = fields.Char('Reason', required=True)

    date = fields.Datetime('Date')
    direct_memo_user = fields.Many2one(
        'hr.employee', 'Initiator', required=True)
    users_followers = fields.Many2many('hr.employee', string='Add followers')
    purchase_id = fields.Many2one('purchase.order', 'PO REF')

    @api.multi
    def post_back(self):
        email_from = self.env.user.email
        email_to = self.direct_memo_user.work_email

        store = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.store_keeper_ikoyi")
        inv = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.inventory_manager_ikoyi")
        pro_office = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.procurement_officer_ikoyi")
        pm = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.procurement_manager_ikoyi")
        apo = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.account_payable_ikoyi")
        aud_boss = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.audit_boss_ikoyi")
        acc_boss = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.account_boss_ikoyi")
        acc = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.accountant_ikoyi")
        gm = self.direct_memo_user.user_id.has_group("ikoyi_module.gm_ikoyi")

        vice = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.vice_chairman_ikoyi")
        chair = self.direct_memo_user.user_id.has_group(
            "ikoyi_module.chairman_ikoyi")

        get_state = self.env['ikoyi.request'].search(
            [('id', '=', self.memo_record.id)])
        reasons = "<b><h4>From %s </br></br>Please refer to the reasons below </br> %s.</h4></b>" % (
            self.env.user.name, self.reason)
        get_state.write({'reason_back': reasons}) 
        if pm:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'procurement_manager_one'})
        elif apo:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'account_payable_one'})
        elif aud_boss:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'inter_control'})

        elif acc:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'accountant'})

        elif acc_boss:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'finance_manager_two'})
        elif gm:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'general_manager_one'})
        elif vice:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'vice'})

        elif chair:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'chair'})

        elif store:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'store_officer_one'})

        elif inv:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'store_manager_one'})

        elif pro_office:
            self.send_back_mail(email_from, email_to, reasons)
            get_state.write({'state': 'procurement_manager_one'})

        else:
            self.send_back_mail(email_from, email_to, reasons)

        return{'type': 'ir.actions.act_window_close'}

    def send_back_mail(self):
        email_from = self.env.user.email
        email_to = self.direct_memo_user.work_email

        bodyx = "Dear Sir, <br/>A request with MOF reference Number: {} have been refused\
        by {}<br/>for the following reasons:\
        </br><li>{}</li> <br/>\
        Regards".format(self.purchase_id.name, self.env.user.name, self.reason)
        self.mail_sending(email_from, email_to, bodyx)

    def mail_sending(self, email_from, email_to, bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            append_mails = []
            if order.users_followers:
                for followers in order.users_followers:
                    append_mails.append(followers.work_email)

                email_froms = str(from_browse) + " <" + str(email_from) + ">"
                mail_appends = (', '.join(str(item)for item in append_mails))

            subject = "Request Return"
 
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': email_to,
                'email_cc': mail_appends,
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)


class PickingInherit(models.Model):
    _inherit = "stock.picking"
    _order = "id desc" 
    file_upload = fields.Binary('File Upload')
    binary_fname = fields.Char('Binary Name')

    '''state = fields.Selection([
        ('draft', 'Draft'),('inspect', 'Inspection Completed'),('await_approval', 'Awaiting Approval'),('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'), ('done', 'Done')], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n"
             " * Waiting Availability: still waiting for the availability of products\n"
             " * Partially Available: some products are available and reserved\n"
             " * Ready to Transfer: products reserved, simply waiting for confirmation.\n"
             " * Transferred: has been processed, can't be modified or cancelled anymore\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore")

    @api.multi
    def first_approve(self):  # # #  state inspect
        for rec in self:
            rec.state = "await_approval"
            po_obj =self.env['purchase.order'].search([('name','=',self.origin)])
            search_req = self.env['ikoyi.request'].search([('purchase_order_id','=',po_obj.id)])

            if search_req:
                search_req.write({'state':'account_payable_one'})
                # self.send_mail_to_two()'''

    @api.multi
    def print_grn(self):
        """print GRN"""
        return self.env['report'].get_action(self, 'ikoyi_module.print_grn_template')
    
    @api.multi
    def print_gro(self):
        """print GRo"""
        return self.env['report'].get_action(self, 'ikoyi_module.print_gro_template')

    
    @api.multi
    def do_new_transfer(self):
        origin = self.origin#value.get('origin')
        
        res = super(PickingInherit, self).do_new_transfer()
        po_obj = self.env['purchase.order'].search(
            [('name', '=', self.origin)])
        search_req = self.env['ikoyi.request'].search(
            [('purchase_order_id', '=', po_obj.id)])
        good_return = self.env['ikoyi.goods_return'].search([('stock_id', '=', self.id)], limit=1)
        if good_return:
            if good_return.state == "update":
                good_return.storer_send_vendor()
                
            if good_return.state == "account":
                good_return.storer_send_vendor() 

        if search_req:
            search_req.write({'state': 'account_payable_one'})
            self.send_mail_to_two(origin,search_req)
    
        return res

    def get_url_pur(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>".format(base_url)

    def send_mail_to_two(self, origin,pay):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.account_payable_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.accountant_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.costing_manager_ikoyi').id
        '''purchase_d = self.env['purchase.order'].search(
            [('name', 'ilike',origin)])

        pay = self.env['ikoyi.request'].search(
            [('purchase_order_id', '=', purchase_d.id)])'''
            
        pay_model = 'ikoyi.request' 
        if pay:
            bodyx = "Dear Sir/Madam, <br/>Prior to the request with purchase reference Number: {}, store Manager have confirmed the goods from the Supplier.\
            </br>Kindly Let us know when you are ready to inspect the recieved goods. You can also {} to review<br/>\
            Regards".format(self.origin, self.get_url_pur(pay[0].id, pay_model))
            self.mail_sending(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
        else:
            raise ValidationError('No record found')

    def mail_sending(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:

            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            print(all_mails)
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item)for item in all_mails))

            subject = "Good Recieve Notification"

            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    doc_count = fields.Integer(
        compute='_compute_attached_docs_count',
        string="Number of documents attached")

    '''@api.multi
    def attachment_tree_view(self):

        domain = ['&', ('res_model', '=', 'stock.picking'), ('res_id', 'in',
                                                             self.ids)]

        res_id = self.ids and self.ids[0] or False

        return {

            'name': _('Attachments'),

            'domain': domain,

            'res_model': 'ir.attachment',

            'type': 'ir.actions.act_window',

            'view_id': False,

            'view_mode': 'kanban,tree,form',

            'view_type': 'form',

            'help': _('<p class="oe_view_nocontent_create">

                                                    Attach
                documents of your employee.</p>'),

            'limit': 80,

            'context': "{'default_res_model': '%s','default_res_id': %d}"
            % (self._name, res_id)

        }'''

    def _compute_attached_docs_count(self):
        pass
        '''Attachment = self.env['ir.attachment']
        for attach in self:
            attach.doc_count = Attachment.search_count(
                [('res_model', '=', 'stock.picking'), ('res_id', '=', attach.id)])'''



class payment_schedule_ikoyi(models.Model):  #  mandate
    _name = 'payment.schedule.ikoyi'
    _inherit = "ir.attachment"

    name = fields.Many2one(
        'res.partner',
        domain=[
            ('supplier',
             '=',
             True)],
        string='Vendor Name',
        required=True)
    vendor_account = fields.Many2one(
        'res.partner.bank',
        readonly=False,
        store=True,
        string='Vendor Account',
        compute="vendor_account_changes")
    #  , store=True, compute="vendor_account_changes")
    vendor_bank = fields.Many2one(
        'res.bank',
        string='Vendor Bank',
        readonly=False)
    purchase_id = fields.Many2one('purchase.order', string='Purchase Id')
    pay_amount = fields.Float(string='Amount to Pay', store =True, compute="change_bill")
    date_sche = fields.Date(string='Schedule Date', required=True)
    pay_account = fields.Many2one('account.journal', string='Journal')
    invoice_ids = fields.Many2many('account.invoice', string='Vendor Bills')
    
    select_mode = fields.Selection([('mat',
                                     'Ikoyi Procurement Request'),
                                    ('lab',
                                     'Usage Request'),
                                    ('pur',
                                     'Direct Request')],
                                   'Status',
                                   default="pur",
                                   required=True,
                                   track_visibility="always")
    ikoyi_ref = fields.Many2one('ikoyi.request', 'Ikoyi Payment Ref')
    # labour_ref = fields.Many2one('direct.labourx', 'Usage Request')
    product_qty = fields.Float('Requested Quantity', default=1)
    file_upload = fields.Binary('File Upload')
    binary_fname = fields.Char('Binary Name')
    payment_date = fields.Date(string='Payment Date', required=True)

    #  NEW FIELDS
    users_followers = fields.Many2many('hr.employee', string='Add followers')
    signatures_accountant = fields.Binary(string='Accountant Signature')
    signatures_apo = fields.Binary(string='APO Signature')
    
    signatures_fa = fields.Binary(string='F&A Signature')
    signatures_ic = fields.Binary(string='Internal Control Signature')
    signatures_gm = fields.Binary(string='GM Signature')
     
    signatures_acc = fields.Binary(string='Account 2nd Approval') 
    state = fields.Selection([
        ('draft', 'Draft Schedule'),

        ('account_payable', 'Account Payable'),
        ('accountant', 'Accountant'),
        ('f_and_a', 'F&A Manager'),
        ('internal_control', 'Internal Control'),
        ('gm', 'General Manager'),
        ('account_payable_mandate', 'Account Payable'),
        
        ('accountant2_mandate', 'Mandate'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
    ], 'Status', default='account_payable', index=True, required=True, readonly=True, copy=False, track_visibility='always')

    # @api.one
    @api.onchange('name')
    def vendor_account_changes(self):
        bank_acc = self.env['res.partner.bank'].search(
            [('partner_id', '=', self.name.id)])
        for tec in bank_acc:
            self.vendor_account = tec[0].id
            
    @api.onchange('vendor_account')
    def get_account(self):
        for rec in self:
            rec.vendor_bank = rec.vendor_account.bank_id.id
    
    @api.onchange('name')
    def onchange_partner_invoice(self):
        res = {}
        if self.name:
            res['domain'] = {
                            'invoice_id': [('partner_id', '=', self.name.id)],
                            'vendor_account':[('partner_id', '=', self.name.id)],}
        return res
    # @api.one
    @api.depends('invoice_ids')
    def change_bill(self):
        total = 0.0
        for rex in self:
            for rec in rex.invoice_ids:
                total += rec.amount_total
            rex.pay_amount = total

    def create_account_pm_account(self):
        pass  

    def mail_sending(self, email_from, group_user_id, bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_emails = group_users.users
            mail_to = []
            append_mails = []
            for mai in group_emails:
                mail_to.append(mai.login)

            for group_mail in self.users_followers:
                append_mails.append(group_mail.work_email)

            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_appends = (', '.join(str(item)for item in append_mails))
            email_to = (', '.join(str(item)for item in mail_to))
            subject = "Payment Requisition Notification" 
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': email_to,
                'email_cc': mail_appends,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'payment.schedule.ikoyi'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'payment.schedule.ikoyi', 'default_res_id': self.id}
        return res
            
    @api.multi
    def get_vendor_bills(self):  # verify,

        search_view_ref = self.env.ref(
            'account.view_account_invoice_filter', False)
        form_view_ref = self.env.ref('account.invoice_form', False) 
        tree_view_ref = self.env.ref('account.invoice_tree', False)

        return {
            'domain': [('id', 'in', [item.id for item in self.invoice_ids])],
            'name': 'Invoices',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            #  'views': [(form_view_ref.id, 'form')],
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'search_view_id': search_view_ref and search_view_ref.id,
        }

    @api.multi
    def accountpay_accountant(self):
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.accountant_ikoyi').id
        #  extra=self.employee_id.work_email
        bodyx = "Dear Sir, <br/> A request to approve a payment Requisition has been made with vendor Name {}. Please kindly Review. <br/>\
        Regards".format(self.name.name)
        self.mail_sending(email_from, group_user_id, bodyx)

        self.write({'state': 'accountant'})

    @api.multi
    def accountant_fa(self):  #  state accountant account_boss_ikoyi account_payable_ikoyi
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        #  extra=self.employee_id.work_email
        bodyx = "Dear Sir, <br/> A approval has been made on the Requisition made earlier. Please kindly Review. <br/>\
        Regards"
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'f_and_a'})

    @api.multi   #  Raise Mandate
    #  state account_payable_mandate grp apo
    def fa_internal(self):
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.audit_boss_ikoyi').id
        bodyx = "Dear Sir, <br/> A approval has been made on the mandate raised earlier. Please kindly Review. <br/>\
        Regards"
        self.mail_sending(email_from, group_user_id, bodyx)

        self.write({'state': 'internal_control'})

    @api.multi
    def internal_control_gm(self):
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
        bodyx = "Dear Sir, <br/> A approval has been made on the Requisition raised earlier. Please kindly Review. <br/>\
        Regards" 
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'gm'})
        
    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>".format(base_url)   
      
        
    @api.multi
    def gm_apo_mandate(self):
        self.write({'state': 'account_payable_mandate'})
        self.auto_create_mandate()
        return self.send_mail_all_account()
        
    def send_mail_all_account(self):
        bodyx = "Dear Sir, <br/>Payment Requisition have been approved by the general manager \
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.accountant_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.account_payable_ikoyi').id

        if self.id:
            bodyx = bodyx
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx) 
        else:
            raise ValidationError('No Record created')
        
    def mail_sending_for_three(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            # print all_mails
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item) for item in all_mails))
            subject = "Account Requisition Notification"
            
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                #'email_cc': mail_sender,
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
        
    @api.multi
    def button_print_mandate(self):  #  state  approve #  apo
        pass  #  self.write({'state':'approve'})

    @api.multi
    def button_register_payment(self):  #  state  approve #  apo
        self.register_payment()

    @api.multi
    def button_cancel(self):  #  state  ALL #  apo
        self.write({'state': 'cancel'})

    @api.multi
    def button_reject_accountant(self):  #  state  accountant 
        self.write({'state': 'account_payable'})

    @api.multi
    def button_reject_fa(self):  #  state  f_and_a
        self.write({'state': 'accountant'})
    
    @api.multi
    def button_reject_internal_control(self):  #  state  internal_control
        self.write({'state': 'f_and_a'})
        
    @api.multi
    def button_reject_gm(self):  #  state  gm
        self.write({'state': 'internal_control'})
        
     
    @api.multi
    def button_set_draft(self):  #  state  reject, cancel #  apo
        self.write({'state': 'draft'})
 
    def auto_create_mandate(self):
        requisition = self.env['payment.mandate.ikoyi']
        for rec in self:
            vals = {}
            inv_list = []
            vals = {'pay_amount':self.pay_amount,'select_mode':"pur",
                    'vendor_account':self.vendor_account.id,
                    'vendor_bank':self.vendor_bank.id,
                    'date_sche':self.date_sche,
                    'name':self.name.id,
                    'requisition_ref':self.id,
                    'payment_date':fields.Date.today(),
                    }
            for tex in self.invoice_ids:
                inv_list.append(tex.id)
            pay = requisition.create(vals) 
            pay.write({'invoice_ids': [(6, 0, inv_list)]})       
            
    @api.multi
    def accountant_reject(self):
         #  state  accountant #  apo
        self.write({'state': 'account_payable'})
        return self.mail_refusal()

    def mail_refusal(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.accountant_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.account_payable_ikoyi').id

        name = 'Reason for Refusal'
        bodyx = "<b>{} <b/></br> The Payment Requisition with Reference {} is refused by {}. </br>\
        [SEE FULL REMARKS - {} ]".format(name,
                                         self.purchase_id.name,
                                         self.env.user.name,
                                         self.get_url_pur(self.id,
                                                          self._name))
        self.mail_sending_refusal(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def mail_sending_refusal(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            print (all_mails)
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item)for item in all_mails))
            subject = "Request Refusal"
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
            
    def get_url_pur(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>".format(base_url) 
    
    @api.multi
    def print_requisition_pop(self):
        return self.env['report'].get_action(self, 'ikoyi_module.print_singlerequisition_template')


class payment_mandate_ikoyi(models.Model):
    _name = 'payment.mandate.ikoyi'
    _inherit = "ir.attachment"

    name = fields.Many2one(
        'res.partner',
        domain=[
            ('supplier',
             '=',
             True)],
        string='Vendor Name',
        required=True)
    vendor_account = fields.Many2one(
        'res.partner.bank',
        readonly=False,
        store=True,
        string='Vendor Account',
        compute="vendor_account_changes")
    requisition_ref = fields.Many2one(
        'payment.schedule.ikoyi',
        readonly=False)
    payment_date = fields.Date(string='Payment Date', required=False) 
    vendor_bank = fields.Many2one(
        'res.bank',
        string='Vendor Bank',
        readonly=False)
           
    purchase_id = fields.Many2one('purchase.order', string='Purchase Id')
    pay_amount = fields.Float(string='Amount to Pay', store =True, compute="change_bill")
    date_sche = fields.Date(string='Schedule Date', required=True)
    pay_account = fields.Many2one('account.journal', string='Journal')
    select_mode = fields.Selection([('mat',
                                     'Ikoyi Procurement Request'),
                                    ('lab',
                                     'Usage Request'),
                                    ('pur',
                                     'Direct Request')],
                                   'Status',
                                   default="pur",
                                   required=True,
                                   track_visibility="always")
    ikoyi_ref = fields.Many2one('ikoyi.request', 'Ikoyi Payment Ref')
    ikoyi_req_ref = fields.Many2one(
        'payment.mandate.ikoyi',
        'Requisition Ref',
        required=False)
    invoice_ids = fields.Many2many('account.invoice', string='Vendor Bills')
    ref = fields.Many2one('direct.labourx', 'Usage Request')
    product_qty = fields.Float('Requested Quantity', default=1)
    file_upload = fields.Binary('File Upload')
    binary_fname = fields.Char('Binary Name')

    @api.onchange('requisition_ref')
    def get_requisition(self):
        for rec in self.requisition_ref:
            self.name = rec.name
            self.date_sche = rec.date_sche
            self.select_mode=rec.select_mode
            self.pay_account =rec.pay_account
            self.invoice_ids = [(6,0,[item.id for item in rec.invoice_ids])]
            self.file_upload = rec.file_upload
            # self.payment_date = rec.payment_date
            self.vendor_account = rec.vendor_account

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'payment.mandate.ikoyi'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'payment.mandate.ikoyi', 'default_res_id': self.id}
        return res
            
    @api.multi
    def get_vendor_bills(self):  # verify,

        search_view_ref = self.env.ref(
            'account.view_account_invoice_filter', False)
        form_view_ref = self.env.ref('account.invoice_form', False) 
        tree_view_ref = self.env.ref('account.invoice_tree', False)

        return {
            'domain': [('id', 'in', [item.id for item in self.invoice_ids])],
            'name': 'Invoices',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            #  'views': [(form_view_ref.id, 'form')],
            'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
            'search_view_id': search_view_ref and search_view_ref.id,
        }
           
    @api.multi
    def print_mandate_pop(self):
        return self.env['report'].get_action(self, 'ikoyi_module.print_singlemandate_template') 
                
    def popup_notification(self,popup_message):
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = popup_message # 'Successful'
        return {'name':'Alert!',
                    'type':'ir.actions.act_window',
                    'view_type':'form',
                    'res_model':'sh.message.wizard',
                    'views':[(view.id, 'form')],
                    'view_id':view.id,
                    'target':'new',
                    'context':context,
                }  

    #  NEW FIELDS
    users_followers = fields.Many2many('hr.employee', string='Add followers')
    #  NEW FIELDS
    signatures_accountant = fields.Binary(string='Accountant Signature')
    signatures_apo = fields.Binary(string='APO Signature')

    state = fields.Selection([('draft',
                               'Draft Mandate'),
                              ('account_payable',
                               'Account Payable'),
                              ('accountant',
                               'Accountant'),
                              ('approve',
                               'Approved'),
                              ('cancel',
                               'Cancelled'),
                              ('done',
                               'Done'),
                              ('reject',
                               'Rejected'),
                              ],
                             'Status',
                             default='draft',
                             index=True,
                             required=True,
                             readonly=True,
                             copy=False,
                             track_visibility='always')

    # @api.one
    @api.onchange('name')
    def vendor_account_changes(self):
        bank_acc = self.env['res.partner.bank'].search(
            [('partner_id', '=', self.name.id)])
        for tec in bank_acc:
            self.vendor_account = tec[0].id
            
    @api.onchange('vendor_account')
    def get_account(self):
        for rec in self:
            rec.vendor_bank = rec.vendor_account.bank_id.id
    
    @api.onchange('name')
    def domain_get(self):
        domain = {}
        appends = []
        bank_acc = self.env['res.partner.bank'].search(
            [('partner_id', '=', self.name.id)])
        if bank_acc:
            for rec in self:
                for vec in bank_acc:
                    appends.append(vec.id)
                    domain = {'vendor_account': [('id', '=', appends)]}
            return {'domain': domain}
        else:
            pass
            #  return {'domain':None}
            #raise ValidationError(
            #    'There is no Bank Account Set for the selected customer')
          
    @api.onchange('name')
    def get_all_bills(self):
        self.ensure_one
        lists = []
        domain = {}
        account = self.env["account.invoice"].search([
            ('partner_id', '=', self.name.id),
            ('state', 'not in', ['draft','paid'])
            ])
        for rec in account:
            lists.append(rec.id)
            domain = {'invoice_ids':[('id','in',lists)]}
        return {'domain':domain}
        
    # @api.one
    @api.depends('invoice_ids')
    def change_bill(self):
        total = 0.0
        for rex in self:
            for rec in rex.invoice_ids:
                total += rec.amount_total
            rex.pay_amount = total

    def create_account_pm_account(self):
        dummy, view_id = self.env['ir.model.data'].get_object_reference(
            'account', 'view_account_payment_form')
        ret = {
            'name': 'Register Payment',
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'domain': [],
            'context': {
                'default_amount': self.pay_amount,
                'default_partner_type': 'supplier',
                'default_partner_id': self.name.id,
 
            },
            'target': 'current'
        }
        return ret
    
     
    def mail_sending(self, email_from, group_user_id, bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_emails = group_users.users
            mail_to = []
            append_mails = []
            for mai in group_emails:
                mail_to.append(mai.login)

            for group_mail in self.users_followers:
                append_mails.append(group_mail.work_email)

            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_appends = (', '.join(str(item)for item in append_mails))
            email_to = (', '.join(str(item)for item in mail_to))
            subject = "Mandate / Payment Notification"
             
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': email_to,
                'email_cc': mail_appends,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    def names(self):
        name = " "

        if self.ikoyi_req_ref:
            name = str(self.ikoyi_req_ref.name)

        elif self.purchase_id:
            name = str(self.purchase_id.name)
        else:
            name="Mandate Request"

    def get_url_pur(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>".format(base_url)   
        
    @api.multi
    def apo_raise_mandate(self):
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.accountant_ikoyi').id
        
        pay_model = self._name
        bodyx = "Dear Sir, <br/> A request to approve a payment mandate has been approve. Please kindly {} to Review. <br/>\
        Regards".format(self.get_url_pur(self.id, pay_model))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'accountant'})
        
    @api.one
    def get_default_images(self, colorize=False):# get_module_resource('base', 'static/src/img', 'money.png')
        account_sign = get_module_resource('ikoyi_module','static/img', 'accountant.jpeg') 
        apo_sign = get_module_resource('ikoyi_module','static/img', 'apo.jpeg') 
        #apo_sign = tools.image_colorize(open(get_module_resource('ikoyi_module','static/img', 'avatar.jpeg')).read()) 
        if self.state in ['draft','account_payable']:
            self.signatures_apo = tools.image_resize_image_big(apo_sign)#.encode('base64'))
        elif self.state == "accountant":
            self.signatures_accountant = tools.image_resize_image_big(account_sign)# .encode('base64'))
    
    @api.model
    def get_default_image(self):

         colorize, img_path, image = False, False, False

         if not image:
             img_path = get_module_resource('ikoyi_module', 'static/img', 'accountant.jpeg')
         elif not image:
             img_path = get_module_resource('base', 'static/src/img', 'truck.png')
         elif not image:
             img_path = get_module_resource('base', 'static/src/img', 'avatar.png')
             colorize = True

         if img_path:
             with open(img_path, 'wb') as f:
                 image = f.write()
         if image and colorize:
             image = tools.image_colorize(image)
         return self.write({'signatures_accountant': tools.image_resize_image_big(image)})# .encode('base64')

    @api.multi
    def accountpay_accountant(self):
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.accountant_ikoyi').id
        
        pay_model = self._name
        bodyx = "Dear Sir, <br/> A request to approve a payment mandate has been approve. Please kindly {} to Review. <br/>\
        Regards".format(self.get_url_pur(self.id, pay_model))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'accountant'})
        self.get_default_image()

    @api.multi
    def accountant_accountpay2_print(self):
        email_from = self.env.user.email
        group_user_id = self.env.ref('ikoyi_module.account_payable_ikoyi').id
 
        bodyx = "Dear Sir, <br/> A approval has been made on the mandate raised earlier with reference {}. Please kindly {} Review. <br/>\
        Regards".format(self.names(), self.get_url_pur(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)
        self.write({'state': 'approve'})
        self.get_default_image()
        
    def mail_sending_for_three(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            print (all_mails)
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item)for item in all_mails)) 
            subject = "MOF Request"
            bodyxx = "Dear Sir/Madam, </br>We wish to notify you that a mandate has been sent to you for approval </br> </br>Kindly review it. </br> </br>Thanks"
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
         
    @api.multi
    def button_print_mandate(self): 
        pass

    @api.multi
    def button_register_payment(self):  #  state  approve #  apo
        self.register_payment()

    @api.multi
    def button_cancel(self):  #  state  ALL #  apo
        self.write({'state': 'cancel'})

    @api.multi
    def accountant_reject(self):
         #  state  accountant #  apo
        self.write({'state': 'account_payable'})
        return self.mail_refusal_account_to_apo()

    def mail_refusal_account_to_apo(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.accountant_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.account_payable_ikoyi').id

        name = 'Reason for Refusal'
        bodyx = "<b>{} <b/></br> The Payment Mandate with Reference {} is refused by {}. </br>\
        [SEE FULL REMARKS - {} ]".format(name,
                                         self.purchase_id.name,
                                         self.env.user.name,
                                         self.get_url_pur(self.id,
                                                          self._name))
        self.mail_sending_refusal(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def mail_sending_refusal(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            print (all_mails)
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item)for item in all_mails))
            subject = "Request Refusal"
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    @api.multi
    def button_set_draft(self):  #  state  reject, cancel #  apo
        self.write({'state': 'draft'})

    @api.multi
    def register_payment(self):
        for rey in self:
            name = " "
            if rey.ikoyi_req_ref:
                name = str(rey.ikoyi_req_ref.name)

            elif rey.purchase_id:
                name = str(rey.purchase_id.name)

            email_from = self.env.user.email
            group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
            bodyx = "Dear Sir, <br/>You are Notified that a payment with reference Number: {}\
            has been submitted for payment after all necessary approvals. <br/>\
            Regards".format(self.purchase_id.name)
            self.mail_sending(email_from, group_user_id, bodyx)

            acm = self.env['account.payment.method'].create(
                {'payment_type': 'inbound', 'name': name, 'code': str(name)})
            payment_data = {
                #  values.get('amount'),
                'amount': rey.pay_amount or rey.ikoyi_req_ref.amountfig,
                'payment_date': fields.Datetime.now(),
                'partner_type': 'customer',
                'payment_type': 'outbound',
                'partner_id': rey.name.id,
                'journal_id': rey.pay_account.id,

                'communication': rey.name,
                'branch_id': self.env.user.branch_id.id,
                'payment_method_id': acm.id  #  values.get('advance_account'),
            }
            payment_model = self.env['account.payment'].create(payment_data)
            self.state = "done"
            # return self.auto_create_vendor_bills()
   
     
        
       
# class res_module(models.Model):
#     _inherit = "product.template"

#     #photo = fields.Binary(string="Image to upload", default=lambda self:self._get_default_image())

#     image_medium = fields.Binary(
#         "Medium-sized image", attachment=True,default=lambda self:self._get_default_image(),
#         help="Medium-sized image of the product. It is automatically "
#              "resized as a 128x128px image, with aspect ratio preserved, "
#              "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")

#     @api.one
#     def get_default_image(self):
#         colorize, img_path, image = False, False, False
#         if not image:
#             img_path = get_module_resource('base', 'static/src/img', 'money.png')
#         elif not image:
#             img_path = get_module_resource('base', 'static/src/img', 'truck.png')
#         elif not image:
#             img_path = get_module_resource('base', 'static/src/img', 'avatar.png')
#             colorize = True

#         if img_path:
#             with open(img_path, 'rb') as f:
#                 image = f.read()
#         if image and colorize:
#             image = tools.image_colorize(image)

#         return tools.image_resize_image_big(image.encode('base64'))

