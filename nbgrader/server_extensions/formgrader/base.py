import os
import json
import functools

from tornado import web
from jupyter_server.base.handlers import JupyterHandler
from ...api import Gradebook
from ...apps.api import NbGraderAPI


class BaseHandler(JupyterHandler):

    @property
    def base_url(self):
        return super(BaseHandler, self).base_url.rstrip("/")

    @property
    def db_url(self):
        return self.settings['nbgrader_coursedir'].db_url

    @property
    def url_prefix(self):
        return self.settings['nbgrader_formgrader'].url_prefix

    @property
    def coursedir(self):
        return self.settings['nbgrader_coursedir']

    @property
    def authenticator(self):
        return self.settings['nbgrader_authenticator']

    @property
    def gradebook(self):
        gb = self.settings['nbgrader_gradebook']
        if gb is None:
            self.log.debug("creating gradebook")
            gb = Gradebook(self.db_url, self.coursedir.course_id)
            self.settings['nbgrader_gradebook'] = gb
        return gb

    @property
    def mathjax_url(self):
        return self.settings['mathjax_url']

    @property
    def exporter(self):
        return self.settings['nbgrader_exporter']

    @property
    def api(self):
        level = self.log.level
        self.coursedir.parent.load_config_file()
        api = NbGraderAPI(
            self.coursedir, self.authenticator, parent=self.coursedir.parent)
        api.log_level = level
        return api

    def render(self, name, **ns):
        template = self.settings['nbgrader_jinja2_env'].get_template(name)
        return template.render(**ns)

    def write_error(self, status_code, **kwargs):
        if status_code == 500:
            html = self.render(
                'base_500.tpl',
                base_url=self.base_url,
                error_code=500)

        elif status_code == 502:
            html = self.render(
                'base_500.tpl',
                base_url=self.base_url,
                error_code=502)

        elif status_code == 403:
            html = self.render(
                'base_403.tpl',
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


def check_xsrf(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        _ = self.xsrf_token
        return f(self, *args, **kwargs)
    return wrapper


def check_notebook_dir(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.settings['nbgrader_bad_setup']:
            return self.write_error(500)
        return f(self, *args, **kwargs)
    return wrapper
