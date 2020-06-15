from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils
from odoo import http
from odoo.exceptions import UserError, ValidationError


class EmptyBottleLine(models.Model):
    _name = "stock.inventory.line.fam"

    def change_uom(self):
        uom = self.env['product.uom'].search([('name', '=', 'Unit(s)')], limit=1)
        return uom.id
    inventory_fixed_id = fields.Many2one('cost.fixed.asset.move',string='ID')
    product_id = fields.Many2one('product.product', string="Product")  
    location_id = fields.Many2one('stock.location', string="Stock location") 
    product_qty =fields.Integer(string='Qty')
    product_uom_id = fields.Many2one(
        'product.uom',
        string='UOM',
        default=change_uom,
        required=True)     

class CostFixedAssetMove(models.Model):
    _name = "cost.fixed.asset.move"
    _description = "Costing Fixed Asset Move"

    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>. ".format(base_url)
    
    def _default_all_location(self):
        lists = []
        stock_location_obj = self.env["stock.location"]
        search_stock_loc = stock_location_obj.search([('usage','=', 'internal')])
        for rec in search_stock_loc:
            lists.append (rec.id)
        return lists
        
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cost.fixed.asset.move')# or '/'
        return super(CostFixedAssetMove, self).create(vals)


    name = fields.Char(
        'Inventory Reference',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})

    notes = fields.Text('Note')
    employee_id = fields.Many2one('hr.employee',string='Employee', required=True)
    date = fields.Datetime(
        'Inventory Date',
        readonly=True,
        default=fields.Datetime.now)

    line_ids = fields.One2many(
        'stock.inventory.line.fam', 'inventory_fixed_id', string='Inventories',
        copy=True, readonly=False)

    location_id = fields.Many2many(
        'stock.location', string='Inventoried Location',
        required=True,
        states={'draft': [('readonly', False)]},
        default=_default_all_location)

    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('confirm', 'In Progress'),
        ('internal_control', 'Internal Control'),
        ('fa_manager', 'F & A'),
        ('gm', 'General Manager'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ],
        copy=False, index=True, readonly=True,
        default='draft')

    @api.multi
    def action_start(self):
        # def _get_inventory_lines_values(self):
        total_qty = 0.0
        Product = self.env['product.product']
        stock_quant = self.env['stock.quant']
        if self.location_id:
            for loc in self.location_id:
                search_quanty = stock_quant.search([('location_id', '=', loc.id)])
                if search_quanty:
                    for rey in search_quanty:
                        line_values = {
                            'product_id': rey.product_id.id,
                            'location_id': rey.location_id.id,
                            # 'theoretical_qty': rey.qty,
                            'product_qty': rey.qty,
                            'product_uom_id' : rey.product_id.uom_id.id
                        }
                        self.line_ids = [(0, 0, line_values)]
                        # return [(0, 0, line_values)]
                  

        else:
            raise ValidationError('Please Select a Location')

        for inventory in self:
            vals = {'state': 'confirm', 'date': fields.Datetime.now()}
            # vals.update({'line_ids': self._get_inventory_lines_values()})
            inventory.write(vals)
        return True

    @api.multi
    def action_officer_ic(self):
        body = "Dear Sir, <br/>\
                A request for Fixed Asset Movement with reference Name: {} have been sent by {} \
                for internal control appoval.<br/>\
                Please kindly {} Review or Go to the 'Costing App/ Fixed Asset Movement' to access the record. <br/>\
                Regards".format(self.name, self.env.user.name, self.get_url(self.id, self._name))
        self.state = "internal_control"
        self.send_mail_ic(body)

    @api.multi
    def action_ic_fa(self):
        body = "Dear Sir, <br/>\
                A request for Fixed Asset Movement with reference Name: {} have been sent by {} to \
                the Finance and Admin Manager.<br/>\
                Please kindly {} Review or Go to the 'Costing App/ Fixed Asset Movement' to access the record. <br/>\
                Regards".format(self.name, self.env.user.name, self.get_url(self.id, self._name))
        self.send_mail_fa(body)
        self.state = "fa_manager"

    @api.multi
    def action_fa_to_gm(self):
        body = "Dear Sir, <br/>\
                A request for Fixed Asset Movement with reference Name: {} have been sent by {} to \
                the General Manager.<br/>\
                Please kindly {} Review or Go to the 'Costing App/ Fixed Asset Movement' to access the record. <br/>\
                Regards".format(self.name, self.env.user.name, self.get_url(self.id, self._name))
        self.send_mail_gm(body)
        self.state = "gm"

    @api.multi
    def action_gm_approve(self):
        body = "Dear Sir/Madam, <br/>\
                A request for Fixed Asset Movement with reference Name: {} have been approved by {}(General Manager).<br/>\
                Please kindly {} Review or Go to the 'Costing App/ Fixed Asset Movement' to access the record. <br/>\
                Regards".format(self.name, self.env.user.name, self.get_url(self.id, self._name))
        self.send_mail_gm_to_officer()
        self.state = "approved"

    @api.multi
    def action_complete(self):
        self.send_mail('Completed')
        self.state = "done"

    

    @api.multi
    def _get_inventory_lines_valuesxx(self):
        # TDE CLEANME: is sql really necessary ? I don't think so
        locations = self.env['stock.location'].search([('id', 'in', [rec.id for rec in self.location_id])])
        domain = ' location_id in %s'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']  

        self.env.cr.execute("""SELECT product_id, sum(qty) as product_qty, location_id,
            FROM stock_quant
            WHERE %s
            GROUP BY product_id, location_id""" % domain, args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        return vals

    def mail_sending_one(self, email_from, mail_to, bodyx, subject):
		for order in self:
			mail_tos = str(mail_to)
			email_froms = email_from # "Ikoyi Club: " + " <" + str(email_from) + ">"
			subject = subject
			mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_tos,
                'reply_to': email_from,
                'body_html': bodyx,
                        }
			mail_id = order.env['mail.mail'].create(mail_data)
			order.env['mail.mail'].send(mail_id)

    def send_mail(self, types):
        email_from = self.env.user.email
        mail_to=self.employee_id.work_email
        subject = "Ikoyi Club Fixed Asset Notification"
        bodyx = "This is to notify you that a request for fixed asset Movement initiated by {}\
             with reference {} have been {} on the date \
        {}. Kindly {} to view<br/> Thanks".format(self.employee_id.name, self.name, types, fields.Date.today(), self.get_url(self.id, self._name))
        self.mail_sending_one(email_from, mail_to, bodyx, subject)

        
    def send_mail_ic(self, body):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.costing_officer_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.costing_manager_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.audit_boss_ikoyi').id
        bodyx = body
        self.mail_sending_for_three(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def send_mail_fa(self, body):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.costing_officer_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.costing_manager_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        bodyx = body
        self.mail_sending_for_three(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

    def send_mail_gm(self, body):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.gm_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.costing_manager_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.audit_boss_ikoyi').id
        bodyx = body
        self.mail_sending_for_three(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)
 
    def send_mail_gm_to_officer(self, body):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.costing_officer_ikoyi').id
        group_user_id = self.env.ref('ikoyi_module.costing_manager_ikoyi').id
        group_user_id3 = self.env.ref('ikoyi_module.account_boss_ikoyi').id
        bodyx = body
        self.mail_sending_for_three(
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx)

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
 
            subject = "Fixed Asset Movement Notification"

            # bodyx = "This is to notify you that a request for Fixed Asset Movement\
            #  with reference {} have been sent {} on the date {}. Kindly {} to view<br/> Thanks".format(self.name, types, fields.Date.today(), self.get_url(self.id, self._name))
                
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
