import time
import queue
import random
import csv
from ros2_sdk.ros2_sdk import ROS2SDK, TrajPoint

hz = 400  # Frequency of messages in Hz
messages_to_send = 240000  # Number of messages to send
sdk = ROS2SDK()
sdk.connect("UDS", {"path_recv": "/tmp/test_ros2.socket", "path_send": "/tmp/test_sdk.socket"})
sdk.send_effort([0, 0, 0, 0, 0, 0], "test")


def construct_messages(): 
    messages = []
    for i in range(messages_to_send):
        vel_array = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        messages.append(vel_array)
    return messages
        
messages = construct_messages()

def send_messages():
    for message in messages: 
        sdk.send_velocity(message, name="velocity") 
        time.sleep(1 / hz)  
        
send_messages()