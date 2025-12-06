from nbgrader.auth import JupyterHubAuthPlugin
c = get_config()
c.Exchange.path_includes_course = True
c.Authenticator.plugin_class = JupyterHubAuthPlugin
c.NbGrader.course_titles = {
    'course101': 'Course 101',
    'course123': 'Course 123'
}
