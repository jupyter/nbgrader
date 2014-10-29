import os

from IPython.nbconvert.postprocessors import PostProcessorBase
from IPython.utils.traitlets import Unicode, Integer
from nbgrader.html.formgrade import app
from pymongo import MongoClient

class ServeFormGrader(PostProcessorBase):

    db_ip = Unicode("localhost", config=True, help="IP address for the database")
    db_port = Integer(27017, config=True, help="Port for the database")

    ip = Unicode("localhost", config=True, help="IP address for the server")
    port = Integer(5000, config=True, help="Port for the server")

    def postprocess(self, input):
        dirname, filename = os.path.split(input)
        filename = os.path.splitext(filename)[0]
        app.notebook_dir = dirname

        url = "http://{:s}:{:d}/{:s}".format(self.ip, self.port, filename)
        self.log.info("Form grader running at {}".format(url))
        self.log.info("Use Control-C to stop this server")

        app.client = MongoClient(self.db_ip, self.db_port)
        app.db = app.client['assignments']
        app.grades = app.db['grades']
        app.comments = app.db['comments']

        app.run(host=self.ip, port=self.port, debug=True, use_reloader=False)

def main(path):
    """Allow running this module to serve the form grader"""
    server = ServeFormGrader()
    server(path)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
