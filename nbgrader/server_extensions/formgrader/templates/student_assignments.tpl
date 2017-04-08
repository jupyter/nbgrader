{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="{{ base_url }}/formgrader/students">Students</a></li>
<li class="active">{{ student.id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists the assignments turned in by
  {{ student.last_name }}, {{ student.first_name }}. Click on a notebook name
  to see the scores for individual notebooks.
</div>
{%- endblock -%}

{%- block table -%}
<table id="student-assignments" class="table table-hover">
<thead>
  <tr>
    <th>Assignment ID</th>
    <th class="center">Overall Score</th>
    <th class="center">Code Score</th>
    <th class="center">Written Score</th>
    <th class="center">Needs manual grade?</th>
  </tr>
</thead>
<tbody></tbody>
</table>
{%- endblock -%}

{%- block script -%}
<script type="text/javascript">
  var assignment_link = function (name) {
    return ''+
      '<a href="{{ base_url }}/formgrader/students/{{ student.id }}/'+name+'">'+
        name+
      '</a>';
  };

  $(document).ready(function(){
    $('#student-assignments').DataTable({
      info: false,
      paging: false,
      ajax: "/formgrader/api/students/{{ student.id }}",
      columns: [
        { data: {
            _: "name",
            display: function (data) {
              if (data.id) {
                return assignment_link(data.name);
              } else {
                return data.name+' (no submission)';
              };
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
      ],
      columnDefs: [
        { targets: [0],
          createdCell: function (td, cellData, rowData, row, col) {
            $(td).addClass('left')
        } },
        { targets: ['_all'],
          createdCell: function (td, cellData, rowData, row, col) {
            $(td).addClass('center')
        } },
      ],
      deferRender: true,
      saveState: true,
    });
  });
</script>
{%- endblock -%}
