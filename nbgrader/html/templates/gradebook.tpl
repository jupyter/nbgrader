<!doctype html>
<head>
  <title>nbgrader formgrade</title>

  <script src="/static/lib/jquery-2.1.1.min.js"></script>
  <script src="/static/lib/underscore-min.js"></script>
  <script src="/static/lib/backbone-min.js"></script>
  <script src="/static/lib/bootstrap.min.js"></script>

  <link rel="stylesheet" href="/static/css/bootstrap.min.css">
  <link rel="stylesheet" href="/static/css/formgrade.css">
</head>

<body>
  <nav class="navbar navbar-default" role="navigation">
    <div class="container">
      <div class="navbar-header">
        <a class="navbar-brand" href="#">nbgrader formgrade</a>
      </div>
      <div>
        <ul class="nav navbar-nav navbar-left">
          <ul class="breadcrumb list-inline">
            {%- block breadcrumb -%}
            {%- endblock -%}
          </ul>
        </ul>
        <ul class="nav navbar-nav navbar-right">
          <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">Change View <b class="caret"></b></a>
            <ul class="dropdown-menu">
              <li><a href="/assignments">Assignments</a></li>
              <li><a href="/students">Students</a></li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
  </nav>
  <div class="container">
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

