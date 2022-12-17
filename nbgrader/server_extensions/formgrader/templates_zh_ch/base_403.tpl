{%- extends 'base.tpl' -%}

{%- block title -%}
未授权
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
抱歉，您无权访问 formgrader
<span id="error-{{ error_code }}"></span>
</div>
{%- endblock -%}