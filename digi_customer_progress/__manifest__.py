# -*- coding: utf-8 -*-
{
    'name': 'DSS Customer Progress Management',
    'version': '15.0.1.0.0',
    'summary': 'Báo Cáo Tiến Độ Khách Hàng - DSS Group',
    'description': """
        Hệ thống quản lý tiến độ khách hàng toàn diện cho DSS Group
        ================================================================
        
        Tính năng chính:
        * Quản lý thông tin khách hàng đầy đủ
        * Theo dõi tiến độ đào tạo nghề (4 giai đoạn)
        * Quản lý đào tạo tiếng Anh và điểm thi PTE/IELTS
        * Workflow xử lý visa 7 bước
        * Dashboard và báo cáo PDF
        * Hệ thống phân quyền 5 cấp độ
        * Tự động hóa thông báo và báo cáo
        
        Phù hợp cho:
        * Công ty tư vấn du học
        * Trung tâm đào tạo nghề
        * Dịch vụ xử lý visa
    """,
    'category': 'Customer Relationship Management',
    'author': 'DSS Group Development Team',
    'website': 'https://dssgroup.com.au',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'mail',
        'contacts',
        'web',
        'base_setup',
        'web_gantt',
        'web_dashboard',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Master Data
        'data/visa_types.xml',
        'data/job_categories.xml',
        'data/customer_tags.xml',
        'data/sequences.xml',
        
        # Views
        'views/customer_record_views.xml',
        'views/training_progress_views.xml',
        'views/english_training_views.xml',
        'views/visa_process_views.xml',
        'views/visa_type_views.xml',
        'views/customer_tag_views.xml',
        'views/job_category_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
        
        # Reports
        'reports/customer_progress_template.xml',
        
        # Email Templates
        'data/email_templates.xml',
        
        # Cron Jobs
        'data/cron_jobs.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'digi_customer_progress/static/src/css/dashboard.css',
            'digi_customer_progress/static/src/js/dashboard.js',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
    'currency': 'AUD',
}