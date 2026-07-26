package com.example.musicplayer.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FastForward
import androidx.compose.material.icons.filled.FastRewind
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.QueueMusic
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material.icons.filled.SkipPrevious
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.musicplayer.data.Track
import com.example.musicplayer.player.PlayerState

@Composable
fun MusicPlayerApp(
    tracks: List<Track>,
    playerState: PlayerState,
    permissionGranted: Boolean,
    onRequestPermission: () -> Unit,
    onTrackSelected: (Track) -> Unit,
    onPlayPause: () -> Unit,
    onSeek: (Long) -> Unit,
    onStop: () -> Unit,
    onNext: () -> Unit,
    onPrevious: () -> Unit,
) {
    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colors.background) {
            Column(modifier = Modifier.padding(16.dp)) {
                TopAppBar(
                    title = { Text(text = "Music Player") },
                    backgroundColor = MaterialTheme.colors.primary,
                    contentColor = Color.White,
                    navigationIcon = {
                        Icon(imageVector = Icons.Default.QueueMusic, contentDescription = null, modifier = Modifier.padding(12.dp))
                    }
                )

                Spacer(modifier = Modifier.height(16.dp))

                if (!permissionGranted) {
                    PermissionRequestCard(onRequestPermission)
                } else if (tracks.isEmpty()) {
                    EmptyState()
                } else {
                    TrackList(tracks = tracks, onTrackSelected = onTrackSelected, currentTrack = playerState.currentTrack)
                }

                Spacer(modifier = Modifier.height(16.dp))

                PlayerPanel(
                    playerState = playerState,
                    onPlayPause = onPlayPause,
                    onSeek = onSeek,
                    onStop = onStop,
                    onNext = onNext,
                    onPrevious = onPrevious,
                )
            }
        }
    }
}

@Composable
private fun PermissionRequestCard(onRequestPermission: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth(), elevation = 4.dp) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Permissão de áudio necessária", style = MaterialTheme.typography.h6)
            Spacer(modifier = Modifier.height(8.dp))
            Text("Conceda acesso para ler as músicas do seu aparelho e permitir reprodução fluida em segundo plano.")
            Spacer(modifier = Modifier.height(12.dp))
            Button(onClick = onRequestPermission) {
                Text("Conceder permissão")
            }
        }
    }
}

@Composable
private fun EmptyState() {
    Box(modifier = Modifier.fillMaxWidth().height(220.dp), contentAlignment = Alignment.Center) {
        Text("Nenhuma música encontrada. Adicione arquivos MP3 ao dispositivo e abra o app novamente.")
    }
}

@Composable
private fun TrackList(tracks: List<Track>, onTrackSelected: (Track) -> Unit, currentTrack: Track?) {
    Column(modifier = Modifier.fillMaxWidth().weight(1f)) {
        LazyColumn(modifier = Modifier.fillMaxWidth()) {
            items(tracks) { track ->
                TrackItem(track = track, isPlaying = track == currentTrack, onClick = { onTrackSelected(track) })
                Divider()
            }
        }
    }
}

@Composable
private fun TrackItem(track: Track, isPlaying: Boolean, onClick: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(track.title, style = MaterialTheme.typography.subtitle1, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(track.artist, style = MaterialTheme.typography.body2, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }

        if (isPlaying) {
            Icon(Icons.Default.Pause, contentDescription = null, tint = MaterialTheme.colors.primary)
        }
    }
}

@Composable
private fun PlayerPanel(
    playerState: PlayerState,
    onPlayPause: () -> Unit,
    onSeek: (Long) -> Unit,
    onStop: () -> Unit,
    onNext: () -> Unit,
    onPrevious: () -> Unit,
) {
    val track = playerState.currentTrack

    Card(modifier = Modifier.fillMaxWidth(), elevation = 6.dp) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(track?.title ?: "Nenhuma música selecionada", style = MaterialTheme.typography.h6)
            Spacer(modifier = Modifier.height(4.dp))
            Text(track?.artist ?: "Aguardando seleção", style = MaterialTheme.typography.body2)

            Spacer(modifier = Modifier.height(12.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(playerState.position.formatMillis())
                Slider(
                    value = playerState.position.coerceAtMost(playerState.duration).toFloat(),
                    onValueChange = { onSeek(it.toLong()) },
                    valueRange = 0f..playerState.duration.coerceAtLeast(1L).toFloat(),
                    modifier = Modifier.weight(1f).padding(horizontal = 12.dp)
                )
                Text(playerState.duration.formatMillis())
            }

            Spacer(modifier = Modifier.height(12.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceAround) {
                IconButton(onClick = onPrevious) {
                    Icon(Icons.Default.SkipPrevious, contentDescription = "Anterior")
                }
                IconButton(onClick = onPlayPause) {
                    Icon(if (playerState.isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow, contentDescription = "Play/Pause")
                }
                IconButton(onClick = onNext) {
                    Icon(Icons.Default.SkipNext, contentDescription = "Próxima")
                }
                IconButton(onClick = onStop) {
                    Icon(Icons.Default.FastRewind, contentDescription = "Parar")
                }
            }
        }
    }
}

private fun Long.formatMillis(): String {
    val seconds = (this / 1000).toInt()
    val minutes = seconds / 60
    val remaining = seconds % 60
    return "%d:%02d".format(minutes, remaining)
}
