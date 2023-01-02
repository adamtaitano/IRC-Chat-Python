from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from Constants import *
import tkinter

# constants for message length limit and end of message CR-LF
# BUFF_SIZE = 512
# crlf = "\r\n"
# HOST = '127.0.0.1'
# PORT = 6667

# receive any messsages in a continuous loop
class Client:
    def __init__(self, host=HOST, port=PORT):
        # address to server, adjust accordingly
        self.ADDR = (host, port)

    def connect(self):
        # connect to server
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(self.ADDR)
        # create thread with receive method as worker function
        self.receive_thread = Thread(target=self.receive)
        self.receive_thread.start()

    def receive(self, display):
        self.display = display
        while self.receive_thread.isAlive():
            try:
                # decode message
                msg = self.client_socket.recv(BUFF_SIZE).decode("ascii")
                # add message to GUI as one line
                self.display.msg_list.insert(tkinter.END, msg)
            except OSError as e:    
                print('OS Error: {}'.format(e))
                break
        # notify client of disconnect
        self.display.msg_list.insert(tkinter.END,'Lost connection to server. Restart the GUI to reconnect.')
        # GUI.quit() # left out to give user option to close GUI

    # function bound by clicking send button or using return key
    def send(self, event=None):
        # grab current message from text entry
        self.msg = self.display.my_msg.get()
        # set entry field text to empty
        self.display.my_msg.set("")
        # add carriage return - line feed pair
        msg += crlf
        # send encoded message over socket
        self.client_socket.send(bytes(msg, "ascii"))

    def on_closing(self, event=None):
        # inform server that user exited the chat GUI, then quit tkinter app
        self.display.my_msg.set("QUIT")
        self.send()
        GUI.quit()

    def close(self):
        GUI.destroy()

class Display:
    def __init__(self, gui, client, height=10, width=62, font=10):
        self.gui = gui
        self.client = client
        self.height = height
        self.width = width
        self.font = font
        self.set_frame()
        self.set_scrollbar()
        self.pack_messages()
        self.set_exit()

    def set_frame(self): 
        self.messages_frame = tkinter.Frame(self.gui)
        # String for messages to be sent from GUI
        self.my_msg = tkinter.StringVar()
        self.my_msg.set("")

    def set_scrollbar(self):
        # allows navigation of previous messages
        self.scrollbar = tkinter.Scrollbar(self.messages_frame)

    def pack_messages(self):
        # message list will contain all received messages.
        self.msg_list = tkinter.Listbox(self.messages_frame, height=self.height, width=self.width, yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
        self.msg_list.pack()
        self.messages_frame.pack()

    def set_entry(self):
        # entry field containing text variable and key/button bindings
        self.entry_field = tkinter.Entry(self.gui, textvariable=self.my_msg, font=('default', self.font))
        self.entry_field.bind("<Return>", client.send)
        self.entry_field.pack()
        self.send_button = tkinter.Button(self.gui, text="Send", command=self.client.send)
        self.send_button.pack()

    def set_exit(self):
        # add button for closing out
        self.exit_button = tkinter.Button(self, text="Exit", command=self.client.close)

    def on_close(self):
        # protocol with registered callback function upon user manually closing GUI
        self.gui.protocol("WM_DELETE_WINDOW", self.client.on_closing)

# Instantiate GUI, client, and display
## Need to find clear way to intantiate client and display without being intertwined ##
GUI = tkinter.Tk()
GUI.title("IRC Chat")
client = Client(HOST, PORT)
display = Display(GUI, client)
client.connect()
client.receive()
display.set_entry()
# begin GUI
GUI.mainloop()

# # address to server, adjust accordingly
# ADDR = ('127.0.0.1', 6667)
# # connect to server
# client_socket = socket(AF_INET, SOCK_STREAM)
# client_socket.connect(ADDR)
# # create thread with receive method as worker function
# receive_thread = Thread(target=receive)
# receive_thread.start()
# # add button for closing out
# exit_button = tkinter.Button(GUI, text="Exit", command=client.close)

