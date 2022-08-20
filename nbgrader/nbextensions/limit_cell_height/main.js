define([
    'base/js/namespace',
    'base/js/events'
    ], function (Jupyter, events) {

    var limit_cell_heights = function() {
        cells = Jupyter.notebook.get_cells();
        console.log(cells)
        for (var i=0; i < cells.length; i++) {
            if (cells[i].metadata.max_height !== undefined) {
                console.log('found max height cell')
                mh = cells[i].metadata.max_height;
                console.log(mh)
                var code = cells[i].element.find(".CodeMirror")[0].CodeMirror;
                console.log(code)
                code.options.fold = true;
                code.setSize(null, mh);
            }
        }
    };
    return {
        load_ipython_extension: limit_cell_heights
    };
});