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
from odoo import http

# MOF REQUEST WORKFLOW --

class Raise_Requistion(models.Model):
    _name = "requisition.inventory"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Fixed Asset Request"
    _order = "id desc"

    def get_url_pur(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>".format(base_url)

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
        ('draft', 'draft'),
        ('hou', 'HOU'),
        ('hod', 'HOD'),
        ('authorize', 'Authorization'),
        ('gm', 'General Manager'),
        ('store', 'Store'),
        ('siv', 'SIV'),
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
    origin = fields.Char('Source Document', states=READONLY_STATES)
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.currency_id.id)
    order_line = fields.One2many(
        'requisition.line', 'order_id', string='Items', states={
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
    users_followers = fields.Many2many(
        'hr.employee', string='Add followers', required=True)
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=_default_employee)
    department_id = fields.Many2one(
        'hr.department', 'Department', required=True)
    manager = fields.Many2one('hr.employee', 'Manager')
    unit = fields.Many2one('hr.unit', required=True)
    unit_manager = fields.Many2one('hr.employee', 'Unit Manager')
    account_recievable = fields.Many2one(
        'account.account', 'Account Receivable')
    account_payable = fields.Many2one(
        'account.account',
        'Account Payabale')
    notes = fields.Text('Terms and Conditions')
    total_amount = fields.Float('Grand Total', compute="get_all_total")
    state = fields.Selection(
        states,
        string='Status',
        readonly=True,
        index=True,
        copy=False,
        default='draft',
        track_visibility='onchange')
    branch_id = fields.Many2one(
        'res.branch',
        string="Section",
        default=lambda self: self.env.user.branch_id.id)
    cost_center = fields.Selection([('profit',
                                     'Profit'),
                                    ('cost',
                                     'Cost')],
                                   default="cost",
                                   string='Status',
                                   required=True,
                                   index=True,
                                   copy=False,
                                   track_visibility='onchange')

    monthly = fields.Selection([('month',
                                 'Monthly Beverage'),
                                ('non_month',
                                 'None Monthly Beverage')],
                               string='Status',
                               default="month",
                               index=True,
                               copy=False,
                               track_visibility='onchange')
    reason = fields.Text('Reason')
    @api.onchange('department_id')
    def domain_units(self):
        domain = {}
        units = []
        for rec in self:
            unit_obj = self.env['hr.unit']
            search_unit = unit_obj.search(
                [('department', '=', rec.department_id.id)])
            for r in search_unit:
                units.append(r.id)
                domain = {'unit': [('id', 'in', units)]}
            return {'domain': domain}

    @api.onchange('employee_id')
    def get_fields_department(self):
        for rec in self:
            if rec.employee_id:
                for rex in rec.employee_id:
                    rec.unit = rex.unit_emp.id
                    rec.unit_manager = rex.unit_manager.id
                    rec.department_id = rex.department_id.id
                    rec.manager = rex.department_id.manager_id.id

    @api.onchange('department_id')
    def get_department_account(self):
        for rec in self:
            if rec.department_id:
                for rex in rec.department_id:
                    rec.account_recievable = rex.account_recievable.id
                    rec.account_payable = rex.account_payable.id
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
        for order in self:
            if not order.state == 'cancel':
                raise ValidationError(
                    _('In order to delete a Request order, you must cancel it first.'))
        return super(Raise_Requistion, self).unlink()

    @api.multi
    def button_draft(self):

        self.write({'state': 'draft'})
        return {}

    @api.multi  # draft
    def button_officer_raise(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.ikoyi_hou').id
        group_user_id = self.env.ref('ikoyi_module.ikoyi_hod').id
        group_user_id3 = self.env.ref('ikoyi_module.store_keeper_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been sent to you for approval. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'hou'})

        else:
            raise ValidationError('Not created')

    @api.multi  # hou
    def button_headunit_approve(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.ikoyi_hod').id
        group_user_id = self.env.ref('ikoyi_module.store_keeper_ikoyi').id
        group_user_id3 = self.env.ref(
            'ikoyi_module.inventory_manager_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with Reference Number: {} have been sent to HOD for approval. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'hod'})

        else:
            raise ValidationError('Not created')

    @api.multi  # hod
    def button_hod_authorize(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.ikoyi_authorize').id
        group_user_id = self.env.ref('ikoyi_module.ikoyi_hou').id
        group_user_id3 = self.env.ref('ikoyi_module.ikoyi_hod').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been sent to authorize for approval. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'authorize'})

        else:
            raise ValidationError('Not created')

    @api.multi  # authorize
    def button_authorize_gm(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.ikoyi_authorize').id
        group_user_id3 = self.env.ref('ikoyi_module.ikoyi_hou').id

        if self.monthly == "non_month":
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been approved by the authorize department to you. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'store'})

        else:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been sent to department for approval. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'gm'})

    @api.multi  # gm
    def button_gm_store(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.store_keeper_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.inventory_manager_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.ikoyi_hou').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been sent to General manager for approval. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'store'})

        else:
            raise ValidationError('Not created')

    @api.multi  # store
    def button_store_confirm(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.ikoyi_hou').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.costing_manager_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been release to the respective unit. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'siv'})
        else:
            raise ValidationError('Not created')
        #
        # Do some store check
        return self.compute_stock()
    
    def compute_stock(self):
        order_product = []
        total = 0.0
      
        for rev in self.order_line:
            order_product.append(rev.product_id.id)
            
        stock_quant = self.env['stock.quant']
        search_quant = stock_quant.search([('product_id', 'in', order_product)])
        if search_quant:
            for rec in search_quant:   
                total += rec.qty
            if total < 0:
                raise ValidationError(
                        'Product qty is low in the store or is not \
                        available because the total is %s' % total)
      
            # self.update_stock()   
            return self.create_stock_move()    
        else:
            raise ValidationError('The requested product is not available \
                                   in the Stock location')
            
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Picking Type', 
        readonly=True, 
        states={'draft': [('readonly', False)], 'store': [('readonly', False)]})

    picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')],string='Operation Type',
       required=False, related='picking_type_id.code', states={'draft': [('readonly', False)]})

    def create_stock_move(self):
        # picking_type_id2 = self.env['stock.picking.type'].search(
        #             [('id', '=', self.picking_type_code)], limit=1)
        picking = self.env['stock.picking']
        partner_id = 0 
        partner_search = self.env['res.partner'].search([('name', '=', self.department_id.name)], limit=1)
        if not partner_search:
            partner_obj = self.env['res.partner'].create({'name':self.department_id.name})
            partner_id = partner_obj.id

        value_obj = {
                    'partner_id':partner_id,
                    'min_date': self.date_order,
                    'location_id': self.picking_type_id.default_location_src_id.id, #locate_out[0].id,
                    'location_dest_id': self.picking_type_id.default_location_src_id.id,# locate_in[0].id,
                    'branch_id': self.env.user.branch_id.id,
                    'picking_type_id': self.picking_type_id.id,
                    'picking_type_code': self.picking_type_id.code
                    #'origin': self.purchase_order_id.name,
                    }
        pick_id = picking.create(value_obj)
        pick_browse = picking.browse([pick_id.id])           
        for line in self.order_line:
            lines = {'name':"Requisition Request from {}".format(self.department_id.name),
                    'product_id':line.product_id.id,
                     'product_uom_qty':line.qty,
                     'product_uom': line.label.id,
                     'location_id': line.product_id.picking_source_location_id.id, #locate_out[0].id,
                     'location_dest_id': line.product_id.picking_destination_location_id.id,
                     }

            pick_browse.write({'move_lines':[(0,0, lines)]})
        # pick_browse.action_confirm()
        self.origin = pick_browse.name
        xxxxlo = self.env['stock.picking'].search([('id', '=', pick_id.id)])
        if not xxxxlo:
            raise ValidationError('There is no related Pickings Created.')
        resp = {
            'type': 'ir.actions.act_window',
            'name': _('Request Reference'),
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id': xxxxlo.id
        }
        return resp

    def print_siv(self):
        """Print SIV"""
        self.button_send_siv_costing_account()
        self.state = "done"
        return self.env['report'].get_action(self, 'ikoyi_module.print_siv_template')
    
    def view_siv(self):
        """View SIV"""
        self.ensure_one()
        report = self.env['ir.actions.report.xml'].search([('report_name','=', 'ikoyi_module.edit_siv_ikoyi')])
        if report:
            report.write({'report_type':'qweb-html'})
        return self.env['report'].get_action(self.id, 'ikoyi_module.edit_siv_ikoyi')
    
    @api.multi
    def account_approval(self):  # Send memo back
        partner_ref = ''
        partner = self.env['res.partner']
        part_search = partner.search([('name','=ilike', self.employee_id.name)])
        if part_search:
            partner_ref = part_search.id
        else:
            partner_k = self.env['res.partner'].create({'name': self.department_id.name})
            partner_ref = partner_k.id
        
        return {
            'name': "Journal Payment",
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'ikoyi.journal',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                
                'default_date': fields.Date.today(),
                'default_amount_to_pay': self.total_amount, #  self.int_form_price,
                'default_ref_id': self.id,
                'default_partner_id': partner_ref or False, 
                'default_revenue_account_rec':self.account_recievable.id,
                'default_revenue_account_pay':self.account_payable.id,
                'default_model_id':self._name,
                'default_refund':False,
            },
        }

    # api.onchange('product_id','qty')

    def update_stock(self):
        stock_quant = self.env['stock.quant'].search([])
        stock_location = self.env['stock.location']
        search_location = stock_location.search(
                    [('branch_id', '=', self.branch_id.id)])
        
        global search_location  
        if search_location:
            for rem in self.order_line:
                stock_create = stock_quant.create({
                                                    'product_id': rem.product_id.id,
                                                    'qty': -rem.qty,
                                                    'location_id': search_location[0].id,
                                                    'in_date': self.date_order})

        else:
            raise ValidationError('No branch found in the location')
        
    @api.multi  # authorize
    def button_send_siv_costing_account(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.costing_manager_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.account_payable_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number:\
             {} have confirm and an SIV have been generated by the Store.\
            Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
             
        else:
            raise ValidationError('Not Record created')
# ############# REFUSE BUTTONS #################
    @api.multi  # draft
    def button_reject_hou(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.accountant_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been Rejected by the HOU. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'draft'})
            return self.button_return_request_back(self.id)
        else:
            raise ValidationError('Not created')

    @api.multi  # hou
    def button_reject_hod(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.accountant_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been Rejected by the HOD. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'hou'})
            return self.button_return_request_back(self.id)
        else:
            raise ValidationError('Not created')

    @api.multi  # hod
    def button_reject_authorize(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.accountant_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A Goods requisition with reference Number: {} have been Rejected by the Authorize Unit. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'hod'})
            return self.button_return_request_back(self.id)

        else:
            raise ValidationError('Not created')

    @api.multi  # authorize
    def button_reject_gm(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.accountant_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been Rejected by the General Manager. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'authorize'})
            self.button_return_request_back(self.id)
        else:
            raise ValidationError('Not created')

    @api.multi  # gm
    def button_reject_store(self):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.accountant_ikoyi').id

        if self.id:
            bodyx = "Dear Sir, <br/>A goods requisition with reference Number: {} have been Rejected by the store manager. Kindly {} to view. <br/>\
            Regards".format(self.name, self.get_url_pur(self.id, self._name))
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
            self.write({'state': 'draft'})
            return self.button_return_request_back(self.id)
        else:
            raise ValidationError('Not created')

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

            #mail_appends = (', '.join(str(item)for item in append_mails))
            #mail_appends_to = (', '.join(str(item)for item in append_mails_to))
            subject = "Goods Requisition"
            bodyxx = "Dear Sir/Madam, <br/>We wish to notify you that a request from {} has been sent to you for approval <br/> <br/>Kindly review it. </br> <br/>Thanks".format(
                self.employee_id.name)
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                'email_cc': mail_sender,  # + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    @api.multi
    def button_return_request_back(self, id):  # vis_account,
        statename = str(self.state).capitalize().replace('_', ' ')
        users = []
        for rec in self.users_followers:
            users.append(rec.id)
        return {
            'name': 'Return of Request',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'main.return',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_number': id,
                'default_date': self.date_order,
                'default_state': statename,
                'default_users_followers': [(6, 0, users)]
            },
        }


class Send_Main_Sendback(models.Model):
    _name = "main.return"

    resp = fields.Many2one(
        'res.users',
        'Responsible',
        default=lambda self: self.env.user.id)  # , default=self.write_uid.id)
    number = fields.Integer('Number ID')
    # <tree string="Memo Payments" colors="red:state == 'account';black:state == 'manager';green:state == 'coo';grey:state == 'refused';">
    reason = fields.Text('Reason', required=True)
    date = fields.Datetime('Date')
    state = fields.Char('State')
    users_followers = fields.Many2many('hr.employee', string='Add followers')

    @api.multi
    def post_back(self):
        #############################
        #state = 'refuse'
        model = 'requisition.inventory'

        #############################
        search = self.env['requisition.inventory'].search(
            [('id', '=', self.number)])
        message = "Memo Rejected at {} stage - Remarks: {}".format(
            str(search.state).capitalize().replace('_', ' '), self.reason)
        if search:
            search.write({'reason': message})
        else:
            raise ValidationError('Not found')
        return{'type': 'ir.actions.act_window_close'}


class Requisition_Line(models.Model):
    _name = 'requisition.line'
    _description = 'Requisition Line'
    _order = 'id desc'
    _rec_name = "product_id"

    def change_uom(self):
        uom = self.env['product.uom'].search([('name', '=', 'Unit(s)')])
        return uom.id

    def branch_name_compute(self):
        branch = self.order_id.branch_id
        return branch

    def compute_unit(self):
        unit = self.order_id.unit
        return unit

    '''def get_context_dateplan(self):
        if 'dplan' in self._context:
            return self._context['dplan']
        return self.date_planned or fields.Datetime.now()'''

    def get_unit_context(self):
        if "dplan" in self._context:
            return self._context['dplan']
        return self.unit

    order_id = fields.Many2one(
        'requisition.inventory',
        string='Reference',
        index=True,
        required=True,
        ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        change_default=True,
        required=True)
    name = fields.Text(string='Purpose', required=False)
    unit = fields.Many2one('hr.unit', required=False, default=compute_unit)
    label = fields.Many2one(
        'product.uom',
        string='UOM',
        default=change_uom,
        required=True)
    qty = fields.Float('Requested Qty', default=1.0, )
    taxes_id = fields.Many2many('account.tax', string=u'Taxes', store=True, compute="get_product_taxes")
    rate = fields.Float('Item Rate', related='product_id.list_price')
    total = fields.Float('Total', compute='get_total')
    date_planned = fields.Datetime(
        string='Exp. Date',
        default=fields.Datetime.now,
        required=False,
        index=True)

    remaining_qty = fields.Float('Remaining Qty')

    branch_id = fields.Many2one(
        'res.branch',
        string="Branch",
        default=lambda self: self.env.user.branch_id.id)
    actual_qty = fields.Float('Stock Qty', compute="Quantity_Moves", store=True)

    @api.one
    @api.depends('product_id')
    def get_product_taxes(self):
        appends = []
        for rec in self.product_id.supplier_taxes_id:
            appends.append(rec.id)
        self.taxes_id = [(6, 0, appends)]
        #return appends

    @api.depends('qty', 'rate', 'taxes_id')
    def get_total(self):
        totals = 0.0
        taxes = 0.0
        for rec in self:
            if rec.taxes_id:
                for tax in rec.taxes_id:
                    if tax.amount_type == "fixed":
                        taxes += tax.amount
                        totals = (rec.qty * rec.rate) + taxes
                    if tax.amount_type == "percent":
                        taxes += tax.amount / 100
                        totals = (rec.qty * rec.rate) * taxes + (rec.qty * rec.rate)   
            elif not rec.taxes_id:
                totals = rec.qty * rec.rate
            rec.total = totals

    # @api.one                   
    # @api.depends('product_id')
    # def Quantity_Moves(self):
    #     diff = 0.0
    #     # for rec in self:
    #     stock_location = self.env['stock.location']
    #     search_location = stock_location.search(
    #             [('branch_id', '=', self.branch_id.id)])
    #     for r in search_location[0]:
    #         stock_quant = self.env['stock.quant']
    #         search_quanty = stock_quant.search(
    #                 [('location_id', '=', r.id), ('product_id', '=', self.product_id.id)])
    #     if search_quanty:
    #         for rey in search_quanty:
    #             diff += rey.qty
    #         self.actual_qty = diff
            
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


    # @api.depends('qty', 'rate')
    # def get_total(self):
    #     for rec in self:
    #         totals = rec.qty * rec.rate
    #         rec.total = totals
