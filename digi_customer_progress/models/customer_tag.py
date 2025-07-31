# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomerTag(models.Model):
    _name = 'digi.customer.tag'
    _description = 'Thẻ Khách Hàng'
    _order = 'sequence, name'
    
    name = fields.Char(string='Tên Thẻ', required=True, translate=True)
    description = fields.Text(string='Mô Tả')
    color = fields.Integer(string='Màu Sắc', default=0)
    sequence = fields.Integer(string='Thứ Tự', default=10)
    
    category = fields.Selection([
        ('status', 'Trạng Thái'),
        ('priority', 'Ưu Tiên'),
        ('type', 'Loại Khách Hàng'),
        ('source', 'Nguồn'),
        ('special', 'Đặc Biệt'),
    ], string='Danh Mục', required=True, default='status')
    
    active = fields.Boolean(string='Hoạt Động', default=True)
    
    # Statistics
    customer_count = fields.Integer(string='Số Khách Hàng', compute='_compute_customer_count')
    
    @api.depends('customer_ids')
    def _compute_customer_count(self):
        for record in self:
            record.customer_count = len(record.customer_ids)
    
    customer_ids = fields.Many2many('digi.customer.record', 'customer_tag_rel', 
                                   'tag_id', 'customer_id', string='Khách Hàng')
    
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Tên thẻ phải là duy nhất!')
    ]