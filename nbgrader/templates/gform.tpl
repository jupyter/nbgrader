{%- extends 'full.tpl' -%}

{%- block header -%}

{{ super() }}

<style type="text/css">
body {
  padding: 0px;
}
#main-form {
  position: fixed;
  top: 0px;
  z-index: 100000;
  border-bottom: 2px solid grey;
  width: 100%;
  background-color: white;
}
#main-form iframe {
  width: 100%;
  height: 300px;
}

#form-spacer {
  height: 300px;
}
</style>

{%- endblock header -%}


{% block body %}
<body>
  <div id="main-form">
    <span>Student ID: {{ resources['nbgrader']['student_id'] }}</span>
    <div class="container">
      <iframe src="https://docs.google.com/forms/d/{{resources['nbgrader']['form_id']}}/viewform?embedded=true" width="940" height="500" frameborder="0" marginheight="0" marginwidth="0">Loading...</iframe>
    </div>
  </div>
  <div id="form-spacer"></div>
  <div tabindex="-1" id="notebook" class="border-box-sizing">
    <div class="container" id="notebook-container">
{{ super() }}
    </div>
  </div>
</body>
{%- endblock body %}