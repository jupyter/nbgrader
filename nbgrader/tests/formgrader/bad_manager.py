from .manager import HubAuthManager

__all__ = [
    'BadHubAuthManager'
]


class BadHubAuthManager(HubAuthManager):

    def _start_formgrader(self, configproxy_auth_token='foo'):
        self.env['JPY_API_TOKEN'] = 'abc'
        self.env['CONFIGPROXY_AUTH_TOKEN'] = configproxy_auth_token
        super(HubAuthManager, self)._start_formgrader()
