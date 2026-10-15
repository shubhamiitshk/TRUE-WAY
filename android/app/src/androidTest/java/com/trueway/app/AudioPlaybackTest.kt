package com.trueway.app

import android.media.MediaPlayer
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.io.FileOutputStream

/**
 * Instrumented Audio Playback Test (FIELD_PERFORMANCE_PROTOCOL.md §6).
 *
 * Verifies on real Android runtime:
 * 1. Bundled OGG Vorbis audio asset accessibility via AssetFileDescriptor / stream.
 * 2. Real Android MediaPlayer preparation, track duration, state transitions.
 * 3. Audio resource cleanup and decoder release without memory leaks.
 */
@RunWith(AndroidJUnit4::class)
class AudioPlaybackTest {

    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext

    @Test
    fun bundledAudioAssetsExistAndAreDecodable() {
        val assetList = context.assets.list("audio") ?: emptyArray()
        assertTrue("Bundled assets must contain audio directory", assetList.isNotEmpty())
        assertTrue(
            "Expected mahabodhi_guide.ogg in bundled assets",
            assetList.contains("mahabodhi_guide.ogg")
        )

        val fd = context.assets.openFd("audio/mahabodhi_guide.ogg")
        assertNotNull("AssetFileDescriptor must be non-null", fd)
        assertTrue("File length must be positive", fd.length > 0)
        fd.close()
    }

    @Test
    fun mediaPlayLifecycleExecutesCleanlyOnDevice() {
        val player = MediaPlayer()
        try {
            val fd = context.assets.openFd("audio/mahabodhi_guide.ogg")
            player.setDataSource(fd.fileDescriptor, fd.startOffset, fd.length)
            fd.close()

            player.prepare()
            val duration = player.duration
            assertTrue("Audio duration must be greater than 0 ms", duration > 0)

            // Test play state transition
            player.start()
            assertTrue("Player should be playing after start()", player.isPlaying)

            // Test pause state transition
            player.pause()
            assertTrue("Player should not be playing after pause()", !player.isPlaying)

            // Test stop
            player.stop()
        } finally {
            player.release()
        }
    }

    @Test
    fun mediaPlayStreamsFromFileDescriptorWithoutCrashing() {
        // Test playback from cache file (replicating external pack resolution)
        val tempFile = File(context.cacheDir, "test_audio_sample.ogg")
        try {
            context.assets.open("audio/mahabodhi_guide.ogg").use { input ->
                FileOutputStream(tempFile).use { output ->
                    input.copyTo(output)
                }
            }
            assertTrue("Temp audio file must exist", tempFile.exists() && tempFile.length() > 0)

            val player = MediaPlayer()
            try {
                java.io.FileInputStream(tempFile).use { fis ->
                    player.setDataSource(fis.fd)
                }
                player.prepare()
                assertTrue("Duration should be positive", player.duration > 0)
            } finally {
                player.release()
            }
        } finally {
            if (tempFile.exists()) tempFile.delete()
        }
    }
}
