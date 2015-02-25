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
  assignment.assignment_id }}". By clicking on a submission id, you
  can grade the submitted notebook.
</div>
{%- endblock -%}

{%- block table -%}
<thead>
  <tr>
    <th>Submission ID</th>
    <th class="center">Score</th>
    <th class="center">Manual grade?</th>
  </tr>
</thead>
<tbody>
  {%- for submission in submissions -%}
  <tr>
    <td><a href="/submissions/{{ submission._id }}">Submission #{{ submission.index + 1 }}</a></td>
    <td class="center">
      {{ submission.score | float | round(2) }} / {{ submission.max_score | float | round(2) }}
    </td>
    <td class="center">
      {%- if submission.needs_manual_grade -%}
      <span class="glyphicon glyphicon-ok"></span>
      {%- endif -%}
    </td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
