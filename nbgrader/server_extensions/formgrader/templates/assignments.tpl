{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li class="active">Assignments</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all of the assignments that have been added to the
  gradebook. Click on the name of an assignment to see the notebooks that are
  associated with that assignment.
</div>
{%- endblock -%}

{%- block table -%}
<table id="assignments" class="table table-hover">
<thead>
  <tr>
    <th>Assignment ID</th>
    <th class="center">Due date</th>
    <th class="center">Submissions</th>
    <th class="center">Avg. score</th>
    <th class="center">Max. score</th>
  </tr>
</thead>
<tbody></tbody>
</table>
{%- endblock -%}

{%- block script -%}
<script type="text/javascript">
  var assignment_link = function (assignment_id) {
    return ''+
      '<a href="{{ base_url }}/formgrader/assignments/'+assignment_id+'">'+
        assignment_id+
      '</a>';
  };

  $(document).ready(function(){
    $('#assignments').DataTable({
      info: false,
      paging: false,
      ajax: "/formgrader/api/assignments",
      columns: [
        { data: {
            _: "name",
            sort: "name",
            display: function (data) { return assignment_link(data.name); }
        } },
        { data: "duedate" },
        { data: "num_submissions" },
        { data: "average_score" },
        { data: "max_score" },
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
