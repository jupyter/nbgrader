{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li class="active">Students</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all of the students in the class. Click on the name
  of a student to see their grades on individual assignments.
</div>
{%- endblock -%}

{%- block table -%}
<table id="students" class="table table-hover">
<thead>
  <tr>
    <th>Surname, Name</th>
    <th class="center">Student ID</th>
    <th class="center">Overall score</th>
  </tr>
</thead>
<tbody></tbody>
</table>
{%- endblock -%}

{%- block script -%}
<script type="text/javascript">
  var assignments_link = function (student_id, first_name, last_name) {
    return ''+
      '<a href="{{ base_url }}/formgrader/students/'+student_id+'">'+
        last_name+', '+first_name+
      '</a>';
  };

  $(document).ready(function(){
    $('#students').DataTable({
      info: false,
      ajax: "/formgrader/api/students",
      columns: [
        { data: {
            _: "last_name",
            sort: "last_name",
            display: function (data) {
              return assignments_link(data.id, data.first_name, data.last_name);
            }
        } },
        { data: "id" },
        { data: {
            _: "score.display",
            sort: "score.sort",
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
      scrollY: 600,
      scroller: true,
      scrollCollapse: true,
      deferRender: true,
      saveState: true,
    });
  });
</script>
{%- endblock -%}
