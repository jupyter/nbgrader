{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="{{ base_url }}/formgrader/assignments">Assignments</a></li>
<li class="active">{{ assignment.name }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists the notebooks that are associated with the
  assignment "{{ assignment.name }}". Click on a notebook
  name to see the list of student submissions for that notebook.
</div>
{%- endblock -%}

{%- block table -%}
<thead>
  <tr>
    <th>Notebook ID</th>
    <th class="center">Avg. Score</th>
    <th class="center">Avg. Code Score</th>
    <th class="center">Avg. Written Score</th>
    <th class="center">Needs manual grade?</th>
  </tr>
</thead>
<tbody>
  {%- for notebook in notebooks -%}
  <tr>
    <td><a href="{{ base_url }}/formgrader/assignments/{{ assignment.name }}/{{ notebook.name }}">{{ notebook.name }}</a></td>
    {%- if notebook.max_score is greaterthan 0 -%}
    <td data-order="{{ notebook.average_score / notebook.max_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
        {{ notebook.average_score | float | round(2) }} / {{ notebook.max_score | float | round(2) }}
    </td>
    {%- if notebook.max_code_score is greaterthan 0 -%}
    <td data-order="{{ notebook.average_code_score / notebook.max_code_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
        {{ notebook.average_code_score | float | round(2) }} / {{ notebook.max_code_score | float | round(2) }}
    </td>
    {%- if notebook.max_written_score is greaterthan 0 -%}
    <td data-order="{{ notebook.average_written_score / notebook.max_written_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
        {{ notebook.average_written_score | float | round(2) }} / {{ notebook.max_written_score | float | round(2) }}
    </td>
    {%- if notebook.needs_manual_grade -%}
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
