{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="/assignments">Assignments</a></li>
<li><a href="/assignments/{{ assignment.assignment_id }}">{{ assignment.assignment_id }}</a></li>
<li class="active">{{ notebook_id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all the student submissions for the
  notebook "{{ notebook_id }}", which is part of the assignment "{{
  assignment.assignment_id }}". By clicking on a student's name, you
  can grade their submitted notebook.
</div>
{%- endblock -%}

{%- block table -%}
<thead>
  <tr>
    <th>Student name</th>
    <th class="center">Student ID</th>
    <th class="center">Score</th>
    <th class="center">Received?</th>
    <th class="center">Manual grade?</th>
  </tr>
</thead>
<tbody>
  {%- for submission in submissions -%}
  {%- if submission.score == None -%}
  <tr class="warning">
  {%- else -%}
  <tr>
  {%- endif -%}
    <td><a href="/assignments/{{ assignment.assignment_id }}/{{ notebook_id }}/{{ submission.student.student_id }}">
      {{ submission.student.last_name }}, {{ submission.student.first_name }}
    </a></td>
    <td class="center">{{ submission.student.student_id }}</td>
    <td class="center">
      {%- if submission.score == None -%}
      -
      {%- else -%}
      {{ submission.score }} / {{ submission.max_score }}
      {%- endif -%}
    </td>
    <td class="center">
      {%- if submission.score == None -%}
      <span class="glyphicon glyphicon-remove"></span>
      {%- else -%}
      <span class="glyphicon glyphicon-ok"></span>
      {%- endif -%}
    <td class="center">
      {%- if submission.needs_manual_grade -%}
      <span class="glyphicon glyphicon-ok"></span>
      {%- endif -%}
    </td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
