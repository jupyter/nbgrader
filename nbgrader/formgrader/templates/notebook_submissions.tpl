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
<li><a href="{{base_url}}/assignments">Assignments</a></li>
<li><a href="{{base_url}}/assignments/{{ assignment_id }}">{{ assignment_id }}</a></li>
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
    <td>
      <span class="glyphicon glyphicon-eye-open name-hidden" aria-hidden="true" onclick="toggle_name(true, {{ submission.index + 1 }});"></span>
      <span class="glyphicon glyphicon-eye-close name-shown" aria-hidden="true" onclick="toggle_name(false, {{ submission.index + 1 }});"></span>
    </td>
    <td>
      <a href="{{base_url}}/submissions/{{ submission.id }}" class="name-hidden">Submission #{{ submission.index + 1 }}</a>
      <a href="{{base_url}}/submissions/{{ submission.id }}" class="name-shown">{{ submission.last_name }}, {{ submission.first_name }}</a>
    </td>
    <td class="center">
      {{ submission.score | float | round(2) }} / {{ submission.max_score | float | round(2) }}
    </td>
    <td class="center">
      {{ submission.code_score | float | round(2) }} / {{ submission.max_code_score | float | round(2) }}
    </td>
    <td class="center">
      {{ submission.written_score | float | round(2) }} / {{ submission.max_written_score | float | round(2) }}
    </td>
    <td class="center">
      {%- if submission.needs_manual_grade -%}
      <span class="glyphicon glyphicon-ok"></span>
      {%- endif -%}
    </td>
    <td class="center">
      {%- if submission.failed_tests -%}
      <span class="glyphicon glyphicon-ok"></span>
      {%- endif -%}
    </td>
    <td class="center">
      {%- if submission.flagged -%}
      <span class="glyphicon glyphicon-flag"></span>
      {%- endif -%}
    </td>
  </tr>
  {%- endfor -%}
</tbody>
<script type="text/javascript">
$('span.glyphicon.name-hidden').tooltip({title: "Show student name"});
$('span.glyphicon.name-shown').tooltip({title: "Hide student name"});
</script>
{%- endblock -%}
