import os
import time

from twisted.internet import reactor
from twisted.internet.error import ConnectionDone

from client.config import Config
from client.logs import SetupLogs
from client.connection import ClaymoreConnectionFactory, ServerReport


class App(object):
    """
    This class represents the client. It is called when application starts and performs all connections, logging etc.
    """

    """
    Current client version. It is checked with server app to redirect it to right API version.
    """
    version = "0.0.2"

    def __init__(self, path):
        """
        Create client.
        :param str path: Path to client.py file. It is used as a base for all relative paths.
        """
        self.path = path

        self.logger = SetupLogs(self.path)

        # Load configuration
        self.config = Config(self.logger)
        self.config.open(os.path.abspath(os.path.join(self.path, "./config.ini")))

    def run(self):
        """
        Starts a client.
        """
        self.logger.info("Started up after boot up.")
        
        # Create inner TCP connection factory
        reactor.connectTCP(self.config.client.host, int(self.config.client.port), ClaymoreConnectionFactory(self))
        reactor.run()

    def onConnectionClosed(self, reason, connector):
        """
        Callback executed every time connection with claymore miner is closed.
        :param object reason: One of twisted.internet.error classes with reason for closing connection.
        :param object connector: Object for reconnecting.
        """

        # Check closing reason
        if isinstance(reason.type(), ConnectionDone):

            # Everything went ok. 
            self.logger.info("Waiting for {} s".format(self.config.client.interval))
            time.sleep(int(self.config.client.interval))
            
            # Reconect
            connector.connect()

        else:
            
            # Some kind of error
            self.logger.error("Connection lost: {}".format(reason))

    def onConnectionFailed(self, reason, connector):
        """
        Callback called when connection to claymore miner fails.
        :param object reason: One of twisted.internet.error reasons.
        :param object connector: Object for reconnecting.
        """
        pass

    def onMinerResponse(self, status):
        """
        Callback called when claymore miner responses to a message.
        :param client.connection.ClaymoreResponse status: Response data.
        """

        if not status:
            self.logger.error("Status error: {}".format(status.getError()))
            return False

        self.logger.info("Hashrate: {} H/s".format(status.hashrate()))

        # Restart Miner
        if status.hashrate() < int(self.config.client.hashrate):
            self.logger.info("Hashrate is too low. Restarting computer.")
            os.system("r")

        # Send data to monitoring server
        report = ServerReport(status, self)
        report.send()

        self.logger.debug("Report sent to collecting server.")

        if report.return_code() != 200:
            self.logger.error("Server responded with error: Code: {} - {}".format(report.return_code(), report.response()))
            return False

        else:
            self.logger.info("Server responded with success code.")
            return True
