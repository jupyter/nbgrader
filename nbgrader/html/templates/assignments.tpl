{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li class="active">Assignments</li>
{%- endblock -%}

{%- block table -%}
<thead>
  <tr>
    <th>Assignment ID</th>
    <th class="center">Due date</th>
    <th class="center">Submissions</th>
    <th class="center">Avg score</th>
    <th class="center">Max score</th>
  </tr>
</thead>
<tbody>
  {%- for assignment in assignments -%}
  <tr>
    <td><a href="/assignments/{{ assignment.assignment_id }}">{{ assignment.assignment_id }}</a></td>
    <td class="center">{{ assignment.duedate }}</td>
    <td class="center">{{ assignment.num_submissions }}</td>
    <td class="center">{{ assignment.avg_score }}</td>
    <td class="center">{{ assignment.max_score }}</td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
