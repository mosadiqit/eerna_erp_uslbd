odoo.define('usl_office_food.kiosk_mode', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var Session = require('web.session');

var QWeb = core.qweb;
var g_barcode = null;

var KioskModeTest = AbstractAction.extend({

    events: {
     "click .o_hr_attendance_button_employee_new": function() {
            this.do_action('usl_office_food.usl_hr_employee_attendance_action_kanban_n', {
                additional_context: {'no_group_by': true},
            });
        },
        "click .o_hr_attendance_button_apply": function() {
        var self = this;

        console.log(g_barcode)
                this._rpc({
                model: 'hr.employee',
                method: 'meal_eat_scan',
                args: [g_barcode, ],
            })
            .then(function (result) {
//            console.log('barcode')
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_action(result.warning);
                    core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
                }
            }, function () {
                core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
            });

        },
    },

    start: function () {
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        self.session = Session;
        var def = this._rpc({
                model: 'res.company',
                method: 'search_read',
                args: [[['id', '=', this.session.company_id]], ['name']],
            })
            .then(function (companies){

                self.company_name = companies[0].name;
                self.company_image_url = self.session.url('/web/image', {model: 'res.company', id: self.session.company_id, field: 'logo',});
                self.$el.html(QWeb.render("HrAttendanceKioskMode", {widget: self}));
                self.start_clock();
            });
        // Make a RPC call every day to keep the session alive
        self._interval = window.setInterval(this._callServer.bind(this), (60*60*1000*24));
        return Promise.all([def, this._super.apply(this, arguments)]);
    },

    _onBarcodeScanned: function(barcode) {
        var self = this;
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        g_barcode = barcode;
         var def = this._rpc({
                model: 'hr.employee',
                method: 'employee_from_barcode',
                args: [barcode,],
            })
            .then(function (employee){
            console.log(typeof employee.name)
            if(employee.name){
                self.name = employee.name;
                self.company_image_url = self.session.url('/web/image', {model: 'hr.employee', id: employee.id, field: 'image_1920',});
                self.$el.html(QWeb.render("OpenEmployeeView", {widget: self}));
            }
            else{
            self.do_action("already_receive_meal")
            }


//
            });


//        this._rpc({
//                model: 'hr.employee',
//                method: 'meal_eat_scan',
//                args: [barcode, ],
//            })
//            .then(function (result) {
////            console.log('barcode')
//                if (result.action) {
//                    self.do_action(result.action);
//                } else if (result.warning) {
//                    self.do_warn(result.warning);
//                    core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
//                }
//            }, function () {
//                core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
//            });
    },

    start_clock: function() {
        this.clock_start = setInterval(function() {this.$(".o_hr_attendance_clock").text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit', second:'2-digit'}));}, 500);
        // First clock refresh before interval to avoid delay
        this.$(".o_hr_attendance_clock").show().text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit', second:'2-digit'}));
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        clearInterval(this.clock_start);
        clearInterval(this._interval);
        this._super.apply(this, arguments);
    },

    _callServer: function () {
        // Make a call to the database to avoid the auto close of the session
        return ajax.rpc("/employee_eat/kiosk_keepalive", {});
    },

});

core.action_registry.add('test_kiosk_mode', KioskModeTest);

return KioskModeTest;

});
