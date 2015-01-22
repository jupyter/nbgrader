{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}

{%- block header -%}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<title>{{ resources.notebook_id }}</title>

<script src="/static/lib/jquery-2.1.1.min.js"></script>
<script src="/static/lib/underscore-min.js"></script>
<script src="/static/lib/backbone-min.js"></script>
<script src="/static/lib/bootstrap.min.js"></script>

<script type="text/javascript">
var nb_uuid = "{{ resources.notebook_uuid }}";
</script>

<script src="/static/js/formgrade.js"></script>

<link rel="stylesheet" href="/static/css/bootstrap.min.css" />

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<!-- Loading mathjax macro -->
{{ mathjax() }}

<link rel="stylesheet" href="/static/css/formgrade.css" />

</head>
{%- endblock header -%}

{% block body %}
<body>
  <nav class="navbar navbar-default navbar-fixed-top" role="navigation">
    <div class="container">
      <div class="col-md-2">
        <ul class="nav navbar-nav navbar-left">
          {%- if resources.prev -%}
          <li class="previous">
            <a data-toggle="tooltip" data-placement="right" title="{{ resources.prev.last_name }}, {{ resources.prev.first_name }}" href="/assignments/{{ resources.assignment_id }}/{{ resources.notebook_id }}/{{ resources.prev.student_id }}">
            &larr; Prev
            </a>
          </li>
          {%- else -%}
          <li class="previous disabled"><a>&larr; Prev</a></li>
          {%- endif -%}
        </ul>
      </div>
      <div class="col-md-8">
        <ul class="nav text-center">
          <ul class="breadcrumb">
            <li><a href="/assignments">Assignments</a></li>
            <li><a href="/assignments/{{ resources.assignment_id }}">{{ resources.assignment_id }}</a></li>
            <li><a href="/assignments/{{ resources.assignment_id }}/{{ resources.notebook_id }}">{{ resources.notebook_id }}</a></li>
            <li class="active">{{ resources.student.student_id }}</li>
          </ul>
        </ul>
      </div>
      <div class="col-md-2">
        <ul class="nav navbar-nav navbar-right">
          {%- if resources.next -%}
          <li class="next">
            <a data-toggle="tooltip" data-placement="left" title="{{ resources.next.last_name }}, {{ resources.next.first_name }}" href="/assignments/{{ resources.assignment_id }}/{{ resources.notebook_id }}/{{ resources.next.student_id }}">
            Next &rarr;
            </a>
          </li>
          {%- else -%}
          <li class="next disabled"><a>Next &rarr;</a></li>
          {%- endif -%}
        </ul>
      </div>
    </div>
    </div>
  </nav>
  <div class="container">
    <div class="panel panel-default">
      <div class="panel-heading">
        <h4>{{ resources.notebook_id }} - {{ resources.student.last_name }}, {{ resources.student.first_name }}</h4>
      </div>
      <div class="panel-body">
        <div id="notebook" class="border-box-sizing">
          <div class="container" id="notebook-container">
            {{ super() }}
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
{%- endblock body %}

{% block footer %}
</html>
{% endblock footer %}

{%- block any_cell scoped -%}
{%- if 'nbgrader' in cell.metadata and cell.metadata.nbgrader.grade -%}
<div class="cell border-box-sizing code_cell rendered">
  <div class="input">
    <div class="prompt input_prompt">
      {%- if cell.prompt_number is defined -%}
      Score[{{ cell.prompt_number|replace(None, "&nbsp;") }}]:
      {%- else -%}
      Score:
      {%- endif -%}
    </div>
    <div class="inner_cell">
      <div style="display: inline;">
        <input class="score" id="{{ cell.metadata.nbgrader.grade_id }}" style="width: 4em;" type="number" /> / {{ cell.metadata.nbgrader.points }}
        <span style="margin-left: 1em;" class="glyphicon glyphicon-floppy-saved"></span>
      </div>
    </div>
  </div>
</div>
{%- endif -%}
{{ super() }}
{%- if 'nbgrader' in cell.metadata and cell.metadata.nbgrader.solution -%}
<div class="cell border-box-sizing code_cell rendered">
  <div class="input">
    <div class="prompt input_prompt">
      {%- if cell.prompt_number is defined -%}
      Comments[{{ cell.prompt_number|replace(None, "&nbsp;") }}]:
      {%- else -%}
      Comments:
      {%- endif -%}
    </div>
    <div class="inner_cell">
      <p style="margin: 0.4em 0;">Instructor feedback:<span style="margin-left: 1em;" class="glyphicon glyphicon-floppy-saved"></span></p>
      <textarea class="comment" placeholder="Comments"></textarea>
    </div>
  </div>
</div>
{%- endif -%}
{%- endblock any_cell -%}
