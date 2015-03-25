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
    <th class="center">Overall score</th>
  </tr>
</thead>
<tbody>
  {%- for student in students -%}
  <tr>
    <td><a href="{{base_url}}/students/{{ student.id }}">{{ student.last_name }}, {{ student.first_name }}</a></td>
    <td class="center">{{ student.id }}
    <td class="center">{{ student.score | float | round(2) }} / {{ student.max_score | float | round(2) }}</td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
