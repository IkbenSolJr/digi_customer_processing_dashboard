# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class TrainingProgress(models.Model):
    _name = 'digi.training.progress'
    _description = 'Tiến Độ Đào Tạo'
    _order = 'customer_id, stage_sequence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Link to customer
    customer_id = fields.Many2one('digi.customer.record', string='Khách Hàng', required=True, ondelete='cascade')
    
    # Training Stage
    stage = fields.Selection([
        ('theory', 'Lý Thuyết'),
        ('practical', 'Thực Hành'),
        ('video', 'Video'),
        ('internship', 'Thực Tập')
    ], string='Giai Đoạn', required=True)
    
    stage_sequence = fields.Integer(string='Thứ Tự Giai Đoạn', compute='_compute_stage_sequence', store=True)
    
    # Status and Progress
    status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Thực Hiện'),
        ('completed', 'Hoàn Thành'),
        ('failed', 'Thất Bại'),
        ('waiting', 'Chờ Đợi'),
        ('approved', 'Đã Duyệt')
    ], string='Trạng Thái', default='not_started', required=True, tracking=True)
    
    progress_percentage = fields.Float(string='Tiến Độ (%)', default=0.0, tracking=True)
    
    # Dates
    start_date = fields.Date(string='Ngày Bắt Đầu', tracking=True)
    planned_end_date = fields.Date(string='Ngày Kế Hoạch Kết Thúc')
    actual_end_date = fields.Date(string='Ngày Thực Tế Kết Thúc', tracking=True)
    
    # Duration tracking
    planned_hours = fields.Float(string='Giờ Kế Hoạch')
    actual_hours = fields.Float(string='Giờ Thực Tế', tracking=True)
    remaining_hours = fields.Float(string='Giờ Còn Lại', compute='_compute_remaining_hours')
    
    # Performance
    score = fields.Float(string='Điểm', digits=(3, 1), tracking=True)
    grade = fields.Selection([
        ('A', 'Xuất Sắc (8.5-10)'),
        ('B', 'Giỏi (7.0-8.4)'),
        ('C', 'Khá (5.5-6.9)'),
        ('D', 'Trung Bình (4.0-5.4)'),
        ('F', 'Yếu (<4.0)')
    ], string='Xếp Loại', compute='_compute_grade', store=True)
    
    # Staff Assignment
    trainer_id = fields.Many2one('hr.employee', string='Giảng Viên', tracking=True)
    supervisor_id = fields.Many2one('hr.employee', string='Giám Sát Viên')
    
    # Training Details
    location = fields.Char(string='Địa Điểm')
    equipment_needed = fields.Text(string='Thiết Bị Cần Thiết')
    materials = fields.Text(string='Tài Liệu')
    
    # Assessment
    assessment_method = fields.Selection([
        ('test', 'Kiểm Tra Viết'),
        ('practical', 'Thực Hành'),
        ('project', 'Dự Án'),
        ('presentation', 'Thuyết Trình'),
        ('portfolio', 'Hồ Sơ')
    ], string='Phương Pháp Đánh Giá')
    
    assessment_date = fields.Date(string='Ngày Đánh Giá')
    pass_criteria = fields.Float(string='Điểm Đạt', default=5.0)
    is_passed = fields.Boolean(string='Đã Đạt', compute='_compute_is_passed', store=True)
    
    # Notes and Feedback
    notes = fields.Html(string='Ghi Chú')
    feedback = fields.Html(string='Phản Hồi Từ Giảng Viên')
    student_feedback = fields.Html(string='Phản Hồi Từ Học Viên')
    
    # Attachments
    attachment_count = fields.Integer(string='Số Tài Liệu', compute='_compute_attachment_count')
    
    # Dependencies
    depends_on_ids = fields.Many2many(
        'digi.training.progress', 
        'training_dependency_rel', 
        'dependent_id', 
        'prerequisite_id',
        string='Phụ Thuộc Vào'
    )
    
    blocking_ids = fields.Many2many(
        'digi.training.progress', 
        'training_dependency_rel', 
        'prerequisite_id', 
        'dependent_id',
        string='Đang Chặn'
    )
    
    can_start = fields.Boolean(string='Có Thể Bắt Đầu', compute='_compute_can_start')
    
    @api.depends('stage')
    def _compute_stage_sequence(self):
        stage_order = {'theory': 1, 'practical': 2, 'video': 3, 'internship': 4}
        for record in self:
            record.stage_sequence = stage_order.get(record.stage, 0)
    
    @api.depends('planned_hours', 'actual_hours')
    def _compute_remaining_hours(self):
        for record in self:
            record.remaining_hours = record.planned_hours - record.actual_hours
    
    @api.depends('score')
    def _compute_grade(self):
        for record in self:
            if record.score >= 8.5:
                record.grade = 'A'
            elif record.score >= 7.0:
                record.grade = 'B'
            elif record.score >= 5.5:
                record.grade = 'C'
            elif record.score >= 4.0:
                record.grade = 'D'
            elif record.score > 0:
                record.grade = 'F'
            else:
                record.grade = False
    
    @api.depends('score', 'pass_criteria')
    def _compute_is_passed(self):
        for record in self:
            record.is_passed = record.score >= record.pass_criteria if record.score > 0 else False
    
    @api.depends('depends_on_ids.status')
    def _compute_can_start(self):
        for record in self:
            prerequisites = record.depends_on_ids
            if prerequisites:
                record.can_start = all(prereq.status == 'completed' for prereq in prerequisites)
            else:
                record.can_start = True
    
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])
    
    def action_start(self):
        """Start the training stage"""
        self.ensure_one()
        if not self.can_start:
            raise UserError(_('Không thể bắt đầu vì chưa hoàn thành các điều kiện tiên quyết.'))
        
        self.write({
            'status': 'in_progress',
            'start_date': fields.Date.today(),
            'progress_percentage': 10
        })
        
        # Update customer record
        if self.stage == 'theory':
            self.customer_id.theory_status = 'in_progress'
        elif self.stage == 'practical':
            self.customer_id.practical_status = 'in_progress'
        elif self.stage == 'video':
            self.customer_id.video_status = 'in_progress'
        elif self.stage == 'internship':
            self.customer_id.internship_status = 'in_progress'
    
    def action_complete(self):
        """Complete the training stage"""
        self.ensure_one()
        self.write({
            'status': 'completed',
            'actual_end_date': fields.Date.today(),
            'progress_percentage': 100
        })
        
        # Update customer record
        if self.stage == 'theory':
            self.customer_id.theory_status = 'completed'
        elif self.stage == 'practical':
            self.customer_id.practical_status = 'completed'
        elif self.stage == 'video':
            self.customer_id.video_status = 'completed'
        elif self.stage == 'internship':
            self.customer_id.internship_status = 'completed'
    
    def action_reset(self):
        """Reset the training stage"""
        self.ensure_one()
        self.write({
            'status': 'not_started',
            'start_date': False,
            'actual_end_date': False,
            'progress_percentage': 0,
            'score': 0
        })
    
    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Tài Liệu Đào Tạo'),
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
    def create_training_stages_for_customer(self, customer_id):
        """Create all training stages for a new customer"""
        customer = self.env['digi.customer.record'].browse(customer_id)
        job_category = customer.job_category_id
        
        stages_data = [
            {
                'customer_id': customer_id,
                'stage': 'theory',
                'planned_hours': job_category.theory_hours if job_category else 40,
                'pass_criteria': 5.0,
                'assessment_method': 'test'
            },
            {
                'customer_id': customer_id,
                'stage': 'practical',
                'planned_hours': job_category.practical_hours if job_category else 120,
                'pass_criteria': 6.0,
                'assessment_method': 'practical'
            },
            {
                'customer_id': customer_id,
                'stage': 'video',
                'planned_hours': job_category.video_hours if job_category else 20,
                'pass_criteria': 7.0,
                'assessment_method': 'presentation'
            },
            {
                'customer_id': customer_id,
                'stage': 'internship',
                'planned_hours': (job_category.internship_weeks * 40) if job_category else 160,
                'pass_criteria': 6.0,
                'assessment_method': 'portfolio'
            }
        ]
        
        # Create dependencies
        created_stages = []
        for stage_data in stages_data:
            stage = self.create(stage_data)
            created_stages.append(stage)
        
        # Set up dependencies (theory -> practical -> video -> internship)
        for i in range(1, len(created_stages)):
            created_stages[i].depends_on_ids = [(4, created_stages[i-1].id)]
        
        return created_stages
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.customer_id.name} - {dict(record._fields['stage'].selection)[record.stage]}"
            result.append((record.id, name))
        return result