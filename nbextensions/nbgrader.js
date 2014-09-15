/*global define, require */
/**
 * To load this extension, add the following to your custom.js:
 *
 * $([IPython.events]).on('app_initialized.NotebookApp', function() {
 *     require(['nbextensions/nbgrader'], function (nbgrader) {
 *         console.log('nbgrader extension loaded');
 *         nbgrader.register(IPython.notebook);
 *         // Optional: uncomment this line if you always want to display
 *         // the notebook based on the nbgrader metadata, even if the
 *         // toolbar isn't activated. This has the effect of coloring
 *         // gradeable and autograder cells.
 *         //nbgrader.display(IPython.notebook);
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
     * Get the nbgrader cell type. Default is "-".
     */
    var get_cell_type = function (cell) {
        if (cell.metadata.nbgrader === undefined) {
            return '';
        } else {
            return cell.metadata.nbgrader.cell_type;
        }
    };

    /**
     * Add a display class to the cell element, depending on the
     * nbgrader cell type.
     */
    var display_cell_type = function (cell) {
        var cell_type = get_cell_type(cell),
            grade_cls = "nbgrader-gradeable-cell",
            test_cls = "nbgrader-autograder-cell",
            elem = cell.element;

        if (!elem) {
            return;
        }

        if (cell_type === "grade" && !elem.hasClass(grade_cls)) {
            elem.addClass(grade_cls);
        } else if (cell_type !== "grade" && elem.hasClass(grade_cls)) {
            elem.removeClass(grade_cls);
        }

        if (cell_type === "autograder" && !elem.hasClass(test_cls)) {
            elem.addClass(test_cls);
            if (IPython.notebook.metadata.hide_autograder_cells) {
                elem.hide();
            }
        } else if (cell_type !== "autograder" && elem.hasClass(test_cls)) {
            elem.removeClass(test_cls);
        }
    };

    /**
     * Create a select drop down menu for the nbgrader cell type. On
     * change, this rebuilds the cell toolbar so that other elements
     * may (possibly) be displayed -- for example, "grade" cells need
     * input text boxes for the problem id and points.
     */
    var create_type_select = function (div, cell, celltoolbar) {
        var list_list = [
            ['-'             , ''          ],
            ['To be graded'  , 'grade'     ],
            ['Release only'  , 'release'   ],
            ['Solution only' , 'solution'  ],
            ['Skip'          , 'skip'      ],
            ['Autograder'    , 'autograder'],
        ];

        var local_div = $('<div/>');
        var select = $('<select/>');
        for(var i=0; i < list_list.length; i++){
            var opt = $('<option/>')
                    .attr('value', list_list[i][1])
                    .text(list_list[i][0]);
            select.append(opt);
        }

        select.addClass('nbgrader-type-select');
        select.val(get_cell_type(cell));
        select.change(function () {
            cell.metadata.nbgrader.cell_type = select.val();
            celltoolbar.rebuild();
            display_cell_type(cell);
        });

        local_div.addClass('nbgrader-type');
        $(div).append(local_div.append($('<span/>').append(select)));
    };

    /**
     * Create the input text box for the problem or test id.
     */
    var create_id_input = function (div, cell, celltoolbar) {
        var local_div = $('<div/>');
        var text = $('<input/>').attr('type', 'text');
        var lbl;
        if (get_cell_type(cell) === 'grade') {
            lbl = $('<label/>').append($('<span/>').text('Problem ID: '));
        } else {
            lbl = $('<label/>').append($('<span/>').text('Test name: '));
        }
        lbl.append(text);

        text.addClass('nbgrader-id-input');
        text.attr("value", cell.metadata.nbgrader.id);
        text.keyup(function () {
            cell.metadata.nbgrader.id = text.val();
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
     * Create the input text box for the autograder test weight.
     */
    var create_weight_input = function (div, cell, celltoolbar) {
        var local_div = $('<div/>');
        var text = $('<input/>').attr('type', 'text');
        var lbl = $('<label/>').append($('<span/>').text('Weight: '));
        lbl.append(text);

        text.addClass('nbgrader-weight-input');
        text.attr("value", cell.metadata.nbgrader.weight);
        text.keyup(function () {
            cell.metadata.nbgrader.weight = text.val();
        });

        local_div.addClass('nbgrader-weight');
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

        var cell_type = get_cell_type(cell);

        if (cell_type === 'grade') {
            // grade cells need the id input box and points input box
            create_id_input(div, cell, celltoolbar);
            create_points_input(div, cell, celltoolbar);
            
        } else if (cell_type === 'autograder') {
            // autograder cells need the id input box and weight input box
            create_id_input(div, cell, celltoolbar);
            create_weight_input(div, cell, celltoolbar);
        }

        // all cells get the cell type dropdown menu
        create_type_select(div, cell, celltoolbar);
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

        var metadata = IPython.notebook.metadata;
        if (!metadata.disable_nbgrader_toolbar) {
            CellToolbar.register_callback('nbgrader.create_assignment', nbgrader);
            CellToolbar.register_preset('Create Assignment', ['nbgrader.create_assignment'], notebook);
            console.log('nbgrader extension for metadata editing loaded.');
        }
    };

    /**
     * Display cells appropriately depending on whether they're
     * gradeable, etc.
     */
    var display = function (notebook) {
        var cells = notebook.get_cells();
        for (var i = 0; i < cells.length; i++) {
            display_cell_type(cells[i]);
        }
    };

    return {
        'register': register,
        'display': display
    };
});
