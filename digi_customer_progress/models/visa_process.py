# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class VisaProcess(models.Model):
    _name = 'digi.visa.process'
    _description = 'Quy Trình Xử Lý Visa'
    _order = 'customer_id, step_sequence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Link to customer
    customer_id = fields.Many2one('digi.customer.record', string='Khách Hàng', required=True, ondelete='cascade')
    
    # Visa Process Step
    step = fields.Selection([
        ('checklist', '1. Checklist'),
        ('job_offer', '2. Job Offer'),
        ('lmia', '3. LMIA'),
        ('sa', '4. Skills Assessment'),
        ('sbs', '5. State/Province Sponsorship'),
        ('nomination', '6. Nomination'),
        ('visa', '7. Visa Application')
    ], string='Bước', required=True)
    
    step_sequence = fields.Integer(string='Thứ Tự Bước', compute='_compute_step_sequence', store=True)
    
    # Status and Progress
    status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Thực Hiện'),
        ('submitted', 'Đã Nộp'),
        ('under_review', 'Đang Xem Xét'),
        ('approved', 'Đã Duyệt'),
        ('completed', 'Hoàn Thành'),
        ('rejected', 'Bị Từ Chối'),
        ('expired', 'Hết Hạn'),
        ('cancelled', 'Đã Hủy')
    ], string='Trạng Thái', default='not_started', required=True, tracking=True)
    
    is_completed = fields.Boolean(string='Đã Hoàn Thành', compute='_compute_is_completed', store=True)
    progress_percentage = fields.Float(string='Tiến Độ (%)', default=0.0, tracking=True)
    
    # Dates and Timeline
    start_date = fields.Date(string='Ngày Bắt Đầu', tracking=True)
    planned_completion_date = fields.Date(string='Ngày Kế Hoạch Hoàn Thành')
    actual_completion_date = fields.Date(string='Ngày Thực Tế Hoàn Thành', tracking=True)
    
    submission_date = fields.Date(string='Ngày Nộp Hồ Sơ', tracking=True)
    decision_date = fields.Date(string='Ngày Có Quyết Định', tracking=True)
    expiry_date = fields.Date(string='Ngày Hết Hạn')
    
    # Duration tracking
    estimated_days = fields.Integer(string='Số Ngày Ước Tính')
    actual_days = fields.Integer(string='Số Ngày Thực Tế', compute='_compute_actual_days', store=True)
    days_remaining = fields.Integer(string='Số Ngày Còn Lại', compute='_compute_days_remaining')
    
    # Staff Assignment
    case_officer_id = fields.Many2one('hr.employee', string='Nhân Viên Phụ Trách', tracking=True)
    lawyer_id = fields.Many2one('res.partner', string='Luật Sư', 
                               domain=[('is_company', '=', False), ('category_id.name', 'ilike', 'lawyer')],
                               tracking=True)
    
    # Application Details
    application_number = fields.Char(string='Số Hồ Sơ', tracking=True)
    reference_number = fields.Char(string='Số Tham Chiếu')
    application_fee = fields.Float(string='Phí Hồ Sơ', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Tiền Tệ', default=lambda self: self.env.company.currency_id)
    
    # Requirements and Documents
    required_documents = fields.Text(string='Tài Liệu Yêu Cầu')
    submitted_documents = fields.Text(string='Tài Liệu Đã Nộp')
    missing_documents = fields.Text(string='Tài Liệu Còn Thiếu', compute='_compute_missing_documents')
    
    document_checklist_ids = fields.One2many('digi.visa.document', 'visa_process_id', string='Danh Sách Tài Liệu')
    
    # External References
    employer_id = fields.Many2one('res.partner', string='Nhà Tuyển Dụng', domain=[('is_company', '=', True)])
    job_title = fields.Char(string='Vị Trí Công Việc')
    salary_offered = fields.Float(string='Mức Lương Đề Nghị')
    
    # Assessment Authority (for Skills Assessment)
    assessing_authority = fields.Char(string='Cơ Quan Đánh Giá')
    assessment_outcome = fields.Selection([
        ('positive', 'Tích Cực'),
        ('negative', 'Tiêu Cực'),
        ('pending', 'Chờ Đợi')
    ], string='Kết Quả Đánh Giá')
    
    # State/Province Sponsorship Details
    sponsoring_state = fields.Char(string='Bang/Tỉnh Bảo Lãnh')
    sponsorship_number = fields.Char(string='Số Bảo Lãnh')
    
    # Visa Application Details
    visa_lodge_date = fields.Date(string='Ngày Nộp Visa')
    visa_decision_date = fields.Date(string='Ngày Quyết Định Visa')
    visa_grant_number = fields.Char(string='Số Visa Được Cấp')
    visa_conditions = fields.Text(string='Điều Kiện Visa')
    
    # Priority and Urgency
    priority = fields.Selection([
        ('low', 'Thấp'),
        ('normal', 'Bình Thường'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn Cấp')
    ], string='Độ Ưu Tiên', default='normal', tracking=True)
    
    is_urgent = fields.Boolean(string='Khẩn Cấp', tracking=True)
    urgent_reason = fields.Text(string='Lý Do Khẩn Cấp')
    
    # Communication and Updates
    last_update_date = fields.Date(string='Ngày Cập Nhật Cuối', default=fields.Date.today)
    next_follow_up_date = fields.Date(string='Ngày Theo Dõi Tiếp Theo')
    
    # Notes and Comments
    notes = fields.Html(string='Ghi Chú')
    internal_notes = fields.Html(string='Ghi Chú Nội Bộ')
    client_communication = fields.Html(string='Giao Tiếp Với Khách Hàng')
    
    # Attachments
    attachment_count = fields.Integer(string='Số Tài Liệu', compute='_compute_attachment_count')
    
    # Dependencies
    depends_on_ids = fields.Many2many(
        'digi.visa.process', 
        'visa_dependency_rel', 
        'dependent_id', 
        'prerequisite_id',
        string='Phụ Thuộc Vào'
    )
    
    blocking_ids = fields.Many2many(
        'digi.visa.process', 
        'visa_dependency_rel', 
        'prerequisite_id', 
        'dependent_id',
        string='Đang Chặn'
    )
    
    can_start = fields.Boolean(string='Có Thể Bắt Đầu', compute='_compute_can_start')
    
    @api.depends('step')
    def _compute_step_sequence(self):
        step_order = {
            'checklist': 1, 'job_offer': 2, 'lmia': 3, 'sa': 4,
            'sbs': 5, 'nomination': 6, 'visa': 7
        }
        for record in self:
            record.step_sequence = step_order.get(record.step, 0)
    
    @api.depends('status')
    def _compute_is_completed(self):
        completed_statuses = ['completed', 'approved']
        for record in self:
            record.is_completed = record.status in completed_statuses
    
    @api.depends('start_date', 'actual_completion_date')
    def _compute_actual_days(self):
        for record in self:
            if record.start_date and record.actual_completion_date:
                delta = record.actual_completion_date - record.start_date
                record.actual_days = delta.days
            else:
                record.actual_days = 0
    
    @api.depends('planned_completion_date')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for record in self:
            if record.planned_completion_date and not record.is_completed:
                delta = record.planned_completion_date - today
                record.days_remaining = delta.days
            else:
                record.days_remaining = 0
    
    @api.depends('required_documents', 'submitted_documents')
    def _compute_missing_documents(self):
        for record in self:
            if record.required_documents and record.submitted_documents:
                required = set(line.strip() for line in record.required_documents.split('\n') if line.strip())
                submitted = set(line.strip() for line in record.submitted_documents.split('\n') if line.strip())
                missing = required - submitted
                record.missing_documents = '\n'.join(sorted(missing))
            else:
                record.missing_documents = record.required_documents or ''
    
    @api.depends('depends_on_ids.is_completed')
    def _compute_can_start(self):
        for record in self:
            prerequisites = record.depends_on_ids
            if prerequisites:
                record.can_start = all(prereq.is_completed for prereq in prerequisites)
            else:
                record.can_start = True
    
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])
    
    def action_start(self):
        """Start the visa process step"""
        self.ensure_one()
        if not self.can_start:
            raise UserError(_('Không thể bắt đầu vì chưa hoàn thành các bước tiên quyết.'))
        
        self.write({
            'status': 'in_progress',
            'start_date': fields.Date.today(),
            'progress_percentage': 10
        })
        
        # Update customer record
        if hasattr(self.customer_id, self.step):
            setattr(self.customer_id, self.step, True)
    
    def action_submit(self):
        """Submit the application for this step"""
        self.ensure_one()
        self.write({
            'status': 'submitted',
            'submission_date': fields.Date.today(),
            'progress_percentage': 60
        })
    
    def action_approve(self):
        """Approve this step"""
        self.ensure_one()
        self.write({
            'status': 'approved',
            'decision_date': fields.Date.today(),
            'actual_completion_date': fields.Date.today(),
            'progress_percentage': 100
        })
        
        # Update customer record
        if hasattr(self.customer_id, self.step):
            setattr(self.customer_id, self.step, True)
    
    def action_complete(self):
        """Complete this step"""
        self.ensure_one()
        self.write({
            'status': 'completed',
            'actual_completion_date': fields.Date.today(),
            'progress_percentage': 100
        })
        
        # Update customer record
        if hasattr(self.customer_id, self.step):
            setattr(self.customer_id, self.step, True)
    
    def action_reject(self):
        """Reject this step"""
        self.ensure_one()
        self.write({
            'status': 'rejected',
            'decision_date': fields.Date.today(),
            'progress_percentage': 0
        })
    
    def action_reset(self):
        """Reset this step"""
        self.ensure_one()
        self.write({
            'status': 'not_started',
            'start_date': False,
            'submission_date': False,
            'decision_date': False,
            'actual_completion_date': False,
            'progress_percentage': 0
        })
        
        # Update customer record
        if hasattr(self.customer_id, self.step):
            setattr(self.customer_id, self.step, False)
    
    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Tài Liệu Visa'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }
    
    @api.model
    def create_visa_steps_for_customer(self, customer_id):
        """Create all visa process steps for a new customer"""
        customer = self.env['digi.customer.record'].browse(customer_id)
        
        steps_data = [
            {
                'customer_id': customer_id,
                'step': 'checklist',
                'estimated_days': 7,
                'required_documents': 'Passport\nEducation Certificates\nWork Experience\nEnglish Test Results'
            },
            {
                'customer_id': customer_id,
                'step': 'job_offer',
                'estimated_days': 30,
                'required_documents': 'Job Offer Letter\nEmployer Details\nSalary Package\nJob Description'
            },
            {
                'customer_id': customer_id,
                'step': 'lmia',
                'estimated_days': 90,
                'required_documents': 'LMIA Application\nJob Advertisement Proof\nLabour Market Information'
            },
            {
                'customer_id': customer_id,
                'step': 'sa',
                'estimated_days': 60,
                'required_documents': 'Skills Assessment Application\nQualifications\nWork Experience Evidence'
            },
            {
                'customer_id': customer_id,
                'step': 'sbs',
                'estimated_days': 45,
                'required_documents': 'State Nomination Application\nCommitment Statement\nSettlement Funds'
            },
            {
                'customer_id': customer_id,
                'step': 'nomination',
                'estimated_days': 30,
                'required_documents': 'Nomination Application\nSupporting Documents\nState Requirements'
            },
            {
                'customer_id': customer_id,
                'step': 'visa',
                'estimated_days': 120,
                'required_documents': 'Visa Application\nHealth Checks\nCharacter Checks\nAll Supporting Documents'
            }
        ]
        
        created_steps = []
        for step_data in steps_data:
            step = self.create(step_data)
            created_steps.append(step)
        
        # Set up dependencies (each step depends on the previous one)
        for i in range(1, len(created_steps)):
            created_steps[i].depends_on_ids = [(4, created_steps[i-1].id)]
        
        return created_steps
    
    def name_get(self):
        result = []
        for record in self:
            step_name = dict(record._fields['step'].selection)[record.step]
            name = f"{record.customer_id.name} - {step_name}"
            result.append((record.id, name))
        return result


class VisaDocument(models.Model):
    _name = 'digi.visa.document'
    _description = 'Tài Liệu Visa'
    _order = 'visa_process_id, sequence, name'
    
    visa_process_id = fields.Many2one('digi.visa.process', string='Quy Trình Visa', required=True, ondelete='cascade')
    
    name = fields.Char(string='Tên Tài Liệu', required=True)
    description = fields.Text(string='Mô Tả')
    sequence = fields.Integer(string='Thứ Tự', default=10)
    
    document_type = fields.Selection([
        ('passport', 'Hộ Chiếu'),
        ('certificate', 'Chứng Chỉ'),
        ('transcript', 'Bảng Điểm'),
        ('experience', 'Kinh Nghiệm'),
        ('reference', 'Thư Giới Thiệu'),
        ('financial', 'Tài Chính'),
        ('medical', 'Y Tế'),
        ('police', 'Chứng Minh Nhân Dân'),
        ('other', 'Khác')
    ], string='Loại Tài Liệu', required=True)
    
    is_required = fields.Boolean(string='Bắt Buộc', default=True)
    is_submitted = fields.Boolean(string='Đã Nộp', default=False, tracking=True)
    submission_date = fields.Date(string='Ngày Nộp')
    
    # Document Details
    document_number = fields.Char(string='Số Tài Liệu')
    issued_by = fields.Char(string='Cấp Bởi')
    issue_date = fields.Date(string='Ngày Cấp')
    expiry_date = fields.Date(string='Ngày Hết Hạn')
    
    is_valid = fields.Boolean(string='Còn Hiệu Lực', compute='_compute_is_valid', store=True)
    
    # File attachment
    attachment_id = fields.Many2one('ir.attachment', string='Tệp Đính Kèm')
    
    notes = fields.Text(string='Ghi Chú')
    
    @api.depends('expiry_date')
    def _compute_is_valid(self):
        today = fields.Date.today()
        for record in self:
            if record.expiry_date:
                record.is_valid = record.expiry_date >= today
            else:
                record.is_valid = True
    
    def action_mark_submitted(self):
        self.ensure_one()
        self.write({
            'is_submitted': True,
            'submission_date': fields.Date.today()
        })
    
    def action_attach_file(self):
        self.ensure_one()
        return {
            'name': _('Đính Kèm Tài Liệu'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.name,
                'default_res_model': 'digi.visa.document',
                'default_res_id': self.id,
            }
        }