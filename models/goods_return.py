from datetime import datetime, timedelta
import time
from dateutil.relativedelta import relativedelta
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo import http

'''# GRO REQUEST WORKFLOW --
view and print grn, 
upload, 
select the Stock id,
system restrict to  the product in MOF
Selects how many to return
send to manager &
sends mail to and others
system deducts in inventory
credit not and debit note created,
send mail to vendor

'''

class Goods_Return(models.Model):
    _name = "ikoyi.goods_return"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Ikoyi Goods Return"
    _order = "id desc"

    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/> to Review. ".format(base_url)
        
    '''def get_url(self, id, model):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, model)'''
        #  base_url += '/web# id=%d&view_type=form&model=%s' % (self.id,
        #  self._name)

        #  self.get_url(self.id, self._name)

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    def default_partner_id(self):
        partner = self.env['res.partner'].browse([0])
        return partner.id
   
    """USED TO GET LIST OF USERS IN THE GROUP CATEGORY
    And then append them as followers"""
    
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
        'store_manager': [('readonly', True)],
        'update': [('readonly', True)],
        'account': [('readonly', True)],
        'manager_two': [('readonly', True)],
        'to_vendor': [('readonly', True)],
        
    }

    name = fields.Char(
        'Order Reference',
        required=True,
        index=True,
        copy=False,
        )
    origin = fields.Char('Source Document', compute="Get_Stock", copy=False,)
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.currency_id.id)
    
    stock_id = fields.Many2one(
        'stock.picking',
        string="Stock Move (GRN) ID", 
        copy=False, 
        required=True,
        )
    
    stock_in_id = fields.Many2one(
        'stock.picking',
        string="Incoming Stock Reference", 
        copy=False,  
        )
    order_line = fields.One2many(
        'good.return.line', 'order_id', string='Goods Return Lines', copy=True, store=True, readonly = False, compute="Get_Stock")
    
    user_id = fields.Many2one(
        'res.users',
        string="Users", readonly=True,
        default=lambda a: a.env.user.id)

    date_order = fields.Datetime(
        'Order Date',
        required=True,
        states=READONLY_STATES,
        index=True,
        copy=False,
        default=fields.Datetime.now)
    
    users_followers = fields.Many2many(
        'hr.employee',
        string='Add followers',
        required=False,
        default=_get_all_followers)
    
    branch_id = fields.Many2one(
        'res.branch',
        string="Section",
        default=lambda self: self.env.user.branch_id.id,
        help="Tell Admin to set your branch... (Users-->Preferences-->Allowed Branch)",compute="Get_Product_of_Stock")

    location = fields.Many2one(
        'stock.location',
        string = 'Stock Location', compute="Get_Product_of_Stock", domain=[('usage','=','supplier')],
        help="Go to inventory config, set branch for warehouse and location")
    
    location_dest = fields.Many2one('stock.location', string="Destination Location", 
                                    compute="Get_Product_of_Stock",
                                    domain=[('usage','=','internal')])
               
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string='Purchase Order', copy=False,compute="Get_Product_of_Stock")
    
    file_upload = fields.Binary('File Upload', 
    )
    binary_fname = fields.Char('Binary Name')

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.id)
    state = fields.Selection([
        
        ('grn', 'View GRN'),
        ('draft', 'Draft'),
        ('store_manager', 'Manager'),
        ('update', 'In Progress'),
        ('to_vendor', 'Waiting Availability'),
        ('manager_two', 'Manager'),
        ('account', 'Account Payable'),
        ('done', 'Done'),
        ('refuse', 'Refuse'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True, copy=False, default='grn', track_visibility='onchange')

    employee_id = fields.Many2one(
        'hr.employee',states=READONLY_STATES,
        string='Employee',
        required=True,
        default=_default_employee)
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        default=default_partner_id,
        track_visibility='always',compute="Get_Product_of_Stock")
    notes = fields.Text('Terms and Conditions')
    total_amount = fields.Float('Total Items to Return',store=True,compute="get_total")
    total_amount_cost = fields.Float('Total Cost of Item',store=True,compute="get_total")
    description_two = fields.Text('Refusal Reasons')
    
    @api.depends('stock_id')
    @api.one
    def Get_Product_of_Stock(self):
        po_obj = self.env['purchase.order']
        if self.stock_id:
            po_search = po_obj.search([('name', 'ilike', self.stock_id.origin)])
            po_id = 0
            if po_search:
                po_id = po_search.id
            else:
                pass # raise ValidationError('No PO found for the GRN')
                    
        for rec in self:
            for tec in rec.stock_id:
                rec.update({# 'location': tec.location_id.id,
                            'origin': tec.origin,
                            # 'location_dest': tec.location_dest_id.id,
                            'branch_id': tec.branch_id.id,
                            'purchase_order_id': po_id,
                            'partner_id': po_search.partner_id.id,})
         
    
    @api.one
    @api.depends('order_line')
    def get_total(self):
        for rec in self.order_line:
            self.total_amount += rec.qty
            self.total_amount_cost += rec.product_id.list_price
        
            
    @api.onchange('stock_id')
    #@api.one
    def Get_Stock(self):
        prod_ids = self.stock_id.pack_operation_product_ids
        stock_id = self.stock_id
        for prod_id in prod_ids:
            lines = {'order_id': self.id,
                     'product_id': prod_id.product_id.id, 
                     'qty': 0,
                     'initial_qty': prod_id.qty_done,
                     'location_dest': prod_id.location_dest_id,
                     'location': prod_id.location_id}
            self.order_line = [(0, 0, lines)]
    #################################################
    
    @api.multi
    def send_to_manager(self): # draft officer
        self.write({'state':'store_manager','description_two':''})
        body = "Dear Sir, <br/>A GRO with reference Number: {} have been sent for confirmation.\
            Kindly {} to view. <br/>\
            Regards".format(self.name,self.get_url(self.id, self._name))
        check_return = self.mapped('order_line').filtered(lambda check:check.qty < 1)   
        if check_return:
            pass
            #raise ValidationError('You must Set the Returned quantity to be greater than 0')
        return self.send_mail_manager(body)
    
    @api.multi
    def manager_approve(self): # store_manager manager
        self.write({'state':'update','description_two':''})
        body = "Dear Sir, <br/>A GRO with reference Number: {} have been confirmed and will be returned to the vendor:\
             {}. Also an Credit and Debit Note have been generated by the Store.\
            Kindly {} to view. <br/>\
            Regards".format(self.name, self.partner_id.name,self.get_url(self.id, self._name))
        return self.send_mail_all(body)
    
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Picking Type')
        # states={'update': [('readonly', False)],'store_manager': [('readonly', False)]})

    picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')],string='Operation Type',
       required=False, related='picking_type_id.code', states={'draft': [('readonly', False)]})
 
    @api.multi
    def return_goods(self):
        # return self.goods_reference(self.stock_id)
        uom = self.env['product.uom'].search([('name', 'ilike', 'Unit(s)')]).id
        picking = self.env['stock.picking']
        partner_id = 0 
        partner_search = self.env['res.partner'].search([('name', '=', self.employee_id.name)], limit=1)
        if not partner_search:
            partner_obj = self.env['res.partner'].create({'name':self.employee_id.name})
            partner_id = partner_obj.id
        else:
            partner_id = partner_search.id

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
            lines = {'name':"Requisition Request from {}".format(self.employee_id.name),
                    'product_id':line.product_id.id,
                     'product_uom_qty':line.qty,
                     'product_uom': uom, # line.label.id,
                     'location_id': line.product_id.picking_source_location_id.id, #locate_out[0].id,
                     'location_dest_id': line.product_id.picking_destination_location_id.id,
                     }

            pick_browse.write({'move_lines':[(0,0, lines)]})
        # pick_browse.action_confirm()
        self.origin = pick_browse.name
        self.stock_id = pick_id.id
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
        
    
    def goods_reference(self, stock_id):
        xxxxlo = self.env['stock.picking'].search([('id', '=', stock_id.id)])
        if not xxxxlo:
            raise ValidationError('There is no related Pickings Selected.')
        resp = {
            'type': 'ir.actions.act_window',
            'name': _('Return Reference'),
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id': xxxxlo.id
        }
        return resp
    
    @api.multi
    def storer_send_vendor(self):
        self.write({'state':'to_vendor','description_two':''})
        # self.Quantity_Moves()
        return self.send_mail_vendor()
    
    
    # def view_grns(self):
    #     """View GRN"""
    #     self.ensure_one()
    #     self.state = "draft"
    #     report = self.env['ir.actions.report.xml'].search([('report_name','=', 'ikoyi_module.print_grn_view_template')])
    #     if report:
    #         report.write({'report_type':'qweb-html'})
    #     return self.env['report'].get_action(self.id, 'ikoyi_module.print_grn_view_template')
  
    def Confirm_gro(self):
        if self.state == "grn":
            self.state = "draft"
        elif self.state == "store_manager":
            pass  
    def view_grn(self):
        # if self.state == "grn":
        #     self.state = "draft"
        # elif self.state == "store_manager":
        #     pass
        dummy, view_id = self.env['ir.model.data'].get_object_reference(
            'ikoyi_module', 'grnview_report_view')
        ret = {
            'name': 'Print and View GRN!',
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'grn.wizardho',
            'type': 'ir.actions.act_window',
            'domain': [],
            'context': { 
                'default_stock_id': self.stock_id.id,
 
            },
            'target': 'new'
        }
        return ret
    
    @api.multi
    def print_credit_note(self): # to_vendor
        report = self.env['ir.actions.report.xml'].search([('report_name','=', 'ikoyi_module.print_creditdebit_template')])
        if report:
            report.write({'report_type':'qweb-html'})
        return self.env['report'].get_action(self, 'ikoyi_module.print_creditdebit_template')
    
    @api.multi
    def print_debit_note(self): # to_vendor
        report = self.env['ir.actions.report.xml'].search([('report_name','=', 'ikoyi_module.print_creditdebit_template')])
        if report:
            report.write({'report_type':'qweb-html'})
        return self.env['report'].get_action(self, 'ikoyi_module.print_creditdebit_template')
    
    @api.multi
    def view_gro_note(self): # to_vendor
        report = self.env['ir.actions.report.xml'].search([('report_name','=', 'ikoyi_module.print_gro_template')])
        if report:
            report.write({'report_type':'qweb-pdf'})
        return self.env['report'].get_action(self, 'ikoyi_module.print_gro_template')
    
    @api.multi
    def print_viewgro_note(self): # to_vendor
        report = self.env['ir.actions.report.xml'].search([('report_name','=', 'ikoyi_module.print_gro_template')])
        if report:
            report.write({'report_type':'qweb-html'})
        return self.env['report'].get_action(self, 'ikoyi_module.print_gro_template')
     
    # ########################### REJECTs ##############################
    @api.multi
    def button_rejects(self):  
        if not self.description_two:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note tab below')
        else:
            if self.state == "store_manager":
                self.state = "draft"
                
            elif self.state == "manager_two":
                self.state = "to_vendor"
             
    ############################# RECEIVING GOOD ######################
    @api.multi
    def storer_officer_receive(self): # to_vendor  officer
        self.write({'state':'manager_two'})
        body = "Dear Sir, <br/>We wish to notify you that prior to GRO with Number: {}, \
        the vendor: {} have returned the goods and we have confirmed them.\
            Kindly {} to approve. <br/>\
            Regards".format(self.name,self.partner_id.name,self.get_url(self.id,self._name))
            
        # moves = self.mapped('order_line').filtered(lambda move: move.receive_qty < 1)
        ## moves = [rec for rec in self.order_line if rec.receive_qty < 1]
        # if moves:
        #     raise ValidationError('You must Set the received quantity to be greater than 0')  
            
        #import pdb; pdb.set_trace()  
        return self.send_mail_manager(body)
    
    @api.multi
    def manager_two_approve(self): # manager_two  manager
        self.write({'state':'account'})
        body = "Dear Sir, <br/>Prior to the GRO with reference Number: {} the goods have been returned by the vendor:\
             {}. Also GRN have been generated by the Store.\
            Kindly {} to view. <br/>\
            Regards".format(self.name, self.partner_id.name,self.get_url(self.id, self._name))
            
        self.send_mail_all(body)
        return self.goods_reference(self.stock_in_id)
        # return self.create_picking()
        
    
    @api.multi
    def manager_two_approve(self): # manager_two  manager
        self.write({'state':'account'})
        body = "Dear Sir, <br/>Prior to the GRO with reference Number: {} the goods have been returned by the vendor:\
             {}. Also GRN have been generated by the Store.\
            Kindly {} to view. <br/>\
            Regards".format(self.name, self.partner_id.name,self.get_url(self.id, self._name))
            
        self.send_mail_all(body)
        uom = self.env['product.uom'].search([('name', 'ilike', 'Unit(s)')]).id
        picking = self.env['stock.picking']
        partner_id = 0 
        partner_search = self.env['res.partner'].search([('name', '=', self.employee_id.name)], limit=1)
        if not partner_search:
            partner_obj = self.env['res.partner'].create({'name':self.employee_id.name})
            partner_id = partner_obj.id
        else:
            partner_id = partner_search.id

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
            lines = {'name':"Requisition Request from {}".format(self.employee_id.name),
                    'product_id':line.product_id.id,
                     'product_uom_qty':line.receive_qty,
                     'product_uom': uom, # line.label.id,
                     'location_id': line.product_id.picking_source_location_id.id, #locate_out[0].id,
                     'location_dest_id': line.product_id.picking_destination_location_id.id,
                     }

            pick_browse.write({'move_lines':[(0,0, lines)]})
        # pick_browse.action_confirm()
        self.origin = pick_browse.name
        self.stock_id = pick_id.id
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
      
    # 3###################### MAIL FUNCTIONS ########################
    
    def send_mail_manager(self, body):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.inventory_manager_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.store_keeper_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.procurement_officer_ikoyi').id

        if self.id:
            bodyx = body
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
             
        else:
            raise ValidationError('No Record created')
    
    def send_mail_all(self,body):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.costing_manager_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.internal_control_ikoyi').id

        if self.id:
            bodyx = body
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx)
             
        else:
            raise ValidationError('No Record created')
        
    @api.multi
    def send_mail_vendor(self, force=False):
        email_from = self.env.user.company_id.email
        mail_to = self.partner_id.email
        subject = "Ikoyi Club GRO Notification"
        bodyx = "This is to notify you that some goods will be returned to you on {} because of some reasons \
        </br> For further enquires,\
         kindly contact {} </br> {} </br>\
        Thanks".format(fields.Date.today(), self.env.user.company_id.name, self.env.user.company_id.phone)
        self.mail_sending_one(email_from, mail_to, bodyx, subject)
    
        
    def mail_sending_one(self, email_from, mail_to, bodyx, subject):
        REPORT_NAME = 'ikoyi_module.print_creditdebit_template' #ikoyi_module.print_creditdebit_template
        # pdf = self.env['report'].sudo().get_pdf([invoice.id], 'ikoyi_module.print_credit_report')
        pdf = self.env['report'].get_pdf(self.ids, REPORT_NAME) # 
        b64_pdf = base64.encodestring(pdf)
        lists= []
        # save pdf as attachment 
        ATTACHMENT_NAME = "NOTE"
        tech = self.env['ir.attachment'].create({
            'name': ATTACHMENT_NAME,
            'type': 'binary',
            'datas': b64_pdf,
            'datas_fname': ATTACHMENT_NAME + '.pdf',
            'store_fname': ATTACHMENT_NAME,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype' : 'application/x-pdf'
        })
        lists.append(tech.id)
        
        for order in self:
            #report_ref = self.env.ref('ikoyi_module.print_credit_report').id #'report_template':report_ref,
            mail_tos = str(mail_to)
            email_froms = "Ikoyi Club " + " <" + str(email_from) + ">"
            subject = subject
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_tos,
                #  'email_cc':,#  + (','.join(str(extra)),<field name="report_template" ref="YOUR_report_xml_id"/>
                'reply_to': email_from,
                'attachment_ids': [(6,0,lists)],#tech.id,
                #'report_template':report_ref,
                'body_html': bodyx,
                        }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
            

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
            subject = "Goods Return Notification"
            bodyxx = "Dear Sir/Madam, <br/>We wish to notify you that a GRO from {} has been sent to you for approval <br/> <br/>Kindly review it. </br> <br/>Thanks".format(
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
            
    def Quantity_Moves(self):
        diff = 0.0
        stock_location = self.env['stock.location']
        stock_quant = self.env['stock.quant']
        product_return_moves = []
        
        for line in self.order_line:
            if line.location and line.product_id:
                picking = self.env['stock.picking'].browse(self.stock_id.id)#(self.env.context.get('active_id'))
   
                moves = [move.id for move in picking.move_lines]
                locate = line.location# self.env['stock.location'].search([('usage','=','supplier')])
                
                stock_inv = stock_quant.create({
                                                    'product_id': line.product_id.id,
                                                    'qty': -line.qty,
                                                    'location_id': line.location_dest.id, #locate[0].id,
                                                    
                                                    'in_date': self.date_order,
                                                    'move.history_ids':[(4,moves)]
                                                    })
                # stock_location.search([('id','=', line.location.id)])
                stock_vendor = stock_quant.create({
                                                    'product_id': line.product_id.id,
                                                    'qty': line.qty,
                                                    'location_id': line.location.id, #locate[0].id,
                                                    
                                                    'in_date': self.date_order,
                                                    'move.history_ids':[(4,moves)]
                                                    })
                
            else:
                raise ValidationError('Cannot find any Location')
   
    @api.one
    def complete_order(self):
        # for rec in self.order_line:
        #     if rec.remain_qty >= 1:
        #         rec.receive_qty = rec.remain_qty
        moves = self.mapped('order_line').filtered(lambda move: move.remain_qty > 0)
        if moves:
            #self.state = "manager_two"
            self.storer_officer_receive()
            moves.receive_qty = moves.remain_qty
            moves.remain_qty = 0  
        else:
            raise ValidationError('You do not have any orders to recieve')  
            
    def create_picking(self):
        picking = self.env['stock.picking']
        locate_in = self.location.id # self.env['stock.location'].search([('usage','=','internal')])
        locate_out = self.location_dest.id# self.env['stock.location'].search([('usage','=','supplier')])
        
        warehouse = self.env['stock.warehouse'].search(
            [('branch_id', '=', self.env.user.branch_id.id)],limit=1)
        
        domain = [
                    ('code', '=', 'incoming'),
                    ('warehouse_id', '=', warehouse.id),
                    ('active', '=', True),
                    ('default_location_dest_id', '=', locate_in)
                ]

        picking_type_id = self.env['stock.picking.type'].search(domain)
        picking_type_id2 = self.env['stock.picking.type'].search(
                    [('active', '=', True)])[0]
        
            
        value_obj = {'partner_id':self.partner_id.id,
                  'min_date':self.date_order,
                  'location_id': locate_in, #locate_out[0].id,
                  'location_dest_id':locate_out,# locate_in[0].id,
                  'branch_id':self.branch_id.id,
                  'picking_type_id': picking_type_id2.id,
                  'origin': self.purchase_order_id.name,
                  }
        pick_id = picking.create(value_obj)
        pick_browse = picking.browse([pick_id.id])           
        for line in self.order_line:
            lines = {'product_id':line.product_id.id,
                     'qty_done': line.receive_qty,
                     'product_qty':line.receive_qty,
                     'location_id': line.location.id, # locate_out[0].id,
                     'location_dest_id':line.location_dest.id,#locate_in[0].id
                     }
        
            pick_browse.write({'pack_operation_product_ids':[(0,0, lines)]})
        pick_browse.action_confirm()
        # self.origin = pick_browse.name
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
     
     
    def see_breakdown_invoice(self,source):  #  vis_account, 
        form_view_ref = self.env.ref('stock.view_picking_form', False)
        tree_view_ref = self.env.ref('stock.vpicktree', False)

        return {
            'domain': [('id', '=', source)],
            'name': 'Stock Picking',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            #  'views': [(form_view_ref.id, 'form')],
            'views': [(form_view_ref.id, 'form'),(tree_view_ref.id, 'tree')],
            #'search_view_id': search_view_ref and search_view_ref.id,
        }
        
    # @api.multi
    # def Return_Moves(self):
    #     if not self.stock_id:
    #         raise ValidationError('Please Select the Move Reference')
    #     else:
            
        
        
    @api.multi
    def account_approval(self):  #  Send memo back view_and_send_invoice
        return {
            'name': "Jornal Payment",
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'ikoyi.journal',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                
                'default_date': fields.Date.today(),
                'default_amount_to_pay': self.total_amount_cost, #  self.int_form_price,
                'default_ref_id': self.id,
                'default_partner_id': self.partner_id.id, 
                'default_revenue_account_rec':self.partner_id.property_account_receivable_id.id,
                'default_revenue_account_pay':self.partner_id.property_account_payable_id.id,
                'default_model_id':self._name,
            },
        }
    
    @api.constrains('order_line')
    def check_qty(self):
        for rec in self.order_line:
            if self.state == 'draft':
                if rec.qty < 0:
                    raise ValidationError('You must define the number of product to return in the lines must be greater than 0 ')
                else:
                    pass
            elif self.state == 'to_vendor':
                if rec.receive_qty < 0:
                    raise ValidationError('You must define the number of product received in the lines must be greater than 0')
                else:
                    pass
                #rec.write({'qty':1})       
                
                
class Ikoyi_Journal(models.Model):
    _name = 'ikoyi.journal'
 
    date = fields.Date('Date', required = True, default=fields.Date.today())
    ref_id = fields.Float('Reference ID')
    amount_to_pay = fields.Float('Amount', required=True)
    bank = fields.Many2one('account.journal', 'Journal')
    revenue_account_pay = fields.Many2one('account.account','Account Payable', readonly= False, store=True,compute="account_payable")
    revenue_account_rec = fields.Many2one('account.account','Partner Receivable', readonly= False, store=True, compute="account_payable")
    remarks = fields.Text('Remarks')
    partner_id = fields.Many2one('res.partner', 'Customer')
    
    refund = fields.Boolean('Vendor Refund', default=True)
    model_id = fields.Char('Model')
    
    @api.depends('partner_id') 
    def account_payable(self):
        if self.partner_id:
            accpay = self.partner_id.property_account_payable_id.id
            accrec = self.partner_id.property_account_receivable_id.id
            if accpay:
                self.revenue_account_pay = accpay
            else:
                raise('No Vendor payable account found')
            if accrec:
                self.revenue_account_rec = accrec
            else:
                raise('No Vendor Receivable account found')
        else:
            raise('You must select a vendor')
            

    @api.one
    def button_pay(self):
        #get the required info to post to journal entries e.g bank, revenue_account,
        bank = self.bank
        revenue = '' #self.partner_id.property_account_payable_id.id,
        amount = self.amount_to_pay
        date = ''
        model_id = str(self.model_id)
        odoo_id = self.env[model_id].search([('id','=',self.ref_id)])
        
        if self.remarks:
            narration = self.remarks
        else:
            narration = 'GRO Payment'

        if self.date:
            date = self.date
        else:
            date = datetime.today().strftime('%Y-%m-%d')

        '''if self.refund == True:
            revenue = self.revenue_account_pay.id
        else:
            revenue = self.revenue_account_rec.id'''
        #create account.move
            # acm = self.env['account.payment.method'].create({'payment_type':'inbound','name':self.partner_id.name,'code': 'GRO Payment')})
        # Save the account.voucher leg of the transaction


        move_id = self.env['account.move'].create({'journal_id': bank.id, 'date': date, 'narration': narration})
        #create account.move.line for both debit and credit
        line_id_dr = self.env['account.move.line'].with_context(check_move_validity=False).with_context(check_move_validity=False).create({
                                        'move_id': move_id.id,
                                        'ref': odoo_id.name,
                                        'name': narration,
                                        'partner_id': self.partner_id.id,
                                        'account_id': bank.default_debit_account_id.id or 1,
                                        'debit': amount,
                                        #'analytic_account_id': self.offer_id.project_site.name.id
                        })

        line_id_cr = self.env['account.move.line'].with_context(check_move_validity=False).create({
                                        'move_id': move_id.id,
                                        'ref': odoo_id.name,
                                        'name': narration,
                                        'partner_id': self.partner_id.id,
                                        'account_id': self.revenue_account_pay.id or self.partner_id.property_account_payable_id.id or 1,#revenue,
                                        'credit': amount, 
                                        #'analytic_account_id': self.offer_id.project_site.name.id values.get('revenue_account_pay')
                        })  
        
        move =self.env['account.move'].search([('id','=',move_id.id)])
        move.post()
        odoo_id.write({'state':'done'})
                   
                    
class Goods_return_Line(models.Model):
    _name = "good.return.line"
    _description = 'Goods return Line'
    _order = 'id desc'
    _rec_name = "product_id"

    def change_uom(self):
        uom = self.env['product.uom'].search([('name', 'ilike', 'Unit(s)')])
        return uom.id


    order_id = fields.Many2one(
        'ikoyi.goods_return',
        string='Reference',
        index=True,
         
        ondelete='cascade')

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        change_default=True,
        required=True)
    
    label = fields.Many2one(
        'product.uom',
        string='UOM',
        default=change_uom,
        required=False)
    qty = fields.Integer('Qty to Return', store=True, default=1, required=False )
    
    initial_qty = fields.Integer('Initial Received Qty', required=False )
    receive_qty = fields.Integer('Received Qty', required=False )
    remain_qty = fields.Integer('Remaining Qty', compute="get_remain_qty", required=False )
    
    # @api.one
    @api.onchange('qty','receive_qty')
    def get_remain_qty(self):
        self.remain_qty = self.qty - self.receive_qty
         
    location = fields.Many2one(
        'stock.location',
        string = 'Stock Location', required=False,
        help="Go to inventory config, set branch for warehouse and location") 
        #  domain=[('usage','=','internal')], related="product_id.picking_source_location_id",

    location_dest = fields.Many2one('stock.location', string="Destination Location",)
                                    # related="product_id.picking_destination_location_id")
                                    # domain=[('usage','=','supplier')])
                  
'''class Send_Main_Sendback(models.Model):
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




'''