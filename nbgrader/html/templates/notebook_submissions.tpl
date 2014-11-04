{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="/assignments">Assignments</a></li>
<li><a href="/assignments/{{ assignment.assignment_id }}">{{ assignment.assignment_id }}</a></li>
<li class="active">{{ notebook_id }}</li>
{%- endblock -%}

{%- block table -%}
<thead>
  <tr>
    <th>Student name</th>
    <th class="center">Student ID</th>
    <th class="center">Score</th>
    <th class="center">Needs manual grade?</th>
  </tr>
</thead>
<tbody>
  {%- for submission in submissions -%}
  <tr>
    <td><a href="/assignments/{{ assignment.assignment_id }}/{{ notebook_id }}/{{ submission.student.student_id }}">
      {{ submission.student.last_name }}, {{ submission.student.first_name }}
    </a></td>
    <td class="center">{{ submission.student.student_id }}</td>
    <td class="center">{{ submission.score }} / {{ submission.max_score }}</td>
    <td class="center">
      {%- if submission.needs_manual_grade -%}
      <span class="glyphicon glyphicon-remove"></span>
      {%- endif -%}
    </td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
