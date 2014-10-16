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

    // wait for the toolbars to appear
    this.waitForSelector(".celltoolbar input");
    this.then(function () {
        var type = this.evaluate(function () {
            return $(".celltoolbar input").attr("type");
        });
        this.test.assertEquals(type, "checkbox", "toolbar activated");
    });

    // does the nbgrader metadata exist?
    this.then(function () {
        var metadata = this.evaluate(function () {
            return IPython.notebook.get_cell(0).metadata.nbgrader;
        });
        this.test.assertEquals(metadata, {}, "nbgrader metadata created");
    });

    // click the "solution?" checkbox
    this.then(function () {
        var solution = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[0]).find("input").click();
            return cell.metadata.nbgrader.solution;
        });
        this.test.assertTrue(solution, "cell is marked as a solution cell");
    });

    // unclick the "solution?" checkbox
    this.then(function () {
        var solution = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[0]).find("input").click();
            return cell.metadata.nbgrader.solution;
        });
        this.test.assertTrue(!solution, "cell is marked as not a solution cell");
    });

    // click the "grade?" checkbox
    this.then(function () {
        var grade = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[1]).find("input").click();
            return cell.metadata.nbgrader.grade;
        });
        this.test.assertTrue(grade, "cell is marked as a grade cell");
    });

    // wait for points/grade_id elements to appear
    this.waitForSelector(".nbgrader-points");
    this.waitForSelector(".nbgrader-id");

    // set the points
    this.then(function () {
        var points = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elem = cell.element.find(".nbgrader-points-input");
            elem.val("2");
            elem.trigger("change");
            return cell.metadata.nbgrader.points;
        });
        this.test.assertEquals(points, "2", "point value changed");
    });

    // set the id
    this.then(function () {
        var id = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elem = cell.element.find(".nbgrader-id-input");
            elem.val("foo");
            elem.trigger("change");
            return cell.metadata.nbgrader.grade_id;
        });
        this.test.assertEquals(id, "foo", "grade id changed");
    });

    // unclick the grade? checkbox
    this.then(function () {
        var metadata = this.evaluate(function () {
            var cell = IPython.notebook.get_cell(0);
            var elems = cell.element.find(".button_container");
            $(elems[1]).find("input").click();
            return cell.metadata.nbgrader;
        });
        this.test.assertTrue(!metadata.grade, "cell is no longer marked as a grade cell");
    });
});
