#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Dosu Chukwudi Evans
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

#########################################################################################################################################
##########################################3   DEPARTMENT LINES ############################################################
class MasterBudget(models.Model):
	_name = "master.budget"

	@api.model
	def create(self, vals):
		if vals.get('name', 'Budget No.') == 'Budget No.':
			vals['name'] = self.env['ir.sequence'].next_by_code('master.budget')# or '/'
		return super(MasterBudget, self).create(vals)

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	name = fields.Char(
		'Subject',default='Budget No.', readonly=True, 
		index=True, copy=False)

	prepare_date = fields.Datetime(
		string='Prepared Date',default=fields.Datetime.now, 
		required=True, copy=False)

	apprv_date = fields.Datetime(
		string='Approved Date',
		readonly=True, copy=False)

	date_from = fields.Date(string='Period From', copy=False)

	date_to = fields.Date(
		string='Period To:',
		copy=False)


	employee_id = fields.Many2one(
		'hr.employee', string = 'Employee Responsible', 
		required=True, default =_default_employee)

	dept_ids = fields.Char(
		string ='Department', related='employee_id.department_id.name',
		readonly = True, store =True)

	unit_ids = fields.Char(
		string ='Unit', related='employee_id.unit_emp.name',
		readonly = True, store =True)

	state = fields.Selection([
		('draft', 'Department/Section Officer'),
		('budget', 'Budget Officer'),
		('account', 'Accountant'),
		('fam', 'F&A Manager'),
		('hon_tre', 'Hon Treasurer'),
		('chair', 'Chairman'),
		('gm', 'GM'),
		('done', 'Done'),
		('refuse', 'Refuse'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, default="budget", index=True, copy=False, track_visibility='onchange')
	
	variance = fields.Float(string="Variance", compute='get_general_budget_total', track_visibility='onchange', store=True)
	budget_variance = fields.Float(string="Budget Amount After Variance", track_visibility='onchange', store=True)

	total_amount = fields.Float(string="Total Input Budget", store=True, track_visibility='onchange', compute='get_general_budget_total')
	amount_release = fields.Float(
		string="Released Amount", store=True)
	balance_id = fields.Float(
		string="Department Balance", compute='get_general_budget_total', track_visibility='onchange', help="Total balance from each department budget after expenses", store=True)

	balance_overall = fields.Float(
		string="Overall Balance", compute='get_overall_balance', store=True, help="This is computed based on the amount released - the total balances")
	users_followers = fields.Many2many('hr.employee', string='Add followers', required=False)
	status_progress = fields.Float(
		string="Progress(%)", compute='_taken_states')
	notes = fields.Text(string='Comment')
	file_upload = fields.Binary(string='File Upload')
	file_namex = fields.Char(string='File Name')
	budget_type = fields.Selection([('operation','Operation'),
									('capital','Capital'),
									], string='Budget Type', index=True, copy=False, default='operation', track_visibility='onchange')

	master_budget_line = fields.One2many('department.budget', 'department_budgetid', string='Budget ID', index=True)

	@api.multi 
	def print_master_report(self):
		return self.env['report'].get_action(self, 'ikoyi_module.ikoyi_master_budget_report_template_main')

	def button_return_budget(self):
		mapped = self.mapped('master_budget_line').filtered(lambda s: s.return_check == True)
		if mapped:
			for rec in mapped:
				rec.button_return()
				self.write({'master_budget_line': [(2, rec.id) for rec in mapped]}) 
			
	@api.one
	@api.depends('master_budget_line')
	def get_general_budget_total(self):
		total = 0.0
		for rez in self:
			if rez.master_budget_line:
				val = [rec.total_amount for rec in rez.master_budget_line if rec.total_amount] 
				bal = [recs.total_balance_amount for recs in rez.master_budget_line if recs.total_balance_amount]
				variance = [recs.variance for recs in rez.master_budget_line if recs.variance]

				total += sum(val)
				rez.balance_id += sum(bal)
				rez.total_amount = total
				rez.variance += sum(variance)

	@api.multi
	@api.depends('total_amount','amount_release')
	def get_overall_balance(self):
		for rec in self:
			total = rec.amount_release - rec.total_amount
			rec.balance_overall = total

	@api.multi
	@api.depends('state')
	def _taken_states (self):
		pass
		for order in self:
			if order.state == "draft":
				order.status_progress = 20

			elif order.state == "budget":
				order.status_progress = 30

			elif order.state == "account":
				order.status_progress = 50

			elif order.state == "fam":
				order.status_progress = 60

			elif order.state == "hon_tre":
				order.status_progress = 70

			elif order.state == "chair":
				order.status_progress = 80

			elif order.state == "gm":
				order.status_progress = 90

			elif order.state == "done":
				order.status_progress = 100

			elif order.state == "cancel":
				order.status_progress = 10
			
			elif order.state == "refused":
				order.status_progress = 0
			
			else:
				order.status_progress = 100/len(order.state)

	def get_employee_follower(self):
		return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id

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

	@api.multi
	def button_account_to_fam(self): #Accountant Approve
		for order in self:
			email_from = order.env.user.email
			group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
			extra=self.employee_id.work_email
			order.mail_sending(email_from,group_user_id,extra)
			order.write({'state': 'fam', 'users_followers': [(4, self.get_employee_follower())]})
		return True

	@api.multi
	def button_fam_to_hon_tre(self): #F&A Manager Approve
		for order in self:
			email_from = order.env.user.email
			group_user_id = self.env.ref('ikoyi_module.honorary_treasurer_ikoyi').id
			extra=self.employee_id.work_email
			order.mail_sending(email_from,group_user_id,extra)
			order.write({'state': 'hon_tre', 'users_followers': [(4, self.get_employee_follower())]})
		return True
		
	@api.multi
	def button_hon_trea_to_chair(self): #Honorary Treasurer Approve
		for order in self:
			email_from = order.env.user.email
			group_user_id = self.env.ref('ikoyi_module.chairman_ikoyi').id
			extra=self.employee_id.work_email
			order.mail_sending(email_from,group_user_id,extra)
			order.write({'state': 'chair', 'users_followers': [(4, self.get_employee_follower())]})
		return True
		
	@api.multi
	def button_chair_to_gm(self): #Chairman Approve
		for order in self:
			email_from = order.env.user.email
			group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
			extra=self.employee_id.work_email
			order.mail_sending(email_from,group_user_id,extra)
			order.write({'state': 'gm', 'users_followers': [(4, self.get_employee_follower())]})
		return True

	@api.multi
	def button_gm_approves(self): #General Manager Approve
		for order in self:
			email_from = order.env.user.email
			group_user_id = self.env.ref('base.group_user').id
			extra=self.employee_id.work_email
			order.mail_sending(email_from,group_user_id,extra)
			order.write({'state': 'done', 'apprv_date': fields.Datetime.now(), 'users_followers': [(4, self.get_employee_follower())]})
		return True
				
	### Mail Send Function			
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
			subject = "Master Budget Request"
			bodyx = "Dear Sir/Madam, </br>We wish to notify you that a request with REF: {}, from {}\
				 has been sent to you for approval </br> </br>Kindly review it. </br> </br>Thanks".format(self.name,self.employee_id.name)
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

			
##################################################################################################################################
############################# Rejection Buttons  #########################################

	@api.multi
	def button_reject_account(self): # Budget Refusal,
		return {
			  	'name': 'Reason for Return',
				'view_type': 'form',
				"view_mode": 'form',
				'res_model': 'master.budget.back',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': {
					'default_memo_record': self.id,
					'default_date': fields.Datetime.now(),
					'default_direct_memo_user':self.employee_id.id,
				},
		}
 
class ikoyiMasterBudgetxBack(models.Model):
	_name = 'master.budget.back'

	resp = fields.Many2one('res.users','Responsible')
	memo_record = fields.Many2one('master.budget', 'Ref ID',)
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
		fam = self.direct_memo_user.user_id.has_group("ikoyi_module.account_boss_ikoyi")
		hon_tre = self.direct_memo_user.user_id.has_group("ikoyi_module.honorary_treasurer_ikoyi")
		chair = self.direct_memo_user.user_id.has_group("ikoyi_module.vice_chairman_ikoyi")
		gm = self.direct_memo_user.user_id.has_group("ikoyi_module.gm_ikoyi")

		get_state = self.env['master.budget'].search([('id','=', self.memo_record.id)])
		reasons = "<b><h4>Refusal of %s From %s </br></br>Please refer to the reasons below :</br></br> %s.</h4></b>" %(get_state.name, self.env.user.name, self.reason)
		get_state.write({'reason_back': reasons})

		for record in self:

			if budget:
				email_from = order.env.user.email
				mail_to=self.employee_id.work_email
				name = self.name
				subject = "Ikoyi Club Budget Notification"
				bodyx = "This is to notify you that budget with reference {} have been {} on the date \
				{}. <br/> Thanks".format(name, 'Rejected', fields.Date.today())
				self.mail_sending_one(email_from, mail_to, bodyx, subject)

				# self.send_mail_sectional_officer('Rejected')
				get_state.write({'state':'draft'})

			elif account:
				group_user_id = self.env.ref('ikoyi_module.budget_officer_ikoyi').id
				self.direct_mail_sending(email_from,group_user_id,bodyx,extra)
				get_state.write({'state':'budget'})

			elif fam:
				group_user_id = self.env.ref('ikoyi_module.accountant_ikoyi').id
				self.direct_mail_sending(email_from,group_user_id,bodyx,extra)
				get_state.write({'state':'account'})

			elif hon_tre:
				group_user_id = self.env.ref('ikoyi_module.account_boss_ikoyi').id
				self.direct_mail_sending(email_from,group_user_id,bodyx,extra)
				get_state.write({'state':'fam'})
				
			elif chair:
				group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
				self.direct_mail_sending(email_from,group_user_id,bodyx,extra)
				get_state.write({'state':'hon_tre'})

			else:
				raise ValidationError('You don\'t have the right to refuse this document')
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
			subject = "Master Budget Rejected"
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
			