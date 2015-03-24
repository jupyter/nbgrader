"""JupyterHub authenticator."""
import requests
import os
import json
from flask import request, redirect, abort
from IPython.utils.traitlets import Unicode, Int, List
from .base import BaseAuth
from nbgrader.html.formgrade import blueprint


class HubAuth(BaseAuth):
    """Jupyter hub authenticator."""

    graders = List([], config=True, help="List of JupyterHub user names allowed to grade.")

    proxy_address = Unicode(None, config=True, help="Address of the configurable-http-proxy server.")
    def _proxy_address_default(self):
        return self._ip
    proxy_port = Int(8001, config=True, help="Port of the configurable-http-proxy server.")

    hub_address = Unicode(None, config=True, help="Address of the hub server.")
    def _hub_address_default(self):
        return self._ip
    hub_port = Int(8000, config=True, help="Port of the hub server.")
    
    hubapi_address = Unicode(None, config=True, help="Address of the hubapi server.")
    def _hubapi_address_default(self):
        return self._ip
    hubapi_port = Int(8081, config=True, help="Port of the hubapi server.")
    hubapi_cookie = Unicode("jupyter-hub-token", config=True, help="Name of the cookie used by JupyterHub")

    def __init__(self, *args, **kwargs):
        super(HubAuth, self).__init__(*args, **kwargs)

        # Save API auth tokens.
        self._hubapi_token = os.environ.get('JPY_API_TOKEN')
        self._proxy_token = os.environ.get('CONFIGPROXY_AUTH_TOKEN')

        # If the proxy and/or hub address aren't set, assume that it's on the
        # same machine as the formgrader server.
        if self.hub_address is None:
            self.hub_address = self._ip
        if self.hubapi_address is None:
            self.hubapi_address = self._ip
        if self.proxy_address is None:
            self.proxy_address = self._ip

        # Create base URLs for the hub and proxy.
        self._hub_base_url = 'http://{}:{}'.format(self.hub_address, self.hub_port)
        self._hubapi_base_url = 'http://{}:{}'.format(self.hubapi_address, self.hubapi_port)
        self._proxy_base_url = 'http://{}:{}'.format(self.proxy_address, self.proxy_port)

        # Register self as a route of the configurable-http-proxy and then
        # update the base_url to point to the new path.
        response = self._proxy_request('/api/routes/hub/formgrade', method='POST', body={
            'target': self._base_url
        })
        if response.status_code != 201:
            raise Exception('Error while trying to add JupyterHub route. {}: {}'.format(response.status_code, response.text))
        self._base_url = self._hub_base_url + '/hub/formgrade'

        # Redirect all formgrade request to the correct API method.
        self._app.register_blueprint(blueprint, static_url_path='/hub/formgrade/static', url_prefix='/hub/formgrade', url_defaults={'name': 'hub'})

    def authenticate(self):
        """Authenticate a request.
        Returns a boolean or flask redirect."""

        # If auth cookie doesn't exist, redirect to the login page with
        # next set to redirect back to the this page.
        if 'jupyter-hub-token' not in request.cookies:
            return redirect(self._hub_base_url + '/hub/login?next=' + self._hub_base_url + '/hub/formgrade')
        cookie = request.cookies[self.hubapi_cookie]

        # Check with the Hub to see if the auth cookie is valid.
        response = self._hubapi_request('/hub/api/authorizations/cookie/' + self.hubapi_cookie + '/' + cookie)
        if response.status_code == 200:

            #  Auth information recieved.
            data = response.json()
            if 'user' in data:
                user = data['user']

                # Check if the user name is registered as a grader.
                if user in self.graders:
                    self._user = user
                    return True
                else:
                    self.log.warn('Unauthorized user "%s" attempted to access the formgrader.' % user)
            else:
                self.log.warn('Malformed response from the JupyterHub auth API.')
                abort(500, "Failed to check authorization, malformed response from Hub auth.")
        elif response.status_code == 403:
            self.log.error("I don't have permission to verify cookies, my auth token may have expired: [%i] %s", response.status_code, response.reason)
            abort(500, "Permission failure checking authorization, I may need to be restarted")
        elif response.status_code >= 500:
            self.log.error("Upstream failure verifying auth token: [%i] %s", response.status_code, response.reason)
            abort(502, "Failed to check authorization (upstream problem)")
        elif response.status_code >= 400:
            self.log.warn("Failed to check authorization: [%i] %s", response.status_code, response.reason)
            abort(500, "Failed to check authorization")
        else:
            # Auth invalid, reauthenticate.
            return redirect(self._hub_base_url + '/hub/login?next=' + self._hub_base_url + '/hub/formgrade')
        return False

    def notebook_server_exists(self):
        """Does the notebook server exist?"""
        return True

    def get_notebook_url(self, relative_path):
        """Gets the notebook's url."""
        return "http://{}:{}/{}/notebooks/{}".format(
            self.hub_address,
            self.hub_port,
            self._user,
            relative_path)

    def _hubapi_request(self, *args, **kwargs):
        return self._request('hubapi', *args, **kwargs)

    def _proxy_request(self, *args, **kwargs):
        return self._request('proxy', *args, **kwargs)

    def _request(self, service, relative_path, method='GET', body=None):
        base_url = getattr(self, '_%s_base_url' % service)
        token = getattr(self, '_%s_token' % service)

        data = body
        if isinstance(data, (dict,)):
            data = json.dumps(data)

        return requests.request(method, base_url + relative_path, headers={
            'Authorization': 'token %s' % token
        }, data=data)
