/*global define, require */
/**
 * To load this extension, add the following to your custom.js:
 *
 * $([IPython.events]).on('app_initialized.NotebookApp', function() {
 *     require(['nbextensions/nbgrader'], function (nbgrader) {
 *         console.log('nbgrader extension loaded');
 *         nbgrader.register(IPython.notebook);
 *     });
 * });
 *
**/

define([
    'base/js/namespace',
    'jquery',
    'notebook/js/celltoolbar',

], function (IPython, $, celltoolbar) {
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
        var local_div = $('<div/>');
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
        $(div).append(local_div.append($('<span/>').append(lbl)));
    };

    /**
     * Create a checkbox to mark whether the cell is a solution cell
     * or not.
     */
    var create_solution_checkbox = function (div, cell, celltoolbar) {
        var local_div = $('<div/>');
        var chkb = $('<input/>').attr('type', 'checkbox');
        var lbl = $('<label/>').append($('<span/>').text("Solution? "));
        lbl.append(chkb);
        chkb.attr("checked", is_solution(cell));
        chkb.click(function () {
            var v = !is_solution(cell);
            cell.metadata.nbgrader.solution = v;
            chkb.attr("checked", v);
        });
        $(div).append(local_div.append($('<span/>').append(lbl)));
    };

    /**
     * Create the input text box for the problem or test id.
     */
    var create_id_input = function (div, cell, celltoolbar) {
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
        var local_div = $('<div/>');
        var text = $('<input/>').attr('type', 'text');
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
     * Create the cell toolbar nbgrader element, which will include
     * different subelements depending on what the nbgrader cell
     * type is.
     */
    var nbgrader = function (div, cell, celltoolbar) {
        var button_container = $(div);
        button_container.addClass('nbgrader-controls');

        // create the metadata dictionary if it doesn't exist
        if (!cell.metadata.nbgrader) {
            cell.metadata.nbgrader = {};
        }

        // grader cells need the id input box and points input box
        if (is_grader(cell)) {
            create_id_input(div, cell, celltoolbar);
            create_points_input(div, cell, celltoolbar);
        }

        // all cells get the grade and solution checkboxes
        create_grader_checkbox(div, cell, celltoolbar);
        create_solution_checkbox(div, cell, celltoolbar);
    };

    /**
     * Load custom css for the nbgrader toolbar.
     */
    var load_css = function () {
        var link = document.createElement('link');
        link.type = 'text/css';
        link.rel = 'stylesheet';
        link.href = '/nbextensions/nbgrader.css';
        console.log(link);
        document.getElementsByTagName('head')[0].appendChild(link);
    };

    /**
     * Load the nbgrader toolbar extension.
     */
    var register = function (notebook) {
        load_css();
        CellToolbar.register_callback('nbgrader.create_assignment', nbgrader);
        CellToolbar.register_preset('Create Assignment', ['nbgrader.create_assignment'], notebook);
        console.log('nbgrader extension for metadata editing loaded.');
    };

    return {
        'register': register
    };
});
