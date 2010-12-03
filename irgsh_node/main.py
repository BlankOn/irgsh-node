#!/usr/bin/env python

import ConfigParser, os
import errno
import sys
import time
import xmlrpclib
import tarfile
import shutil
import bz2
from threading import Timer
import logging

from debian_bundle import deb822
from debian_bundle.changelog import Changelog

from irgsh.dvcs import *
from irgsh.sourcepackage import *
from irgsh.builder_pbuilder import *
from irgsh.buildjob import BuildJob
from irgsh.uploader_dput import UploaderDput
from irgsh.uploadlog import UploadLog

CONFIG_FILES = ['/etc/irgsh/irgsh-node.conf','irgsh-node.conf']

class SSLTransport(xmlrpclib.SafeTransport):
    def __init__(self, cert, key):
        self.cert = cert
        self.key = key
        self._use_datetime = True

    def make_connection(self, host):
        host_cert = (host, {
            'cert_file': self.cert,
            'key_file': self.key,
        })
        return xmlrpclib.SafeTransport.make_connection(self, host_cert)

class IrgshNodeError(Exception):
    pass

class InvalidConfiguration(IrgshNodeError):
    pass

class IrgshNode(object):
    assignment = -1
    _uploading = False

    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('irgsh-node')

    def setup_logging(self):
        self.log.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    def load_config(self):
        config = self.config

        try:
            self.server = config.get('irgsh', 'server')
        except ConfigParser.NoSectionError:
            raise InvalidConfiguration, \
                  "No 'irgsh' section in configuration file(s):"
        except ConfigParser.NoOptionError:
            raise InvalidConfiguration, \
                  "No 'server' option in configuration file(s):"

        try:
            self.node_name = config.get('irgsh', 'node-name')
        except ConfigParser.NoOptionError:
            raise InvalidConfiguration, \
                  "No 'node-name' option in configuration file(s):"

        try:
            self.build_path = config.get('irgsh', 'build-path')
        except ConfigParser.NoOptionError:
            raise InvalidConfiguration, \
                  "No 'build-path' option in configuration file(s):"

        self.cert = None
        self.key = None
        try:
            self.cert = config.get('irgsh', 'cert')
        except ConfigParser.NoOptionError:
            pass

        if self.cert is not None:
            try:
                self.key = config.get('irgsh', 'cert-key')
            except ConfigParser.NoOptionError:
                raise InvalidConfiguration, \
                      "No 'cert-key' option in configuration file(s):"

    def connect(self):
        if self.cert is not None:
            transport = SSLTransport(cert, key)
        else:
            transport = None

        try:
            self.x = xmlrpclib.ServerProxy(self.server, transport=transport)
        except Exception as e:
            self.log.critical("Unable to contact %s: %s" % (server, str(e)))
            sys.exit(-1)

    def start(self):
        self.setup_logging()
        self.load_config()
        self.connect()

        while True:
            Timer(1, self.upload)
            self.run()
            time.sleep(10)

    def upload(self):
        if self._uploading:
            return

        self._uploading = True
        try:
            (code, reply) = self.x.get_assignments_to_upload(self.node_name)
            if code == -1:
                self.log.error("Error getting assignments to upload: %s" %
                               reply)
            else:
                assignments = reply
                for assignment in assignments:
                    (code, reply) = self.x.get_assignment_info(assignment)
                    if code == -1:
                        raise Exception(reply)
                    info = reply
                    task_info = self.x.get_task_info(info['task'])
                    distribution = task_info['distribution']
                    upload_log = os.path.join(self.build_path, \
                                              "upload.%d.log" % assignment)
                    log = UploadLog(upload_log)
                    uploader = UploaderDput("", distribution, info['dsc'])
                    if uploader.upload():
                        self.x.assignment_upload(assignment)
                        self.x.assignment_wait_for_installing(assignment)
                    else:
                        with open(upload_log, "r") as handle:
                            reason = handle.read()
                        self.log.error("Upload %d failed: %s" %
                                       (assignment, reason))
                        self.x.assignment_fail(assignment, reason)
                    log.close()
                    log = None
                    os.unlink(upload_log)
        except Exception as e:
            self.log.error(str(e))

        self._uploading = False

    def run(self):
        self.log.debug("Running")
        try:
            self.x.builder_ping(self.node_name)
            (code, reply) = self.x.get_assignment_for_builder(self.node_name)
            if code == -1:
                raise Exception(reply)
            if reply == -1:
                self.log.debug("No pending assignment for me now. Look for new one..")
            else:
                self.assignment = reply
                (code, reply) = self.x.get_assignment_info(self.assignment)
                if code == -1:
                    raise Exception(reply)

                assignment_info = reply
                self.info = self.x.get_task_info(assignment_info['task'])
                self.id = assignment_info['task']
                self.build()
        except BuildBuilderFailureError as e:
            if self.assignment != -1:
                self.x.assignment_fail(self.assignment, str(e))

                if self.log is not None:
                    filename = self.log.filename
                    self.log.close()
                    self.log = None
                    if filename is not None:
                        with open(filename, "rb") as handle:
                            fname = "%s.bz2" % os.path.basename(filename)
                            data = xmlrpclib.Binary(bz2.compress(handle.read()))
                            self.x.assignment_upload_log(self.assignment,
                                                         fname, data)

            self.assignment = None
            self.log = None
        except Exception as e:
            raise

        try:
            (code, reply) = self.x.get_unassigned_task(self.node_name)

            if code == -1:
                raise Exception(reply)
            if reply == -1:
                self.log.debug("No more tasks")
                return
            self.id = reply
            self.assign()
        except Exception as e:
            self.log.error("Error getting unassigned task: %s" % str(e))

    def assign(self):
        self.x.builder_ping(self.node_name)
        code, reply = self.x.assign_task(self.id, self.node_name)
        if code == -1:
            self.x.task_init_failed(self.id, reply)
            raise Exception(reply)

    def build(self):
        self.x.builder_ping(self.node_name)
        self.x.assignment_building(self.assignment)
        self.log = BuildLog(os.path.join(self.build_path, \
                                         "task.%d.log" % self.assignment))
        diff = DvcsLoader("tarball", self.info['debian_copy'])

        orig_copy = None
        if self.info['orig_copy']:
            orig_copy = self.info['orig_copy']

        builder = builder_pbuilder(Distro(self.info['distribution']))
        builder.components = self.info['components']
        build_job = BuildJob(diff.instance, orig_copy)
        result = build_job.build(builder)

        self.log.close()
        self.log = None

        info = self.x.get_task_info(self.id)
        if info['state'] == "F":
            self.x.assignment_cancel(self.assignment, \
                                     "Cancelling successful build because " \
                                     "the task as a whole is failed")
        else:
            self.x.assignment_wait_for_upload(self.assignment, result)

def main():
    config = ConfigParser.ConfigParser()
    files = config.read(CONFIG_FILES)

    t = IrgshNode(config)
    try:
        t.start()
    except InvalidConfiguration, e:
        print >>sys.stderr, e
        sys.exit(-1)

if __name__ == '__main__':
    main()

