from datetime import datetime, timedelta
import time
from dateutil.relativedelta import relativedelta

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

# MOF REQUEST WORKFLOW --


class Ikoyi_FIXED_ASSET_Request(models.Model):
    _name = "ik.fixed.request"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Fixed Asset Request"
    _order = "id desc"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    def default_partner_id(self):
        partner = self.env['res.partner'].browse([0])
        return partner.id

    READONLY_STATES = {

        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    states = [
        ('draft', 'Draft'),
        ('cost_office', 'Costing'),

        ('store_manager_one', 'Store Manager'),
        ('finance_manager_one', 'F&A Manager'),
        ('general_manager_one', 'General Manager'),
        ('main_committee', 'Committee Review'),
        ('procurement_manager_one', 'Procurement Manager'),
        ('finance_manager_two', 'F&A Manager'),
        ('general_manager_two', 'General Manager'),
        ('procurement_manager_two', 'Procurement Manager'),
        ('finance_manager_three', 'F&A Manager'),
        ('general_manager_three', 'General Manager'),


        ('account_payable_one', 'Account Payable'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('refused', 'Refused'),

    ]

    name = fields.Char(
        'Order Reference',
        required=True,
        index=True,
        copy=False,
        default='New')
    ####partner_ref = fields.Char('Vendor Reference', copy=False)
    origin = fields.Char('Source Document', states=READONLY_STATES)
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.currency_id.id)

    order_line = fields.One2many(
        'ik.fixed.line', 'order_id', string='Fixed Asset Items', states={
            'cancel': [
                ('readonly', True)], 'done': [
                ('readonly', True)]}, copy=True)

    user_id = fields.Many2one(
        'res.users',
        string="Users",
        default=lambda a: a.env.user.id)
    ####boq_id = fields.Many2one('construction.material', string="Bill of Quantity")
    ####budget_id = fields.Many2one('construction.budget', string="Based on Budget")
    ####house_type = fields.Many2one('construction.housetype', string="House Type")

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
        'hr.employee', string='Add followers', required=True)
    branch_id = fields.Many2one(
        'res.branch',
        string="Branch",
        default=lambda self: self.env.user.branch_id.id)
    location = fields.Many2one('stock.location', 'Stock Location')
    warehouse = fields.Many2one('stock.warehouse', 'Warehouse')
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string='Purchase Order')

    
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.id)
    state = fields.Selection(
        states,
        string='Status',
        readonly=True,
        index=True,
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
    total_amount = fields.Float('Grand Total', compute="get_all_total")

    @api.depends('purchase_order_id')
    def get_po_name(self):
        for rec in self:
            rec.origin = rec.purchase_order_id.name

    @api.depends('order_line')
    def get_all_total(self):
        total = 0.0
        for rec in self:
            for tec in rec.order_line:
                total += tec.total
            rec.total_amount = total

    @api.multi
    def unlink(self):
        for order in self:
            if not order.state == 'cancel':
                raise ValidationError(
                    _('In order to delete a Request order, you must cancel it first.'))
        return super(Ikoyi_FIXED_ASSET_Request, self).unlink()

    @api.multi
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}

    @api.multi
    def button_refuse(self):
        self.write({'state': 'refuse'})
        return {}

    @api.multi
    def button_cancel(self):
        for order in self:
            if order.state not in ['cost_office', 'done']:
                order.write({'state': 'cancel'})
            else:
                raise ValidationError('You can cancel a confirmed request')

    @api.multi
    def to_cost_officer(self):  # draft state employee group
        email_from = self.env.user.email
        extra = self.employee_id.work_email

        group_user_id = self.env.ref('ikoyi_module.costing_manager_ikoyi').id
        bodyx = "Dear Sir, <br/>A request with reference Number: {} have been raised by {} and is waiting \
        for your approval. Please kindly Review. <br/> Regards".format(self.name, self.employee_id.name)

        self.mail_sending(email_from, group_user_id, extra, bodyx)
        self.write({'state': 'cost_office'})

    @api.multi
    def cost_officer_FA(self):  # cost_office , costing_manager_ikoyi group
        email_from = self.env.user.email
        extra = self.employee_id.work_email

        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        bodyx = "Dear Sir, <br/>A request with reference Number: {} have been raised by {} and is waiting \
        for your approval. Please kindly Review. <br/> Regards".format(self.name, self.employee_id.name)

        self.mail_sending(email_from, group_user_id, extra, bodyx)
        self.write({'state': 'finance_manager_one'})

    @api.multi
    def cost_FA_GM(self):  # finance_manager_one  grp account_boss_ikoyi
        email_from = self.env.user.email
        extra = self.employee_id.work_email

        group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
        bodyx = "Dear Sir, <br/>A request with reference Number: {} have been raised by {} and is waiting \
        for your approval. Please kindly Review. <br/> Regards".format(self.name, self.employee_id.name)

        self.mail_sending(email_from, group_user_id, extra, bodyx)
        self.write({'state': 'general_manager_one'})

    @api.multi
    def GM_to_committee_Members(self):  # general_manager_one  grp gm_ikoyi
        email_from = self.env.user.email
        extra = self.employee_id.work_email

        group_user_id = self.env.ref('ikoyi_module.main_committee_ikoyi').id
        bodyx = "Dear Sir, <br/>A request with reference Number: {} have been raised by {} and is waiting \
        for your approval. Please kindly Review. <br/> Regards".format(self.name, self.employee_id.name)

        self.mail_sending(email_from, group_user_id, extra, bodyx)
        self.write({'state': 'main_committee'})

    @api.multi
    # main_committee  grp main_committee_ikoyi
    def Committee_to_Procurement(self):
        email_from = self.env.user.email
        extra = self.employee_id.work_email

        group_user_id = self.env.ref(
            'ikoyi_module.procurement_manager_ikoyi').id
        bodyx = "Dear Sir, <br/>A request with reference Number: {} have been approved by {} and is waiting \
        for your approval. Please kindly Review. <br/> Regards".format(self.name, self.write_uid.name)

        self.mail_sending(email_from, group_user_id, extra, bodyx)
        self.write({'state': 'procurement_manager_one'})

    @api.multi
    # procurement_manager_one  grp procurement_manager_ikoyi
    def Procurement_to_LPO(self):
        email_from = self.env.user.email
        extra = self.employee_id.work_email

        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        bodyx = "Dear Sir/Madam, <br/>A Local Purchase Order with reference Number: {} have been raised by {} and is waiting \
        for your approval. Please kindly Review. <br/> Regards".format(self.name, self.write_uid.name)

        self.mail_sending(email_from, group_user_id, extra, bodyx)
        self.procure_btn()
        self.deduction_on_budget()
        self.write({'state': 'done'})

    def deduction_on_budget(self):
        lines = self.mapped('order_line')
        for rec in lines:
            budget_lines = self.env['department_budget.line'].search([('capex_num', '=', rec.capex_num.id)], limit=1)
            budget_lines.write({
                'paid_amount': budget_lines.paid_amount + rec.total,
                'qty_used': budget_lines.qty_used + rec.qty
            })
        

    # @api.multi
    # # finance_manager_two  grp account_boss_ikoyi
    # def Finance_admin_to_GMTWO(self):
    #     email_from = self.env.user.email
    #     extra = self.employee_id.work_email

    #     group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
    #     bodyx = "Dear Sir/Madam, <br/>A Local Purchase Order have been raised for the Fixed asset request with \
    #     reference Number: {} and is waiting \
    #     for your approval. Please kindly Review. <br/> Regards".format(self.name)

    #     self.mail_sending(email_from, group_user_id, extra, bodyx)
    #     # self.procure_btn()
    #     self.write({'state': 'general_manager_two'})

    # @api.multi
    # def GMTWO_Procurement(self):  # general_manager_two  grp account_boss_ikoyi
    #     email_from = self.env.user.email
    #     extra = self.employee_id.work_email

    #     group_user_id = self.env.ref(
    #         'ikoyi_module.procurement_manager_ikoyi').id
    #     bodyx = "Dear Sir/Madam, <br/>A Local Purchase Order have been raised for the Fixed asset request with \
    #     reference Number: {} and is waiting \
    #     for your approval. Please kindly Review. <br/> Regards".format(self.name)

    #     self.mail_sending(email_from, group_user_id, extra, bodyx)
    #     # self.procure_btn()
    #     self.write({'state': 'procurement_manager_two'})

    # @api.multi
    # # general_manager_two  grp account_boss_ikoyi
    # def Procurement_to_ConfirmS(self):
    #     email_from = self.env.user.email
    #     extra = self.employee_id.work_email

    #     group_user_id = self.env.ref('ikoyi_module.inventory_manager_ikoyi').id
    #     bodyx = "Dear Sir/Madam, <br/>A Local Purchase Order have been confirm for the Purchase of Fixed asset items with \
    #     reference Number: {}. Please kindly Notifiy us if the goods are recieved. <br/> Regards".format(self.name)

    #     self.mail_sending(email_from, group_user_id, extra, bodyx)
    #     # self.procure_btn()
    #     self.write({'state': 'done'})

    def mail_sending(self, email_from, group_user_id, extra, bodyx):
        mail_from = self.env.user.name
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

            email_froms = str(mail_from) + " <" + str(email_from) + ">"
            mail_appends = (', '.join(str(item)for item in append_mails))
            email_to = (', '.join(str(item)for item in mail_to))
            subject = "Fixed Asset Request Notification"
            #bodyx = "Dear Sir/Madam, </br>We wish to notify you that a request from {} has been sent to you for approval </br> </br>Kindly review it. </br> </br>Thanks".format(self.employee_id.name)
            extrax = (', '.join(str(extra)))
            append_mails.append(extrax)
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': email_to,
                'email_cc': mail_appends,  # + (','.join(str(extra)),
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
                for rex in self.order_line:
                    domain = [
                        ('code', '=', 'incoming'),
                        ('warehouse_id', '=', reck),
                        ('active', '=', True),
                        ('default_location_dest_id', '=', tec)
                    ]

                    picking_type_id = self.env['stock.picking.type'].search(
                        domain)
                    picking_type_id2 = self.env['stock.picking.type'].search(
                        [('active', '=', True)])[0]
                    partner_obj = self.env['res.partner']
                    partner_id = partner_obj.search([('name', '=', '/')]) and partner_obj.search(
                        [('name', '=', '/')]).id or partner_obj.create({'name': 'Client', 'supplier': True}).id

                    values = {

                        'partner_id': partner_id,  # compulsory
                        # compulsory
                        'date_order': time.strftime("%m/%d/%Y %H:%M:%S"),
                        'picking_type_id': picking_type_id2.id,  # compulsory
                        # compulsory str
                        'date_planned': time.strftime("%m/%d/%Y %H:%M:%S"),
                        'branch_id': self.branch_id.id,
                        'state': 'draft',
                        'state_mode': 'fixed',

                        'order_line': [
                            (0, 0, {
                                'order_id': purchase_obj.id,
                                # 'request_ref':self.id,
                                'product_id': rex.product_id.id,
                                'name': rex.name,
                                'product_qty': rex.qty,
                                'price_unit': rex.product_id.list_price,
                                'product_uom': rex.label.id,
                                'name': rex.product_id.name,
                                # time.strftime("%m/%d/%Y %H:%M:%S"),
                                'date_planned': rex.date_planned,
                                'price_subtotal': rex.product_id.list_price * rex.qty,
                                'price_total': rex.product_id.list_price * rex.qty,

                            })
                        ]  # compulsory fields: product_id, product_qty, price_unit, date_planned
                    }
                    purchase_order_id = purchase_obj.create(values)
                    # purchase_order_id.write({'state':'pm'})
                    namex = 'purchase.order'
                    purchase_order_id.button_confirm()
                    purchase_order_id.action_rfq_send()
                    purchase_order_id.send_recieve_account_mail(
                        purchase_order_id.id, namex)
                return self.write(
                    {'purchase_order_id': purchase_order_id.id, 'state': 'draft'})


class Fixed_Asset_Line(models.Model):
    _name = 'ik.fixed.line'
    _description = 'Fixed Line'
    _order = 'id desc'
    _rec_name = "product_id"

    def change_uom(self):
        uom = self.env['product.uom'].search([('name', '=', 'Unit(s)')])
        return uom.id

    def branch_name_compute(self):
        branch = self.order_id.branch_id
        return branch

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
        'ik.fixed.request',
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
    name = fields.Text(string='Purpose', required=True)
    label = fields.Many2one(
        'product.uom',
        string='UOM',
        default=change_uom,
        required=True)
    qty = fields.Float('Qty', default=1.0, )
    rate = fields.Float('Rate', related='product_id.list_price')
    total = fields.Float('Total', compute='get_total')
    date_planned = fields.Datetime(
        string='Exp. Date', required=False, index=True)
    remaining_qty = fields.Float('Remaining Qty')
    actual_price = fields.Float(
        'Actual Price',
        related='product_id.list_price')
    branch_id = fields.Many2one(
        'res.branch',
        string="Branch",
        default=lambda self: self.env.user.branch_id.id)
    actual_qty = fields.Float('Stock Qty')
    account_id = fields.Many2one(
		'account.account', string='Fixed Assets', required=False)
    capex_num = fields.Many2one(
		'capex.number', string='Capex No')
    #move_ids = fields.One2many('stock.move', 'purchase_line_id', string='Reservation', readonly=True, ondelete='set null', copy=False)

    @api.onchange('total','qty')
    def check_capex_budget(self):
        if self.total >= 1:
            balances, qtys, apprv = 0.0, 0.0, 0.0
            dept_budget_line= self.env['department_budget.line'].search([('capex_num','=', self.capex_num.id), 
            ('department_line_m2o.state','=', 'done')]) 
            if dept_budget_line:
                for record in dept_budget_line:
                    balances += record.balance
                    qtys += record.qty_used
                    apprv += record.quantity_approved
                    # if dept_budget_line.budget_type == "capital":
            if self.total > balances:
                raise ValidationError('You are trying to use more than the designated budget'+ str(balances))
            qty_diff = apprv - qtys
            if self.qty > qty_diff:
                raise ValidationError('You are trying to use more than the Approved Budget Qty'+ str(qtys))
            # else:
            #     raise ValidationError('Good to go'+ str(qtys))

        # lines = [rec.balance for rec in dept_budget if rec.capex_num == self.capex_num and rec.account_id == self.account_id]

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

    # @api.onchange('product_id', 'qty')
    # def Quantity_Moves(self):
    #     diff = 0.0
        
    #     stock_location = self.env['stock.location']
    #     search_location = stock_location.search(
    #             [('branch_id', '=', self.branch_id.id)])
    #     for r in search_location:
    #         stock_quant = self.env['stock.quant']
    #         search_quanty = stock_quant.search(
    #                 ['&', ('location_id', '=', r.id), ('product_id', '=', self.product_id.id)])
    #         if search_quanty:
    #             for rey in search_quanty:
    #                 diff = rey.qty - self.qty
    #                 self.write({'actual_qty': rey.qty})
    #                 remain = self.actual_qty - rey.qty
    #                 self.write({'qty': diff, 'remaining_qty': remain})
                        # rec.write({'remaining_qty':remain})
    

    @api.depends('qty', 'rate')
    def get_total(self):
        for rec in self:
            totals = rec.qty * rec.actual_price
            rec.total = totals
