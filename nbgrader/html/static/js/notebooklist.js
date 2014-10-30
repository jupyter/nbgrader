/*global $*/

var displayScore = function (nb) {
    $.get("/" + nb + "/score", function (data) {
        score = JSON.parse(data);
        var elem = $("li#" + nb + " span");
        elem.html(score["score"] + " / " + score["max_score"]);
        if (score["needs_manual_grade"]) {
            elem.addClass("badge-warning");
            elem.tooltip({
                title: "Needs manual grading",
                placement: "left"
            });
        }
    });
};

$(document).ready(function () {
    for (var i=0; i < notebooks.length; i++) {
        displayScore(notebooks[i]);
    }
});
