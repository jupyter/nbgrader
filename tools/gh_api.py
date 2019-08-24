"""Various GitHub API tools. Based on the gh_api.py library in the IPython repo."""

import requests
import json
import sys
import getpass

try:
    import requests_cache
except ImportError:
    print("no cache", file=sys.stderr)
else:
    requests_cache.install_cache("gh_api", expire_after=3600)

# Keyring stores passwords by a 'username', but we're not storing a username and
# password
fake_username = 'ipython_tools'


class Obj(dict):
    """Dictionary with attribute access to names."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, val):
        self[name] = val


token = None
def make_auth_header():
    global token

    if token is None:
        print("Please enter your GitHub access token. This will not be stored.")
        token = input("Token: ")

    return {'Authorization': 'token {}'.format(token)}


def get_paged_request(url, headers=None, **params):
    """get a full list, handling APIv3's paging"""
    results = []
    params.setdefault("per_page", 100)
    while True:
        if '?' in url:
            params = None
            print("fetching %s" % url, file=sys.stderr)
        else:
            print("fetching %s with %s" % (url, params), file=sys.stderr)
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        results.extend(response.json())
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            break
    return results


def get_issues_list(project, auth=False, **params):
    """get issues list"""
    params.setdefault("state", "closed")
    url = "https://api.github.com/repos/{project}/issues".format(project=project)
    if auth:
        headers = make_auth_header()
    else:
        headers = None
    pages = get_paged_request(url, headers=headers, **params)
    return pages


def get_pull_request(project, num, auth=False):
    """get pull request info  by number
    """
    url = "https://api.github.com/repos/{project}/pulls/{num}".format(project=project, num=num)
    if auth:
        header = make_auth_header()
    else:
        header = None
    print("fetching %s" % url, file=sys.stderr)
    response = requests.get(url, headers=header)
    response.raise_for_status()
    return json.loads(response.text, object_hook=Obj)


def get_pull_request_files(project, num, auth=False):
    """get list of files in a pull request"""
    url = "https://api.github.com/repos/{project}/pulls/{num}/files".format(project=project, num=num)
    if auth:
        header = make_auth_header()
    else:
        header = None
    return get_paged_request(url, headers=header)


def is_pull_request(issue):
    """Return True if the given issue is a pull request."""
    return bool(issue.get('pull_request', {}).get('html_url', None))


def get_milestones(project, auth=False, **params):
    params.setdefault('state', 'all')
    url = "https://api.github.com/repos/{project}/milestones".format(project=project)
    if auth:
        headers = make_auth_header()
    else:
        headers = None
    milestones = get_paged_request(url, headers=headers, **params)
    return milestones


def get_milestone(project, milestone, auth=False, **params):
    milestones = get_milestones(project, auth=auth, **params)
    for mstone in milestones:
        if mstone['title'] == milestone:
            return mstone
    else:
        raise ValueError("milestone %s not found" % milestone)


def get_milestone_id(project, milestone, auth=False, **params):
    milestones = get_milestones(project, auth=auth, **params)
    for mstone in milestones:
        if mstone['title'] == milestone:
            return mstone['number']
    else:
        raise ValueError("milestone %s not found" % milestone)


def get_pulls_list(project, auth=False, **params):
    """get pull request list"""
    params.setdefault("state", "closed")
    url = "https://api.github.com/repos/{project}/pulls".format(project=project)
    if auth:
        headers = make_auth_header()
    else:
        headers = None
    pages = get_paged_request(url, headers=headers, **params)
    return pages
