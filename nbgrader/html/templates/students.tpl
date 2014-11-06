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
<thead>
  <tr>
    <th>Name</th>
    <th class="center">Student ID</th>
    <th class="center">Score</th>
  </tr>
</thead>
<tbody>
  {%- for student in students -%}
  <tr>
    <td><a href="/students/{{ student.student_id }}">{{ student.last_name }}, {{ student.first_name }}</a></td>
    <td class="center">{{ student.student_id }}
    <td class="center">{{ student.score }} / {{ student.max_score }}</td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
