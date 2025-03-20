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
const hz = 100;  // 100Hz frequency
const messagesToSend = 60000;  // Number of messages to send

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
    let jointNamesMsgs = [];

    for (let idStr in idNameMapInt) {
        let jointNames = [idStr, "x", "y", "z", "w", "t"];
        jointNamesMsgs.push(jointNames);

        let trajPoints = [];

        for (let i = 0; i < 10; i++) { // Only 1 TrajPoint per message (like Python)
            let velArray = Array(6).fill().map(() => (Math.random() * 10 - 5));  // Random floats
            let posArray = Array(6).fill().map(() => (Math.random() * 10 - 5));  // Random floats
            let seconds = Math.floor(Math.random() * 10);  // Random float (not floored!)
            let nanoseconds = Math.floor(Math.random() * 500000);  // Random float (not floored!)

            trajPoints.push({
                positions: posArray,
                velocities: velArray,
                accelerations: [],
                effort: [],
                time_from_start: { sec: seconds, nanosec: nanoseconds }
            });
        }
        messages.push(trajPoints);
    }
    return { messages, jointNamesMsgs };
}

// Construct messages
let { messages, jointNamesMsgs } = constructMessages();

// Tracking messages
let expectedIncomingQueue = [];
let invalidIdsNeverArrived = {};
let invalidIdsArrivedTooLate = {};
let arrivedMessages = {};

// Publisher for sending trajectory messages
let trajectoryPublisher = new ROSLIB.Topic({
    ros: ros,
    name: '/trajectory',
    messageType: 'trajectory_msgs/JointTrajectory'
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
        const idStr = idNum.toString();
        const sentTime = getNanoSecTime();
        
        expectedIncomingQueue.push({ idNum, sentTime });

        let message = new ROSLIB.Message({
            header: { stamp: { sec: 0, nanosec: 0 }, frame_id: '' },
            joint_names: jointNamesMsgs[idNum],
            points: messages[idNum]
        });

        trajectoryPublisher.publish(message);
        
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
    let idStr = msg.name[0];
    let id = idNameMapInt[idStr];

    while (expectedIncomingQueue.length > 0) {
        let { idNum, sentTime } = expectedIncomingQueue.shift();

        if (id === idNum) {
            arrivedMessages[id] = { sentTime, ros2Time: msg.header.stamp, receivedTime: currentTime };
            return;
        }
        if (id < idNum) {
            invalidIdsNeverArrived[id] = sentTime;
            invalidIdsArrivedTooLate[id] = { sentTime, ros2Time: msg.header.stamp, receivedTime: currentTime };
            return;
        } else if (id > idNum) {
            invalidIdsNeverArrived[idNum] = sentTime;
        }
    }
});

// Start sending messages
ros.on('connection', async() => {
    sendMessages();
    await new Promise(resolve => setTimeout(resolve, messagesToSend * 1000 / hz + 3000));
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
