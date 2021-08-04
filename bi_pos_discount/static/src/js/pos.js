// bi_pos_discount js
odoo.define('bi_pos_discount.pos', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var popups = require('point_of_sale.popups');
	var QWeb = core.qweb;
	var utils = require('web.utils');
	var round_pr = utils.round_precision;
	var _t = core._t;

	// exports.Order = Backbone.Model.extend ...
	var OrderSuper = models.Order;
	models.Order = models.Order.extend({
	
		get_fixed_discount: function() {
			var total=0.0;
			var i;
			for(i=0;i<this.orderlines.models.length;i++) 
			{	
				console.log(i,"----4-----------------",this.orderlines.models[i])
				total = total + Math.min(Math.max(parseFloat(this.orderlines.models[i].discount * this.orderlines.models[i].quantity) || 0, 0),10000);
			}
			return total
		},
		
	});
	// End Order start


	// exports.Orderline = Backbone.Model.extend ...
	var OrderlineSuper = models.Orderline;
	models.Orderline = models.Orderline.extend({
	

		set_discount: function(discount){
			if (this.pos.config.discount_type == 'percentage')
			{
				var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
			}
			if (this.pos.config.discount_type == 'fixed')
			{
				var disc = discount;
			}
			this.discount = disc;
			this.discountStr = '' + disc;
			this.trigger('change',this);
		},
	

		get_base_price:    function(){
			var rounding = this.pos.currency.rounding;
			if (this.pos.config.discount_type == 'percentage')
			{
				return round_pr(this.get_unit_price() * this.get_quantity() * (1 - this.get_discount()/100), rounding);
			}
			if (this.pos.config.discount_type == 'fixed')
			{
				return round_pr((this.get_unit_price()- this.get_discount())* this.get_quantity(), rounding);	
			}
		},
		
		get_all_prices: function(){
			
			if (this.pos.config.discount_type == 'percentage')
			{
				var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
			}
			if (this.pos.config.discount_type == 'fixed')
			{
				// var price_unit = this.get_unit_price() - this.get_discount();
				var price_unit = this.get_base_price()/this.get_quantity();		
			}	
			var taxtotal = 0;

			var product =  this.get_product();
			var taxes_ids = product.taxes_id;
			var taxes =  this.pos.taxes;
			var taxdetail = {};
			var product_taxes = [];

			_(taxes_ids).each(function(el){
				product_taxes.push(_.detect(taxes, function(t){
					return t.id === el;
				}));
			});

			var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
			_(all_taxes.taxes).each(function(tax) {
				taxtotal += tax.amount;
				taxdetail[tax.id] = tax.amount;
			});

			return {
				"priceWithTax": all_taxes.total_included,
				"priceWithoutTax": all_taxes.total_excluded,
				"tax": taxtotal,
				"taxDetails": taxdetail,
			};
		},

		get_display_price_one: function(){
			var rounding = this.pos.currency.rounding;
			var price_unit = this.get_unit_price();
			if (this.pos.config.iface_tax_included !== 'total') {
				if (this.pos.config.discount_type == 'percentage')
				{
					return round_pr(price_unit * (1.0 - (this.get_discount() / 100.0)), rounding);
				}
				if (this.pos.config.discount_type == 'fixed')
				{
					return round_pr(price_unit  - this.get_discount(), rounding);
				}	
			} else {
				var product =  this.get_product();
				var taxes_ids = product.taxes_id;
				var taxes =  this.pos.taxes;
				var product_taxes = [];

				_(taxes_ids).each(function(el){
					product_taxes.push(_.detect(taxes, function(t){
						return t.id === el;
					}));
				});

				var all_taxes = this.compute_all(product_taxes, price_unit, 1, this.pos.currency.rounding);
				if (this.pos.config.discount_type == 'percentage')
				{
					return round_pr(all_taxes.total_included * (1 - this.get_discount()/100), rounding);
				}
				if (this.pos.config.discount_type == 'fixed')
				{
					return round_pr(all_taxes.total_included  - this.get_discount(), rounding);
				}	
			}
	},
		
	});
	// End Orderline start
		
	
	
});
