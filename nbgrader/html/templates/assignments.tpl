{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li class="active">Assignments</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all of the assignments that have been
  added to the gradebook. Click on the name of an assignment to see
  the notebooks that are associated with that assignment.
</div>
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
    <td><a href="{{base_url}}/assignments/{{ assignment.name }}">{{ assignment.name }}</a></td>
    <td class="center">{{ assignment.duedate }}</td>
    <td class="center">{{ assignment.num_submissions }}</td>
    <td class="center">{{ assignment.average_score | float | round(2) }}</td>
    <td class="center">{{ assignment.max_score | float | round(2) }}</td>
  </tr>
  {%- endfor -%}
</tbody>
{%- endblock -%}
