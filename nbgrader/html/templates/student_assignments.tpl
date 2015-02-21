{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="/students">Students</a></li>
<li class="active">{{ student.student_id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists the assignments turned in by {{ student.last_name }}, {{ student.first_name }}. Click on a notebook
  name to see the scores for individual notebooks.
</div>
{%- endblock -%}

{%- block table -%}
<thead>
  <tr>
    <th>Assignment ID</th>
    <th class="center">Received?</th>
    <th class="center">Score</th>
  </tr>
</thead>
<tbody>
  {%- for assignment in assignments -%}
  {%- if assignment.score == None -%}
  <tr class="warning">
  {%- else -%}
  <tr>
  {%- endif -%}
    {%- if assignment.score != None -%}
    <td><a href="/students/{{ student.student_id }}/{{ assignment.assignment_id }}">{{ assignment.assignment_id }}</a></td>
    {%- else -%}
    <td>{{ assignment.assignment_id }}</td>
    {%- endif -%}
    <td class="center">
      {%- if assignment.score == None -%}
      <span class="glyphicon glyphicon-remove"></span>
      {%- else -%}
      <span class="glyphicon glyphicon-ok"></span>
      {%- endif -%}
    </td>
    <td class="center">
      {%- if assignment.score != None -%}
      {{ assignment.score | float | round(2) }} / {{ assignment.max_score | float | round(2) }}
      {%- else -%}
      -
      {%- endif -%}
    </td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
