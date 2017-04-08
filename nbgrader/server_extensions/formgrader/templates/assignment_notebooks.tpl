{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="{{ base_url }}/formgrader/assignments">Assignments</a></li>
<li class="active">{{ assignment_id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists the notebooks that are associated with the
  assignment "{{ assignment_id }}". Click on a notebook name to see the list
  of student submissions for that notebook.
</div>
{%- endblock -%}

{%- block table -%}
<table id="assignment-notebooks" class="table table-hover">
<thead>
  <tr>
    <th>Notebook ID</th>
    <th class="center">Avg. Score</th>
    <th class="center">Avg. Code Score</th>
    <th class="center">Avg. Written Score</th>
    <th class="center">Needs manual grade?</th>
  </tr>
</thead>
<tbody></tbody>
</table>
{%- endblock -%}

{%- block script -%}
<script type="text/javascript">
  var notebook_link = function (notebook_id) {
    return ''+
      '<a href="{{ base_url }}/formgrader/assignments/{{ assignment_id }}/'+notebook_id+'">'+
        notebook_id+
      '</a>';
  };

  $(document).ready(function(){
    $('#assignment-notebooks').DataTable({
      info: false,
      paging: false,
      ajax: "/formgrader/api/assignments/{{ assignment_id }}",
      columns: [
        { data: {
            _: "name",
            sort: "name",
            display: function (data) { return notebook_link(data.name); }
        } },
        { data: {
            _: "ave_score.display",
            sort: "ave_score.sort",
        } },
        { data: {
            _: "ave_code_score.display",
            sort: "ave_code_score.sort",
        } },
        { data: {
            _: "ave_written_score.display",
            sort: "ave_written_score.sort",
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
      saveState: true,
    });
  });
</script>
{%- endblock -%}
