# -*- coding: utf-8 -*-

from odoo import models, fields, api


class VisaType(models.Model):
    _name = 'digi.visa.type'
    _description = 'Loại Visa'
    _order = 'country_id, code'
    
    name = fields.Char(string='Tên Visa', required=True, translate=True)
    code = fields.Char(string='Mã Visa', required=True)
    description = fields.Text(string='Mô Tả')
    country_id = fields.Many2one('res.country', string='Quốc Gia', required=True)
    category = fields.Selection([
        ('work', 'Work Visa'),
        ('student', 'Student Visa'),
        ('training', 'Training Visa'),
        ('permanent', 'Permanent Visa'),
        ('temporary', 'Temporary Visa'),
        ('family', 'Family Visa'),
    ], string='Loại', required=True)
    
    duration_months = fields.Integer(string='Thời Hạn (Tháng)')
    renewable = fields.Boolean(string='Có Thể Gia Hạn', default=False)
    processing_time_weeks = fields.Integer(string='Thời Gian Xử Lý (Tuần)')
    
    # Requirements
    english_required = fields.Boolean(string='Yêu Cầu Tiếng Anh', default=True)
    skills_assessment = fields.Boolean(string='Đánh Giá Kỹ Năng', default=False)
    min_age = fields.Integer(string='Tuổi Tối Thiểu')
    max_age = fields.Integer(string='Tuổi Tối Đa')
    
    active = fields.Boolean(string='Hoạt Động', default=True)
    color = fields.Integer(string='Màu Sắc', default=0)
    
    # Statistics
    customer_count = fields.Integer(string='Số Khách Hàng', compute='_compute_customer_count')
    success_rate = fields.Float(string='Tỷ Lệ Thành Công (%)', compute='_compute_success_rate')
    
    @api.depends('customer_ids')
    def _compute_customer_count(self):
        for record in self:
            record.customer_count = len(record.customer_ids)
    
    @api.depends('customer_ids.visa_result')
    def _compute_success_rate(self):
        for record in self:
            customers = record.customer_ids
            if customers:
                granted = customers.filtered(lambda c: c.visa_result == 'granted')
                record.success_rate = (len(granted) / len(customers)) * 100
            else:
                record.success_rate = 0.0
    
    customer_ids = fields.One2many('digi.customer.record', 'visa_type_id', string='Khách Hàng')
    
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            if record.country_id:
                name += f" ({record.country_id.name})"
            result.append((record.id, name))
        return result
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()