<!doctype html>
<head>
  <title>nbgrader formgrade</title>

  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/components/bootstrap/css/bootstrap.min.css" />
  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/components/datatables.net-bs/css/dataTables.bootstrap.min.css">
  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/components/datatables.net-scroller-bs/css/scroller.bootstrap.min.css">
  <link rel="stylesheet" href="{{ base_url }}/formgrader/static/css/formgrade.css">

  <script src="{{ base_url }}/formgrader/static/components/jquery/jquery.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/underscore/underscore-min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/backbone/backbone-min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/bootstrap/js/bootstrap.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/datatables.net/js/jquery.dataTables.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>
  <script src="{{ base_url }}/formgrader/static/components/datatables.net-scroller/js/dataTables.scroller.min.js"></script>

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
      {%- endblock -%}
      {%- block table -%}
      {%- endblock -%}
    </div>
  </div>
  {%- block script -%}
  {%- endblock -%}
</body>

