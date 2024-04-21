var msgs;
var webSocket;
var username;
var mapPeers = {};
var btnSendMessage = document.querySelector('#btn-message');
var messageInput = document.querySelector('#messageTxt');

var usernameInput = document.querySelector('#username');
var labelUsername = document.querySelector('#label-user');
var btnJoin = document.querySelector('#btn-join');
var username = '123';


function webSocketOnMessage(event) {
    console.log('webSocketOnMessage', mapPeers);
    var parseData = JSON.parse(event.data);

    var peerUsername = parseData['peer'];
    var action = parseData['action'];

    if(username == peerUsername) { 
        return;
    }

    var receiver_channel_name = parseData['message']['receiver_channel_name'];
    console.log('receiver_channel', receiver_channel_name);
    if(action=='new-peer') {
        createOfferer(peerUsername, receiver_channel_name);

        return;
    }

    if(action=='new-offer') {
        var offer = parseData['message']['sdp'];

        createAnswerer(offer, peerUsername, receiver_channel_name);

        return;
    }

    if(action == 'new-answer') {
        var answer = parseData['message']['sdp'];

        var peer = mapPeers[peerUsername][0];

        peer.setRemoteDescription(answer);

        return;
    }
}






btnJoin.addEventListener('click', () => { 
    username = usernameInput.value;

    usernameInput.value = '';
    usernameInput.disabled = true;
    usernameInput.style.visibility = 'hidden';

    btnJoin.disabled = true;
    btnJoin.style.visibility = 'hidden';

    labelUsername.innerHTML = username;

    var loc = window.location;
    var wsStart = 'ws://';

    if(loc.protocol == 'https:') {
        wsStart = 'wss://';
    }
    
    var endPoint = wsStart + loc.host + loc.pathname;

    console.log('End Point : ' + endPoint);

    webSocket = new WebSocket(endPoint);

    webSocket.addEventListener('open', (e) => {
        console.log('Connection Open', username);

        sendSignal('new-peer', {});
    });
    webSocket.addEventListener('message', webSocketOnMessage);
    webSocket.addEventListener('close', (e) => {
        console.log('Connection Close');
    });
    webSocket.addEventListener('error', (e) => {
        console.log('Error Occured');
    });
});

function getDataChannels() {
    console.log('getDataChannels', mapPeers);
    var dataChannels = [];

    for(peerUsername in mapPeers) {
        var dataChannel = mapPeers[peerUsername][1];

        dataChannels.push(dataChannel);
    }

    return dataChannels;
}

var localStream = new MediaStream();

const constraints = {
    'video': true,
    'audio': true
};

const localVideo = document.querySelector('#live-video');
const btnToggleAudio = document.querySelector('#btn-toggle-audio');
const btnToggleVideo = document.querySelector('#btn-toggle-video');

var userMedia = navigator.mediaDevices.getUserMedia(constraints)
    .then(stream => {
        localStream = stream;
        localVideo.srcObject = localStream;
        localVideo.muted = true;

        var audioTracks = stream.getAudioTracks();
        var videoTracks = stream.getVideoTracks();

        audioTracks[0].enabed = true;
        videoTracks[0].enabed = true;

        btnToggleAudio.addEventListener('click', () => {
            audioTracks[0].enabled = !audioTracks[0].enabled;

            if(audioTracks[0].enabled) {
                btnToggleAudio.innerHTML = 'Audio Mute';

                return;
            }

            btnToggleAudio.innerHTML = 'Audio Unmute';
        });

        btnToggleVideo.addEventListener('click', () => {
            videoTracks[0].enabled = !videoTracks[0].enabled;

            if(videoTracks[0].enabled) {
                btnToggleVideo.innerHTML = 'Video Off';

                return;
            }

            btnToggleVideo.innerHTML = 'Video On';
        });
    })
    .catch(error => {
        console.log('Error accessing Video', error);
    })
    

function sendSignal(action, message) {
    console.log('sendSignal', mapPeers);
    var jsonStr = JSON.stringify({
        'peer': username,
        'action': action,
        'message': message,
    });
    webSocket.send(jsonStr);
}



function createOfferer(peerUsername, receiver_channel_name) {
    console.log('createOfferer', mapPeers);
    var peer = new RTCPeerConnection(null);

    addLocalTracks(peer);

    var dc = peer.createDataChannel('channel');
    dc.addEventListener('open', () => {
        console.log('Connection opened!');
    });
    dc.addEventListener('message', dcOnMessage);

    var remoteVideo = createVideo(peerUsername);
    setOnTrack(peer, remoteVideo)

    mapPeers[peerUsername] = [peer, dc];

    peer.addEventListener('iceconnectionstatechange', () => {
        var iceConnectionState = peer.iceConnectionState;

        if(iceConnectionState === 'failed' || iceConnectionState === 'disconnected' || iceConnectionState === 'closed') {
            delete mapPeers[peerUsername];

            if(iceConnectionState != 'closed') {
                peer.close();
            }
            removeVideo(remoteVideo);
        }
    });

    peer.addEventListener('icecandidate ', (event) => {
        if(event.candidate) {
            console.log('New ice candidate ', JSON.stringify(peer.localDescription));

            return;
        }

        sendSignal('new-offer', {
            'sdp': peer.localDescription,
            'receiver_channel_name': receiver_channel_name
        });
    });

    peer.createOffer()
        .then(o => peer.setLocalDescription(o))
        .then(() => {
            console.log('Local description set successfully');
        });
}



function createAnswerer(offer, peerUsername, receiver_channel_name) {
    console.log('createAnswerer', mapPeers);
    var peer = new RTCPeerConnection(null);

    addLocalTracks(peer);

    var remoteVideo = createVideo(peerUsername);
    setOnTrack(peer, remoteVideo)

    peer.addEventListener('datachannel', e => {
        peer.dc = e.channel;
        peer.dc.addEventListener('open', () => {
            console.log('Connection opened!');
        });
        peer.dc.addEventListener('message', dcOnMessage);

        mapPeers[peerUsername] = [peer, peer.dc];
    }); 

    peer.addEventListener('iceconnectionstatechange', () => {
        var iceConnectionState = peer.iceConnectionState;

        if(iceConnectionState === 'failed' || iceConnectionState === 'disconnected' || iceConnectionState === 'close')
            delete mapPeers[peerUsername];

            if(iceConnectionState != 'closed') {
                peer.close();
            }
            removeVideo(remoteVideo);
    });

    peer.addEventListener('icecandidate ', (event) => {
        if(event.candidate) {
            console.log('New ice candidate ', JSON.stringify(peer.localDescription));

            return;
        }

        sendSignal('new-answer', {
            'sdp': peer.localDescription,
            'receiver_channel_name': receiver_channel_name
        });
    });

    peer.setRemoteDescription(offer)
        .then(() => {
            console.log('Remote description set successfully for %s.', peerUsername);

            return peer.createAnswer();
        })
        .then(a => {
            console.log('Answer created!');

            peer.setLocalDescription(a);
        })
}



function addLocalTracks(peer) {
    console.log('addLocalTracks', mapPeers);
    localStream.getTracks().forEach(track => {
        peer.addTrack(track, localStream);
    });

    return;
}


var chatbox = document.querySelector('#chatbox');
function dcOnMessage(event) {
    console.log('dcOnMessage', mapPeers);
    var message = event.data;

    var li = document.createElement('li');
    li.appendChild(document.createTextNode(message));
    chatbox.appendChild(li);
}

function createVideo(peerUsername) {
    console.log('createVideo', mapPeers);
    var videoContainer = document.querySelector('#vid-container')

    var remoteVideo = document.createElement('video');

    remoteVideo.id = peerUsername + '-video';
    remoteVideo.autoplay = true;
    remoteVideo.playsInline = true;

    var videoWrapper = document.createElement('div');
    videoWrapper.class = 'row';

    videoContainer.appendChild(videoWrapper);
    videoWrapper.appendChild(remoteVideo);

    return remoteVideo;
}

function removeVideo(video) {
    console.log('removeVideo', mapPeers);
    var videoWrapper = video.parentNode;

    videoWrapper.parentNode.removeChild(videoWrapper);
}

function setOnTrack(peer, remoteVideo) {
    console.log('setOnTrack', mapPeers);
    var remoteStream = new MediaStream();

    remoteVideo.srcObject = remoteStream;

    peer.addEventListener('track', async (event) => {
        remoteStream.addTrack(event.track, remoteStream);
    });
}




function sendMsgOnClick() {
    console.log('sendMsgOnClick', mapPeers);
    var message = messageInput.value;
    console.log(message);
    var li = document.createElement('li');
    li.appendChild(document.createTextNode('Me: ' + message));
    chatbox.append(li);

    var dataChannels = getDataChannels();
    message = username +': '+ message;
    for(index in dataChannels) {
        dataChannels[index].send(message);
    }

    messageInput.value = '';
}



btnSendMessage.addEventListener('click', () => { 
    sendMsgOnClick();
});
