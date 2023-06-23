{%- extends 'manage_students_base.tpl' -%}

{%- block head -%}
<script src="{{ base_url }}/formgrader/static/js/manage_students.js"></script>
{%- endblock -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li class="active">学生</li>
</ol>
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>姓名</th>
  <th class="text-center">学生 ID</th>
  <th class="text-center">邮箱</th>
  <th class="text-center">总体得分</th>
  <th class="text-center no-sort">编辑学生</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="5">加载请稍候...</td></tr>
{%- endblock -%}

{%- block table_footer -%}
<tr>
  <td colspan="5">
    <span class="glyphicon glyphicon-plus" aria-hidden="true"></span>
    <a href="#" onClick="createStudentModal();">添加新学生...</a>
  </td>
</tr>
{%- endblock -%}