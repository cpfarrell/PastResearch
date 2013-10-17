import json

from autobahn.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
from twisted.internet import reactor

# WebSocketClientFactory class for accessing Attensity pipeline
#
# required params:   url  -  websocket url
# optional params:   filename - output jsons from pipeline to filename
#                    msg_function - function or callable class to perform
#                                   additional processing on items from pipeline
class AttensityFactory(WebSocketClientFactory):

  def __init__(self, url, file_handle=None, msg_function=None):
    
    WebSocketClientFactory.__init__(self, url)
    self._msg_function = msg_function
    self._file_handle = file_handle
    
  def clientConnectionLost(self, connector, reason):
    connector.connect()

  def buildProtocol(self, addr):

    protocol = AttensityWS()
    protocol.msg_function = self._msg_function
    protocol.file_handle = self._file_handle
    protocol.factory = self
    return protocol


class AttensityWS(WebSocketClientProtocol):

  def onMessage(self, msg, binary):
  
    if self.msg_function is not None:
      msg = self.msg_function(msg)

    if self.file_handle is not None:
      output_msg = msg + '\n'
      self.file_handle.write(output_msg.encode('utf-8'))


  def onClose(self, a, b, c):
    print 'on close'

    if self.file_handle is not None:
      self.file_handle.close()

    reactor.stop()
    reactor.disconnectAll()

  def kill(self):
    print 'on kill'
    self.transport.loseConnection()
    reactor.stop()
    reactor.disconnectAll()

  def onOpen(self):
    print 'opening'
