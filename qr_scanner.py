import QRCodeScanner from 'react-native-qrcode-scanner';

<QRCodeScanner onRead={(e) => {
  const playlistToken = extractTokenFromUrl(e.data);
  addPlaylistByToken(playlistToken);
}} />
