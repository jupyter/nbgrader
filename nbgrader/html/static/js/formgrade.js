/*global $, Backbone, student, nb */

var Grade = Backbone.Model.extend({
    idAttribute: "_id",
    urlRoot: "/grades",
    initialize: function () {
        var elem = $("#" + this.get("grade_id"));
        var glyph = $(elem.siblings()[0]);
        elem.val(this.get("score"));
        elem.attr("placeholder", this.get("autoscore"));
        glyph.hide();

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
                }
            });
        });
    }
});

var Grades = Backbone.Collection.extend({
    model: Grade,
    url: "/" + student + "/" + nb + "/grades"
});

var Comment = Backbone.Model.extend({
    idAttribute: "_id",
    urlRoot: "/comments",
    initialize: function () {
        var elem = $($(".comment")[this.get("comment_id")]);
        elem.val(this.get("comment"));

        var that = this;
        elem.on("change", function (evt) {
            that.set("comment", elem.val());
            that.save();
        });
    }
});

var Comments = Backbone.Collection.extend({
    model: Comment,
    url: "/" + student + "/" + nb + "/comments"
});

var grades;
var comments;
    
$(document).ready(function () {
    grades = new Grades();
    grades.fetch();

    comments = new Comments();
    comments.fetch();

    $.get("/" + nb + "/next", function (data) {
        nb = JSON.parse(data);
        if (nb === null) {
            $("li.next-notebook a").attr("href", "#");
            $("li.next-notebook").addClass("disabled");
        } else {
            $("li.next-notebook a").attr("href", "/" + nb);
            if ($("li.next-notebook").hasClass("disabled")) {
                $("li.next-notebook").removeClass("disabled");
            }
        }
    });

    $.get("/" + nb + "/prev", function (data) {
        nb = JSON.parse(data);
        if (nb === null) {
            $("li.prev-notebook a").attr("href", "#");
            $("li.prev-notebook").addClass("disabled");
        } else {
            $("li.prev-notebook a").attr("href", "/" + nb);
            if ($("li.prev-notebook").hasClass("disabled")) {
                $("li.prev-notebook").removeClass("disabled");
            }
        }
    });
});
