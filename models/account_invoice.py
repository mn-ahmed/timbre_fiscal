# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (http://tiny.be). All Rights Reserved
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################


from odoo import fields, api, models, _
from odoo.addons import decimal_precision as dp

class TmAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line_ids', 'invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'invoice_line_ids.product_id')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.discount = sum((line.quantity * line.price_unit * line.discount) / 100 for line in self.invoice_line_ids)
        timbre = '0.0'
        tax = sum(line.amount_total for line in self.tax_line_ids)
        for line in self.invoice_line_ids:
            if line.product_id.timbre_fiscal:
                tax = sum(line.amount_total for line in self.tax_line_ids) - 0.6
                timbre = '0.600'
            self.amount_tax = tax
            self.timbre = timbre
        self.amount_total = self.amount_untaxed + self.amount_tax + self.timbre
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id,
                                                               self.company_id,
                                                               self.date_invoice or fields.Date.today())
            amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id,
                                                         self.company_id, self.date_invoice or fields.Date.today())
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.one
    @api.depends('invoice_line_ids', 'amount_untaxed', 'discount')
    def compute_total_before_discount(self):
        total = 0
        for line in self.invoice_line_ids:
            total += line.price_subtotal
        self.total_before_discount = self.amount_untaxed + self.discount  # sum((line.quantity * line.price_unit * line.discount)/100 for line in self.invoice_line_ids)

    discount = fields.Monetary(string='Discount', digits=dp.get_precision('Product Price'), default=0.0, compute='_compute_amount',
                               track_visibility='always')
    total_before_discount = fields.Monetary(string='Total Before Discount', digits=dp.get_precision('Product Price'),
                                            compute='compute_total_before_discount')
    timbre = fields.Float(string='Timbre fiscal', readonly=True, digits=dp.get_precision('Product Price'), compute='_compute_amount',
                          track_visibility='always')  # store=True, compute='computeçtax', track_visibility='always'
    amount_tax = fields.Monetary(string='TVA', readonly=True, compute='_compute_amount', track_visibility='always')

    @api.multi
    def button_dummy(self):
        self.set_lines_discount()
        return True


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.one
    @api.depends('quantity', 'price_unit')
    def compute_line_price(self):
        self.subtotal_price = self.quantity * self.price_unit

    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('discount'), default=0.0)
    subtotal_price = fields.Float(string='Montant', digits=dp.get_precision('Product Price'), store=True, compute='compute_line_price')

