/*global $*/

var assignments;

$(document).ready(function () {
    $.get("/api/assignments", function (data) {
        assignments = JSON.parse(data);
        var elem = $("#assignment-list");
        var a, row, link;
        for (var i=0; i < assignments.length; i++) {
            a = assignments[i];

            link = $("<a />");
            link.attr("href", "/assignments/" + a.assignment_id);
            link.text(a.assignment_id);

            row = $("<tr />");
            row.append($("<td />").append(link));
            row.append($("<td />").text(a.duedate));

            elem.append(row);
        }
    });
});
