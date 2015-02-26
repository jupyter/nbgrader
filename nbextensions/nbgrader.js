/*global define*/
/**
 * To load this extension, add the following to your custom.js:
 *
 * require(['base/js/events'], function (events) {
 *     events.on('app_initialized.NotebookApp', function() {
 *         IPython.load_extensions('nbgrader');
 *     });
 * });
 *
**/

define([
    'require',
    'jquery',
    'base/js/namespace',
    'base/js/dialog',
    'notebook/js/celltoolbar',
    'base/js/events'

], function (require, $, IPython, dialog, celltoolbar, events) {
    "use strict";

    var nbgrader_preset_name = "Create Assignment";
    var grade_cls = "nbgrader-grade-cell";
    var total_points = 0;
    var warning;

    var CellToolbar = celltoolbar.CellToolbar;

    // trigger an event when the toolbar is being rebuilt
    CellToolbar.prototype._rebuild = CellToolbar.prototype.rebuild;
    CellToolbar.prototype.rebuild = function () {
        events.trigger('toolbar_rebuild.CellToolbar', this.cell);
        this._rebuild();
    };

    // trigger an event when the toolbar is being (globally) hidden
    CellToolbar._global_hide = CellToolbar.global_hide;
    CellToolbar.global_hide = function () {
        $("#nbgrader-total-points-group").hide();
        total_points = 0;

        CellToolbar._global_hide();
        for (var i=0; i < CellToolbar._instances.length; i++) {
            events.trigger('global_hide.CellToolbar', CellToolbar._instances[i].cell);
        }
    };

    // show the total points when the preset is activated
    events.on('preset_activated.CellToolbar', function(evt, preset) {
        var elem = $("#nbgrader-total-points-group");
        if (preset.name === nbgrader_preset_name) {
            if (elem.length == 0) {
                elem = $("<div />").attr("id", "nbgrader-total-points-group");
                elem.addClass("btn-group");
                elem.append($("<span />").text("Total points:"));
                elem.append($("<input />")
                            .attr("disabled", "disabled")
                            .attr("type", "number")
                            .attr("id", "nbgrader-total-points"));
                $("#maintoolbar-container").append(elem);
            }
            elem.show();
            update_total();
        } else {
            elem.hide();
            total_points = 0;
        }
    });

    // remove nbgrader class when the cell is either hidden or rebuilt
    events.on("global_hide.CellToolbar toolbar_rebuild.CellToolbar", function (evt, cell) {
        if (cell.element && cell.element.hasClass(grade_cls)) {
            if (is_grade(cell)) {
                total_points -= to_float(cell.metadata.nbgrader.points);
                update_total();
            }
            cell.element.removeClass(grade_cls);
        }
    });

    var to_float = function(val) {
        if (val === undefined || val === "") {
            return 0;
        }
        return parseFloat(val);
    };

    var update_total = function() {
        $("#nbgrader-total-points").attr("value", total_points);
    };

    var validate_ids = function() {
        var elems, set, i, label;

        if (warning !== undefined) {
            return;
        }

        elems = $(".nbgrader-id-input");
        set = new Object();
        for (i = 0; i < elems.length; i++) {
            label = $(elems[i]).val();
            if (label in set) {
                warning = dialog.modal({
                    notebook: IPython.notebook,
                    keyboard_manager: IPython.keyboard_manager,
                    title: "Duplicate grade cell ID",
                    body: "The ID \"" + label + "\" has been used for more than one grade cell. This will cause nbgrader to break! Please make sure all grade cells have unique ids.",
                    buttons: {
                        OK: {
                            class: "btn-primary",
                            click: function () {
                                warning = undefined;
                            }
                        }
                    }
                });
            } else {
                set[label] = true;
            }
        }
    };

    /**
     * Is the cell a solution cell?
     */
    var is_solution = function (cell) {
        if (cell.metadata.nbgrader === undefined) {
            cell.metadata.nbgrader = {};
            return false;
        } else if (cell.metadata.nbgrader.solution === undefined) {
            return false;
        } else {
            return cell.metadata.nbgrader.solution;
        }
    };

    /**
     * Is the cell a grade cell?
     */
    var is_grade = function (cell) {
        if (cell.metadata.nbgrader === undefined) {
            cell.metadata.nbgrader = {};
            return false;
        } else if (cell.metadata.nbgrader.grade === undefined) {
            return false;
        } else {
            return cell.metadata.nbgrader.grade;
        }
    };

    /**
     * Add a display class to the cell element, depending on the
     * nbgrader cell type.
     */
    var display_cell = function (cell) {
        if (cell.element && is_grade(cell) && !cell.element.hasClass(grade_cls)) {
            cell.element.addClass(grade_cls);
        }
    };

    /**
     * Create a checkbox to mark whether the cell is a grader cell or
     * not.
     */
    var create_grader_checkbox = function (div, cell, celltoolbar) {
        var chkb = $('<input/>').attr('type', 'checkbox');
        var lbl = $('<label/>').append($('<span/>').text("Grade? "));
        lbl.append(chkb);
        chkb.attr("checked", is_grade(cell));
        chkb.click(function () {
            if (is_grade(cell)) {
                total_points -= to_float(cell.metadata.nbgrader.points);
                update_total();
            }
            cell.metadata.nbgrader.grade = !is_grade(cell);
            celltoolbar.rebuild();
            display_cell(cell);
            validate_ids();
        });
        display_cell(cell);
        $(div).append($('<span/>').append(lbl));
    };

    /**
     * Create a checkbox to mark whether the cell is a solution cell
     * or not.
     */
    var create_solution_checkbox = CellToolbar.utils.checkbox_ui_generator(
        "Solution? ",
        function (cell, val) {
            cell.metadata.nbgrader.solution = val;
        },
        is_solution);

    /**
     * Create the input text box for the problem or test id.
     */
    var create_id_input = function (div, cell, celltoolbar) {
        if (!is_grade(cell)) {
            return;
        }

        var local_div = $('<div/>');
        var text = $('<input/>').attr('type', 'text');
        var lbl = $('<label/>').append($('<span/>').text('ID: '));
        lbl.append(text);

        text.addClass('nbgrader-id-input');
        text.attr("value", cell.metadata.nbgrader.grade_id);
        validate_ids();
        text.change(function () {
            cell.metadata.nbgrader.grade_id = text.val();
            validate_ids();
        });
                
        local_div.addClass('nbgrader-id');
        $(div).append(local_div.append($('<span/>').append(lbl)));

        IPython.keyboard_manager.register_events(text);
    };

    /**
     * Create the input text box for the number of points the problem
     * is worth.
     */
    var create_points_input = function (div, cell, celltoolbar) {
        if (!is_grade(cell)) {
            return;
        }

        var local_div = $('<div/>');
        var text = $('<input/>').attr('type', 'number');
        var lbl = $('<label/>').append($('<span/>').text('Points: '));
        lbl.append(text);

        text.addClass('nbgrader-points-input');
        text.attr("value", cell.metadata.nbgrader.points);
        total_points += to_float(cell.metadata.nbgrader.points);
        update_total();

        text.change(function () {
            total_points -= to_float(cell.metadata.nbgrader.points);
            cell.metadata.nbgrader.points = to_float(text.val());
            text.val(cell.metadata.nbgrader.points);
            total_points += to_float(cell.metadata.nbgrader.points);
            update_total();
        });

        local_div.addClass('nbgrader-points');
        $(div).append(local_div.append($('<span/>').append(lbl)));

        IPython.keyboard_manager.register_events(text);
    };

    /**
     * Load custom css for the nbgrader toolbar.
     */
    var load_css = function () {
        var link = document.createElement('link');
        link.type = 'text/css';
        link.rel = 'stylesheet';
        link.href = require.toUrl('./nbgrader.css');
        document.getElementsByTagName('head')[0].appendChild(link);
    };

    /**
     * Load the nbgrader toolbar extension.
     */
    var load_extension = function () {
        load_css();
        CellToolbar.register_callback('create_assignment.solution_checkbox', create_solution_checkbox); 
        CellToolbar.register_callback('create_assignment.grader_checkbox', create_grader_checkbox);
        CellToolbar.register_callback('create_assignment.id_input', create_id_input);
        CellToolbar.register_callback('create_assignment.points_input', create_points_input);
        
        var preset = [
            'create_assignment.id_input',
            'create_assignment.points_input',
            'create_assignment.grader_checkbox',
            'create_assignment.solution_checkbox'
        ];
        CellToolbar.register_preset(nbgrader_preset_name, preset, IPython.notebook);
        console.log('nbgrader extension for metadata editing loaded.');
    };

    return {
        'load_ipython_extension': load_extension
    };
});
