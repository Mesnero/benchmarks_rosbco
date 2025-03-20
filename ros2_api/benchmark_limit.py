import time
import queue
import random
import csv
from ros2_sdk.ros2_sdk import ROS2SDK, TrajPoint
import psutil
import threading
import csv

starting_hz = 100  # Frequency of messages in Hz
time_to_send = 300  # Time to send messages in seconds
increase_hz_per_second = 100  # Increase frequency by this amount every second
messages_to_send = (int) (time_to_send / 2) * (2 * starting_hz + increase_hz_per_second * (time_to_send - 1))  # Number of messages to send
sdk = ROS2SDK()
sdk.connect("UDS", {"path_recv": "/tmp/test_ros2_send.socket", "path_send": "/tmp/test_sdk_send.socket"})
sdk.send_effort([0, 0, 0, 0, 0, 0], "test")

id_name_map_int = {f"{i}": i for i in range(messages_to_send)}  

# Set up monitoring
system_data = []
stop_monitoring = threading.Event()
stop_benchmark = threading.Event()

def monitor_system_resources():
    start_time = time.time()
    while not stop_monitoring.is_set():
        # Record timestamp (milliseconds from start)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_percent = psutil.virtual_memory().percent
        
        # Store data
        system_data.append([elapsed_ms, cpu_percent, memory_percent])
        
        # Sleep for 100ms
        time.sleep(0.1)
        
expected_incoming_queue = queue.Queue()
invalid_ids_never_arrived = dict()  
invalid_ids_arrived_too_late = dict()
arrived_messages = dict()

def send_messages():
    start_time = time.time()
    message_count = 0
    
    for id_str, id_num in id_name_map_int.items():
        
        if stop_benchmark.is_set():
            break
        current_time = time.time()
        elapsed_seconds = current_time - start_time
        
        current_hz = starting_hz + (increase_hz_per_second * elapsed_seconds)
        
        expected_incoming_queue.put((id_num, time.time_ns()))
        sdk.send_trajectory(trajPoints=[TrajPoint(positions=[], velocities=[1.0,1.0,1.0,1.0], effort=[], seconds=0, nanoseconds=0)], joint_names=[id_str], name="trajectory")
        message_count += 1
        
        sleep_time = 1 / current_hz
        time.sleep(sleep_time)



def on_message_arrival(msg):
    current_time = time.time_ns()  
    id_str = msg["names"][0]
    id = id_name_map_int.get(id_str)

    while not expected_incoming_queue.empty():
        dequeued_id, sent_time = expected_incoming_queue.get()
        if id == dequeued_id:
            arrived_messages[id] = (sent_time, current_time)
            return
        elif id > dequeued_id:
            invalid_ids_never_arrived[dequeued_id] = (sent_time)
    

subscription = sdk.get_state_stream().subscribe(on_message_arrival)
monitoring_thread = threading.Thread(target=monitor_system_resources)
monitoring_thread.daemon = True

monitoring_thread.start()
send_messages()

stop_monitoring.set()
monitoring_thread.join()

time.sleep(60) # Wait for messages to arrive
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
            
with open("benchmark/system_usage.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Time", "CPU Usage", "Memory Usage"])
    writer.writerows(system_data)
        
write_csv_arrived("benchmark/arrived_messages.csv", arrived_messages, ["ID", "Sent Time", "Received Time"])
write_csv_missing("benchmark/invalid_ids_never_arrived.csv", invalid_ids_never_arrived, ["ID", "Sent Time"])  
write_csv_arrived("benchmark/invalid_ids_arrived_too_late.csv", invalid_ids_arrived_too_late, ["ID", "Sent Time", "Received Time"])
