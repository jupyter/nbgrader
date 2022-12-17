{%- extends 'base.tpl' -%}

{%- block title -%}
错误
{%- endblock -%}

{%- block body -%}
<div class="panel-body">
抱歉，formgrader 遇到错误。请联系管理员
formgrader 以获得进一步的帮助。
<span id="error-{{ error_code }}"></span>
</div>
{%- endblock -%}