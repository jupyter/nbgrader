{%- extends 'basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}


{%- block header -%}
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8" />
<title>{{ nb.metadata.nbgrader.notebook_id }}</title>

<script>
nb = "{{ nb.metadata.nbgrader.notebook_id }}";
student = "{{ nb.metadata.nbgrader.student_id }}";
</script>

<script src="/static/lib/jquery-2.1.1.min.js"></script>
<script src="/static/lib/underscore-min.js"></script>
<script src="/static/lib/backbone-min.js"></script>
<script src="/static/lib/bootstrap.min.js"></script>
<script src="/static/js/formgrade.js"></script>

<link rel="stylesheet" href="/static/css/bootstrap.min.css" />

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<style type="text/css">
/* Overrides of notebook CSS for static HTML export */
body {
  overflow: visible;
  padding: 8px;
}

div#notebook {
  overflow: visible;
  border-top: none;
}

@media print {
  div.cell {
    display: block;
    page-break-inside: avoid;
  } 
  div.output_wrapper { 
    display: block;
    page-break-inside: avoid; 
  }
  div.output { 
    display: block;
    page-break-inside: avoid; 
  }
}

div.prompt {
  min-width: 21ex;
}
</style>

<!-- Loading mathjax macro -->
{{ mathjax() }}

</head>
{%- endblock header -%}

{% block body %}
<body>
  <div tabindex="-1" id="notebook" class="border-box-sizing">
    <div class="container" id="notebook-container">
{{ super() }}
    </div>
  </div>
</body>
{%- endblock body %}

{% block footer %}
</html>
{% endblock footer %}

{%- block any_cell scoped -%}
{%- if cell.metadata.nbgrader.grade -%}
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
{%- if cell.metadata.nbgrader.solution -%}
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
      <textarea class="comment" placeholder="Comments"></textarea>
    </div>
  </div>
</div>
{%- endif -%}
{%- endblock any_cell -%}
