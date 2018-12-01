import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
from threading import Thread
import os.path
import asyncio
from tornado.platform.asyncio import AnyThreadEventLoopPolicy


callback = None

class WebServer():    
    def __init__(self, callbackArg=None):        
        global callback
        callback = callbackArg
        self.serverThread = ServerThread()
        self.serverThread.daemon = True
        self.serverThread.start()
        
        
class ServerThread(Thread):    
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        try:
            LISTEN_PORT = 8888
            LISTEN_ADDRESS = "192.168.1.50"
            asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
            ws_app = Application()
            server = tornado.httpserver.HTTPServer(ws_app)
            print("Listen to " + str(LISTEN_PORT) + " port on " + LISTEN_ADDRESS)
            server.listen(LISTEN_PORT, LISTEN_ADDRESS)
            tornado.ioloop.IOLoop.current().start()
        except Exception as e:
            print("Server stopped: ", e);
        
        
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        pass
 
    def on_message(self, message):
        global callback
        if not callback == None:
            response = callback(message)
            if response:
                self.write_message(response)
 
    def on_close(self):
        pass

 
class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
 
 
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexPageHandler),
            (r"/websocket", WebSocketHandler)
        ]
        settings = {
            "template_path": os.path.join(os.path.dirname(__file__), "templates"),
            "static_path": os.path.join(os.path.dirname(__file__), "static")
        }
        tornado.web.Application.__init__(self, handlers, **settings)
    