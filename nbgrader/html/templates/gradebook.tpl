<!doctype html>
<head>
  <title>nbgrader formgrade</title>

  <script src="/static/lib/jquery-2.1.1.min.js"></script>
  <script src="/static/lib/underscore-min.js"></script>
  <script src="/static/lib/backbone-min.js"></script>
  <script src="/static/lib/bootstrap.min.js"></script>

  <link href="//maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/bootstrap.min.css">
  <link rel="stylesheet" href="/static/css/formgrade.css">
</head>

<body>
  <div class="container">
    <h2>nbgrader formgrade</h2>
    <div class="panel panel-default">
      <div class="panel-heading">
        <ol class="breadcrumb">
          {%- block breadcrumb -%}
          {%- endblock -%}
        </ol>
      </div>
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

