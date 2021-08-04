odoo.define('usl_office_food.already_receive_meal', function (require) {
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Session = require('web.session');

    var QWeb = core.qweb;
    var g_barcode = null;

    AllReadyMeal = AbstractAction.extend({
     events: {
        "click .o_usl_button_dismiss": function() { this.do_action("test_kiosk_mode"); },
    },
    start: function() {
       var self = this;
       self.$el.html(QWeb.render("EmployeeAlreadyGetMeal", {widget: self}));
    },


    });

    core.action_registry.add('already_receive_meal', AllReadyMeal);

    return AllReadyMeal;





});