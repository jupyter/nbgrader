var GradeUI = Backbone.View.extend({

    events: {
        "change .score": "save",
        "click .full-credit": "assignFullCredit",
        "click .no-credit": "assignNoCredit",
        "click .mark-graded": "save"
    },

    initialize: function () {
        this.$glyph = this.$el.find(".score-saved");
        this.$score = this.$el.find(".score");
        this.$mark_graded = this.$el.find(".mark-graded");

        this.listenTo(this.model, "change", this.render);
        this.listenTo(this.model, "request", this.animateSaving);
        this.listenTo(this.model, "sync", this.animateSaved);

        this.$score.attr("placeholder", this.model.get("auto_score"));
        this.render();
    },

    render: function () {
        this.$score.val(this.model.get("manual_score"));
        if (this.model.get("needs_manual_grade")) {
            this.$score.addClass("needs_manual_grade");
            if (this.model.get("manual_score") !== null) {
                this.$mark_graded.show();
            }
        } else {
            this.$score.removeClass("needs_manual_grade");
            this.$mark_graded.hide();
        }
    },

    save: function () {
        if (this.$score.val() === "") {
            this.model.save({"manual_score": null});
        } else {
            var val = this.$score.val();
            var max_score = this.model.get("max_score");
            if (val > max_score) {
                this.animateInvalidValue();
                this.model.save({"manual_score": max_score});
            } else if (val < 0) {
                this.animateInvalidValue();
                this.model.save({"manual_score": 0});
            } else {
                this.model.save({"manual_score": val});
            }
        }

        this.render();
    },

    animateSaving: function () {
        this.$glyph.removeClass("glyphicon-ok");
        this.$glyph.addClass("glyphicon-refresh");
        this.$glyph.fadeIn(10);
    },

    animateSaved: function () {
        this.$glyph.removeClass("glyphicon-refresh");
        this.$glyph.addClass("glyphicon-ok");
        var that = this;
        setTimeout(function () {
            that.$glyph.fadeOut();
        }, 1000);
        $(document).trigger("finished_saving");
    },

    animateInvalidValue: function () {
        var that = this;
        this.$score.animate({
            "background-color": "#FF8888",
            "border-color": "red"
        }, 100, undefined, function () {
            setTimeout(function () {
                that.$score.animate({
                    "background-color": "white",
                    "border-color": "white"
                }, 100);
            }, 50);
        });
    },

    assignFullCredit: function () {
        this.model.save({"manual_score": this.model.get("max_score")});
        this.$score.select();
        this.$score.focus();
    },

    assignNoCredit: function () {
        this.model.save({"manual_score": 0});
        this.$score.select();
        this.$score.focus();
    }
});

var Grade = Backbone.Model.extend({
    urlRoot: base_url + "/api/grade"
});

var Grades = Backbone.Collection.extend({
    model: Grade,
    url: base_url + "/api/grades"
});

var CommentUI = Backbone.View.extend({

    events: {
        "change .comment": "save",
    },

    initialize: function () {
        this.$glyph = this.$el.find(".comment-saved");
        this.$comment = this.$el.find(".comment");

        this.listenTo(this.model, "change", this.render);
        this.listenTo(this.model, "request", this.animateSaving);
        this.listenTo(this.model, "sync", this.animateSaved);

        this.$comment.attr("placeholder", this.model.get("auto_comment") || "Comments");


        this.render();
        autosize(this.$comment);        
    },

    render: function () {
        this.$comment.val(this.model.get("manual_comment"));
    },

    save: function () {
        this.model.save({"manual_comment": this.$comment.val()});
    },

    animateSaving: function () {
        this.$glyph.removeClass("glyphicon-ok");
        this.$glyph.addClass("glyphicon-refresh");
        this.$glyph.fadeIn(10);
    },

    animateSaved: function () {
        this.$glyph.removeClass("glyphicon-refresh");
        this.$glyph.addClass("glyphicon-ok");
        var that = this;
        setTimeout(function () {
            that.$glyph.fadeOut();
        }, 1000);
        $(document).trigger("finished_saving");
    },
});

var Comment = Backbone.Model.extend({
    urlRoot: base_url + "/api/comment"
});

var Comments = Backbone.Collection.extend({
    model: Comment,
    url: base_url + "/api/comments"
});
