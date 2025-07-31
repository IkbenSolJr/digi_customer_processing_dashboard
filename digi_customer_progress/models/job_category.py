# -*- coding: utf-8 -*-

from odoo import models, fields, api


class JobCategory(models.Model):
    _name = 'digi.job.category'
    _description = 'Ngành Nghề'
    _order = 'sequence, name'
    
    name = fields.Char(string='Tên Ngành Nghề', required=True, translate=True)
    code = fields.Char(string='Mã Ngành', required=True)
    description = fields.Text(string='Mô Tả')
    
    # Training Details
    theory_hours = fields.Integer(string='Giờ Lý Thuyết', default=40)
    practical_hours = fields.Integer(string='Giờ Thực Hành', default=120)
    video_hours = fields.Integer(string='Giờ Video', default=20)
    internship_weeks = fields.Integer(string='Tuần Thực Tập', default=4)
    
    # Requirements
    english_level_required = fields.Selection([
        ('beginner', 'Beginner'),
        ('foundation', 'Foundation'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], string='Trình Độ Tiếng Anh Yêu Cầu', default='foundation')
    
    min_pte_score = fields.Float(string='Điểm PTE Tối Thiểu', default=30.0)
    min_ielts_score = fields.Float(string='Điểm IELTS Tối Thiểu', default=5.0)
    
    # Skills Assessment
    assessing_authority = fields.Char(string='Cơ Quan Đánh Giá Kỹ Năng')
    assessment_duration_weeks = fields.Integer(string='Thời Gian Đánh Giá (Tuần)', default=12)
    
    sequence = fields.Integer(string='Thứ Tự', default=10)
    active = fields.Boolean(string='Hoạt Động', default=True)
    color = fields.Integer(string='Màu Sắc', default=0)
    
    # Statistics
    customer_count = fields.Integer(string='Số Khách Hàng', compute='_compute_customer_count')
    avg_completion_days = fields.Float(string='Thời Gian Hoàn Thành TB (Ngày)', compute='_compute_avg_completion')
    
    @api.depends('customer_ids')
    def _compute_customer_count(self):
        for record in self:
            record.customer_count = len(record.customer_ids.filtered(lambda c: c.job_contract == record.name))
    
    @api.depends('customer_ids.training_completion_date')
    def _compute_avg_completion(self):
        for record in self:
            customers = record.customer_ids.filtered(
                lambda c: c.job_contract == record.name and c.training_completion_date
            )
            if customers:
                total_days = sum(
                    (c.training_completion_date - c.contract_date).days 
                    for c in customers if c.contract_date
                )
                record.avg_completion_days = total_days / len(customers)
            else:
                record.avg_completion_days = 0.0
    
    customer_ids = fields.One2many('digi.customer.record', 'job_category_id', string='Khách Hàng')
    
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Mã ngành nghề phải là duy nhất!'),
        ('name_unique', 'UNIQUE(name)', 'Tên ngành nghề phải là duy nhất!')
    ]