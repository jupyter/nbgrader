{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="{{ base_url }}/formgrader/students">Students</a></li>
<li class="active">{{ student.id }}</li>
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
    <th class="center">Overall Score</th>
    <th class="center">Code Score</th>
    <th class="center">Written Score</th>
    <th class="center">Needs manual grade?</th>
  </tr>
</thead>
<tbody>
  {%- for assignment in assignments -%}
  <tr>
    {%- if assignment.id is none -%}
    <td>{{ assignment.name }} (no submission)</td>
    {%- else -%}
    <td><a href="{{ base_url }}/formgrader/students/{{ student.id }}/{{ assignment.name }}">{{ assignment.name }}</a></td>
    {%- endif -%}
    {%- if assignment.max_score is greaterthan 0 -%}
    <td data-order="{{ assignment.score / assignment.max_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
      {{ assignment.score | float | round(2) }} / {{ assignment.max_score | float | round(2) }}
    </td>
    {%- if assignment.max_code_score is greaterthan 0 -%}
    <td data-order="{{ assignment.code_score / assignment.max_code_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
      {{ assignment.code_score | float | round(2) }} / {{ assignment.max_code_score | float | round(2) }}
    </td>
    {%- if assignment.max_written_score is greaterthan 0 -%}
    <td data-order="{{ assignment.written_score / assignment.max_written_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
      {{ assignment.written_score | float | round(2) }} / {{ assignment.max_written_score | float | round(2) }}
    </td>
    {%- if assignment.needs_manual_grade -%}
    <td data-search="needs manual grade" class="center">
      <span class="glyphicon glyphicon-ok"></span>
    {%- else -%}
    <td data-search="" class="center">
    {%- endif -%}
    </td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
