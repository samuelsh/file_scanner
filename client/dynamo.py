"""
Client load generator
2016 samules (c)
"""
import random
import time
import os
import zmq
import sys
import socket

sys.path.append('/qa/dynamo')
from config import CTRL_MSG_PORT, CLIENT_MOUNT_POINT
from utils import shell_utils


class Dynamo(object):
    def __init__(self, logger, stop_event, controller, server, proc_id=None):
        self.stop_event = stop_event
        self.logger = logger
        self._server = server  # Server Cluster hostname
        self._context = zmq.Context()
        self._controller_ip = socket.gethostbyname(controller)
        # Socket to send messages on by client
        self._socket = self._context.socket(zmq.DEALER)
        # We don't need to store the id anymore, the socket will handle it
        # all for us.
        # We'll use client host name + process ID to identify the socket
        self._socket.identity = "{0}:0x{1:x}".format(socket.gethostname(), proc_id)
        self._socket.connect("tcp://{0}:{1}".format(self._controller_ip, CTRL_MSG_PORT))
        logger.info("Dynamo {0} init done".format(self._socket.identity))

    def run(self):
        self.logger.info("Dynamo {0} started".format(self._socket.identity))
        try:
            # Send a connect message
            self._socket.send_json({'message': 'connect'})
            # Poll the socket for incoming messages. This will wait up to
            # 0.1 seconds before returning False. The other way to do this
            # is is to use zmq.NOBLOCK when reading from the socket,
            # catching zmq.AGAIN and sleeping for 0.1.
            while not self.stop_event.is_set():
                if self._socket.poll(100):
                    # Note that we can still use send_json()/recv_json() here,
                    # the DEALER socket ensures we don't have to deal with
                    # client ids at all.
                    job_id, work = self._socket.recv_json()
                    self._socket.send_json(
                        {'message': 'job_done',
                         'result': self._do_work(work),
                         'job_id': job_id})
        except KeyboardInterrupt:
            pass
        finally:
            self._disconnect()

    def _disconnect(self):
        """Send the Controller a disconnect message and end the run loop.
        """
        self.stop_event.set()
        self._socket.send_json({'message': 'disconnect'})

    def _do_work(self, work):
        action = work['action']
        data = None
        if work['target'] == 'None':
            return "failed:{0}:{1}".format(action, "Target not specified")
        try:
            if action == 'mkdir':
                os.mkdir("{0}/{1}".format(CLIENT_MOUNT_POINT, work['target']))
                data = os.stat("{0}/{1}".format(CLIENT_MOUNT_POINT, work['target'])).st_size
            elif action == 'touch':
                shell_utils.touch('{0}{1}'.format(CLIENT_MOUNT_POINT, work['target']))
                data = os.stat("{0}/{1}".format(CLIENT_MOUNT_POINT, work['target'].split('/')[1])).st_size
            elif action == 'stat':
                os.stat("{0}/{1}".format(CLIENT_MOUNT_POINT, work['target'].split('/')[1]))
            elif action == 'list':
                os.listdir('{0}/{1}'.format(CLIENT_MOUNT_POINT, work['target']))
            elif action == 'delete':
                dirpath = work['target'].split(',')[0].split('/')[1]
                if os.path.exists('{0}{1}/dir.lock'.format(CLIENT_MOUNT_POINT, dirpath)):
                    return "failed:{0}:{1}".format(action, CLIENT_MOUNT_POINT + dirpath + ": Directory is locked!")
                for path in work['target'].split(','):
                    shell_utils.touch('{0}/{1}/dir.lock'.format(CLIENT_MOUNT_POINT, path.split('/')[1]))
                    self.logger.debug("dir " + dirpath + " is locked")
                    os.remove('{0}{1}'.format(CLIENT_MOUNT_POINT, path))
                os.remove('{0}/{1}/dir.lock'.format(CLIENT_MOUNT_POINT, dirpath))
                self.logger.debug("dir " + dirpath + " is unlocked")
        except Exception as work_error:
            return "failed:{0}:{1}:{2}".format(action, work_error, sys.exc_info()[-1].tb_lineno)
        result = "success:{0}:{1}:{2}".format(action, work['target'], data)
        # time.sleep(random.randint(1, 10))
        return result
