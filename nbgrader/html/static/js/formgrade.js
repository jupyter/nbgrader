/*global $, Backbone, student, nb_uuid */

var Grade = Backbone.Model.extend({
    idAttribute: "_id",
    urlRoot: "/api/grade",
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
    url: "/api/notebook/" + nb_uuid + "/grades"
});

var Comment = Backbone.Model.extend({
    idAttribute: "_id",
    urlRoot: "/api/comment",
    initialize: function () {
        var elem = $($(".comment")[this.get("comment_id")]);
        var glyph = $($(elem.siblings()[0]).children()[0]);
        elem.val(this.get("comment"));
        glyph.hide();

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
                }
            });
        });
    }
});

var Comments = Backbone.Collection.extend({
    model: Comment,
    url: "/api/notebook/" + nb_uuid + "/comments"
});

var grades;
var comments;
    
$(document).ready(function () {
    grades = new Grades();
    grades.fetch();

    comments = new Comments();
    comments.fetch();

    $("li.previous a").tooltip();
    $("li.next a").tooltip();
});
