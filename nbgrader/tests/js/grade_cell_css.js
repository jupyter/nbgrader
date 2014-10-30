casper.notebook_test(function () {
    // load the extension
    this.thenEvaluate(function () {
        IPython.load_extensions('nbgrader');
    });
    this.wait(1000);

    // select the extension
    this.thenEvaluate(function () {
        $("#ctb_select").val("Create Assignment");
        $("#ctb_select").trigger("change");
    });

    // click the "grade?" checkbox
    this.then(function () {
        var grade = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[2]).find("input").click();
            return cell.metadata.nbgrader.grade;
        });
        this.test.assertTrue(grade, "cell is marked as a grade cell");
    });

    // check that the nbgrader css class was added
    this.then(function () {
        this.test.assertExists(".nbgrader-grade-cell");
    });

    // unclick the grade? checkbox
    this.then(function () {
        var metadata = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[2]).find("input").click();
            return cell.metadata.nbgrader;
        });
        this.test.assertTrue(!metadata.grade, "cell is no longer marked as a grade cell");
    });

    // check that the nbgrader css class was removed
    this.then(function () {
        this.test.assertNotExists(".nbgrader-grade-cell");
    });

    // click the "grade?" checkbox
    this.then(function () {
        var grade = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[2]).find("input").click();
            return cell.metadata.nbgrader.grade;
        });
        this.test.assertTrue(grade, "cell is marked as a grade cell");
    });

    // check that the nbgrader css class was added 
    this.then(function () {
        this.test.assertExists(".nbgrader-grade-cell");
    });

    // deselect the extension
    this.thenEvaluate(function () {
        $("#ctb_select").val("");
        $("#ctb_select").trigger("change");
    });

    // check that the nbgrader css class was removed
    this.then(function () {
        this.test.assertNotExists(".nbgrader-grade-cell");
    });

    // select the extension
    this.thenEvaluate(function () {
        $("#ctb_select").val("Create Assignment");
        $("#ctb_select").trigger("change");
    });

    // check that the nbgrader css class was added
    this.then(function () {
        this.test.assertExists(".nbgrader-grade-cell");
    });

    // select a different extension
    this.thenEvaluate(function () {
        $("#ctb_select").val("Edit Metadata");
        $("#ctb_select").trigger("change");
    });

    // check that the nbgrader css class was removed
    this.then(function () {
        this.test.assertNotExists(".nbgrader-grade-cell");
    });
});
