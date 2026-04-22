// VoiceCommandHandler.js
import Voice from '@react-native-voice/voice';

const parseCommand = (text) => {
  if (text.includes('play playlist')) {
    const playlistName = extractPlaylistName(text);
    playPlaylist(playlistName);
  } else if (text.includes('skip')) {
    skipTrack();
  }
};

Voice.onSpeechResults = (e) => {
  parseCommand(e.value[0]);
};

const startListening = async () => {
  await Voice.start('en-US');
};
