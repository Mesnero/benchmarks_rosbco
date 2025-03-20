import time
import queue
import random
import csv
from ros2_sdk.ros2_sdk import ROS2SDK, TrajPoint

hz = 100  # Frequency of messages in Hz
messages_to_send = 60000  # Number of messages to send
sdk = ROS2SDK()
sdk.connect("TCP", {"port_send": 5555, "port_recv": 5556, "ip": "localhost"})
sdk.send_effort([0, 0, 0, 0, 0, 0], "test")

id_name_map_int = {f"{i}": i for i in range(messages_to_send)}  

def construct_messages(): 
    messages = []
    joint_names_msgs = []
    for id_str, _ in id_name_map_int.items():
        joint_names = [id_str, "x", "y", "z", "w", "t"] 
        joint_names_msgs.append(joint_names)
        trajPoints = []
        for _ in range(10):
            # random arrays of size 6 as floats
            vel_array = [random.uniform(-5, 5) for _ in range(6)]
            pos_array = [random.uniform(-5, 5) for _ in range(6)]
            seconds = random.randint(0, 10)
            nanoseconds = random.randint(0, 500000)
            trajPoints.append(TrajPoint(positions=pos_array, velocities=vel_array, effort=[], seconds=seconds, nanoseconds=nanoseconds))
        messages.append(trajPoints)
    return messages, joint_names_msgs

        
messages, joint_names = construct_messages()

expected_incoming_queue = queue.Queue()
invalid_ids_never_arrived = dict()  
invalid_ids_arrived_too_late = dict()
arrived_messages = dict()

def send_messages():
    for _, id_num in id_name_map_int.items():
        expected_incoming_queue.put((id_num, time.time_ns())) 
        sdk.send_trajectory(trajPoints=messages[id_num], joint_names=joint_names[id_num], name="trajectory") 
        time.sleep(1 / hz)  # Sleep for the desired frequency



def on_message_arrival(msg):
    current_time = time.time_ns()  
    id_str = msg["names"][0]
    id = id_name_map_int.get(id_str)

    while not expected_incoming_queue.empty():
        dequeued_id, sent_time = expected_incoming_queue.get()
        if id == dequeued_id:
            arrived_messages[id] = (sent_time, current_time)
            return
        if id < dequeued_id:
            _, sent_time = invalid_ids_never_arrived.pop(id)
            invalid_ids_arrived_too_late[id] = (sent_time, current_time)
            return
        elif id > dequeued_id:
            invalid_ids_never_arrived[dequeued_id] = sent_time
    

subscription = sdk.get_state_stream().subscribe(on_message_arrival)

send_messages()
time.sleep(5) # Wait for messages to arrive
sdk.write_time_data_to_csv()
subscription.dispose()

def write_csv_arrived(filename, data, headers):
    """ Writes dictionary data to a CSV file. """
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for id, (sent_time, received_time) in data.items():
            writer.writerow([id, sent_time, received_time])
            
def write_csv_missing(filename, data, headers):
    """ Writes dictionary data to a CSV file. """
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for id, (sent_time) in data.items():
            writer.writerow([id, sent_time])

        
write_csv_arrived("arrived_messages.csv", arrived_messages, ["ID", "Sent Time", "Received Time"])
write_csv_missing("invalid_ids_never_arrived.csv", invalid_ids_never_arrived, ["ID", "Sent Time"])  
write_csv_arrived("invalid_ids_arrived_too_late.csv", invalid_ids_arrived_too_late, ["ID", "Sent Time", "Received Time"])
