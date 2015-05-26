/*global $, Backbone, student, submission_id */

var Grade = Backbone.Model.extend({
    urlRoot: base_url + "/api/grade",
    initialize: function () {
        var elem = $("#" + this.get("name"));
        var glyph = $("#" + this.get("name") + "-saved");
        elem.val(this.get("manual_score"));
        elem.attr("placeholder", this.get("auto_score"));

        var that = this;
        $("#" + this.get("name") + "-full-credit").click(function () {
            elem.val(that.get("max_score"));
            elem.trigger("change");
            elem.select();
            elem.focus();
        });
        $("#" + this.get("name") + "-no-credit").click(function () {
            elem.val(0);
            elem.trigger("change");
            elem.select();
            elem.focus();
        });
        elem.on("change", function (evt) {
            console.log("Saving score " + that.get("name"));

            if (elem.val() === "") {
                that.set("manual_score", null);
            } else {
                var val = elem.val();
                var max_score = that.get("max_score");
                if (val > max_score) {
                    invalidValue(elem);
                    that.set("manual_score", max_score);
                } else if (val < 0) {
                    invalidValue(elem);
                    that.set("manual_score", 0);
                } else {
                    that.set("manual_score", val);
                }
            }

            elem.val(that.get("manual_score"));
            glyph.removeClass("glyphicon-ok");
            glyph.addClass("glyphicon-refresh");
            glyph.fadeIn(10);

            that.save("manual_score", that.get("manual_score"), {
                success: function () {
                    glyph.removeClass("glyphicon-refresh");
                    glyph.addClass("glyphicon-ok");
                    setTimeout(function () {
                        glyph.fadeOut();
                    }, 1000);
                    console.log("Finished saving score " + that.get("name"));
                    $(document).trigger("finished_saving");
                }
            });
        });
    }
});

var Grades = Backbone.Collection.extend({
    model: Grade,
    url: base_url + "/api/grades"
});

var Comment = Backbone.Model.extend({
    urlRoot: base_url + "/api/comment",
    initialize: function () {
        var elem = $($(".comment")[this.get("name")]);
        var glyph = $($(".comment-saved")[this.get("name")]);
        elem.val(this.get("comment"));

        var that = this;
        elem.on("change", function (evt) {
            console.log("Saving comment " + that.get("name"));
            that.set("comment", elem.val());

            glyph.removeClass("glyphicon-ok");
            glyph.addClass("glyphicon-refresh");
            glyph.fadeIn(10);

            that.save("comment", that.get("comment"), {
                success: function () {
                    glyph.removeClass("glyphicon-refresh");
                    glyph.addClass("glyphicon-ok");
                    setTimeout(function () {
                        glyph.fadeOut();
                    }, 1000);
                    console.log("Finished saving comment " + that.get("name"));
                    $(document).trigger("finished_saving");
                }
            });
        });
    }
});

var Comments = Backbone.Collection.extend({
    model: Comment,
    url: base_url + "/api/comments"
});

var getIndex = function (elem) {
    if (elem !== undefined) {
        var elems = $("input, textarea");
        return elems.index(elem);
    } else {
        return parseInt(document.URL.split('#')[1]) || 0;
    }
};

var selectNext = function (target, shift) {
    var index, elems;
    elems = $("input, textarea");
    if (shift) {
        index = getIndex(target) - 1;
    } else {
        index = getIndex(target) + 1;
    }
    if (index === elems.length) {
        index = 0;
    } else if (index === -1) {
        index = elems.length - 1;
    }
    $(elems[index]).select();
    $(elems[index]).focus();
};

var scrollTo = function (elem) {
    var target = elem.parents(".nbgrader_cell");
    return target.offset().top - $(window).height() * 0.33 + 60;
};

var invalidValue = function (elem) {
    elem.animate({
        "background-color": "#FF8888",
        "border-color": "red"
    }, 100, undefined, function () {
        setTimeout(function () {
            elem.animate({
                "background-color": "white",
                "border-color": "white"
            }, 100);
        }, 50);
    });
};

var grades;
var grades_loaded = false;
var comments;
var comments_loaded = false;
var last_selected;

var nextAssignment = function () {
    window.location = base_url + '/submissions/' + submission_id + '/next' + "#" + getIndex(last_selected);
};

var nextIncorrectAssignment = function () {
    window.location = base_url + '/submissions/' + submission_id + '/next_incorrect' + "#" + getIndex(last_selected);
};

var prevAssignment = function () {
    window.location = base_url + '/submissions/' + submission_id + '/prev' + "#" + getIndex(last_selected);
};

var prevIncorrectAssignment = function () {
    window.location = base_url + '/submissions/' + submission_id + '/prev_incorrect' + "#" + getIndex(last_selected);
};

var save_and_navigate = function(callback) {
    elem = document.activeElement;
    if (elem.tagName === "INPUT" || elem.tagName === "TEXTAREA") {
        $(document).on("finished_saving", callback);
        $(elem).blur();
        $(elem).trigger("change");
    } else {
        callback();
    }
};

$(window).load(function () {
    grades = new Grades();
    grades.fetch({
        data: {
            submission_id: submission_id
        },
        success: function () {
            grades_loaded = true;
        }
    });

    comments = new Comments();
    comments.fetch({
        data: {
            submission_id: submission_id
        },
        success: function () {
            comments_loaded = true;
        }
    });

    $("li.previous a").tooltip({container: 'body'});
    $("li.next a").tooltip({container: 'body'});
    $("li.live-notebook a").tooltip({container: 'body'});

    // disable link selection on tabs
    $('a').attr('tabindex', '-1');

    $("input, textarea").on('keydown', function(e) {
        var keyCode = e.keyCode || e.which;

        if (keyCode === 9) { // tab
            e.preventDefault();
            e.stopPropagation();
            selectNext(e.currentTarget, e.shiftKey);

        } else if (keyCode === 27) { // escape
            $(e.currentTarget).blur();
        }
    });

    $("body").on('keydown', function(e) {
        var keyCode = e.keyCode || e.which;
        var href;
        var elem;

        if (keyCode === 9) { // tab
            e.preventDefault();
            selectNext(last_selected, e.shiftKey);
        } else if (keyCode === 13) { // enter
            if (last_selected[0] !== document.activeElement) {
                $("body, html").scrollTop(scrollTo(last_selected));
                MathJax.Hub.Startup.signal.Interest(function (message) {
                    if (message === "End") {
                        last_selected.select();
                        last_selected.focus();
                    }
                });
            }
        } else if (keyCode == 39 && e.shiftKey && e.ctrlKey) { // shift + control + right arrow
            save_and_navigate(nextIncorrectAssignment);
        } else if (keyCode == 37 && e.shiftKey && e.ctrlKey) { // shift + control + left arrow
            save_and_navigate(prevIncorrectAssignment);
        } else if (keyCode == 39 && e.shiftKey) { // shift + right arrow
            save_and_navigate(nextAssignment);
        } else if (keyCode == 37 && e.shiftKey) { // shift + left arrow
            save_and_navigate(prevAssignment);
        }
    });

    $("input, textarea").focus(function (event) {
        last_selected = $(event.currentTarget);
        $("body, html").stop().animate({
            scrollTop: scrollTo(last_selected)
        }, 500);
    });

    var index = parseInt(document.URL.split('#')[1]) || 0;
    if (index < 0) { index = 0; }

    if ($("input, textarea").length > index) {
        last_selected = $($("input, textarea")[index]);
        last_selected.select();
        last_selected.focus();
    }
});
