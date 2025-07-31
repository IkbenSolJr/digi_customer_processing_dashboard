# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class CustomerRecord(models.Model):
    _name = 'digi.customer.record'
    _description = 'Hồ Sơ Khách Hàng DSS'
    _order = 'customer_code desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    
    # ========== BASIC INFORMATION ==========
    customer_code = fields.Char(
        string='Mã Khách Hàng', 
        required=True, 
        copy=False, 
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    
    name = fields.Char(string='Họ Tên Đầy Đủ', required=True, tracking=True)
    display_name = fields.Char(string='Tên Hiển Thị', compute='_compute_display_name', store=True)
    
    # Personal Information
    date_of_birth = fields.Date(string='Ngày Sinh')
    age = fields.Integer(string='Tuổi', compute='_compute_age')
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới Tính')
    
    phone = fields.Char(string='Số Điện Thoại', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    address = fields.Text(string='Địa Chỉ')
    emergency_contact = fields.Char(string='Liên Hệ Khẩn Cấp')
    
    # ========== VISA INFORMATION ==========
    visa_type_id = fields.Many2one(
        'digi.visa.type', 
        string='Loại Visa', 
        required=True, 
        tracking=True
    )
    
    visa_status = fields.Selection([
        ('active', 'Đang Hoạt Động'),
        ('granted', 'Đã Cấp Visa'),
        ('processing', 'Đang Xử Lý'),
        ('cancelled', 'Đã Hủy'),
        ('refused', 'Bị Từ Chối')
    ], string='Trạng Thái Visa', default='active', required=True, tracking=True)
    
    # ========== STAFF ASSIGNMENT ==========
    advisor_id = fields.Many2one(
        'hr.employee', 
        string='Cố Vấn Viên', 
        domain=[('department_id.name', 'ilike', 'advisor')],
        tracking=True
    )
    
    responsible_person_id = fields.Many2one(
        'hr.employee', 
        string='Người Phụ Trách', 
        tracking=True
    )
    
    trainer_id = fields.Many2one(
        'hr.employee', 
        string='Giảng Viên Đào Tạo',
        domain=[('department_id.name', 'ilike', 'training')],
        tracking=True
    )
    
    teacher_id = fields.Many2one(
        'hr.employee', 
        string='Giáo Viên Tiếng Anh',
        domain=[('department_id.name', 'ilike', 'english')],
        tracking=True
    )
    
    lawyer_id = fields.Many2one(
        'res.partner', 
        string='Luật Sư',
        domain=[('is_company', '=', False), ('category_id.name', 'ilike', 'lawyer')],
        tracking=True
    )
    
    # ========== CONTRACT & JOB ==========
    contract_date = fields.Date(string='Ngày Ký Hợp Đồng', required=True, tracking=True)
    contract_months = fields.Integer(string='Số Tháng Từ Ký HĐ', compute='_compute_contract_months', store=True)
    
    job_category_id = fields.Many2one('digi.job.category', string='Ngành Nghề')
    job_contract = fields.Char(string='Nghề Hợp Đồng', tracking=True)
    job_current = fields.Char(string='Nghề Hiện Tại')
    
    # ========== PRIORITY & TAGS ==========
    priority = fields.Selection([
        ('0', 'Thấp'),
        ('1', 'Bình Thường'),
        ('2', 'Cao'),
        ('3', 'Khẩn Cấp')
    ], string='Độ Ưu Tiên', default='1', tracking=True)
    
    tag_ids = fields.Many2many(
        'digi.customer.tag', 
        'customer_tag_rel', 
        'customer_id', 
        'tag_id', 
        string='Thẻ'
    )
    
    # ========== TRAINING PROGRESS ==========
    theory_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('completed', 'Hoàn Thành'),
        ('waiting', 'Chờ Lịch Thi')
    ], string='Trạng Thái Lý Thuyết', default='not_started', tracking=True)
    
    practical_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('completed', 'Hoàn Thành'),
        ('has_skill', 'Đã Có Kỹ Năng')
    ], string='Trạng Thái Thực Hành', default='not_started', tracking=True)
    
    video_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Quay'),
        ('completed', 'Hoàn Thành'),
        ('approved', 'Đã Duyệt')
    ], string='Trạng Thái Video', default='not_started', tracking=True)
    
    internship_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Thực Tập'),
        ('completed', 'Hoàn Thành'),
        ('failed', 'Thất Bại')
    ], string='Trạng Thái Thực Tập', default='not_started', tracking=True)
    
    # Training Scores
    theory_score = fields.Float(string='Điểm Lý Thuyết', digits=(3, 1))
    practical_score = fields.Float(string='Điểm Thực Hành', digits=(3, 1))
    
    # Training Dates
    training_start_date = fields.Date(string='Ngày Bắt Đầu Đào Tạo')
    training_completion_date = fields.Date(string='Ngày Hoàn Thành Đào Tạo')
    
    # Progress Calculation
    training_progress_percentage = fields.Float(
        string='Tiến Độ Đào Tạo (%)', 
        compute='_compute_training_progress',
        store=True
    )
    
    # ========== ENGLISH TRAINING ==========
    # Course Progress
    beginner_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('completed', 'Hoàn Thành'),
        ('passed', 'Đạt')
    ], string='Beginner', default='not_started')
    
    foundation_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('completed', 'Hoàn Thành'),
        ('passed', 'Đạt')
    ], string='Foundation', default='not_started')
    
    intermediate_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('completed', 'Hoàn Thành'),
        ('passed', 'Đạt')
    ], string='Intermediate', default='not_started')
    
    communication_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('completed', 'Hoàn Thành'),
        ('passed', 'Đạt')
    ], string='Communication', default='not_started')
    
    interview_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('completed', 'Hoàn Thành'),
        ('passed', 'Đạt')
    ], string='Interview', default='not_started')
    
    # Test Scores
    pte_1 = fields.Float(string='PTE Lần 1', digits=(3, 1))
    pte_2 = fields.Float(string='PTE Lần 2', digits=(3, 1))
    ielts_1 = fields.Float(string='IELTS Lần 1', digits=(3, 1))
    ielts_2 = fields.Float(string='IELTS Lần 2', digits=(3, 1))
    
    # Latest Scores
    latest_pte_score = fields.Float(
        string='Điểm PTE Mới Nhất', 
        compute='_compute_latest_scores',
        store=True
    )
    latest_ielts_score = fields.Float(
        string='Điểm IELTS Mới Nhất', 
        compute='_compute_latest_scores',
        store=True
    )
    
    # Overall English Status
    english_overall_status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('testing', 'Đang Thi'),
        ('passed', 'Đã Đạt')
    ], string='Trạng Thái Tiếng Anh', compute='_compute_english_overall_status', store=True)
    
    english_progress_percentage = fields.Float(
        string='Tiến Độ Tiếng Anh (%)', 
        compute='_compute_english_progress',
        store=True
    )
    
    # ========== VISA PROCESS (7 STEPS) ==========
    checklist = fields.Boolean(string='1. Checklist', tracking=True)
    job_offer = fields.Boolean(string='2. Job Offer', tracking=True)
    lmia = fields.Boolean(string='3. LMIA', tracking=True)
    sa = fields.Boolean(string='4. SA', tracking=True)
    sbs = fields.Boolean(string='5. SBS', tracking=True)
    nomination = fields.Boolean(string='6. Nomination', tracking=True)
    visa = fields.Boolean(string='7. Visa', tracking=True)
    
    # Visa Dates
    visa_submit_date = fields.Date(string='Ngày Nộp Visa', tracking=True)
    visa_grant_date = fields.Date(string='Ngày Cấp Visa', tracking=True)
    
    visa_result = fields.Selection([
        ('processing', 'Đang Xử Lý'),
        ('granted', 'Đã Cấp'),
        ('refused', 'Bị Từ Chối')
    ], string='Kết Quả Visa', default='processing', tracking=True)
    
    visa_progress_percentage = fields.Float(
        string='Tiến Độ Visa (%)', 
        compute='_compute_visa_progress',
        store=True
    )
    
    # ========== COMPUTED FIELDS ==========
    overall_progress_percentage = fields.Float(
        string='Tiến Độ Tổng Thể (%)', 
        compute='_compute_overall_progress',
        store=True
    )
    
    # ========== ADDITIONAL FIELDS ==========
    notes = fields.Html(string='Ghi Chú')
    active = fields.Boolean(string='Hoạt Động', default=True)
    color = fields.Integer(string='Màu Sắc', default=0)
    
    # Attachments
    attachment_count = fields.Integer(
        string='Số Tài Liệu', 
        compute='_compute_attachment_count'
    )
    
    @api.model
    def create(self, vals):
        if vals.get('customer_code', _('New')) == _('New'):
            vals['customer_code'] = self.env['ir.sequence'].next_by_code('digi.customer.record') or _('New')
        return super(CustomerRecord, self).create(vals)
    
    @api.depends('name', 'customer_code')
    def _compute_display_name(self):
        for record in self:
            if record.customer_code and record.name:
                record.display_name = f"[{record.customer_code}] {record.name}"
            else:
                record.display_name = record.name or record.customer_code or ''
    
    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                today = datetime.now().date()
                record.age = today.year - record.date_of_birth.year - \
                           ((today.month, today.day) < (record.date_of_birth.month, record.date_of_birth.day))
            else:
                record.age = 0
    
    @api.depends('contract_date')
    def _compute_contract_months(self):
        for record in self:
            if record.contract_date:
                today = datetime.now().date()
                delta = relativedelta(today, record.contract_date)
                record.contract_months = delta.years * 12 + delta.months
            else:
                record.contract_months = 0
    
    @api.depends('theory_status', 'practical_status', 'video_status', 'internship_status')
    def _compute_training_progress(self):
        for record in self:
            total = 0
            # Theory: 25%
            if record.theory_status == 'completed':
                total += 25
            elif record.theory_status == 'in_progress':
                total += 12.5
            
            # Practical: 30%
            if record.practical_status == 'completed':
                total += 30
            elif record.practical_status == 'has_skill':
                total += 30
            elif record.practical_status == 'in_progress':
                total += 15
            
            # Video: 20%
            if record.video_status == 'approved':
                total += 20
            elif record.video_status == 'completed':
                total += 15
            elif record.video_status == 'in_progress':
                total += 10
            
            # Internship: 25%
            if record.internship_status == 'completed':
                total += 25
            elif record.internship_status == 'in_progress':
                total += 12.5
            
            record.training_progress_percentage = total
    
    @api.depends('pte_1', 'pte_2', 'ielts_1', 'ielts_2')
    def _compute_latest_scores(self):
        for record in self:
            # PTE Score
            if record.pte_2:
                record.latest_pte_score = record.pte_2
            elif record.pte_1:
                record.latest_pte_score = record.pte_1
            else:
                record.latest_pte_score = 0.0
            
            # IELTS Score
            if record.ielts_2:
                record.latest_ielts_score = record.ielts_2
            elif record.ielts_1:
                record.latest_ielts_score = record.ielts_1
            else:
                record.latest_ielts_score = 0.0
    
    @api.depends('beginner_status', 'foundation_status', 'intermediate_status', 
                 'communication_status', 'interview_status', 'latest_pte_score', 'latest_ielts_score')
    def _compute_english_overall_status(self):
        for record in self:
            courses = [record.beginner_status, record.foundation_status, record.intermediate_status,
                      record.communication_status, record.interview_status]
            
            if all(status == 'not_started' for status in courses):
                record.english_overall_status = 'not_started'
            elif record.latest_pte_score >= 50 or record.latest_ielts_score >= 6.0:
                record.english_overall_status = 'passed'
            elif record.latest_pte_score > 0 or record.latest_ielts_score > 0:
                record.english_overall_status = 'testing'
            else:
                record.english_overall_status = 'in_progress'
    
    @api.depends('beginner_status', 'foundation_status', 'intermediate_status', 
                 'communication_status', 'interview_status', 'english_overall_status')
    def _compute_english_progress(self):
        for record in self:
            total = 0
            courses = [
                record.beginner_status, record.foundation_status, record.intermediate_status,
                record.communication_status, record.interview_status
            ]
            
            for status in courses:
                if status == 'passed':
                    total += 20
                elif status == 'completed':
                    total += 15
                elif status == 'in_progress':
                    total += 10
            
            record.english_progress_percentage = min(total, 100)
    
    @api.depends('checklist', 'job_offer', 'lmia', 'sa', 'sbs', 'nomination', 'visa')
    def _compute_visa_progress(self):
        for record in self:
            steps = [record.checklist, record.job_offer, record.lmia, 
                    record.sa, record.sbs, record.nomination, record.visa]
            completed_steps = sum(1 for step in steps if step)
            record.visa_progress_percentage = (completed_steps / 7) * 100
    
    @api.depends('training_progress_percentage', 'english_progress_percentage', 'visa_progress_percentage')
    def _compute_overall_progress(self):
        for record in self:
            # Weighted average: Training 40%, English 30%, Visa 30%
            record.overall_progress_percentage = (
                record.training_progress_percentage * 0.4 +
                record.english_progress_percentage * 0.3 +
                record.visa_progress_percentage * 0.3
            )
    
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])
    
    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Tài Liệu'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }
    
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.customer_code}] {record.name}"
            result.append((record.id, name))
        return result