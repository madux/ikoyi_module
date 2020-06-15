#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Maduka Sopulu
#
# Created:     06/08/2019
# Copyright:   (c) Evans 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from datetime import datetime, timedelta
import time
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _,SUPERUSER_ID

class DepartmentBudget(models.Model):
	_name = "department.budget"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = 'Ikoyi Department Budget'
	_order = "id desc"

	@api.model
	def create(self, vals):
		if vals.get('name', 'Budget No.') == 'Budget No.':
			vals['name'] = self.env['ir.sequence'].next_by_code('department.budget')# or '/'
		return super(DepartmentBudget, self).create(vals)


	def _default_employee(self):
		return self.env.context.get('default_employee_id')\
			 or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	def default_partner_id(self):
		partner = self.env['res.partner'].browse([0])
		return partner.id

	READONLY_STATES = {
		'to approve': [('readonly', True)],
		'done': [('readonly', True)],
		'cancel': [('readonly', True)],
	}

	name = fields.Char(
		'Subject',default='Budget No.', readonly=True, 
		index=True, copy=False)

	department_budgetid = fields.Many2one(
		'master.budget', string = 'Master Budget ID') 

	prepare_date = fields.Datetime(
		string='Prepared Date',default=fields.Datetime.now, 
		required=True, copy=False)

	apprv_date = fields.Datetime(
		string='Approved Date',
		readonly=True, copy=False)

	date_from = fields.Date(string='Period From',copy=False)

	date_to = fields.Date(
		string='Period To:', copy=False)

	employee_id = fields.Many2one(
		'hr.employee', string = 'Employee Responsible', 
		required=True, default =_default_employee)

	dept_ids = fields.Many2one('hr.department',
		string ='Department', required=True)

	unit_ids = fields.Char(
		string ='Unit', related='employee_id.unit_emp.name',
		readonly = True, store =True)
	
	users_followers = fields.Many2many(
		'hr.employee', string='Add followers', required=True)

	branch_id = fields.Many2one(
		'res.branch',string="Branch", required=True, 
		default=lambda self:self.env.user.branch_id.id)

	status_progress = fields.Float(
		string="Progress(%)", compute='_taken_states')
	total_amount = fields.Float(
		string="Total Budget Amount",compute="get_budgeted_amount", store=True)

	total_balance_amount = fields.Float(
		string="Total Balance",compute="get_budgeted_amount", store=True)
	variance = fields.Float(string="Variance", compute='get_budgeted_amount',store=True)

	notes = fields.Text(string='Note')
	file_upload = fields.Binary(string='File Upload')
	file_namex = fields.Char(string='File Name')
	department_budget_line = fields.One2many(
		'department_budget.line', 'department_line_m2o', string='Budget Lines', 
		store=True, index=True, required=True)
	return_check = fields.Boolean(default=True)
	state = fields.Selection([
		('draft', 'Department/Section Officer'),
		('budget', 'Budget Officer'),
		('account', 'Accountant'),
		('done', 'Done'),
		('refuse', 'Refuse'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

	budget_type = fields.Selection([('operation','Operation'),
									('capital','Capital'),
									], string='Budget Type',
									index=True, copy=False,
									default='operation', required=True, 
									track_visibility='onchange')

	@api.multi
	def submit_button(self): # Officer Submit
		for order in self:
			email_from = order.env.user.email
			group_user_id = self.env.ref('ikoyi_module.budget_officer_ikoyi').id
			extra=self.employee_id.work_email
			order.mail_sending(email_from,group_user_id,extra)
			order.write({'state': 'budget', 'users_followers': [(4, self.get_employee_follower())]})
		return True

	@api.multi
	def button_budget_off_to_account(self): #Budget Officer Approve  
		for order in self:
			email_from = order.env.user.email
			group_user_id = self.env.ref('ikoyi_module.accountant_ikoyi').id
			extra=self.employee_id.work_email
			order.mail_sending(email_from,group_user_id,extra)
			order.write({'state': 'account', 'users_followers': [(4, self.get_employee_follower())]})
		return True
	
	@api.onchange('date_from', 'date_to')
	def domain_master_budget(self):
		budlist = []
		if self.date_from and self.date_to:
			budget_get = self.env['master.budget'].search([])
			for budget in budget_get:
				if (self.date_from >= budget.date_from) and (self.date_to <= budget.date_to):
					budlist.append(budget.id)
			domain = {'department_budgetid': [('id', '=', budlist)]}
			return {'domain': domain}
		return {'department_budgetid': [('id', 'in', [0])]}

	@api.multi
	def button_account_approve(self): #Accountant Approve
		for order in self:
			email_from = order.env.user.email
			mail_to=self.employee_id.work_email
			name = self.name
			subject = "Ikoyi Club Budget Notification"
			bodyx = "This is to notify you that budget with reference {} have been {} on the date \
			{}. <br/> Thanks".format(name, 'Approved', fields.Date.today())
			self.mail_sending_one(email_from, mail_to, bodyx, subject)

			self.send_master_budget()
			order.write({'state': 'done', 'apprv_date': fields.Datetime.now(), 'users_followers': [(4, self.get_employee_follower())]})
			line = self.mapped('department_budget_line')
			for add in line:
				add.write({'quantity_approved': add.quantity_id})
		return True

	# def send_mail_sectional_officer(self, typex):
	# 	email_from = order.env.user.email
	# 	name = self.name
	# 	mail_to=self.employee_id.work_email
    #     subject = "Ikoyi Club Budget Notification"
    #     bodyx = "This is to notify you that budget with reference {} have been {} on the date \
    #     {}. <br/> Thanks".format(name, typex, fields.Date.today())
    #     self.mail_sending_one(email_from, mail_to, bodyx, subject)

	def mail_sending_one(self, email_from, mail_to, bodyx, subject):
		for order in self:
			mail_tos = str(mail_to)
			email_froms = "Ikoyi Club " + " <" + str(email_from) + ">"
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

	def get_employee_follower(self):
		emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		if emp:
			return emp.id
		else:
			raise ValidationError('You are not Added as an Employee. Contact the system Administrator for help!')
	
	@api.multi
	def button_return(self): #Accountant Approve
		for order in self:
			email_from = order.env.user.email
			mail_to=self.employee_id.work_email
			name = self.name
			subject = "Ikoyi Club Budget Notification"
			bodyx = "This is to notify you that budget with reference {} have been {} on the date \
			{}. <br/> Thanks".format(name, 'Rejected', fields.Date.today())
			self.mail_sending_one(email_from, mail_to, bodyx, subject)

			# self.send_mail_sectional_officer('Rejected')
			order.write({'state': 'draft',  'users_followers': [(4, self.get_employee_follower())]})
		return True

	def send_master_budget(self):
		if self.department_budgetid:
			master_budget = self.env['master.budget'].search([('id', '=', self.department_budgetid.id)])
			master_budget.master_budget_line = [(4, self.id)]
		else:
			raise ValidationError('Please Select Master Budget ID')

	@api.multi
	@api.depends('state')
	def _taken_states (self):
		for order in self:
			if order.state == "draft":
				order.status_progress = 20

			elif order.state == "budget":
				order.status_progress = 50

			elif order.state == "account":
				order.status_progress = 70

			elif order.state == "done":
				order.status_progress = 100

			elif order.state == "cancel":
				order.status_progress = 10
			
			elif order.state == "refused":
				order.status_progress = 0
			
			else:
				order.status_progress = 100/len(order.state)

		## Mail Function
	def mail_sending(self, email_from,group_user_id,extra):
		from_browse =self.env.user.name
		groups = self.env['res.groups']
		for order in self:
			group_users = groups.search([('id','=',group_user_id)])
			group_emails = group_users.users
			
			append_mails = []
			email_to = []
			for group_mail in self.users_followers:
				append_mails.append(group_mail.work_email)
			
			for gec in group_emails:
				email_to.append(gec.login)
			
			email_froms = str(from_browse) + " <"+str(email_from)+">"
			mail_appends = (', '.join(str(item)for item in append_mails))
			subject = "Budget Request"
			bodyx = "Dear Sir/Madam, </br>We wish to notify you that a budget with REF: {}, from \
			{} has been sent to you for approval. </br> </br>Kindly review it. </br> </br>Thanks".format(self.name, self.employee_id.name)
			extrax = (', '.join(str(extra)))
			append_mails.append(extrax)
			mail_data={
				'email_from': email_froms,
				'subject':subject,
				'email_to':email_to,
				'email_cc':mail_appends,
				'reply_to': email_from,
				'body_html':bodyx
				}
			mail_id =  order.env['mail.mail'].create(mail_data)
			order.env['mail.mail'].send(mail_id)


	@api.one
	@api.depends('department_budget_line.balance', 
	'department_budget_line.sub_total', 
	'department_budget_line.paid_amount',
	'department_budget_line.variance')
	def get_budgeted_amount(self):
		val, bal, var = [], [], []
		for rex in self.department_budget_line:
			val.append(rex.sub_total)
			bal.append(rex.balance)
			var.append(rex.variance)

			self.total_amount = sum(val)
			self.total_balance_amount = sum(bal)
			self.variance = sum(var)
			
	@api.multi
	def print_account_report(self):
		"""Print Account Report """
		return self.env['report'].get_action(self,'ikoyi_module.ikoyi_department_budget_report_template')

##################################################################################################################################
############################# Rejection Buttons  #########################################


	@api.multi
	def button_reject_budget(self): # Budget Refusal,
		return {
			  	'name': 'Reason for Return',
				'view_type': 'form',
				"view_mode": 'form',
				'res_model': 'input.budget.back',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'default_memo_record': self.id,
					'default_date': fields.Datetime.now(),
					'default_direct_memo_user':self.employee_id.id,
				},
		}

	@api.multi
	def button_reject_account(self): # Accountant Refusal,
		return {
			  	'name': 'Reason for Return',
				'view_type': 'form',
				"view_mode": 'form',
				'res_model': 'input.budget.back',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'default_memo_record': self.id,
					'default_date':fields.Datetime.now(),
					'default_direct_memo_user':self.employee_id.id,
				},
		}

class ikoyiBudgetxlines(models.Model):
	_name = 'capex.number'

	name = fields.Char(
		string='Number', required=True)


class ikoyiBudgetxlines(models.Model):
	_name = 'department_budget.line'

	name = fields.Char(
		string='Description')

	account_id = fields.Many2one(
		'account.account', string='Fixed Assets')
	product_id = fields.Many2one(
		'product.product', string='Item')
	capex_num = fields.Many2one(
		'capex.number', string='Capex No')
	budget_type = fields.Selection([('operation','Operation'),
									('capital','Capital'),
									], string='Budget Type',
									index=True, copy=False,
									default='operation', required=True, 
									track_visibility='onchange')


	quantity_id = fields.Float(
		string='Qty Request', default=1.0)
	qty_used = fields.Float(
		string='Used Qty', default=0.0)
	quantity_approved = fields.Float(
		string='Qty Approved', default=0.0)
	serial_num = fields.Char(
		string="Serial Number", store=True)
	# capex_num = fields.Char(
	# 	string="Capex No", store=True)
	unit_price = fields.Float(
		string='Unit Price', store=True)
	amount_id = fields.Float( 
		string='Amount', store=True)

	sub_total = fields.Float(
		string='Total', compute="get_subtotal", store=True)

	paid_amount = fields.Float(
		string='Amount Used', store=True)
		
	balance = fields.Float(
		string='Balance',compute="get_balance", store=True, readonly=True)

	variance = fields.Float(
		string='Variance')

	comment = fields.Char(
		string='Comment', store=True)
		
	justification = fields.Char(
		string='Justification', store=True)

	department_line_m2o = fields.Many2one(
		'department.budget', string='Budget ID', 
		store=True, index=True, required=True)

	date_from = fields.Date(string='Period From', readonly=True, copy=False)
	date_to = fields.Date(
		string='Period To:',
		readonly=True, copy=False)

	dept_ids = fields.Many2one('hr.department',
		string ='Department')

	@api.multi
	@api.depends('quantity_id', 'unit_price', 'variance')
	def get_subtotal(self):
		for rec in self:
			amount = (rec.quantity_id * rec.unit_price) + rec.variance
			rec.sub_total = amount
			
	@api.depends('sub_total', 'paid_amount')
	def get_balance(self):
		for rec in self:
			bal = rec.sub_total - rec.paid_amount
			rec.balance = bal

	@api.constrains('capex_num')
	def capex_num_checker(self):
		if self.capex_num:
			dept_line = self.env['department_budget.line'].search([])
			filter_cpx = dept_line.filtered(lambda  a: a.capex_num.id == self.capex_num.id)
			if len(filter_cpx) > 1:
				raise ValidationError('You cannot have more than one capex, check the capex number properly')


class ikoyiInputBudgetxBack(models.Model):
	_name = 'input.budget.back'

	resp = fields.Many2one('res.users','Responsible')
	memo_record = fields.Many2one('department.budget', 'Memo ID',)
	reason = fields.Char('Reason')

	date = fields.Datetime('Date')
	users_followers = fields.Many2many('hr.employee', string='Add followers', required=False)
	direct_memo_user = fields.Many2one('hr.employee', 'Initiator', readonly=True)

	# def send_mail_sectional_officer(self, typex):
	# 	email_from = order.env.user.email
	# 	mail_to=self.employee_id.work_email
	# 	name = self.name
    #     subject = "Ikoyi Club Budget Notification"
    #     bodyx = "This is to notify you that budget with reference {} have been {} on the date \
    #     {}. <br/> Thanks".format(name, typex, fields.Date.today())
    #     self.mail_sending_one(email_from, mail_to, bodyx, subject)

	def mail_sending_one(self, email_from, mail_to, bodyx, subject):
		for order in self:
			mail_tos = str(mail_to)
			email_froms = "Ikoyi Club " + " <" + str(email_from) + ">"
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

	@api.multi
	def post_back(self):
		email_from = self.env.user.email
		bodyx = self.reason
		extra = self.direct_memo_user.work_email

		draft = self.direct_memo_user.user_id.has_group("ikoyi_module.sectional_officer_ikoyi")
		budget = self.direct_memo_user.user_id.has_group("ikoyi_module.budget_officer_ikoyi")
		account = self.direct_memo_user.user_id.has_group("ikoyi_module.accountant_ikoyi")

		get_state = self.env['department.budget'].search([('id','=', self.memo_record.id)])
		reasons = "<b><h4>Refusal of %s From %s </br></br>Please refer to the reasons below:</br></br> %s.</h4></b>" %(get_state.name, self.env.user.name,self.reason)
		get_state.write({'reason_back':reasons})

		for record in self:
			if budget:
				email_from = order.env.user.email
				mail_to=self.employee_id.work_email
				name = self.name
				subject = "Ikoyi Club Budget Notification"
				bodyx = "This is to notify you that budget with reference {} have been {} on the date \
				{}. <br/> Thanks".format(name, typex, fields.Date.today())
				self.mail_sending_one(email_from, mail_to, bodyx, subject)

				get_state.write({'state':'draft'})

			elif account:
				group_user_id = self.env.ref('ikoyi_module.budget_officer_ikoyi').id
				self.direct_mail_sending(email_from,group_user_id,bodyx,extra)
				get_state.write({'state':'budget'})

			return{'type': 'ir.actions.act_window_close'}

	# mail sending function for rejection
	def direct_mail_sending(self, email_from, group_user_id, bodyx, extra):

		from_browse =self.env.user.name
		groups = self.env['res.groups']
		for order in self:

			group_users = groups.search([('id','=',group_user_id)])
			group_emails = group_users.users
			append_mails = []
			email_to = []
			for group_mail in self.users_followers:
				append_mails.append(group_mail.work_email)
			for gec in group_emails:
				email_to.append(gec.login)
			email_froms = str(from_browse) + " <"+str(email_from)+">"
			mail_appends = (', '.join(str(item)for item in append_mails))
			subject = "Input Budget Rejected"
			extrax = (', '.join(str(extra)))
			append_mails.append(extrax)
			mail_data={
				'email_from': email_froms,
				'subject':subject,
				'email_to':email_to,
				'email_cc':mail_appends,
				'reply_to': email_from,
				'body_html':bodyx,
			}
			mail_id =  order.env['mail.mail'].create(mail_data)
			order.env['mail.mail'].send(mail_id)