{%- extends 'gradebook_base.tpl' -%}

{%- block head -%}
<script>
var assignment_id = "{{ assignment_id }}";
</script>

<script src="{{ base_url }}/formgrader/static/js/gradebook_notebooks.js"></script>
{%- endblock head -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li><a href="{{ base_url }}/formgrader/gradebook">手动评分</a></li>
  <li class="active">{{ assignment_id }}</li>
</ol>
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>笔记 ID</th>
  <th class="text-center">平均分</th>
  <th class="text-center">平均代码得分</th>
  <th class="text-center">平均笔试成绩</th>
  <th class="text-center">平均任务分数</th>
  <th class="text-center">需要手动评分?</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="6">加载请稍候...</td></tr>
{%- endblock -%}
