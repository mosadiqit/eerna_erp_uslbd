odoo.define('web.CustomCalendar', function (require) {
"use strict";
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var _t = core._t;
    var WebCalendarController = require('web.CalendarController');
    var ajax = require('web.ajax');

    WebCalendarController.include({
        _onOpenCreate: function (event) {

            if(event.target.model==='employee.meal.reserve' && [5].includes(event.data.start.day())) {
                Dialog.alert(this, _t("You cannot create an reservation for Friday!"));
                return;
            }

//var self = this;
//this._rpc({
//                    model: 'holiday.month.date',
//                    method: 'check_is_holiday',
//                    args: [event.data.start.date(),event.data.start.month(),event.data.start.year()],
//                })
//                .then(function(result) {
//                console.log('hello')
//                console.log(result)
//                    if (result.action) {
//                        self.do_action(result.action);
//                    } else if (result.warning) {
//                        self.do_warn(result.warning);
//                    }
//                });

            return this._super(event);
        },
    });
});