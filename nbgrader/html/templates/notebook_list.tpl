<!doctype html>
<head>
<title>{{ assignment_id }}</title>

<script src="/static/lib/jquery-2.1.1.min.js"></script>
<script src="/static/lib/underscore-min.js"></script>
<script src="/static/lib/backbone-min.js"></script>
<script src="/static/lib/bootstrap.min.js"></script>
<script src="/static/js/notebooklist.js"></script>

<link rel="stylesheet" href="/static/css/bootstrap.min.css" />

<script type="text/javascript">
assignment_id = "{{ assignment_id }}";
assignment_uuid = "{{ assignment_uuid }}";
</script>

</head>

<body>
  <div class="container">
    <h1>{{ assignment_id }}</h1>
    <div class="panel panel-default">
      <table class="table">
        <thead><tr>
          <th>Notebook</th>
          <th>Student Name</th>
          <th>Student ID</th>
          <th>Score</th>
          <th>Needs manual grade</th>
        </tr></thead>
        <tbody id="notebook-list"></tbody>
      </table>
    </div>
  </div>
</body>
