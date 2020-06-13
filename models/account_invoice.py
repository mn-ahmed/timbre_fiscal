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

t1 = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize",
      "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
t2 = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt",
      "quatre-vingt dix"]


def tradd(num):
    ch = ''
    if num == 0:
        ch = ''
    elif num < 20:
        ch = t1[num]
    elif num >= 20:
        if (num >= 70 and num <= 79) or (num >= 90):
            z = int(num / 10) - 1
        else:
            z = int(num / 10)
        ch = t2[z]
        num = num - z * 10
        if (num == 1 or num == 11) and z <= 9:
            ch = ch + ' et'
        if num > 0:
            ch = ch + ' ' + tradd(num)
        else:
            ch = ch + tradd(num)
    return ch

def tradn(num):
    ch = ''
    flagcent = False
    if num >= 1000000000:
        z = int(num / 1000000000)
        ch = ch + tradn(z) + ' milliard'
        if z > 1:
            ch = ch + 's'
        num = num - z * 1000000000
    if num >= 1000000:
        z = int(num / 1000000)
        ch = ch + tradn(z) + ' million'
        if z > 1:
            ch = ch + 's'
        num = num - z * 1000000
    if num >= 1000:
        if num >= 100000:
            z = int(num / 100000)
            if z > 1:
                ch = ch + ' ' + tradd(z)
            ch = ch + ' cent'
            flagcent = True
            num = num - z * 100000
            if int(num / 1000) == 0 and z > 1:
                ch = ch + 's'
        if num >= 1000:
            z = int(num / 1000)
            if (z == 1 and flagcent) or z > 1:
                ch = ch + ' ' + tradd(z)
            num = num - z * 1000
        ch = ch + ' mille'
    if num >= 100:
        z = int(num / 100)
        if z > 1:
            ch = ch + ' ' + tradd(z)
        ch = ch + " cent"
        num = num - z * 100
        if num == 0 and z > 1:
            ch = ch + 's'
    if num > 0:
        ch = ch + " " + tradd(num)
    return ch

def amount_to_text(nb, unite="Dinar", decim="Millime"):
    nb = round(nb, 3)
    z1 = int(nb)
    z3 = (nb - z1) * 1000
    z2 = int(round(z3, 0))
    if z1 == 0:
        ch = "zéro"
    else:
        ch = tradn(abs(z1))
    if z1 > 1 or z1 < -1:
        if unite != '':
            ch = ch + " " + unite + 's'
    else:
        ch = ch + " " + unite
    if z2 > 0:
        ch = ch + tradn(z2)
        if z2 > 1 or z2 < -1:
            if decim != '':
                ch = ch + " " + decim + 's'
        else:
            ch = ch + " " + decim
    if nb < 0:
        ch = "moins " + ch
    return ch.capitalize()

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

