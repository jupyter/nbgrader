import json
import functools
from tornado import web


def authenticated(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        result = self.auth.authenticate(self.request)
        if result is True:
            return f(self, *args, **kwargs) # Success
        elif result is False:
            raise web.HTTPError(403) # Forbidden
        else:
            self.redirect(result, permanent=False)  # Redirect
    return wrapper


class BaseHandler(web.RequestHandler):

    @property
    def gradebook(self):
        return self.settings['nbgrader_gradebook']

    @property
    def auth(self):
        return self.settings['nbgrader_auth']

    @property
    def mathjax_url(self):
        return self.settings['nbgrader_mathjax_url']

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
    def log(self):
        return self.settings['nbgrader_log']

    def render(self, name, **ns):
        template = self.settings['nbgrader_jinja2_env'].get_template(name)
        return template.render(**ns)

    def write_error(self, status_code, **kwargs):
        if status_code == 500:
            html = self.render(
                'gradebook_500.tpl',
                base_url=self.auth.base_url,
                error_code=500)

        elif status_code == 502:
            html = self.render(
                'gradebook_500.tpl',
                base_url=self.auth.base_url,
                error_code=502)

        elif status_code == 403:
            html = self.render(
                'gradebook_403.tpl',
                base_url=self.auth.base_url,
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
