{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}

{%- block header -%}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<title>{{ resources.notebook_id }}</title>

<script src="{{resources.base_url}}/static/components/jquery/jquery.min.js"></script>
<script src="{{resources.base_url}}/static/components/underscore/underscore-min.js"></script>
<script src="{{resources.base_url}}/static/components/backbone/backbone-min.js"></script>
<script src="{{resources.base_url}}/static/components/bootstrap/js/bootstrap.min.js"></script>

<script type="text/javascript">
var submission_id = "{{ resources.submission_id }}";
var notebook_id = "{{ resources.notebook_id }}";
var assignment_id = "{{ resources.assignment_id }}";
var base_url = "{{resources.base_url}}";
</script>

<script src="{{resources.base_url}}/static/js/formgrade.js"></script>

<link rel="stylesheet" href="{{resources.base_url}}/static/components/bootstrap/css/bootstrap.min.css" />

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<!-- Loading mathjax macro -->
{{ mathjax() }}

<link rel="stylesheet" href="{{resources.base_url}}/static/css/formgrade.css" />

</head>
{%- endblock header -%}

{% block body %}
<body>
  <nav class="navbar navbar-default navbar-fixed-top" role="navigation">
    <div class="container">
      <div class="col-md-2">
        <ul class="nav navbar-nav navbar-left">
          <li class="previous">
            <a data-toggle="tooltip" data-placement="right" title="{{ resources.index }} remaining" href="{{resources.base_url}}/submissions/{{ resources.submission_id }}/prev">
            &larr; Prev
            </a>
          </li>
        </ul>
      </div>
      <div class="col-md-8">
        <ul class="nav text-center">
          <ul class="breadcrumb">
            <li><a href="{{resources.base_url}}/assignments">Assignments</a></li>
            <li><a href="{{resources.base_url}}/assignments/{{ resources.assignment_id }}">{{ resources.assignment_id }}</a></li>
            <li><a href="{{resources.base_url}}/assignments/{{ resources.assignment_id }}/{{ resources.notebook_id }}">{{ resources.notebook_id }}</a></li>
            {%- if resources.notebook_server_exists -%}
            <li class="active live-notebook">
              <a data-toggle="tooltip" data-placement="right" title="Open live notebook" target="_blank" href="{{ resources.notebook_path }}">
                Submission #{{ resources.index + 1 }}
              </a>
            </li>
            {%- else -%}
              <li>Submission #{{ resources.index + 1 }}</li>
            {%- endif -%}
          </ul>
        </ul>
      </div>
      <div class="col-md-2">
        <ul class="nav navbar-nav navbar-right">
          <li class="next">
            <a data-toggle="tooltip" data-placement="left" title="{{ resources.total - (resources.index + 1) }} remaining" href="{{resources.base_url}}/submissions/{{ resources.submission_id }}/next">
            Next &rarr;
            </a>
          </li>
        </ul>
      </div>
    </div>
    </div>
  </nav>
  <div class="container">
    <div class="panel panel-default">
      <div class="panel-heading">
        <h4 class="panel-title">
          <span>{{ resources.notebook_id }}</span>
          <span class="pull-right">Submission {{ resources.index + 1 }} / {{ resources.total }}</span>
        </h4>
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

{% macro score(cell) -%}
  <span id="{{ cell.metadata.nbgrader.grade_id }}-saved" class="glyphicon glyphicon-floppy-saved save-icon score-saved"></span>
  <div class="pull-right">
    <span class="btn-group btn-group-sm scoring-buttons" role="group">
      <button type="button" class="btn btn-success" id="{{ cell.metadata.nbgrader.grade_id }}-full-credit">Full credit</button>
      <button type="button" class="btn btn-danger" id="{{ cell.metadata.nbgrader.grade_id }}-no-credit">No credit</button>
    </span>
    <span>
      <input class="score" id="{{ cell.metadata.nbgrader.grade_id }}" style="width: 4em;" type="number" /> / {{ cell.metadata.nbgrader.points | float | round(2) }}
    </span>
  </div>
{%- endmacro %}


{% macro nbgrader_heading(cell) -%}
<div class="panel-heading">
{%- if cell.metadata.nbgrader.solution -%}
  <span class="nbgrader-label">Student's answer</span>
  <span class="glyphicon glyphicon-floppy-saved comment-saved save-icon"></span>
  {%- if cell.metadata.nbgrader.grade -%}
  {{ score(cell) }}
  {%- endif -%}
{%- elif cell.metadata.nbgrader.grade -%}
  <span class="nbgrader-label"><code>{{ cell.metadata.nbgrader.grade_id }}</code></span>
  {{ score(cell) }}
{%- endif -%}
</div>  
{%- endmacro %}

{% macro nbgrader_footer(cell) -%}
{%- if cell.metadata.nbgrader.solution -%}
<div class="panel-footer">
  <div><textarea class="comment" placeholder="Comments"></textarea></div>
</div>
{%- endif -%}
{%- endmacro %}

{% block markdowncell scoped %}
<div class="cell border-box-sizing text_cell rendered">
  {{ self.empty_in_prompt() }}

  {%- if 'nbgrader' in cell.metadata and (cell.metadata.nbgrader.solution or cell.metadata.nbgrader.grade) -%}
  <div class="panel panel-primary nbgrader_cell">
    {{ nbgrader_heading(cell) }}
    <div class="panel-body">
      <div class="text_cell_render border-box-sizing rendered_html">
        {{ cell.source  | markdown2html | strip_files_prefix }}
      </div>
    </div>
    {{ nbgrader_footer(cell) }}
  </div>

  {%- else -%}

  <div class="inner_cell">
    <div class="text_cell_render border-box-sizing rendered_html">
      {{ cell.source  | markdown2html | strip_files_prefix }}
    </div>
  </div>

  {%- endif -%}

</div>
{% endblock markdowncell %}

{% block input %}
  {%- if 'nbgrader' in cell.metadata and (cell.metadata.nbgrader.solution or cell.metadata.nbgrader.grade) -%}
  <div class="panel panel-primary nbgrader_cell">
    {{ nbgrader_heading(cell) }}
    <div class="panel-body">
      <div class="input_area">
        {{ cell.source | highlight_code(metadata=cell.metadata) }}
      </div>
    </div>
    {{ nbgrader_footer(cell) }}
  </div>

  {%- else -%}
  
  <div class="inner_cell">
    <div class="input_area">
      {{ cell.source | highlight_code(metadata=cell.metadata) }}
    </div>
  </div>
  {%- endif -%}

{% endblock input %}
