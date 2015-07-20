{%- extends 'gradebook.tpl' -%}

{%- block body -%}
<div class="panel-body">
Sorry, you are not authorized to access the formgrader.
<span id="error-{{ error_code }}"></span>
</div>
{%- endblock -%}