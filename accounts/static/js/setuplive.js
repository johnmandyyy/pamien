const localVideo = document.querySelector('#live-video');
const btnToggleAudio = document.querySelector('#btn-toggle-audio');
const btnToggleVideo = document.querySelector('#btn-toggle-video');
const constraints = {
    'video': true,
    'audio': true
};

var userMedia = navigator.mediaDevices.getUserMedia(constraints)
    .then(stream => {
        localStream = stream;
        localVideo.srcObject = localStream;
        localVideo.muted = true;

        var audioTracks = stream.getAudioTracks();
        var videoTracks = stream.getVideoTracks();

        audioTracks[0].enabed = true;
        videoTracks[0].enabed = true;
    })
    .catch(error => {
        console.log('Error accessing Video', error);
    })

