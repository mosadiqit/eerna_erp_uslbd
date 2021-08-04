openerp.web_slider_widget=function(instance,module)
{
	var QWeb = instance.web.qweb;
	var _t = instance.web._t;

	instance.web.form.widgets = instance.web.form.widgets.extend(
	{
		'slider' : 'instance.web.form.RangeSlider',
	});
    	    
    instance.web.form.RangeSlider = instance.web.form.AbstractField.extend(
	{
        template: 'RangeSlider',
        
        start: function() 
        {
        	var self=this;
        	
            this.on("change:effective_readonly", this, this.check_readonly);
            this.check_readonly.call(this);
            
        	this._super.apply(this, arguments);
        	this.check_readonly.call(this);
       },
       
       check_readonly: function() 
       {
    	    var self=this;
			_.defaults(self.options,
						{
							range:false,
							color: "blue",
							min_val:0,
							max_val:500,
							lower_val:0,
							upper_val:500,
							text_before:"",
							separator:" - ",
							text_after:"",
							orientation:"horizontal",
							step:1,
						});

			var options=self.options;
			var range=false;
			if (options.range=='min')
				range='min';
			else if (options.range=='max')
				range='max';
			else if (options.range=='range' || range==true)
				range=true;
			
			var color=options.color;
			var min_val=parseInt(options.min_val);
			var max_val=parseInt(options.max_val);
			var text_before=options.text_before;
			var separator=options.separator;
			var text_after=options.text_after;
			var orientation=options.orientation;
			var step=options.step;
			self.$("div#slider-range .ui-slider-range").css({"background":color});

			if (range=='min' || range=='max' || range==false)
			{
				var values = self.view.datarecord[self.name];
				var value=min_val;
				if(values && typeof values=='string')
					value = values.substr(0, values.indexOf(',')) || values;
				if (isNaN(value))
					value=min_val;
				self.$("span#amount_value").text(text_before + value + text_after);
				self.$("div#slider-range").slider(
				{
					disabled: self.get("effective_readonly"),
					range: range,
					orientation:orientation,
					min: min_val,
					max: max_val,
					step:step,
					value:value,
					slide: function(event, ui) 
					{
						self.internal_set_value(ui.value);
						self.$("span#amount_value").text(text_before + ui.value + text_after);
				    }
				});
			}
			if (range==true)
			{
				var values = self.view.datarecord[self.name];
				var lower_val=min_val;
				var upper_val=max_val;
				if(values && typeof values=='string')
					lower_val = values.substr(0, values.indexOf(',')); 
					upper_val = values.substr(values.indexOf(',')+1); 
				if (isNaN(lower_val))
					lower_val=min_val;
				if (isNaN(upper_val))
					upper_val=max_val;
				self.$("span#amount_value").text( text_before + lower_val + separator + upper_val + text_after);
				self.$("div#slider-range").slider(
				{
					disabled: self.get("effective_readonly"),
					range: true,
					orientation:orientation,
					min: min_val,
					max: max_val,
					step:step,
					values: [lower_val, upper_val ],
					slide: function( event, ui ) 
					{
						self.internal_set_value(ui.values[0]+","+ui.values[1]);
						self.$("span#amount_value").text( text_before + ui.values[0]+separator+ui.values[1]+text_after);
				    }
				});
			}
       },
	});
}