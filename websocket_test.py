import websocket
import json

SERVER_URL = "ws://127.0.0.1:5000/socket.io/?transport=websocket"

def on_message(ws, message):
    print("Message received from server:", message)

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    print("WebSocket connection established")
    message = {
        "sender": "TestUser",
        "message": "Hello, this is a test message!"
    }
    ws.send(json.dumps(message))

if __name__ == "__main__":
    websocket.enableTrace(True)
    try:
        ws = websocket.WebSocketApp(SERVER_URL,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.on_open = on_open
        ws.run_forever()
    except Exception as e:
        print("An error occurred during WebSocket test:", e)
