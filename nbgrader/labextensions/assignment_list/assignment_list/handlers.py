import json

from notebook.base.handlers import APIHandler
from notebook.utils import url_path_join
import tornado


from ....exchange import ExchangeFactory


lister = ExchangeFactory(config=None).List(coursedir='hi', authenticator='ji', config=None)assignments = lister.start()

class RouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post, 
    # patch, put, delete, options) to ensure only authorized user can request the 
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "This is /assignment_list/get_example endpoint!"
        }))

class CouseListHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post, 
    # patch, put, delete, options) to ensure only authorized user can request the 
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({"success": True, "value": ["math", "english", "history"]}))

class AssignmentListHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        course_id = self.request.headers.get("course_id")
        self.finish(json.dumps({"success": True, "value": [{"course_id": "math", "assignment_id": "a1", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/a1", "notebooks": [{"notebook_id": "f1", "path": "/srv/nbgrader/exchange/math/outbound/a1/f1.ipynb"}]}, {"course_id": "math", "assignment_id": "a2", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/a2", "notebooks": [{"notebook_id": "f2", "path": "/srv/nbgrader/exchange/math/outbound/a2/f2.ipynb"}]}, {"course_id": "math", "assignment_id": "ps1", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/ps1", "notebooks": [{"notebook_id": "problem1", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem1.ipynb"}, {"notebook_id": "problem2", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem2.ipynb"}]}]}))

class AssignmentActionHandler(APIHandler):

    @tornado.web.authenticated
    def post(self, action):
        input_data = self.get_json_body()
        if action == 'fetch':
            assignment_id = input_data['assignment_id']
            if assignment_id == 'a2':
                self.finish({"success": True, "value": [{"course_id": "math", "assignment_id": "a1", "status": "fetched", "path": "a1", "notebooks": [{"notebook_id": "f1", "path": "a1/f1.ipynb"}]}, {"course_id": "math", "assignment_id": "a2", "status": "fetched", "path": "a2", "notebooks": [{"notebook_id": "f2", "path": "a2/f2.ipynb"}]}, {"course_id": "math", "assignment_id": "ps1", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/ps1", "notebooks": [{"notebook_id": "problem1", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem1.ipynb"}, {"notebook_id": "problem2", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem2.ipynb"}]}, {"course_id": "math", "student_id": "math-instructor", "assignment_id": "a1", "status": "submitted", "submissions": [{"course_id": "math", "student_id": "math-instructor", "assignment_id": "a1", "timestamp": "2020-04-29 21:58:53.988500 UTC", "status": "submitted", "path": "/home/math-instructor/.local/share/jupyter/nbgrader_cache/math/math-instructor+a1+2020-04-29 21:58:53.988500 UTC", "notebooks": [{"notebook_id": "f1", "path": "/home/math-instructor/.local/share/jupyter/nbgrader_cache/math/math-instructor+a1+2020-04-29 21:58:53.988500 UTC/f1.ipynb", "has_local_feedback": True, "has_exchange_feedback": True, "local_feedback_path": "./a1/feedback/2020-04-29 21:58:53.988500 UTC/f1.html", "feedback_updated": False}], "has_local_feedback": True, "has_exchange_feedback": True, "feedback_updated": False, "local_feedback_path": "./a1/feedback/2020-04-29 21:58:53.988500 UTC"}]}]})
            else:
                self.finish({"success": True, "value": [{"course_id": "math", "assignment_id": "a1", "status": "fetched", "path": "a1", "notebooks": [{"notebook_id": "f1", "path": "a1/f1.ipynb"}]}, {"course_id": "math", "assignment_id": "a2", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/a2", "notebooks": [{"notebook_id": "f2", "path": "/srv/nbgrader/exchange/math/outbound/a2/f2.ipynb"}]}, {"course_id": "math", "assignment_id": "ps1", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/ps1", "notebooks": [{"notebook_id": "problem1", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem1.ipynb"}, {"notebook_id": "problem2", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem2.ipynb"}]}]})
        elif action == 'submit':
            self.finish({"success": True, "value": [{"course_id": "math", "assignment_id": "a1", "status": "fetched", "path": "a1", "notebooks": [{"notebook_id": "f1", "path": "a1/f1.ipynb"}]}, {"course_id": "math", "assignment_id": "a2", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/a2", "notebooks": [{"notebook_id": "f2", "path": "/srv/nbgrader/exchange/math/outbound/a2/f2.ipynb"}]}, {"course_id": "math", "assignment_id": "ps1", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/ps1", "notebooks": [{"notebook_id": "problem1", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem1.ipynb"}, {"notebook_id": "problem2", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem2.ipynb"}]}, {"course_id": "math", "student_id": "math-instructor", "assignment_id": "a1", "status": "submitted", "submissions": [{"course_id": "math", "student_id": "math-instructor", "assignment_id": "a1", "timestamp": "2020-04-29 21:58:53.988500 UTC", "status": "submitted", "path": "/home/math-instructor/.local/share/jupyter/nbgrader_cache/math/math-instructor+a1+2020-04-29 21:58:53.988500 UTC", "notebooks": [{"notebook_id": "f1", "path": "/home/math-instructor/.local/share/jupyter/nbgrader_cache/math/math-instructor+a1+2020-04-29 21:58:53.988500 UTC/f1.ipynb", "has_local_feedback": False, "has_exchange_feedback": False, "local_feedback_path": None, "feedback_updated": False}], "has_local_feedback": False, "has_exchange_feedback": False, "feedback_updated": False, "local_feedback_path": None}]}]})
        elif action == 'fetch_feedback':
            self.finish({"success": True, "value": [{"course_id": "math", "assignment_id": "a1", "status": "fetched", "path": "a1", "notebooks": [{"notebook_id": "f1", "path": "a1/f1.ipynb"}]}, {"course_id": "math", "assignment_id": "a2", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/a2", "notebooks": [{"notebook_id": "f2", "path": "/srv/nbgrader/exchange/math/outbound/a2/f2.ipynb"}]}, {"course_id": "math", "assignment_id": "ps1", "status": "released", "path": "/srv/nbgrader/exchange/math/outbound/ps1", "notebooks": [{"notebook_id": "problem1", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem1.ipynb"}, {"notebook_id": "problem2", "path": "/srv/nbgrader/exchange/math/outbound/ps1/problem2.ipynb"}]}, {"course_id": "math", "student_id": "math-instructor", "assignment_id": "a1", "status": "submitted", "submissions": [{"course_id": "math", "student_id": "math-instructor", "assignment_id": "a1", "timestamp": "2020-04-29 21:58:53.988500 UTC", "status": "submitted", "path": "/home/math-instructor/.local/share/jupyter/nbgrader_cache/math/math-instructor+a1+2020-04-29 21:58:53.988500 UTC", "notebooks": [{"notebook_id": "f1", "path": "/home/math-instructor/.local/share/jupyter/nbgrader_cache/math/math-instructor+a1+2020-04-29 21:58:53.988500 UTC/f1.ipynb", "has_local_feedback": True, "has_exchange_feedback": True, "local_feedback_path": "./a1/feedback/2020-04-29 21:58:53.988500 UTC/f1.html", "feedback_updated": False}], "has_local_feedback": True, "has_exchange_feedback": True, "feedback_updated": False, "local_feedback_path": "./a1/feedback/2020-04-29 21:58:53.988500 UTC"}]}]})
        elif action == 'validate':
            self.finish({"success": True, "value": {}})

def setup_handlers(web_app):
    host_pattern = ".*$"
    _assignment_action_regex = r"(?P<action>fetch|submit|validate|fetch_feedback)"
    
    base_url = web_app.settings["base_url"]
    route_pattern = url_path_join(base_url, "assignment_list", "get_example")
    courses_pattern = url_path_join(base_url, "assignment_list", "courses")
    assignments_pattern = url_path_join(base_url, "assignment_list", "assignments")
    assignments_action_pattern = url_path_join(base_url, "assignment_list", (r"/assignments/%s" % _assignment_action_regex))
    handlers = [(route_pattern, RouteHandler), (courses_pattern, CouseListHandler), (assignments_pattern, AssignmentListHandler), (assignments_action_pattern, AssignmentActionHandler)]
    web_app.add_handlers(host_pattern, handlers)
