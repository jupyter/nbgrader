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
        var elems = $(".tabbable");
        return elems.index(elem);
    } else {
        return parseInt(getParameterByName(index)) || 0;
    }
};

var getSelectableIndex = function (elem) {
    var target = elem.parents(".nbgrader_cell").find(".score");
    if (target.length == 0) {
        return getIndex(elem);
    } else {
        return getIndex(target);
    }
};

var selectNext = function (target, shift) {
    var index, elems;
    elems = $(".tabbable");
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
    if (target.length == 0) {
        return $("body").offset().top;
    } else {
        return target.offset().top - $(window).height() * 0.33 + 60;
    }
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

var getParameterByName = function (name) {
    // http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
};

var grades;
var grades_loaded = false;
var comments;
var comments_loaded = false;
var last_selected;
var current_index = 0;
var loaded = false;

var nextAssignment = function () {
    window.location = base_url + '/submissions/' + submission_id + '/next' + "?index=" + current_index;
};

var nextIncorrectAssignment = function () {
    window.location = base_url + '/submissions/' + submission_id + '/next_incorrect' + "?index=" + current_index;
};

var prevAssignment = function () {
    window.location = base_url + '/submissions/' + submission_id + '/prev' + "?index=" + current_index;
};

var prevIncorrectAssignment = function () {
    window.location = base_url + '/submissions/' + submission_id + '/prev_incorrect' + "?index=" + current_index;
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
    $('a:not(.tabbable)').attr('tabindex', '-1');

    register_handler(".tabbable", "TAB", function (e) {
        e.preventDefault();
        e.stopPropagation();
        selectNext(e.currentTarget, e.shiftKey);
    });

    register_handler(".tabbable", "ESCAPE", function (e) {
        $(e.currentTarget).blur();
    });

    register_handler("body", "TAB", function (e) {
        e.preventDefault();
        selectNext(last_selected, e.shiftKey);
    });

    register_handler("body", "ENTER", function (e) {
        if (last_selected[0] !== document.activeElement) {
            $("body, html").scrollTop(scrollTo(last_selected));
            last_selected.select();
            last_selected.focus();
        }
    });

    register_handler("body", "RIGHT_ARROW", function (e) {
        if (e.shiftKey && e.ctrlKey) {
            save_and_navigate(nextIncorrectAssignment);
        } else if (e.shiftKey) {
            save_and_navigate(nextAssignment);
        }
    });

    register_handler("body", "LEFT_ARROW", function (e) {
        if (e.shiftKey && e.ctrlKey) {
            save_and_navigate(prevIncorrectAssignment);
        } else if (e.shiftKey) {
            save_and_navigate(prevAssignment);
        }
    });

    $(".tabbable").focus(function (event) {
        last_selected = $(event.currentTarget);
        current_index = getSelectableIndex(last_selected);
        $("body, html").stop().animate({
            scrollTop: scrollTo(last_selected)
        }, 500);
    });

    current_index = parseInt(getParameterByName('index')) || 0;
    if (current_index < 0) { current_index = 0; }

    if ($(".tabbable").length > current_index) {
        last_selected = $($(".tabbable")[current_index]);
        MathJax.Hub.Startup.signal.Interest(function (message) {
            if (message === "End") {
                last_selected.select();
                last_selected.focus();
                loaded = true;
            }
        });
    }
});
