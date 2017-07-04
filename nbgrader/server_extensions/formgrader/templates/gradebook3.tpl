{%- extends 'gradebook.tpl' -%}

{%- block head -%}
<script>
var assignment_id = "{{ assignment_id }}";
var notebook_id = "{{ notebook_id }}";
</script>

<script src="{{ base_url }}/formgrader/static/js/gradebook3.js"></script>
{%- endblock head -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li><a href="{{ base_url }}/formgrader/gradebook">Gradebook</a></li>
  <li><a href="{{ base_url }}/formgrader/gradebook/{{ assignment_id }}">{{ assignment_id }}</a></li>
  <li class="active">{{ notebook_id }}</li>
</ol>
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th></th>
  <th>Submission ID</th>
  <th class="text-center">Overall Score</th>
  <th class="text-center">Code Score</th>
  <th class="text-center">Written Score</th>
  <th class="text-center">Needs Manual Grade?</th>
  <th class="text-center">Tests Failed?</th>
  <th class="text-center">Flagged?</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="7">Loading, please wait...</td></tr>
{%- endblock -%}
