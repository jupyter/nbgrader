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

var loadGrades = function (submission_id) {
    var grades = new Grades();
    grades.loaded = false;
    grades.fetch({
        data: {
            submission_id: submission_id
        },
        success: function () {
            grades.loaded = true;
        }
    });
    return grades;
};

var loadComments = function (submission_id) {
    var comments = new Comments();
    comments.loaded = false;
    comments.fetch({
        data: {
            submission_id: submission_id
        },
        success: function () {
            comments.loaded = true;
        }
    });
    return comments;
};
