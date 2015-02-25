/*global $, Backbone, student, nb_uuid */

var Grade = Backbone.Model.extend({
    idAttribute: "_id",
    urlRoot: "/api/grade",
    initialize: function () {
        var elem = $("#" + this.get("grade_id"));
        var glyph = $("#" + this.get("grade_id") + "-saved");
        elem.val(this.get("score"));
        elem.attr("placeholder", this.get("autoscore"));

        var that = this;
        elem.on("change", function (evt) {
            if (elem.val() === "") {
                that.set("score", null);
            } else {
                that.set("score", Math.min(Math.max(0, elem.val()), that.get("max_score")));
            }

            elem.val(that.get("score"));
            glyph.removeClass("glyphicon-floppy-saved");
            glyph.addClass("glyphicon-refresh");
            glyph.fadeIn(10);

            that.save("score", that.get("score"), {
                success: function () {
                    glyph.removeClass("glyphicon-refresh");
                    glyph.addClass("glyphicon-floppy-saved");
                    setTimeout(function () {
                        glyph.fadeOut();
                    }, 1000);
                    $(document).trigger("finished_saving");
                }
            });
        });
    }
});

var Grades = Backbone.Collection.extend({
    model: Grade,
    url: "/api/notebook/" + nb_uuid + "/grades"
});

var Comment = Backbone.Model.extend({
    idAttribute: "_id",
    urlRoot: "/api/comment",
    initialize: function () {
        var elem = $($(".comment")[this.get("comment_id")]);
        var glyph = $($(".comment-saved")[this.get("comment_id")]);
        elem.val(this.get("comment"));

        var that = this;
        elem.on("change", function (evt) {
            that.set("comment", elem.val());

            glyph.removeClass("glyphicon-floppy-saved");
            glyph.addClass("glyphicon-refresh");
            glyph.fadeIn(10);

            that.save("comment", that.get("comment"), {
                success: function () {
                    glyph.removeClass("glyphicon-refresh");
                    glyph.addClass("glyphicon-floppy-saved");
                    setTimeout(function () {
                        glyph.fadeOut();
                    }, 1000);
                    $(document).trigger("finished_saving");
                }
            });
        });
    }
});

var Comments = Backbone.Collection.extend({
    model: Comment,
    url: "/api/notebook/" + nb_uuid + "/comments"
});

var getIndex = function (elem) {
    var elems = $("input, textarea");
    return elems.index(elem);
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
};

var scrollTo = function (elem) {
    var target = elem.closest(".nbgrader_cell");
    return target.offset().top - $(window).height() * 0.33 + 60;
};

var grades;
var comments;
var last_selected;

var nextAssignment = function () {
    href = $("li.next a").attr("href");
    if (href) {
       window.location = href + "#" + getIndex(last_selected);
    }
};

var prevAssignment = function () {
    href = $("li.previous a").attr("href");
    if (href) {
        window.location = href + "#" + getIndex(last_selected);
    }
};
    
$(window).load(function () {
    grades = new Grades();
    grades.fetch();

    comments = new Comments();
    comments.fetch();

    $("li.previous a").tooltip({container: 'body'});
    $("li.next a").tooltip({container: 'body'});

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
            last_selected.select();

        } else if (keyCode == 39 && e.shiftKey) { // shift + right arrow
            elem = document.activeElement;
            if (elem.tagName === "INPUT" || elem.tagName === "TEXTAREA") {
                $(document).on("finished_saving", nextAssignment);
                $(elem).blur();
                $(elem).trigger("change");
            } else {
                nextAssignment();
            }

        } else if (keyCode == 37 && e.shiftKey) { // shift + left arrow
            elem = document.activeElement;
            if (elem.tagName === "INPUT" || elem.tagName === "TEXTAREA") {
                $(document).on("finished_saving", prevAssignment);
                $(elem).blur();
                $(elem).trigger("change");
            } else {
                prevAssignment();
            }
        }
    });

    var index = parseInt(document.URL.split('#')[1]) || 0;
    last_selected = $($("input, textarea")[index]);
    last_selected.select();
    $("body, html").stop().scrollTop(scrollTo(last_selected));

    $("input, textarea").focus(function (event) {
        last_selected = $(event.currentTarget);
        $("body, html").stop().animate({
            scrollTop: scrollTo(last_selected)
        }, 500);
    });
});
