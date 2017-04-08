{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="{{ base_url }}/formgrader/students">Students</a></li>
<li><a href="{{ base_url }}/formgrader/students/{{ student.id }}">{{ student.id }}</a></li>
<li class="active">{{ assignment_id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all the notebooks for the assignment
  "{{ assignment_id }}" by {{ student.last_name }}, {{ student.first_name }}.
  You can grade a notebook by clicking on its ID.
</div>
{%- endblock -%}

{%- block table -%}
<table id="student-submissions" class="table table-hover">
<thead>
  <tr>
    <th>Notebook ID</th>
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
  var notebook_link = function (id, name) {
    return ''+
      '<a href="{{ base_url }}/formgrader/submissions/'+id+'">'+
          name+
      '</a>';
  };

  $(document).ready(function(){
    $('#student-submissions').DataTable({
      info: false,
      paging: false,
      ajax: "/formgrader/api/students/{{ student.id }}/{{ assignment_id }}",
      columns: [
        { data: {
            _: "name",
            display: function (data) {
                return notebook_link(data.id, data.name);
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
