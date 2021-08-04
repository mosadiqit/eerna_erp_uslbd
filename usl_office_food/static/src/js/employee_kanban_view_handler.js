
odoo.define('usl_office_food.employee_kanban_view_handler', function(require) {
"use strict";

var KanbanRecord = require('web.KanbanRecord');

KanbanRecord.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _openRecord: function () {
    var self = this;
        if (this.modelName === 'hr.employee' && this.$el.parents('.o_usl_attendance_kanban').length) {

        var employee_id = self.record.id.raw_value;


                this._rpc({
                model: 'hr.employee',
                method: 'meal_eat_manual',
                args: [employee_id ],
            })
            .then(function (result) {
//            console.log('barcode')
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_action(result.warning);

                }
            }, function () {

            });
                                            // needed to diffentiate : check in/out kanban view of employees <-> standard employee kanban view

        } else {
            this._super.apply(this, arguments);
        }
    }
});

});
