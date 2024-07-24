var Submission = Backbone.Model.extend({
    idAttribute: 'student',
    urlRoot: base_url + "/formgrader/api/submission/" + assignment_id
});

var Submissions = Backbone.Collection.extend({
    model: Submission,
    url: base_url + "/formgrader/api/submissions/" + assignment_id
});

var SubmissionUI = Backbone.View.extend({

    events: {},

    initialize: function () {
        this.$student_name = this.$el.find(".student-name");
        this.$student_id = this.$el.find(".student-id");
        this.$timestamp = this.$el.find(".timestamp");
        this.$status = this.$el.find(".status");
        this.$score = this.$el.find(".score");
        this.$autograde = this.$el.find(".autograde");
        this.$generate_feedback = this.$el.find(".generate-feedback");
        this.$release_feedback = this.$el.find(".release-feedback");
        this.$grant_extension = this.$el.find(".grant-extension");
        
        this.$modal = undefined;
        this.$modal_save = undefined;

        this.listenTo(this.model, "sync", this.render);

        this.render();
    },

    clear: function () {
        this.$student_name.empty();
        this.$student_id.empty();
        this.$timestamp.empty();
        this.$status.empty();
        this.$score.empty();
        this.$autograde.empty();
        this.$generate_feedback.empty();
        this.$release_feedback.empty();
        this.$grant_extension.empty();
    },

    render: function () {
        this.clear();

        var student = this.model.get("student");
        var assignment = this.model.get("name");

        // student name
        var last_name = this.model.get("last_name");
        var first_name = this.model.get("first_name");
        if (last_name === null) last_name = "None";
        if (first_name === null) first_name = "None";
        var name = last_name + ", " + first_name;
        this.$student_name.attr("data-order", name);
        if (this.model.get("autograded")) {
            this.$student_name.append($("<a/>")
                .attr("href", base_url + "/formgrader/manage_students/" + student + "/" + assignment)
                .text(name));
        } else {
            this.$student_name.text(name);
        }

        // student id
        this.$student_id.attr("data-order", student);
        this.$student_id.text(student);

        // timestamp
        var timestamp = this.model.get("timestamp");
        var display_timestamp = this.model.get("display_timestamp");
        if (timestamp === null) {
            timestamp = "None";
            display_timestamp = "None";
        }
        this.$timestamp.attr("data-order", timestamp);
        this.$timestamp.text(display_timestamp);

        // status
        if (!this.model.get("autograded")) {
            this.$status.attr("data-order", 0);
            this.$status.append($("<span/>")
                .addClass("label label-warning")
                .text("needs autograding"));
        } else if (this.model.get("needs_manual_grade")) {
            this.$status.attr("data-order", 1);
            this.$status.append($("<span/>")
                .addClass("label label-info")
                .text("needs manual grading"));
        } else {
            this.$status.attr("data-order", 2);
            this.$status.append($("<span/>")
                .addClass("label label-success")
                .text("graded"));
        }

        // score
        if (this.model.get("autograded")) {
            var score = roundToPrecision(this.model.get("score"), 2);
            var max_score = roundToPrecision(this.model.get("max_score"), 2);
            if (max_score === 0) {
                this.$score.attr("data-order", 0.0);
            } else {
                this.$score.attr("data-order", score / max_score);
            }
            this.$score.text(score + " / " + max_score);
        } else {
            this.$score.attr("data-order", 0.0);
        }

        // autograde
        this.$autograde.append($("<a/>")
            .attr("href", "#")
            .click(_.bind(this.autograde, this))
            .append($("<span/>")
                .addClass("glyphicon glyphicon-flash")
                .attr("aria-hidden", "true")));

        // generate feedback
        this.$generate_feedback.append($("<a/>")
            .attr("href", "#")
            .click(_.bind(this.generate_feedback, this))
            .append($("<span/>")
                .addClass("glyphicon glyphicon-comment")
                .attr("aria-hidden", "true")));

        // release feedback
        this.$release_feedback.append($("<a/>")
            .attr("href", "#")
            .click(_.bind(this.release_feedback, this))
            .append($("<span/>")
                .addClass("glyphicon glyphicon-envelope")
                .attr("aria-hidden", "true")));

        // grant extension
        this.$grant_extension.append($("<a/>")
            .attr("href", "#")
            .click(_.bind(this.grant_extension, this))
            .append($("<span/>")
                .addClass("glyphicon glyphicon-calendar")
                .attr("aria-hidden", "true")));
    },

    autograde: function () {
        this.clear();
        this.$student_name.text("Please wait...");
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        $.post(base_url + "/formgrader/api/submission/" + assignment + "/" + student + "/autograde")
            .done(_.bind(this.autograde_success, this))
            .fail(_.bind(this.autograde_failure, this));
    },

    autograde_success: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully autograded '" + assignment + "' for student '" + student + "'.",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error autograding '" + assignment + "' for student '" + student + "':",
                response["log"],
                response["error"]);
        }
    },

    autograde_failure: function (response) {
        this.model.fetch();
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        createModal(
            "error-modal",
            "Error",
            "There was an error autograding '" + assignment + "' for student '" + student + "'.");
    },

    generate_feedback: function () {
        this.clear();
        this.$student_name.text("Please wait...");
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        $.post(base_url + "/formgrader/api/assignment/" + assignment + "/" + student + "/generate_feedback")
            .done(_.bind(this.generate_feedback_success, this))
            .fail(_.bind(this.generate_feedback_failure, this));
    },

    generate_feedback_success: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully generated feedback for '" + assignment + "' for student '" + student + "'.",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error generating feedback for '" + assignment + "' for student '" + student + "':",
                response["log"],
                response["error"]);
        }
    },

    generate_feedback_failure: function (response) {
        this.model.fetch();
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        createModal(
            "error-modal",
            "Error",
            "There was an error generating feedback for '" + assignment + "' for student '" + student + "'.");
    },

    release_feedback: function () {
        this.clear();
        this.$student_name.text("Please wait...");
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        $.post(base_url + "/formgrader/api/assignment/" + assignment + "/" + student + "/release_feedback")
            .done(_.bind(this.release_feedback_success, this))
            .fail(_.bind(this.release_feedback_failure, this));
    },

    release_feedback_success: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully released feedback for '" + assignment + "' for student '" + student + "'.",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error releasing feedback for '" + assignment + "' for student '" + student + "':",
                response["log"],
                response["error"]);
        }
    },

    release_feedback_failure: function (response) {
        this.model.fetch();
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        createModal(
            "error-modal",
            "Error",
            "There was an error releasing feedback for '" + assignment + "' for student '" + student + "'.");
    },

    grant_extension: function () {
        if (!this.model.get("autograded")) {
            createModal(
                "error-modal",
                "Error",
                "Extensions cannot be granted for ungraded submissions.");
            return;
        }
        this.openModal();
    },

    openModal: function () {
        var body = $("<table/>").addClass("table table-striped form-table");
        var tableBody = $("<tbody/>");
        body.append(tableBody);

        var days = $("<tr/>");
        tableBody.append(days);
        days.append($("<td/>").addClass("align-middle").text("Days"));
        days.append($("<td/>").append($("<input/>").addClass("modal-days").attr({type: "number", min: 0, step: 1, value: this.modal_extension_days})));

        var hours = $("<tr/>");
        tableBody.append(hours);
        hours.append($("<td/>").addClass("align-middle").text("Hours"));
        hours.append($("<td/>").append($("<input/>").addClass("modal-hours").attr({type: "number", min: 0, step: 1, value: this.modal_extension_hours})));

        var minutes = $("<tr/>");
        tableBody.append(minutes);
        minutes.append($("<td/>").addClass("align-middle").text("Minutes"));
        minutes.append($("<td/>").append($("<input/>").addClass("modal-minutes").attr({type: "number", min: 0, step: 1, value: this.modal_extension_minutes})));

        var footer = $("<div/>");
        footer.append($("<button/>")
            .addClass("btn btn-primary save")
            .attr("type", "button")
            .text("Save"));
        footer.append($("<button/>")
            .addClass("btn btn-danger")
            .attr("type", "button")
            .attr("data-dismiss", "modal")
            .text("Cancel"));

        this.$modal = createModal("grant-extension-modal", "Granting Extension to " + this.model.get("student"), body, footer);
        
        var extension = new Date(this.model.get("extension") || '1970-01-01T00:00:00Z');
        var modal_extension_days = Math.trunc(extension.getTime() / 86400000);
        var modal_extension_hours = extension.getHours();
        var modal_extension_minutes = extension.getMinutes();

        this.$modal.find("input.modal-days").val(modal_extension_days);
        this.$modal.find("input.modal-hours").val(modal_extension_hours);
        this.$modal.find("input.modal-minutes").val(modal_extension_minutes);
        this.$modal.find("button.save").click(_.bind(this.save, this));
    },

    save: function () {
        this.animateSaving();
        
        var days = this.$modal.find("input.modal-days").val() || 0;
        var hours = this.$modal.find("input.modal-hours").val() || 0;
        var minutes = this.$modal.find("input.modal-minutes").val() || 0;

        this.closeModal();
        let student = this.model.get("student");
        let assignment = this.model.get("name");

        $.ajax({
            url: base_url + '/formgrader/api/submission/extension/' + assignment + '/' + student,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                minutes: minutes,
                hours: hours,
                days: days
            }),
            })
            .done(_.bind(this.grant_extension_log, this));
    },

    grant_extension_log: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully granted extension to '" + assignment + "' for student '" + student + "'.",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error granting extension to '" + assignment + "' for student '" + student + "':",
                response["log"],
                response["error"]);
        }
    },

    animateSaving: function () {
        if (this.$modal_save) {
            this.$modal_save.text("Saving...");
        }
    },

    closeModal: function () {
        if (this.$modal) {
            this.$modal.modal('hide')
            this.$modal = undefined;
            this.modal_extension_days = 0;
            this.modal_extension_hours = 0;
            this.modal_extension_minutes = 0;
            this.$modal_save = undefined;
        }

        this.render();
    },

});

var insertRow = function (table) {
    var row = $("<tr/>");
    row.append($("<td/>").addClass("student-name"));
    row.append($("<td/>").addClass("text-center student-id"));
    row.append($("<td/>").addClass("text-center timestamp"));
    row.append($("<td/>").addClass("text-center status"));
    row.append($("<td/>").addClass("text-center score"));
    row.append($("<td/>").addClass("text-center autograde"));
    row.append($("<td/>").addClass("text-center generate-feedback"));
    row.append($("<td/>").addClass("text-center release-feedback"));
    row.append($("<td/>").addClass("text-center grant-extension"));
    table.append(row)
    return row;
};

var loadSubmissions = function () {
    var tbl = $("#main-table");

    models = new Submissions();
    views = [];
    models.loaded = false;
    models.fetch({
        success: function () {
            tbl.empty();
            models.each(function (model) {
                var view = new SubmissionUI({
                    "model": model,
                    "el": insertRow(tbl)
                });
                views.push(view);
            });
            insertDataTable(tbl.parent());
            models.loaded = true;
        }
    });
};

var models = undefined;
var views = [];
$(window).on('load', function () {
    loadSubmissions();
});
