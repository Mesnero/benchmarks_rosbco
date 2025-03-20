const ROSLIB = require('roslib');
const fs = require('fs');

// Connect to ROS 2 via Rosbridge
const ros = new ROSLIB.Ros({
    url: 'ws://localhost:9090'  // Change if Rosbridge runs on another machine
});

// Handle connection events
ros.on('connection', () => console.log('Connected to ROS2 via Rosbridge!'));
ros.on('error', (error) => console.error('Error:', error));
ros.on('close', () => console.log('Connection to ROS2 closed.'));

// Frequency and message settings
const hz = 200;  // 100Hz frequency
const messagesToSend = 100000;  // Number of messages to send

let idNameMapInt = {};
for (let i = 0; i < messagesToSend; i++) {
    idNameMapInt[i.toString()] = i;
}

function getNanoSecTime() {
  var hrTime = process.hrtime();
  return hrTime[0] * 1000000000 + hrTime[1];
}

// Function to generate random trajectory messages
function constructMessages() {
    let messages = [];

    for (let _ in idNameMapInt) {
        let velArray = Array(6).fill().map(() => (Math.random() * 10 - 5));  // Random floats
        messages.push(velArray);
    }
    return messages;
}

// Construct messages
let messages = constructMessages();

// Tracking messages
let expectedIncomingQueue = [];
let invalidIdsNeverArrived = {};
let invalidIdsArrivedTooLate = {};
let arrivedMessages = {};

// Publisher for sending trajectory messages
let velocityPublisher = new ROSLIB.Topic({
    ros: ros,
    name: '/velocity',
    messageType: 'std_msgs/Float64MultiArray'
});

// Function to send messages
function sendMessages() {
    // Send messages at regular intervals
    let messageIndex = 0;
    
    function sendNextMessage() {
        if (messageIndex >= messagesToSend) {
            console.log("All messages sent!");
            return;
        }
        
        const idNum = messageIndex;
        const sentTime = getNanoSecTime();
        
        expectedIncomingQueue.push({ idNum, sentTime });

        let message = new ROSLIB.Message({
            data: messages[messageIndex]
        });

        velocityPublisher.publish(message);
        
        messageIndex++;
        setTimeout(sendNextMessage, 1000 / hz);
    }
    
    // Start sending
    sendNextMessage();
}
// Subscriber to listen for `JointState` messages
let jointStateSubscriber = new ROSLIB.Topic({
    ros: ros,
    name: '/joint_states',
    messageType: 'sensor_msgs/JointState'
});

// Handling received messages
jointStateSubscriber.subscribe((msg) => {
    let currentTime = getNanoSecTime();
    let { idNum, sentTime } = expectedIncomingQueue.shift();
    arrivedMessages[idNum] = { sentTime, ros2Time: msg.header.stamp, receivedTime: currentTime };
});

// Start sending messages
ros.on('connection', async() => {
    sendMessages();
    await new Promise(resolve => setTimeout(resolve, 600000));
    jointStateSubscriber.unsubscribe();
    saveToCSV();
});

// Function to save CSV data
function saveToCSV() {
    let arrivedCSV = "ID,Sent Time,ROS2 Time,Received Time\n";
    for (let id in arrivedMessages) {
        let { sentTime, ros2Time, receivedTime } = arrivedMessages[id];
        let ns = ros2Time.nanosec.toString().padStart(9, '0');
        arrivedCSV += `${id},${sentTime},${ros2Time.sec}${ns},${receivedTime}\n`;
    }

    let neverArrivedCSV = "ID,Sent Time\n";
    for (let id in invalidIdsNeverArrived) {
        neverArrivedCSV += `${id},${invalidIdsNeverArrived[id]}\n`;
    }

    let tooLateCSV = "ID,Sent Time,ROS2 Time,Received Time\n";
    for (let id in invalidIdsArrivedTooLate) {
        let { sentTime, ros2Time, receivedTime } = invalidIdsArrivedTooLate[id];
        tooLateCSV += `${id},${sentTime},${ros2Time.sec}.${ros2Time.nanosec},${receivedTime}\n`;
    }

    fs.writeFileSync("arrived_messages.csv", arrivedCSV);
    fs.writeFileSync("invalid_ids_never_arrived.csv", neverArrivedCSV);
    fs.writeFileSync("invalid_ids_arrived_too_late.csv", tooLateCSV);
}
