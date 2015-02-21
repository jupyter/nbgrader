{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="/assignments">Assignments</a></li>
<li class="active">{{ assignment.assignment_id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists the notebooks that are associated with the
  assignment "{{ assignment.assignment_id }}". Click on a notebook
  name to see the list of student submissions for that notebook.
</div>
{%- endblock -%}

{%- block table -%}
<thead>
  <tr>
    <th>Notebook ID</th>
    <th class="center">Avg score</th>
    <th class="center">Max score</th>
  </tr>
</thead>
<tbody>
  {%- for notebook in notebooks -%}
  <tr>
    <td><a href="/assignments/{{ assignment.assignment_id }}/{{ notebook.notebook_id }}">{{ notebook.notebook_id }}</a></td>
    <td class="center">{{ notebook.avg_score | float | round(2) }}</td>
    <td class="center">{{ notebook.max_score | float | round(2) }}</td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
