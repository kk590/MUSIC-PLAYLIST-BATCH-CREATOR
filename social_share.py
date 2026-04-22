import Share from 'react-native-share';

const sharePlaylist = async (playlist) => {
  await Share.open({
    url: `https://app.com/shared/${playlist.token}`,
    message: `Check out my playlist: ${playlist.name}`,
  });
};
