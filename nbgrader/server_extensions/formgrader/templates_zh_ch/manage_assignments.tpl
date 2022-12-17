{%- extends 'base.tpl' -%}

{%- block head -%}
<script>
var url_prefix = "{{ url_prefix }}";
var is_lab = {% if is_lab %}true{% else %}false{% endif %};
</script>

<script src="{{ base_url }}/formgrader/static/js/manage_assignments.js"></script>
{%- endblock -%}

{%- block title -%}
管理作业
{%- endblock -%}

{%- block sidebar -%}
<li role="presentation" class="active"><a href="{{ base_url }}/formgrader/manage_assignments">管理作业</a></li>
<li role="presentation"><a href="{{ base_url }}/formgrader/gradebook">手动评分</a></li>
<li role="presentation"><a href="{{ base_url }}/formgrader/manage_students">管理学生</a></li>
{%- endblock -%}

{%- block breadcrumbs -%}
<ol class="breadcrumb">
  <li class="active">作业</li>
</ol>
{%- endblock -%}

{%- block messages -%}
<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
  <div class="panel panel-default">
    <div class="panel-heading" role="tab" id="headingOne">
      <h4 class="panel-title">
        <a class="collapsed" role="button" data-toggle="collapse" data-parent="#accordion" href="#collapseOne" aria-expanded="false" aria-controls="collapseOne">
          指示 (click to expand)
        </a>
      </h4>
    </div>
    <div id="collapseOne" class="panel-collapse collapse" role="tabpanel" aria-labelledby="headingOne">
      <div class="panel-body">
        <ol>
          <li>去 <b>创建</b> 一项任务, 点击这个 "添加新作业..." 下面的按钮.</li>
          <li>去 <b>编辑作业文件</b>, 点击作业名称.</li>
          <li>去 <b>编辑作业元数据</b>, 点击编辑按钮.</li>
          <li>去 <b>产生</b> 作业的学生版本, 点击生成按钮.</li>
          <li>去 <b>预习</b> 作业的学生版本, 点击预览按钮.</li>
          <li><i>(JupyterHub only)</i> 去 <b>发布</b> 给学生的作业, 单击发布按钮.
          您可以通过再次单击来“取消发布”作业, 虽然请注意有些学生可能有
          已经访问了作业. <b>笔记</b> 释放按钮变成
          可用的, 这 <code>course_id</code> option must be set in <code>nbgrader_config.py</code>.
          For details, see <a href="http://nbgrader.readthedocs.io/en/stable/configuration/config_options.html">这个文档</a>.</li>
          <li><i>(JupyterHub only)</i> 去 <b>收集</b> 作业, 点击收集按钮.</li>
          <li>去 <b>汽车级</b> 投稿，点击已收集投稿数量. 你必须运行
          提交的自动评分器，然后才能手动评分。</li>
        </ol>
      </div>
    </div>
  </div>
</div>
{% if windows %}
<div class="alert alert-warning" id="warning-windows">
检测到 Windows 操作系统。请注意“发布”和“收集”
功能将不可用。
</div>
{% elif exchange_missing %}
<div class="alert alert-warning" id="warning-exchange">
交换目录在 <code>{{ exchange }}</code>不存在并且可能
不被创建。 “发布”和“收集”功能将不可用。
请参阅文档
<a href="http://nbgrader.readthedocs.io/en/stable/user_guide/managing_assignment_files.html#setting-up-the-exchange">设置交易所</a>
说明
</div>
{% elif not course_id %}
<div class="alert alert-warning" id="warning-course-id">
尚未设置课程ID <code>nbgrader_config.py</code>. 发布”
并且“收集”功能将不可用。请参阅文档
<a href="http://nbgrader.readthedocs.io/en/stable/user_guide/managing_assignment_files.html#setting-up-the-exchange">设置交易所</a>
说明.
</div>
{% endif %}
{%- endblock -%}

{%- block table_header -%}
<tr>
  <th>姓名</th>
  <th class="text-center">截止日期</th>
  <th class="text-center">状态</th>
  <th class="text-center no-sort">编辑</th>
  <th class="text-center no-sort">创建</th>
  <th class="text-center no-sort">预览</th>
  <th class="text-center no-sort">发布</th>
  <th class="text-center no-sort">收集</th>
  <th class="text-center"># 意见书</th>
  <th class="text-center no-sort">产生反馈</th>
  <th class="text-center no-sort">发布反馈</th>
</tr>
{%- endblock -%}

{%- block table_body -%}
<tr><td colspan="11">加载请稍候...</td></tr>
{%- endblock -%}

{%- block table_footer -%}
<tr>
  <td colspan="11">
    <span class="glyphicon glyphicon-plus" aria-hidden="true"></span>
    <a href="#" onClick="createAssignmentModal();">添加新作业...</a>
  </td>
</tr>
{%- endblock -%}
