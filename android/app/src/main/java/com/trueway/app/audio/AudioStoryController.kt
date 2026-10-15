package com.trueway.app.audio

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.os.Build
import com.trueway.app.pack.ResolvedMedia
import com.trueway.app.pack.setResolvedDataSource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface AudioPlaybackState {
    data object Idle : AudioPlaybackState
    data class Playing(val placeId: String, val locale: String, val durationMs: Int) : AudioPlaybackState
    data class Paused(val placeId: String, val locale: String, val positionMs: Int, val durationMs: Int) : AudioPlaybackState
    data class Error(val placeId: String, val message: String) : AudioPlaybackState
}

/**
 * Lifecycle-safe audio narration controller (F101).
 * Hoists MediaPlayer out of composable UI scope, managing audio focus and exposing StateFlow playback state.
 */
class AudioStoryController(context: Context) {

    private val appContext = context.applicationContext
    private val audioManager = appContext.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private var mediaPlayer: MediaPlayer? = null
    private var activePlaceId: String? = null
    private var activeLocale: String = "en"

    private val _state = MutableStateFlow<AudioPlaybackState>(AudioPlaybackState.Idle)
    val state: StateFlow<AudioPlaybackState> = _state.asStateFlow()

    private val focusChangeListener = AudioManager.OnAudioFocusChangeListener { change ->
        when (change) {
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK,
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT -> pause()
            AudioManager.AUDIOFOCUS_LOSS -> stopAndRelease()
        }
    }

    private val focusRequest: AudioFocusRequest? =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
                .setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build()
                )
                .setWillPauseWhenDucked(true)
                .setOnAudioFocusChangeListener(focusChangeListener)
                .build()
        } else null

    private var currentSpeed: Float = 1.0f

    fun play(placeId: String, locale: String, media: ResolvedMedia) {
        stopAndRelease()
        if (!requestAudioFocus()) {
            _state.value = AudioPlaybackState.Error(placeId, "Audio focus denied")
            return
        }
        activePlaceId = placeId
        activeLocale = locale
        val mp = MediaPlayer()
        val bound = runCatching { mp.setResolvedDataSource(appContext, media) }.getOrDefault(false)
        if (!bound) {
            mp.release()
            _state.value = AudioPlaybackState.Error(placeId, "Unverified or missing audio asset")
            return
        }
        mp.setOnPreparedListener { player ->
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && currentSpeed != 1.0f) {
                player.runCatching {
                    val params = runCatching { playbackParams }.getOrDefault(android.media.PlaybackParams())
                    playbackParams = params.setSpeed(currentSpeed)
                }
            }
            player.start()
            _state.value = AudioPlaybackState.Playing(placeId, locale, player.duration)
        }
        mp.setOnCompletionListener { player ->
            _state.value = AudioPlaybackState.Paused(placeId, locale, player.duration, player.duration)
            abandonAudioFocus()
        }
        mp.setOnErrorListener { _, what, extra ->
            _state.value = AudioPlaybackState.Error(placeId, "Decoder error ($what/$extra)")
            stopAndRelease()
            true
        }
        mediaPlayer = mp
        mp.prepareAsync()
    }

    fun pause() {
        val mp = mediaPlayer ?: return
        val pid = activePlaceId ?: return
        if (mp.isPlaying) {
            mp.pause()
            _state.value = AudioPlaybackState.Paused(pid, activeLocale, mp.currentPosition, mp.duration)
        }
    }

    fun resume() {
        val mp = mediaPlayer ?: return
        val pid = activePlaceId ?: return
        if (!mp.isPlaying && requestAudioFocus()) {
            mp.start()
            _state.value = AudioPlaybackState.Playing(pid, activeLocale, mp.duration)
        }
    }

    fun seekTo(positionMs: Int) {
        mediaPlayer?.seekTo(positionMs.coerceAtLeast(0))
    }

    fun setSpeed(speed: Float) {
        currentSpeed = speed
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            mediaPlayer?.runCatching {
                val params = runCatching { playbackParams }.getOrDefault(android.media.PlaybackParams())
                playbackParams = params.setSpeed(speed)
            }
        }
    }

    fun stopAndRelease() {
        mediaPlayer?.runCatching {
            if (isPlaying) stop()
            release()
        }
        mediaPlayer = null
        activePlaceId = null
        abandonAudioFocus()
        _state.value = AudioPlaybackState.Idle
    }

    private fun requestAudioFocus(): Boolean {
        val res = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && focusRequest != null) {
            audioManager.requestAudioFocus(focusRequest)
        } else {
            @Suppress("DEPRECATION")
            audioManager.requestAudioFocus(
                focusChangeListener,
                AudioManager.STREAM_MUSIC,
                AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK
            )
        }
        return res == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
    }

    private fun abandonAudioFocus() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && focusRequest != null) {
            audioManager.abandonAudioFocusRequest(focusRequest)
        } else {
            @Suppress("DEPRECATION")
            audioManager.abandonAudioFocus(focusChangeListener)
        }
    }

    val currentPositionMs: Int
        get() = mediaPlayer?.runCatching { currentPosition }?.getOrDefault(0) ?: 0

    companion object {
        @Volatile
        private var instance: AudioStoryController? = null

        fun get(context: Context): AudioStoryController {
            return instance ?: synchronized(this) {
                instance ?: AudioStoryController(context.applicationContext).also { instance = it }
            }
        }
    }
}
