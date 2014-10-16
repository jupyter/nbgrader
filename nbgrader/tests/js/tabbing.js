// make sure it's possible to tab between the grade_id and points
// input fields
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

    // click in the id field
    this.then(function () {
        var focused = this.evaluate(function () {
            $(".nbgrader-id-input").focus();
            return document.activeElement === $(".nbgrader-id-input")[0];
        });
        this.test.assertTrue(focused, "id input has focus");
    });

    // press tab
    this.then(function () {
        this.sendKeys('.nbgrader-id-input', casper.page.event.key.Tab, {keepFocus: true});
        var focused = this.evaluate(function () {
            return document.activeElement === $(".nbgrader-points-input")[0];
        });
        this.test.assertTrue(focused, "points input has focus");
    });
});
