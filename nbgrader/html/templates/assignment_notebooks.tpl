{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="/assignments">Assignments</a></li>
<li class="active">{{ assignment.assignment_id }}</li>
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
    <td class="center">{{ notebook.avg_score }}</td>
    <td class="center">{{ notebook.max_score }}</td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
