import os
import socket

IP_address = "169.254.49.8"
# networking for syncing Tobii
def Signal_Unity_On():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 56712
        
        sock.connect((IP_address, port))
    
        sock.sendall(b"ToggleOn")
    
        sock.close()
    except:
        print("exception occured trying to signal Unity")
    finally:
        return 0
    
def Signal_Unity_Off():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 56712
        
        sock.connect((IP_address, port))
    
        sock.sendall(b"ToggleOff")
    
        sock.close()
    except:
        print("exception occured trying to signal Unity")
    finally:
        return 0

Signal_Unity_On()
