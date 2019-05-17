# -*- coding: utf-8 -*-

from odoo import models, fields, api
from openerp.exceptions import UserError, RedirectWarning, ValidationError

class AddClaseProduct(models.Model):

	_name = 'class.product'

	clase = fields.Char( string = 'Clase' )

	_rec_name = 'clase'

class AddPresentationProduct(models.Model):

	_name = 'presentation.product'

	presentation = fields.Char( string = 'Presentación' )

	_rec_name = 'presentation'

class AddCodeTypeContainerProduct(models.Model):

	_name = 'typecontainer.product'

	code = fields.Char( string = 'Cod. Tipo de envase' )
	
	_rec_name = 'code'

class AddTasteProduct(models.Model):

	_name = 'taste.product'

	taste = fields.Char( string = 'Sabor' )

	_rec_name = 'taste'

class AddCodeBrandProduct(models.Model):

	_name = 'brand.product'

	brand = fields.Char( string = 'Código de marca' )

	_rec_name = 'brand'

class AddCampsProductPage(models.Model):

	_inherit = 'product.template'

	#-- Relación para agregar clases al producto
	clase_prod = fields.Many2one( 'class.product' , string = 'Clase' )
	
	#-- Relación para agregar una presentación al producto
	presentation_prod = fields.Many2one( 'presentation.product' , string = 'Presentación' )

	#-- Relación para gregar un código al envase del producto 
	code_container_prod = fields.Many2one( 'typecontainer.product' , string = 'Cod. Tipo de envase' )

	# -- Relación para agregar un sabor al producto 
	taste_product = fields.Many2one( 'taste.product' , string = 'Sabor' )

	# -- Relación para gregar un código a la marca del producto
	brand_product = fields.Many2one( 'brand.product' , string = 'Código de marca' )

class AddRateAddressDelivery(models.Model):

	_inherit = 'res.partner'

	rate_address = fields.Many2one( 'product.pricelist', string = 'Tarifa' )

	most_ieps = fields.Boolean( string = 'Mostrar IEPS' )

class OnchangeDirectionFacture(models.Model):

	_inherit = 'sale.order'

	@api.onchange('partner_shipping_id')
	def changeDirFac(self):
		if self.partner_shipping_id:
			self.pricelist_id = self.partner_shipping_id.rate_address.id

class ChangeFunctionAmount(models.Model):

	_inherit = 'account.invoice'				

	@api.one
	@api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
		'currency_id', 'company_id', 'date_invoice', 'type')

	def _compute_amount(self):
		
		round_curr = self.currency_id.round
		self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)

		if self.partner_id.most_ieps == True:
			self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
		else:
			for l in self.tax_line_ids:
				for n in l.tax_id:	
					for f in n.tag_ids:
						if f.name == 'IEPS':
							rest = round_curr(l.amount)
							self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids) - rest
							self.l10n_mx_edi_origin = l.amount_total
						else:
							rest = 2
							self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)

		self.amount_total = self.amount_untaxed + self.amount_tax
		amount_total_company_signed = self.amount_total
		amount_untaxed_signed = self.amount_untaxed
		if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
			currency_id = self.currency_id
			amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
			amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
		sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
		self.amount_total_company_signed = amount_total_company_signed * sign
		self.amount_total_signed = self.amount_total * sign
		self.amount_untaxed_signed = amount_untaxed_signed * sign

class IepsInvoiceLine(models.Model):

	_inherit = 'account.invoice.line'

	@api.onchange('invoice_line_tax_ids')
	def ChangeTax(self):
		if self.invoice_id.partner_id.most_ieps == False:
			for lines in self.invoice_id.invoice_line_ids:
				for tag in self.invoice_line_tax_ids:
					if tag.tag_ids.name == 'IEPS':
						value_prod = lines.product_id.lst_price
						percentaje = tag.amount
						operation = ( value_prod * percentaje ) / 100
						self.price_unit = value_prod + operation