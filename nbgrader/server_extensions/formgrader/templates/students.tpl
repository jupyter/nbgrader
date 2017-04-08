{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li class="active">Students</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all of the students in the class. Click on the name of a student
  to see their grades on individual assignments.
</div>
{%- endblock -%}

{%- block table -%}
<table id="students" class="table table-hover">
<thead>
  <tr>
    <th>Name</th>
    <th class="center">Student ID</th>
    <th class="center">Overall score</th>
  </tr>
</thead>
<tbody>
  {%- for student in students -%}
  <tr>
    <td><a href="{{ base_url }}/formgrader/students/{{ student.id }}">{{ student.last_name }}, {{ student.first_name }}</a></td>
    <td class="center">{{ student.id }}
    {%- if student.max_score is greaterthan 0 -%}
    <td data-order="{{ student.score / student.max_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
        {{ student.score | float | round(2) }} / {{ student.max_score | float | round(2) }}
    </td>
  </tr>
  {%- endfor -%}
</tbody>
</table>
{%- endblock -%}

{%- block script -%}
<script type="text/javascript">
    $(document).ready(function(){
        $('#students').DataTable({
            info: false,
            paging: false,
            saveState: true,
        });
    });
</script>
{%- endblock -%}
