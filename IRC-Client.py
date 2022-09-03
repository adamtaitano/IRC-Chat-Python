from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter

# constants for message length limit and end of message CR-LF
BUFF_SIZE = 512
crlf = "\r\n"

# receive any messsages in a continuous loop
def receive():
    while receive_thread.isAlive():
        try:
            # decode message
            msg = client_socket.recv(BUFF_SIZE).decode("ascii")
            # add message to GUI as one line
            msg_list.insert(tkinter.END, msg)
        except OSError as e:
            print('OS Error: {}'.format(e))
            break
    # notify client of disconnect
    msg_list.insert(tkinter.END,'Lost connection to server. Restart the GUI to reconnect.')
    # GUI.quit() # left out to give user option to close GUI

# function bound by clicking send button or using return key
def send(event=None):
    # grab current message from text entry
    msg = my_msg.get()
    # set entry field text to empty
    my_msg.set("")
    # add carriage return - line feed pair
    msg += crlf
    # send encoded message over socket
    client_socket.send(bytes(msg, "ascii"))

def on_closing(event=None):
    # inform server that user exited the chat GUI, then quit tkinter app
    my_msg.set("QUIT")
    send()
    GUI.quit()

def Close():
    GUI.destroy()
    
# GUI display and configuration using tkinter
GUI = tkinter.Tk()
GUI.title("IRC Chat")

messages_frame = tkinter.Frame(GUI)
# String for messages to be sent from GUI
my_msg = tkinter.StringVar()
my_msg.set("")
# allows navigation of previous messages
scrollbar = tkinter.Scrollbar(messages_frame)
# message list will contain all received messages.
msg_list = tkinter.Listbox(messages_frame, height=10, width=62, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack()
# entry field containing text variable and key/button bindings
entry_field = tkinter.Entry(GUI, textvariable=my_msg, font=('default', 10))
entry_field.bind("<Return>", send)
entry_field.pack()
send_button = tkinter.Button(GUI, text="Send", command=send)
send_button.pack()

# protocol with registered callback function upon user manually closing GUI
GUI.protocol("WM_DELETE_WINDOW", on_closing)

# address to server, adjust accordingly
ADDR = ('127.0.0.1', 6667)
# connect to server
client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)
# create thread with receive method as worker function
receive_thread = Thread(target=receive)
receive_thread.start()
# add button for closing out
exit_button = tkinter.Button(GUI, text="Exit", command=Close)

# begin GUI
GUI.mainloop()
