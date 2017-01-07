<!doctype html>
<head>
  <title>nbgrader formgrade</title>

  <script src="{{ base_url }}/formgrader/static/components/jquery/jquery.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/underscore/underscore-min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/backbone/backbone-min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/bootstrap/js/bootstrap.min.js"></script>

  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/components/bootstrap/css/bootstrap.min.css" />
  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/css/formgrade.css">

  {%- block head -%}
  {%- endblock -%}
</head>

<body>
  <nav class="navbar navbar-default navbar-fixed-top" role="navigation">
    <div class="container">
      <div class="navbar-header">
        <a class="navbar-brand" href="#">nbgrader formgrade</a>
      </div>
      <div>
        <ul class="nav navbar-nav navbar-left">
          <ul class="breadcrumb">
            {%- block breadcrumb -%}
            {%- endblock -%}
          </ul>
        </ul>
        <ul class="nav navbar-nav navbar-right">
          <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">Change View <b class="caret"></b></a>
            <ul class="dropdown-menu">
              <li><a href="{{ base_url }}/formgrader/assignments">Assignments</a></li>
              <li><a href="{{ base_url }}/formgrader/students">Students</a></li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
  </nav>
  <div class="container" id="gradebook">
    <div class="panel panel-default">
      {%- block body -%}
      <div class="panel-body"></div>
      {%- endblock -%}
      <table class="table table-hover">
        {%- block table -%}
        {%- endblock -%}
      </table>
    </div>
  </div>
</body>

