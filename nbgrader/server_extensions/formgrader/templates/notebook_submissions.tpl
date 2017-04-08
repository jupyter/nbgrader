{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="{{ base_url }}/formgrader/assignments">Assignments</a></li>
<li><a href="{{ base_url }}/formgrader/assignments/{{ assignment_id }}">{{ assignment_id }}</a></li>
<li class="active">{{ notebook_id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all the student submissions for the notebook
  "{{ notebook_id }}", which is part of the assignment "{{ assignment_id }}".
  By clicking on a submission id, you can grade the submitted notebook.
</div>
{%- endblock -%}

{%- block table -%}
<table id="notebook-submissions" class="table table-hover">
<thead>
  <tr>
    <th></th>
    <th>Submission ID</th>
    <th class="center">Overall Score</th>
    <th class="center">Code Score</th>
    <th class="center">Written Score</th>
    <th class="center">Needs manual grade?</th>
    <th class="center">Tests failed?</th>
    <th class="center">Flagged?</th>
  </tr>
</thead>
<tbody></tbody>
</table>
{%- endblock -%}

{%- block script -%}
<script type="text/javascript">
  var toggle_name = function (on, index) {
    var elem = $("#submission-" + index);
    if (on) {
      elem.find(".name-shown").show();
      elem.find(".name-hidden").hide();
    } else {
      elem.find(".name-hidden").show();
      elem.find(".name-shown").hide();
    }
  };

  var eye_icon = function (index) {
    return ''+
      '<span '+
        'class="glyphicon glyphicon-eye-open name-hidden" '+
        'aria-hidden="true" '+
        'data-placement="auto left"'+
        'onclick="toggle_name(true, '+index+');">'+
      '</span>'+
      '<span '+
        'class="glyphicon glyphicon-eye-close name-shown" '+
        'aria-hidden="true" '+
        'data-placement="auto left"'+
        'onclick="toggle_name(false, '+index+');">'+
      '</span>';
  };

  var submission_link = function (index, id, first_name, last_name) {
    return ''+
      '<a href="{{ base_url }}/formgrader/submissions/'+id+'"'+
        'class="name-hidden">Submission #'+index+'</a>'+
      '<a href="{{ base_url }}/formgrader/submissions/'+id+'"'+
        'class="name-shown">'+last_name+', '+first_name+'</a>';
  };

  $(document).ready(function () {
    $('#notebook-submissions').DataTable({
      info: false,
      ajax: "/formgrader/api/assignments/{{ assignment_id }}/{{ notebook_id }}",
      columns: [
        { orderable: false,
          data: {
            _: "index",
            display: function (data) { return eye_icon(data.index); },
        } },
        { data: {
            _: "index",
            display: function (data) {
              return submission_link(
                  data.index, data.id, data.first_name, data.last_name);
            },
            filter: function (data) {
              return data.index+' '+data.last_name+' '+data.first_name;
            },
        } },
        { data: {
            _: "score.display",
            sort: "score.sort",
        } },
        { data: {
            _: "code_score.display",
            sort: "code_score.sort",
        } },
        { data: {
            _: "written_score.display",
            sort: "written_score.sort",
        } },
        { data: {
            _: "needs_manual_grade.display",
            sort: "needs_manual_grade.sort",
            filter: "needs_manual_grade.search",
        } },
        { data: {
            _: "failed_tests.display",
            sort: "failed_tests.sort",
            filter: "failed_tests.search",
        } },
        { data: {
            _: "flagged.display",
            sort: "flagged.sort",
            filter: "flagged.search",
        } },
      ],
      columnDefs: [{
        targets: ['_all'],
          createdCell: function (td, cellData, rowData, row, col) {
            $(td).addClass('center');
          }
      }],
      createdRow: function (row, data, dataIndex) {
        $(row).attr('id', 'submission-' + data.index);
        $(row).find('span.glyphicon.name-hidden').tooltip({title: "Show student name"});
        $(row).find('span.glyphicon.name-shown').tooltip({title: "Hide student name"});
      },
      scrollY: 600,
      scroller: true,
      scrollCollapse: true,
      order: [[1, 'asc']],
      deferRender: true,
      saveState: true,
    });
  });
</script>
{%- endblock -%}
