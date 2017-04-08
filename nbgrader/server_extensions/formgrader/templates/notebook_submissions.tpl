{%- extends 'gradebook.tpl' -%}

{%- block head -%}
<script type="text/javascript">
function toggle_name(on, index) {
  var elem = $("#submission-" + index);
  if (on) {
    elem.find(".name-shown").show();
    elem.find(".name-hidden").hide();
  } else {
    elem.find(".name-hidden").show();
    elem.find(".name-shown").hide();
  }
}
</script>
{%- endblock -%}

{%- block breadcrumb -%}
<li><a href="{{ base_url }}/formgrader/assignments">Assignments</a></li>
<li><a href="{{ base_url }}/formgrader/assignments/{{ assignment_id }}">{{ assignment_id }}</a></li>
<li class="active">{{ notebook_id }}</li>
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
  The following table lists all the student submissions for the
  notebook "{{ notebook_id }}", which is part of the assignment "{{
  assignment_id }}". By clicking on a submission id, you
  can grade the submitted notebook.
</div>
{%- endblock -%}

{%- block table -%}
<table id="notebook-submissions" class="table table-hover">
<thead>
  <tr>
    <th></th>
    <th>Submission ID</th>
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
  <tr id="submission-{{ submission.index + 1 }}">
    <td data-order="{{ submission.index + 1 }}">
      <span class="glyphicon glyphicon-eye-open name-hidden" aria-hidden="true" onclick="toggle_name(true, {{ submission.index + 1 }});"></span>
      <span class="glyphicon glyphicon-eye-close name-shown" aria-hidden="true" onclick="toggle_name(false, {{ submission.index + 1 }});"></span>
    </td>
    <td data-order="{{ submission.index + 1 }}">
      <a href="{{ base_url }}/formgrader/submissions/{{ submission.id }}" class="name-hidden">Submission #{{ submission.index + 1 }}</a>
      <a href="{{ base_url }}/formgrader/submissions/{{ submission.id }}" class="name-shown">{{ submission.last_name }}, {{ submission.first_name }}</a>
    </td>
    <td data-order="{{ submission.score }}" class="center">
      {{ submission.score | float | round(2) }} / {{ submission.max_score | float | round(2) }}
    </td>
    <td data-order="{{ submission.code_score }}" class="center">
      {{ submission.code_score | float | round(2) }} / {{ submission.max_code_score | float | round(2) }}
    </td>
    <td data-order="{{ submission.written_score }}" class="center">
      {{ submission.written_score | float | round(2) }} / {{ submission.max_written_score | float | round(2) }}
    </td>
    {%- if submission.needs_manual_grade -%}
    <td data-search="needs manual grade" class="center">
      <span class="glyphicon glyphicon-ok"></span>
    </td>
    {%- else -%}
    <td data-search="" class="center">
    </td>
    {%- endif -%}
    {%- if submission.failed_tests -%}
    <td data-search="tests failed" class="center">
      <span class="glyphicon glyphicon-ok"></span>
    </td>
    {%- else -%}
    <td data-search="" class="center">
    </td>
    {%- endif -%}
    {%- if submission.flagged -%}
    <td data-search="flagged" class="center">
      <span data-search="flagged" class="glyphicon glyphicon-flag"></span>
    </td>
    {%- else -%}
    <td data-search="" class="center">
    </td>
    {%- endif -%}
  </tr>
  {%- endfor -%}
</tbody>
</table>
{%- endblock -%}

{%- block script -%}
<script type="text/javascript">
    $('span.glyphicon.name-hidden').tooltip({title: "Show student name"});
    $('span.glyphicon.name-shown').tooltip({title: "Hide student name"});
    $(document).ready(function(){
        $('#notebook-submissions').DataTable({
            info: false,
            paging: false,
            saveState: true,
        });
    });
</script>
{%- endblock -%}
