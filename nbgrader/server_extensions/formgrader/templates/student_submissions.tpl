{%- extends 'gradebook.tpl' -%}

{%- block breadcrumb -%}
<li><a href="{{ base_url }}/formgrader/students">Students</a></li>
<li><a href="{{ base_url }}/formgrader/students/{{ student.id }}">{{ student.id }}</a></li>
<li class="active">{{ assignment_id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all the notebooks for the assignment "{{ assignment_id }}" by {{ student.last_name }}, {{ student.first_name }}.
  You can grade a notebook by clicking on its ID.
</div>
{%- endblock -%}

{%- block table -%}
<table id="student-submissions" class="table table-hover">
<thead>
  <tr>
    <th>Notebook ID</th>
    <th class="center">Overall Score</th>
    <th class="center">Code Score</th>
    <th class="center">Written Score</th>
    <th class="center">Needs manual grade?</th>
    <th class="center">Tests failed?</th>
    <th class="center">Flagged?</th>
  </tr>
</thead>
<tbody>
  {%- for submission in submissions -%}
  <tr>
    <td>
      <a href="{{ base_url }}/formgrader/submissions/{{ submission.id }}">
        {{ submission.name }}
      </a>
    </td>
    {%- if submission.max_score is greaterthan 0 -%}
    <td data-order="{{ submission.score / submission.max_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
        {{ submission.score | float | round(2) }} / {{ submission.max_score | float | round(2) }}
    </td>
    {%- if submission.max_code_score is greaterthan 0 -%}
    <td data-order="{{ submission.code_score / submission.max_code_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
        {{ submission.code_score | float | round(2) }} / {{ submission.max_code_score | float | round(2) }}
    </td>
    {%- if submission.max_written_score is greaterthan 0 -%}
    <td data-order="{{ submission.written_score / submission.max_written_score | float | round(2) }}" class="center">
    {%- else -%}
    <td data-order="0.00" class="center">
    {%- endif -%}
        {{ submission.written_score | float | round(2) }} / {{ submission.max_written_score | float | round(2) }}
    </td>
    {%- if submission.needs_manual_grade -%}
    <td data-search="needs manual grade" class="center">
      <span class="glyphicon glyphicon-ok"></span>
    {%- else -%}
    <td data-search="" class="center">
    {%- endif -%}
    </td>
    {%- if submission.failed_tests -%}
    <td data-search="tests failed" class="center">
      <span class="glyphicon glyphicon-ok"></span>
    {%- else -%}
    <td data-search="" class="center">
    {%- endif -%}
    </td>
    {%- if submission.flagged -%}
    <td data-search="flagged" class="center">
      <span class="glyphicon glyphicon-flag"></span>
    {%- else -%}
    <td data-search="" class="center">
    {%- endif -%}
    </td>
  </tr>
  {%- endfor -%}
</tbody>
</table>
{%- endblock -%}

{%- block script -%}
<script type="text/javascript">
    $(document).ready(function(){
        $('#student-submissions').DataTable({
            info: false,
            paging: false,
            saveState: true,
        });
    });
</script>
{%- endblock -%}
