import os
import tarfile
import datetime
import shutil
import tempfile

def submit():
    pth = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    
    try:
        # copy everything to a temporary directory
        assignment = os.path.split(pth)[1]
        shutil.copytree(pth, os.path.join(tmpdir, assignment))
        os.chdir(tmpdir)

        # get the user name, write it to file
        user = os.environ['USER']
        with open(os.path.join(assignment, "user.txt"), "w") as fh:
            fh.write(user)

        # save the submission time
        timestamp = str(datetime.datetime.now())
        with open(os.path.join(assignment, "timestamp.txt"), "w") as fh:
            fh.write(timestamp)

        # get the path to where we will save the archive
        archive = os.path.join(
            os.environ['HOME'], ".submissions", "{}.tar.gz".format(assignment))
        if not os.path.exists(os.path.dirname(archive)):
            os.makedirs(os.path.dirname(archive))
        if os.path.exists(archive):
            shutil.copy(archive, "{}.bak".format(archive))
            os.remove(archive)

        # create a tarball with the assignment files
        tf = tarfile.open(archive, "w:gz")
        tf.add(assignment)
        tf.close()
        
    except:
        raise
        
    else:
        print("{} submitted by {} at {}".format(assignment, user, timestamp))
        
    finally:
        shutil.rmtree(tmpdir)
        os.chdir(pth)    
