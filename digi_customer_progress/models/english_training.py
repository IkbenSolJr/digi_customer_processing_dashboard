# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class EnglishTraining(models.Model):
    _name = 'digi.english.training'
    _description = 'Đào Tạo Tiếng Anh'
    _order = 'customer_id, course_level'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Link to customer
    customer_id = fields.Many2one('digi.customer.record', string='Khách Hàng', required=True, ondelete='cascade')
    
    # Course Information
    course_level = fields.Selection([
        ('beginner', 'Beginner'),
        ('foundation', 'Foundation'),
        ('intermediate', 'Intermediate'),
        ('communication', 'Communication'),
        ('interview', 'Interview Preparation')
    ], string='Khóa Học', required=True)
    
    level_sequence = fields.Integer(string='Thứ Tự Cấp Độ', compute='_compute_level_sequence', store=True)
    
    # Status and Progress
    status = fields.Selection([
        ('not_started', 'Chưa Bắt Đầu'),
        ('in_progress', 'Đang Học'),
        ('completed', 'Hoàn Thành'),
        ('passed', 'Đã Đạt'),
        ('failed', 'Thất Bại')
    ], string='Trạng Thái', default='not_started', required=True, tracking=True)
    
    progress_percentage = fields.Float(string='Tiến Độ (%)', default=0.0, tracking=True)
    
    # Dates
    start_date = fields.Date(string='Ngày Bắt Đầu', tracking=True)
    planned_end_date = fields.Date(string='Ngày Kế Hoạch Kết Thúc')
    actual_end_date = fields.Date(string='Ngày Thực Tế Kết Thúc', tracking=True)
    
    # Course Details
    planned_hours = fields.Float(string='Giờ Kế Hoạch', default=40)
    completed_hours = fields.Float(string='Giờ Đã Học', tracking=True)
    remaining_hours = fields.Float(string='Giờ Còn Lại', compute='_compute_remaining_hours')
    
    # Teacher Assignment
    teacher_id = fields.Many2one('hr.employee', string='Giáo Viên', tracking=True)
    class_schedule = fields.Char(string='Lịch Học')
    classroom = fields.Char(string='Phòng Học')
    
    # Assessment
    midterm_score = fields.Float(string='Điểm Giữa Kỳ', digits=(3, 1))
    final_score = fields.Float(string='Điểm Cuối Kỳ', digits=(3, 1))
    average_score = fields.Float(string='Điểm Trung Bình', compute='_compute_average_score', store=True)
    
    pass_score = fields.Float(string='Điểm Đạt', default=6.0)
    is_passed = fields.Boolean(string='Đã Đạt', compute='_compute_is_passed', store=True)
    
    # Attendance
    total_sessions = fields.Integer(string='Tổng Buổi Học', default=20)
    attended_sessions = fields.Integer(string='Buổi Đã Tham Gia', tracking=True)
    attendance_rate = fields.Float(string='Tỷ Lệ Tham Gia (%)', compute='_compute_attendance_rate', store=True)
    
    # Notes and Feedback
    notes = fields.Html(string='Ghi Chú')
    teacher_feedback = fields.Html(string='Phản Hồi Giáo Viên')
    student_feedback = fields.Html(string='Phản Hồi Học Viên')
    
    # Materials and Resources
    textbook = fields.Char(string='Sách Giáo Khoa')
    online_resources = fields.Text(string='Tài Liệu Online')
    
    # Attachments
    attachment_count = fields.Integer(string='Số Tài Liệu', compute='_compute_attachment_count')
    
    @api.depends('course_level')
    def _compute_level_sequence(self):
        level_order = {
            'beginner': 1,
            'foundation': 2,
            'intermediate': 3,
            'communication': 4,
            'interview': 5
        }
        for record in self:
            record.level_sequence = level_order.get(record.course_level, 0)
    
    @api.depends('planned_hours', 'completed_hours')
    def _compute_remaining_hours(self):
        for record in self:
            record.remaining_hours = record.planned_hours - record.completed_hours
    
    @api.depends('midterm_score', 'final_score')
    def _compute_average_score(self):
        for record in self:
            if record.midterm_score and record.final_score:
                record.average_score = (record.midterm_score + record.final_score) / 2
            elif record.final_score:
                record.average_score = record.final_score
            elif record.midterm_score:
                record.average_score = record.midterm_score
            else:
                record.average_score = 0.0
    
    @api.depends('average_score', 'pass_score')
    def _compute_is_passed(self):
        for record in self:
            record.is_passed = record.average_score >= record.pass_score if record.average_score > 0 else False
    
    @api.depends('attended_sessions', 'total_sessions')
    def _compute_attendance_rate(self):
        for record in self:
            if record.total_sessions > 0:
                record.attendance_rate = (record.attended_sessions / record.total_sessions) * 100
            else:
                record.attendance_rate = 0.0
    
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])
    
    def action_start_course(self):
        """Start the English course"""
        self.ensure_one()
        self.write({
            'status': 'in_progress',
            'start_date': fields.Date.today(),
            'progress_percentage': 10
        })
        
        # Update customer record
        if self.course_level == 'beginner':
            self.customer_id.beginner_status = 'in_progress'
        elif self.course_level == 'foundation':
            self.customer_id.foundation_status = 'in_progress'
        elif self.course_level == 'intermediate':
            self.customer_id.intermediate_status = 'in_progress'
        elif self.course_level == 'communication':
            self.customer_id.communication_status = 'in_progress'
        elif self.course_level == 'interview':
            self.customer_id.interview_status = 'in_progress'
    
    def action_complete_course(self):
        """Complete the English course"""
        self.ensure_one()
        status = 'passed' if self.is_passed else 'completed'
        
        self.write({
            'status': status,
            'actual_end_date': fields.Date.today(),
            'progress_percentage': 100
        })
        
        # Update customer record
        if self.course_level == 'beginner':
            self.customer_id.beginner_status = status
        elif self.course_level == 'foundation':
            self.customer_id.foundation_status = status
        elif self.course_level == 'intermediate':
            self.customer_id.intermediate_status = status
        elif self.course_level == 'communication':
            self.customer_id.communication_status = status
        elif self.course_level == 'interview':
            self.customer_id.interview_status = status
    
    def action_record_attendance(self):
        """Record attendance for a session"""
        self.ensure_one()
        if self.attended_sessions < self.total_sessions:
            self.attended_sessions += 1
            
            # Update progress based on attendance
            if self.total_sessions > 0:
                progress = (self.attended_sessions / self.total_sessions) * 80  # 80% for attendance, 20% for tests
                self.progress_percentage = min(progress, 80)
    
    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Tài Liệu Tiếng Anh'),
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
    def create_english_courses_for_customer(self, customer_id):
        """Create all English courses for a new customer"""
        courses_data = [
            {
                'customer_id': customer_id,
                'course_level': 'beginner',
                'planned_hours': 40,
                'total_sessions': 20,
                'pass_score': 5.0
            },
            {
                'customer_id': customer_id,
                'course_level': 'foundation',
                'planned_hours': 60,
                'total_sessions': 30,
                'pass_score': 6.0
            },
            {
                'customer_id': customer_id,
                'course_level': 'intermediate',
                'planned_hours': 80,
                'total_sessions': 40,
                'pass_score': 6.5
            },
            {
                'customer_id': customer_id,
                'course_level': 'communication',
                'planned_hours': 40,
                'total_sessions': 20,
                'pass_score': 7.0
            },
            {
                'customer_id': customer_id,
                'course_level': 'interview',
                'planned_hours': 30,
                'total_sessions': 15,
                'pass_score': 7.5
            }
        ]
        
        created_courses = []
        for course_data in courses_data:
            course = self.create(course_data)
            created_courses.append(course)
        
        return created_courses
    
    def name_get(self):
        result = []
        for record in self:
            level_name = dict(record._fields['course_level'].selection)[record.course_level]
            name = f"{record.customer_id.name} - {level_name}"
            result.append((record.id, name))
        return result


class EnglishTestScore(models.Model):
    _name = 'digi.english.test.score'
    _description = 'Điểm Thi Tiếng Anh'
    _order = 'customer_id, test_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Link to customer
    customer_id = fields.Many2one('digi.customer.record', string='Khách Hàng', required=True, ondelete='cascade')
    
    # Test Information
    test_type = fields.Selection([
        ('pte', 'PTE Academic'),
        ('ielts', 'IELTS')
    ], string='Loại Thi', required=True)
    
    test_date = fields.Date(string='Ngày Thi', required=True, tracking=True)
    test_center = fields.Char(string='Trung Tâm Thi')
    
    # Scores
    overall_score = fields.Float(string='Điểm Tổng', digits=(3, 1), required=True, tracking=True)
    listening_score = fields.Float(string='Listening', digits=(3, 1))
    reading_score = fields.Float(string='Reading', digits=(3, 1))
    writing_score = fields.Float(string='Writing', digits=(3, 1))
    speaking_score = fields.Float(string='Speaking', digits=(3, 1))
    
    # Target and Result
    target_score = fields.Float(string='Điểm Mục Tiêu', digits=(3, 1), default=50.0)
    is_target_achieved = fields.Boolean(string='Đạt Mục Tiêu', compute='_compute_is_target_achieved', store=True)
    
    # Preparation
    preparation_course_id = fields.Many2one('digi.english.training', string='Khóa Chuẩn Bị')
    preparation_hours = fields.Float(string='Giờ Chuẩn Bị')
    
    # Result Details
    certificate_number = fields.Char(string='Số Chứng Chỉ')
    valid_until = fields.Date(string='Có Hiệu Lực Đến')
    is_valid = fields.Boolean(string='Còn Hiệu Lực', compute='_compute_is_valid', store=True)
    
    # Notes
    notes = fields.Html(string='Ghi Chú')
    
    # Attachments (certificate, score report)
    attachment_count = fields.Integer(string='Số Tài Liệu', compute='_compute_attachment_count')
    
    @api.depends('overall_score', 'target_score')
    def _compute_is_target_achieved(self):
        for record in self:
            record.is_target_achieved = record.overall_score >= record.target_score
    
    @api.depends('valid_until')
    def _compute_is_valid(self):
        today = fields.Date.today()
        for record in self:
            record.is_valid = record.valid_until >= today if record.valid_until else True
    
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])
    
    @api.model
    def create(self, vals):
        record = super(EnglishTestScore, self).create(vals)
        
        # Update customer's test scores
        customer = record.customer_id
        if record.test_type == 'pte':
            if not customer.pte_1:
                customer.pte_1 = record.overall_score
            else:
                customer.pte_2 = record.overall_score
        elif record.test_type == 'ielts':
            if not customer.ielts_1:
                customer.ielts_1 = record.overall_score
            else:
                customer.ielts_2 = record.overall_score
        
        return record
    
    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Chứng Chỉ & Bảng Điểm'),
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
            test_type = dict(record._fields['test_type'].selection)[record.test_type]
            name = f"{record.customer_id.name} - {test_type} ({record.overall_score})"
            result.append((record.id, name))
        return result