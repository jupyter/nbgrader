{%- extends 'base.tpl' -%}

{%- block title -%}
手动评分
{%- endblock -%}

{%- block sidebar -%}
<li role="presentation"><a href="{{ base_url }}/formgrader/manage_assignments">管理作业</a></li>
<li role="presentation" class="active"><a href="{{ base_url }}/formgrader/gradebook">手动评分</a></li>
<li role="presentation"><a href="{{ base_url }}/formgrader/manage_students">管理学生</a></li>
{%- endblock -%}