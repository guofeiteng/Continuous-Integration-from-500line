import argparse
import os
import re
import socket
import SocketServer
import subprocess
import sys
import time

import helpers

def poll ():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatcher-server", help="dispatcher host:port," \
                        "by default=""localhost:8888", action="store")
    parser.add_argument("repo", metavar="REPO", type=str,
                        help="path to the repository this will observe")
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")

    while True:
        try:
            # call the bash script that will update the repo and check for
            # changes. if there is changes, it will drop a .commit_id file
            # with the latest commit in the current working directory
            subprocess.check_output(["./update_repo.sh", args.repo])
        except subprocess.CalledProcessError as e:
            raise Exception("could not update and check repository." +
                            "Reason: %s" % e.output)

        if os.path.isfile(".commit_id"):
            # we have a change, lets execute the test
            # first, check the status of the dispatcher server
            # to see if we can send the test
            try:
                response = helpers.communicate(dispatcher_host,
                                               int(dispatcher_port),
                                               "status")
            except socket.error as e:
                raise Exception("could not communicate with dispatcher server: %s" % e)
            if response == "OK":
                # dispatcher is present, lets send it a test
                commit = ""
                with open(".commit_id", "r") as f:
                    commit = f.readline()
                response = helpers.communicate(dispatcher_host,
                                           int(dispatcher_port),
                                           "dispatch:%s" % commit)
                if response != "OK":
                    raise Exception("could not dispatch the test: %s" % response)
                print "dispatched"
            else:
                # something wrong happened to the dispatcher
                raise Exception("could not dispatch the test: %s" % response)
        time.sleep(5)

if __name__ == "__main__":
    poll()