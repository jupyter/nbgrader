{% macro header(resources) %}
<meta charset="utf-8" />
<title>{{ resources.notebook_id }}</title>

<script src="{{resources.base_url}}/static/components/jquery/jquery.min.js"></script>
<script src="{{resources.base_url}}/static/components/jquery-color/jquery.color.js"></script>
<script src="{{resources.base_url}}/static/components/underscore/underscore-min.js"></script>
<script src="{{resources.base_url}}/static/components/backbone/backbone-min.js"></script>
<script src="{{resources.base_url}}/static/components/bootstrap/js/bootstrap.min.js"></script>
<script type="text/javascript" src="{{resources.base_url}}/static/components/autosize/dist/autosize.min.js"></script>

<script type="text/javascript">
var submission_id = "{{ resources.submission_id }}";
var notebook_id = "{{ resources.notebook_id }}";
var assignment_id = "{{ resources.assignment_id }}";
var base_url = "{{resources.base_url}}";
</script>

<script src="{{resources.base_url}}/static/js/keyboardmanager.js"></script>
<script src="{{resources.base_url}}/static/js/models.js"></script>
<script src="{{resources.base_url}}/static/js/formgrade.js"></script>
<script type="text/javascript">
function toggle_name(on) {
  $(".name-shown").tooltip('hide');
  $(".name-hidden").tooltip('hide');
  if (on) {
    $(".name-shown").show();
    $(".name-hidden").hide();
  } else {
    $(".name-hidden").show();
    $(".name-shown").hide();
  }
}
</script>

<link rel="stylesheet" href="{{resources.base_url}}/static/components/bootstrap/css/bootstrap.min.css" />
{% endmacro %}

{% macro nav(resources) %}
  <nav class="navbar navbar-default navbar-fixed-top" role="navigation">
    <div class="container">
      <div class="col-md-2">
        <ul class="nav navbar-nav navbar-left">
          <li class="previous">
            <a data-toggle="tooltip" data-trigger="hover" data-placement="right" title="{{ resources.index }} remaining" href="{{resources.base_url}}/submissions/{{ resources.submission_id }}/prev">
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
              <a class="name-hidden" data-toggle="tooltip" data-placement="bottom" title="Open live notebook" target="_blank" href="{{ resources.notebook_path }}">
                Submission #{{ resources.index + 1 }}
              </a>
              <a class="name-shown" data-toggle="tooltip" data-placement="bottom" title="Open live notebook" target="_blank" href="{{ resources.notebook_path }}">
                {{ resources.last_name }}, {{ resources.first_name }}
              </a>
              <span class="glyphicon glyphicon-eye-open name-hidden" aria-hidden="true" onclick="toggle_name(true);"></span>
              <span class="glyphicon glyphicon-eye-close name-shown" aria-hidden="true" onclick="toggle_name(false);"></span>
            </li>
            {%- else -%}
            <li>
              <span class="name-hidden">
                Submission #{{ resources.index + 1 }}
              </span>
              <span class="name-shown">
                {{ resources.last_name }}, {{ resources.first_name }}
              </span>
              <span class="glyphicon glyphicon-eye-open name-hidden" aria-hidden="true" onclick="toggle_name(true);"></span>
              <span class="glyphicon glyphicon-eye-close name-shown" aria-hidden="true" onclick="toggle_name(false);"></span>
            </li>
            {%- endif -%}
          </ul>
        </ul>
      </div>
      <div class="col-md-2">
        <ul class="nav navbar-nav navbar-right">
          <li class="next">
            <a class="tabbable" data-trigger="hover" data-toggle="tooltip" data-placement="left" title="{{ resources.total - (resources.index + 1) }} remaining" href="{{resources.base_url}}/submissions/{{ resources.submission_id }}/next">
            Next &rarr;
            </a>
          </li>
        </ul>
      </div>
    </div>
    </div>
  </nav>
  <script type="text/javascript">
  $('span.glyphicon.name-hidden').tooltip({title: "Show student name", placement: "bottom", trigger: "hover"});
  $('span.glyphicon.name-shown').tooltip({title: "Hide student name", placement: "bottom", trigger: "hover"});
  </script>
{% endmacro %}