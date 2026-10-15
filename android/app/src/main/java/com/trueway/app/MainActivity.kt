package com.trueway.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.trueway.app.data.PlaceRepository
import com.trueway.app.journal.JournalExporter
import com.trueway.app.journal.JournalGraph
import com.trueway.app.ui.TrueWayApp
import com.trueway.app.ui.theme.TrueWayTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        JournalGraph.init(this) // private journal file; no account, no network.
        com.trueway.app.pack.PackImporter.onBeforePackDirectorySwap = { packDir ->
            PlaceRepository.evictPackDirectory(packDir)
            com.trueway.app.pack.PackMediaResolver.evictSharedPackCache(packDir)
        }
        PlaceRepository.initForPackDir(this) // installed pack DB, else bundled corpus.
        JournalExporter.pruneOldExports(this, maxAgeHours = 1) // prune abandoned share exports
        enableEdgeToEdge()
        setContent {
            TrueWayTheme {
                TrueWayApp()
            }
        }
    }
}
