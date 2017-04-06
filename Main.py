import json
from datetime import datetime

from bottle import *
from gevent.pywsgi           import WSGIServer
from geventwebsocket         import WebSocketError
from geventwebsocket.handler import WebSocketHandler

app = Bottle()

messages = []   #TODO move to SQL database.
observers = []  #Collection of connected clients in the form of their environments.

@app.route('/')
def getMain():
    template_data = {"messages" : messages}
    return template("template.html", template_data)

@app.route('/join_chat')
def handle_websocket():

    env = request.environ
    wsock = env.get("wsgi.websocket")

    if wsock is None: #Check the user is using this endpoint correctly.
        abort(400, "Expected a WebSocket request.")

    observers.append(env) #Add the socket to our collection so we can alert them all to eachothers doings.
    send_message("Client from " + env.get("REMOTE_ADDR") + " has connected. (" + str(len(observers)) + " clients online)", None, "SERVER")

    while True: #Listen to the socket for user input.
        try:

            message = wsock.receive() #Grab the message from the user.

            if message is not None: #We get a None as a response when a socket closes. Don't do anything with those.
                send_message(message, env) #Forward the message to all the other connected clients.

        except WebSocketError: #Connection closed or something else went wrong.
            observers.remove(env)
            send_message("Client from " + env.get("REMOTE_ADDR") + " has disconnected. (" + str(len(observers)) + " clients online)", None, "SERVER")
            break

def send_message(message, poster_env, poster=""):

    message = {
        "message_body"  : message,
        "poster"        : poster_env.get("REMOTE_ADDR") if poster_env is not None else poster,   #TODO replace with cookies and resolve them.
        "time_stamp"    : datetime.now().time().strftime("%H:%M"),
        "date_stamp"    : datetime.today().strftime("%Y-%m-%d")                                  #TODO Convert to more human readible form (29th December)
    }

    for client_env in observers:
        client_env.get("wsgi.websocket").send(json.dumps(message)) #Notify all connected clients

    print(message)
    messages.append(message)

if __name__ == "__main__":

    server = WSGIServer(("0.0.0.0", 8080), app, handler_class=WebSocketHandler)
    server.serve_forever()
