import os
import json

from tornado import web
from notebook.base.handlers import IPythonHandler
from ...api import Gradebook


class BaseHandler(IPythonHandler):

    @property
    def base_url(self):
        return super(BaseHandler, self).base_url.rstrip("/")

    @property
    def db_url(self):
        return self.settings['nbgrader_db_url']

    @property
    def gradebook(self):
        self.log.debug("getting gradebook")
        gb = self.settings['nbgrader_gradebook']
        if gb is None:
            gb = Gradebook(self.db_url)
            self.settings['nbgrader_gradebook'] = gb
        return gb

    @property
    def mathjax_url(self):
        return self.settings['mathjax_url']

    @property
    def notebook_dir(self):
        return self.settings['nbgrader_notebook_dir']

    @property
    def notebook_dir_format(self):
        return self.settings['nbgrader_notebook_dir_format']

    @property
    def nbgrader_step(self):
        return self.settings['nbgrader_step']

    @property
    def exporter(self):
        return self.settings['nbgrader_exporter']

    @property
    def notebook_url_prefix(self):
        return self.settings['nbgrader_notebook_url_prefix']

    def _filter_existing_notebooks(self, assignment_id, notebooks):
        path = os.path.join(
            self.notebook_dir,
            self.notebook_dir_format,
            "{notebook_id}.ipynb"
        )

        submissions = list()
        for nb in notebooks:
            filename = path.format(
                nbgrader_step=self.nbgrader_step,
                assignment_id=assignment_id,
                notebook_id=nb.name,
                student_id=nb.student.id
            )
            if os.path.exists(filename):
                submissions.append(nb)

        return sorted(submissions, key=lambda x: x.id)

    def _notebook_submission_indexes(self, assignment_id, notebook_id):
        notebooks = self.gradebook.notebook_submissions(notebook_id, assignment_id)
        submissions = self._filter_existing_notebooks(assignment_id, notebooks)
        return dict([(x.id, i) for i, x in enumerate(submissions)])

    def render(self, name, **ns):
        template = self.settings['nbgrader_jinja2_env'].get_template(name)
        return template.render(**ns)

    def write_error(self, status_code, **kwargs):
        if status_code == 500:
            html = self.render(
                'gradebook_500.tpl',
                base_url=self.base_url,
                error_code=500)

        elif status_code == 502:
            html = self.render(
                'gradebook_500.tpl',
                base_url=self.base_url,
                error_code=502)

        elif status_code == 403:
            html = self.render(
                'gradebook_403.tpl',
                base_url=self.base_url,
                error_code=403)

        else:
            return super(BaseHandler, self).write_error(status_code, **kwargs)

        self.write(html)
        self.finish()


class BaseApiHandler(BaseHandler):

    def get_json_body(self):
        """Return the body of the request as JSON data."""
        if not self.request.body:
            return None
        body = self.request.body.strip().decode('utf-8')
        try:
            model = json.loads(body)
        except Exception:
            self.log.debug("Bad JSON: %r", body)
            self.log.error("Couldn't parse JSON", exc_info=True)
            raise web.HTTPError(400, 'Invalid JSON in body of request')
        return model
