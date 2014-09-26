/*global define*/
/**
 * To load this extension, add the following to your custom.js:
 *
 * IPython.load_extensions('nbgrader');
 *
**/

define([
    'require',
    'jquery',
    'base/js/namespace',
    'notebook/js/celltoolbar',

], function (require, $, IPython, celltoolbar) {
    "use strict";

    var CellToolbar = celltoolbar.CellToolbar;

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
     * Is the cell a grader cell?
     */
    var is_grader = function (cell) {
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
        var grader = is_grader(cell),
            grade_cls = "nbgrader-grade-cell",
            elem = cell.element;

        if (!elem) {
            return;
        }

        if (grader && !elem.hasClass(grade_cls)) {
            elem.addClass(grade_cls);
        } else if (!grader && elem.hasClass(grade_cls)) {
            elem.removeClass(grade_cls);
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
        chkb.attr("checked", is_grader(cell));
        chkb.click(function () {
            cell.metadata.nbgrader.grade = !is_grader(cell);
            celltoolbar.rebuild();
            display_cell(cell);
        });
        display_cell(cell);
        $(div).append($('<span/>').append(lbl));
    };

    /**
     * Create a checkbox to mark whether the cell is a solution cell
     * or not.
     */
    var create_solution_checkbox = function (div, cell, celltoolbar) {
        var chkb = $('<input/>').attr('type', 'checkbox');
        var lbl = $('<label/>').append($('<span/>').text("Solution? "));
        lbl.append(chkb);
        chkb.attr("checked", is_solution(cell));
        chkb.click(function () {
            var v = !is_solution(cell);
            cell.metadata.nbgrader.solution = v;
            chkb.attr("checked", v);
        });
        $(div).append($('<span/>').append(lbl));
    };

    /**
     * Create the input text box for the problem or test id.
     */
    var create_id_input = function (div, cell, celltoolbar) {
        if (!is_grader(cell)) {
            return;
        }

        var local_div = $('<div/>');
        var text = $('<input/>').attr('type', 'text');
        var lbl = $('<label/>').append($('<span/>').text('ID: '));
        lbl.append(text);

        text.addClass('nbgrader-id-input');
        text.attr("value", cell.metadata.nbgrader.grader_id);
        text.keyup(function () {
            cell.metadata.nbgrader.grader_id = text.val();
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
        if (!is_grader(cell)) {
            return;
        }

        var local_div = $('<div/>');
        var text = $('<input/>').attr('type', 'number');
        var lbl = $('<label/>').append($('<span/>').text('Points: '));
        lbl.append(text);

        text.addClass('nbgrader-points-input');
        text.attr("value", cell.metadata.nbgrader.points);
        text.keyup(function () {
            cell.metadata.nbgrader.points = text.val();
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
        console.log(link);
        document.getElementsByTagName('head')[0].appendChild(link);
    };

    /**
     * Load the nbgrader toolbar extension.
     */
    var load_ipython_extension = function () {
        load_css();
        CellToolbar.register_callback('create_assignment.solution_checkbox', create_solution_checkbox); 
        CellToolbar.register_callback('create_assignment.grader_checkbox', create_grader_checkbox);
        CellToolbar.register_callback('create_assignment.id_input', create_id_input);
        CellToolbar.register_callback('create_assignment.points_input', create_points_input);

        var preset = [
            'create_assignment.solution_checkbox',
            'create_assignment.grader_checkbox',
            'create_assignment.points_input',
            'create_assignment.id_input'
        ];
        CellToolbar.register_preset('Create Assignment', preset, IPython.notebook);
        console.log('nbgrader extension for metadata editing loaded.');
    };

    return {
        'load_ipython_extension': load_ipython_extension
    };
});
