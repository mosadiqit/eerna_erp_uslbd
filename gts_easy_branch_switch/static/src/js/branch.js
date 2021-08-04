odoo.define('gts_easy_branch_switch.SwitchBranchMenu', function(require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');
var rpc = require('web.rpc');

var _t = core._t;

var SwitchBranchMenu = Widget.extend({
    template: 'SwitchBranchMenu',
    events: {
        'click .dropdown-item[data-menu]': '_onClick',
    },
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.isMobile = config.device.isMobile;
        this._onClick = _.debounce(this._onClick, 1500, true);
    },
    /**
     * @override
     */
    willStart: function () {
        return session.user_companies ? this._super() : $.Deferred().reject();
    },
    /**
     * @override
     */
    start: function () {
        var branchList = '';
        if (this.isMobile) {
            branchList = '<li class="bg-info">' +
                _t('Tap on the list to change company') + '</li>';
        }
        else {
            this.$('.oe_topbar_name').text(session.user_companies.allow[1]);
        }


        _.each(session.user_companies.all, function(branch) {
            var a = '';
            if (branch[0] === session.user_companies.allow[0]) {
                a = '<i class="fa fa-check mr8"></i>';
            } else {
                a = '<span style="margin-right: 24px;"/>';
            }
            branchList += '<a role="menuitem" href="#" class="dropdown-item" data-menu="branch" data-branch-id="' +
                            branch[0] + '">' + a + branch[1] + '</a>';


        });
        this.$('.dropdown-menu').html(branchList);
        return this._super();
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onClick: function (ev) {
        ev.preventDefault();
        var branch_id = $(ev.currentTarget).data('branch-id');
        this._rpc({
            model: 'res.users',
            method: 'update_data_user',
            args: [[session.uid], {'branch_id': branch_id}],
        })
        .then(function() {
            location.reload();
        });
    },
});

SystrayMenu.Items.push(SwitchBranchMenu);

return SwitchBranchMenu;

});
