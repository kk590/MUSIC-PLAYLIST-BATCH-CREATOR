// WebSocket handler
ws.on('add_song', async (data) => {
    const { playlistId, songId } = data;
    await addSongToPlaylist(playlistId, songId);
    broadcastToRoom(playlistId, { type: 'song_added', songId });
});
