# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Timbre Fiscal ",
    'summary': """Tunisia based Stamp""",
    'description': """
        This module adds a functionality for Tunisia Invoice like stamp ...
    """,
    'license': 'AGPL-3',
    'author': "	AHMED MNASRI",
    'website': "",
    'category': 'Accounting',
    'version': '12.0.0.2.0',
    'depends': [
        'account',
        'l10n_tn',
        'sale'
    ],
    'data': [
        'views/invoice_view.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/num_to_word_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,


}
