import os
import shutil

from traitlets import Bool

from nbgrader.exchange.abc import ExchangeFetchAssignment as ABCExchangeFetchAssignment
from nbgrader.exchange.default import Exchange
from nbgrader.utils import check_mode


class ExchangeFetchAssignment(Exchange, ABCExchangeFetchAssignment):

    def _load_config(self, cfg, **kwargs):
        if 'ExchangeFetch' in cfg:
            self.log.warning(
                "Use ExchangeFetchAssignment in config, not ExchangeFetch. Outdated config:\n%s",
                '\n'.join(
                    'ExchangeFetch.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.ExchangeFetchAssignment.items()
                )
            )
            cfg.ExchangeFetchAssignment.merge(cfg.ExchangeFetch)
            del cfg.ExchangeFetchAssignment

        super(ExchangeFetchAssignment, self)._load_config(cfg, **kwargs)

    def init_src(self):
        if self.coursedir.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")
        if not self.authenticator.has_access(self.coursedir.student_id, self.coursedir.course_id):
            self.fail("You do not have access to this course.")

        self.course_path = os.path.join(self.root, self.coursedir.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.src_path = os.path.join(self.outbound_path, self.coursedir.assignment_id)
        if not os.path.isdir(self.src_path):
            self._assignment_not_found(
                self.src_path,
                os.path.join(self.outbound_path, "*"))
        if not check_mode(self.src_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.src_path))

    def init_dest(self):
        if self.path_includes_course:
            root = os.path.join(self.coursedir.course_id, self.coursedir.assignment_id)
        else:
            root = self.coursedir.assignment_id
        self.dest_path = os.path.abspath(os.path.join(self.assignment_dir, root))
        if os.path.isdir(self.dest_path) and not self.replace_missing_files:
            self.fail("You already have a copy of the assignment in this directory: {}".format(root))

    def copy_if_missing(self, src, dest, ignore=None):
        filenames = sorted(os.listdir(src))
        if ignore:
            bad_filenames = ignore(src, filenames)
            filenames = sorted(list(set(filenames) - bad_filenames))

        for filename in filenames:
            srcpath = os.path.join(src, filename)
            destpath = os.path.join(dest, filename)
            relpath = os.path.relpath(destpath, os.getcwd())
            if not os.path.exists(destpath):
                if os.path.isdir(srcpath):
                    self.log.warning("Creating missing directory '%s'", relpath)
                    os.mkdir(destpath)

                else:
                    self.log.warning("Replacing missing file '%s'", relpath)
                    shutil.copy(srcpath, destpath)

            if os.path.isdir(srcpath):
                self.copy_if_missing(srcpath, destpath, ignore=ignore)

    def do_copy(self, src, dest):
        """Copy the src dir to the dest dir omitting the self.coursedir.ignore globs."""
        if os.path.isdir(self.dest_path):
            self.copy_if_missing(src, dest, ignore=shutil.ignore_patterns(*self.coursedir.ignore))
        else:
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*self.coursedir.ignore))

    def copy_files(self):
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.do_copy(self.src_path, self.dest_path)
        self.log.info("Fetched as: {} {}".format(self.coursedir.course_id, self.coursedir.assignment_id))
