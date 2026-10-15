# TrueWay: Complete System Architecture Specification

**Architecture Principle: The Android application is the primary system. All critical-path functionality (recognition, content retrieval, journaling, search) must execute with zero network dependency after initial setup. The publishing backend exists solely to prepare and distribute content packs — it is never in the user's critical path.**

- **Document Version:** 1.0 — Production System Architecture
- **Effective Date:** 2026-10-11
- **Status:** Approved System Architecture Baseline
- **Scope:** Defines boundaries, contracts, data flow, security, and packaging across the complete TrueWay system.

---

## I. Architecture Overview

### 1.1 System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    PUBLISHING INFRASTRUCTURE                     │
│                      (Online-only, asynchronous)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐      │
│  │  Curatorial   │   │  ML Training │   │  Content     │      │
│  │  CMS         │   │  Pipeline    │   │  Sources     │      │
│  │  (Partner    │   │  (Dataset    │   │  (Wikimedia, │      │
│  │   Editor)    │   │   Builder,   │   │   ASI, Field  │      │
│  │              │   │   Training,  │   │   Collection) │      │
│  └──────┬───────┘   │   Eval)      │   └──────┬───────┘      │
│         │           └──────┬───────┘          │                │
│         │                  │                  │                │
│         └──────────┬───────┴──────────────────┘                │
│                    │                                             │
│                    ▼                                             │
│         ┌──────────────────┐                                    │
│         │   Pack Builder    │                                    │
│         │   (Validation,   │                                    │
│         │   Compression,  │                                    │
│         │   Ed25519       │                                    │
│         │   Signing)       │                                    │
│         └────────┬─────────┘                                    │
│                  │                                               │
└──────────────────┼───────────────────────────────────────────────┘
                   │
                   ▼ (Signed .twpkg files)
         ┌──────────────────┐
         │  CDN / Object    │──── Optional: Peer Relay (Nearby Connections)
         │  Storage         │
         └────────┬─────────┘
                  │
════════════════════╪════════════════════════════════════════════════
                   │  (User-initiated download only)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANDROID APPLICATION                           │
│                    (Offline-capable, critical path)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                PRESENTATION LAYER                        │    │
│  │  (Jetpack Compose UI)                                   │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐    │
│  │                DOMAIN LAYER                               │    │
│  │  (Use Cases, ViewModels, Business Logic)                 │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐    │
│  │                DATA LAYER                                 │    │
│  │  (Repositories, Local DB, Pack Manager, ML Runtime)      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Architectural Pattern

**Clean Architecture with MVVM presentation, offline-first repository pattern, and unidirectional data flow.**

**Key constraint enforced at the architectural level:** No ViewModel, UseCase, or Repository in the recognition, content, or journaling flow may reference a network-dependent interface. Network access exists only in `PackRepository` (downloading packs) and `AnalyticsRepository` (opt-in telemetry), both of which are decoupled from the critical path via dependency inversion.

---

## II. Presentation Layer

### 2.1 UI Framework

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **UI Toolkit** | **Jetpack Compose** (Material 3) | Declarative UI, state-driven, built for the recommended Android architecture pattern. |
| **Navigation** | **Compose Navigation** with typed safe-args | Single-activity architecture, zero fragmentation. |
| **Image Loading** | **Coil 3.x** | Compose-native, supports custom decoders, offline asset caching. |
| **Camera Preview** | **CameraX PreviewView** wrapped in `AndroidView` | CameraX handles lifecycle, orientation, and device compatibility cleanly. |

### 2.2 Target Multi-Module Structure

```
:app                    # Main application, Hilt dependency injection root
:core:ui               # Shared composables, design system, typography, theming
:core:domain           # Use cases, domain models, repository interfaces
:core:data             # Repository implementations, Room, DataStore
:core:ml              # ML runtime abstraction, model management
:core:pack            # Pack download, verification, lifecycle state machine
:core:camera          # CameraX integration, image capture pipeline
:feature:explore      # Search, nearby, categories, trails
:feature:scan         # Camera recognition flow, ScanGate, abstention cards
:feature:place         # Place detail cards, sourced claims, audio docent
:feature:saved         # User journal, bookmarks, personal passport
:feature:downloads    # Pack management, regional catalogs, changelog
:feature:settings     # Privacy toggles, language, accessibility
```

### 2.3 State Management & Unidirectional Data Flow

```kotlin
// Unidirectional Data Flow with MVI-inspired state
data class ScanUiState(
    val cameraPermission: PermissionState = PermissionState.NotRequested,
    val isCapturing: Boolean = false,
    val recognitionResult: RecognitionResult = RecognitionResult.Idle,
    val siteRestrictionWarning: SiteRestriction? = null,
    val lowPowerMode: Boolean = false
)

sealed class RecognitionResult {
    data object Idle : RecognitionResult()
    data class Processing(val startTime: Long) : RecognitionResult()
    data class Candidates(val places: List<PlaceCandidate>) : RecognitionResult()
    data object Unknown : RecognitionResult()
    data class Error(val reason: ErrorReason) : RecognitionResult()
}
```

ViewModels expose `StateFlow<UiState>` and accept `UiIntent` via a single entry point, using Kotlin Coroutines and Flow for reactive data propagation.

---

## III. Domain Layer

### 3.1 Core Domain Models

```kotlin
data class Place(
    val id: PlaceId,
    val canonicalName: LocalizedString,
    val aliases: List<PlaceAlias>,
    val coordinates: GeoPoint?,
    val parentId: PlaceId?,
    val category: PlaceCategory,
    val claims: List<Claim>,
    val assets: List<AssetReference>,
    val lastReviewed: Instant,
    val packVersion: String
)

data class Claim(
    val id: ClaimId,
    val placeId: PlaceId,
    val claimType: ClaimType,  // DOCUMENTED, INTERPRETATION, TRADITION, CONTESTED, OPERATIONAL, HYPOTHESIS
    val content: LocalizedString,
    val era: HistoricalEra?,
    val sources: List<SourceCitation>,
    val editorId: String,
    val reviewState: ReviewState
)

data class SourceCitation(
    val sourceId: SourceId,
    val page: String?,
    val paragraph: String?,
    val doi: String?,
    val accessedDate: Instant,
    val reviewerDecision: ReviewerDecision
)
```

### 3.2 Use Cases (Critical Path — Zero Network Dependency)

```kotlin
class CaptureAndRecognizePlaceUseCase(
    private val imageCapture: ImageCaptureService,
    private val recognitionEngine: RecognitionEngine,
    private val placeRepository: PlaceRepository,
    private val batteryManager: BatteryManager
) {
    suspend operator fun invoke(mode: CaptureMode): Flow<RecognitionResult> = flow {
        val image = imageCapture.capture(mode)
        val candidates = recognitionEngine.recognize(image)
        emit(RecognitionResult.Candidates(candidates))
    }
}

class SearchPlacesUseCase(
    private val searchRepository: SearchRepository
) {
    suspend operator fun invoke(query: String, filters: SearchFilters): List<Place> {
        return searchRepository.search(query, filters)
    }
}

class GetPlaceDetailUseCase(
    private val placeRepository: PlaceRepository
) {
    suspend operator fun invoke(placeId: PlaceId): PlaceDetail {
        return placeRepository.getPlaceWithClaims(placeId)
    }
}
```

---

## IV. Data Layer

### 4.1 Local Database Architecture

```
┌─────────────────────────────────────────────────────┐
│                  ANDROID APP PROCESS                  │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────┐    ┌──────────────────────────┐   │
│  │   Room       │    │   sqlite-vec extension    │   │
│  │  (Standard   │    │   (Loaded at runtime for  │   │
│  │   SQLite)    │    │    vector search)         │   │
│  │              │    │                            │   │
│  │  • places    │    │  • vec0 virtual tables    │   │
│  │  • claims    │    │  • KNN queries            │   │
│  │  • sources   │    │  • cosine similarity      │   │
│  │  • assets    │    │                            │   │
│  │  • FTS5      │    │  Reference:               │   │
│  │    tables    │    │  github.com/asg017/      │   │
│  └─────────────┘    │  sqlite-vec               │   │
│                     └──────────────────────────┘   │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │  SEPARATE DATABASE (User Private)               │ │
│  │  • journal_entries                              │ │
│  │  • visit_history                               │ │
│  │  • user_preferences (DataStore)                 │ │
│  │  • consent_records                             │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Architectural Rationale:** Production v1 uses flat brute-force cosine vector retrieval (`<1 ms` for corpus scale) loaded zero-copy from `TWVEC001` memory-mapped binary vector files or in-memory arrays (ADR-0003), combined with SQLite FTS5 for text search. `sqlite-vec` (`vec0`, ADR-0004) remains a proposed/gated upgrade for larger corpus scales (>10,000 vectors). User-private data (journal, notes, passport stamps) is stored in a separate, isolated database file (`user_journal.sqlite`) so that regional content pack updates or rollbacks never risk user personal data.

### 4.2 Database Schemas

#### Core Heritage Content Database (`content/places.sqlite` in Pack):
```sql
CREATE TABLE places (
    place_id TEXT PRIMARY KEY,
    canonical_name_key TEXT NOT NULL,
    category TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    parent_place_id TEXT REFERENCES places(place_id),
    visitor_mode TEXT NOT NULL CHECK(visitor_mode IN
      ('PHOTO_SUPPORTED','SEARCH_ONLY','QR_PARTNER','TRAIL_STOP','TEXT_REFERENCE_ONLY')),
    visitor_notice TEXT,
    last_reviewed_at TEXT NOT NULL,
    editorial_state TEXT NOT NULL CHECK(editorial_state IN ('DRAFT','REVIEWED','PUBLISHED'))
);

CREATE VIRTUAL TABLE places_fts USING fts5(
    place_id UNINDEXED,
    name_en,
    name_hi,
    name_transliterated,
    aliases_text,
    tokenize = 'unicode61 remove_diacritics 2'
);

CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    place_id TEXT NOT NULL REFERENCES places(place_id),
    claim_type TEXT NOT NULL CHECK(claim_type IN
      ('DOCUMENTED','INTERPRETATION','TRADITION','CONTESTED','OPERATIONAL','HYPOTHESIS')),
    locale TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    era_start TEXT,
    era_end TEXT,
    reviewed_at TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    editorial_state TEXT NOT NULL CHECK(editorial_state IN ('DRAFT','REVIEWED','PUBLISHED'))
);

CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author_or_publisher TEXT,
    publication_year TEXT,
    source_url TEXT,
    rights_id TEXT,
    accessed_at TEXT,
    archived_anchor TEXT
);

CREATE TABLE claim_sources (
    claim_id TEXT NOT NULL REFERENCES claims(claim_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    page_or_anchor TEXT,
    PRIMARY KEY (claim_id, source_id)
);

CREATE VIRTUAL TABLE reference_embeddings USING vec0(
    embedding_id INTEGER PRIMARY KEY,
    asset_id TEXT NOT NULL,
    place_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    embedding float[128] distance_metric=cosine
);

CREATE TABLE operational_notices (
    notice_id TEXT PRIMARY KEY,
    place_id TEXT NOT NULL REFERENCES places(place_id),
    notice_kind TEXT NOT NULL,
    text TEXT NOT NULL,
    authority_source_id TEXT REFERENCES sources(source_id),
    last_verified_at TEXT NOT NULL,
    expires_at TEXT
);
```

### 4.3 Pack Manager State Machine

```kotlin
class PackManager(
    private val packRepository: PackRepository,
    private val signatureVerifier: SignatureVerifier,
    private val storageManager: StorageManager,
    private val databaseMigrator: DatabaseMigrator
) {
    /**
     * State Machine:
     * OFFERED → DOWNLOADING → PAUSED → DOWNLOADING → STAGED
     *   → VERIFYING (Ed25519 signature + component SHA-256 + archive safety)
     *   → INDEXING (FTS sync, vector table mount)
     *   → ACTIVE (Atomic pointer swap)
     * 
     * Rejection Rule: Any failure → REJECTED → OFFERED (purges staging; retains existing pack).
     */
    suspend fun installPack(packUrl: String): Flow<PackInstallState> = flow {
        emit(PackInstallState.Downloading)
        val staged = packRepository.downloadToStaging(packUrl)
        
        emit(PackInstallState.Verifying)
        // 1. Verify Ed25519 signature BEFORE parsing any unverified manifest fields
        val isValid = signatureVerifier.verifyDetached(
            manifest = staged.manifestBytes,
            signature = staged.signatureBytes,
            publisherKey = trustStore.getPublisherKey(staged.manifest.publisher_id)
        )
        if (!isValid) {
            storageManager.cleanStaging(staged)
            emit(PackInstallState.Rejected(RejectionReason.INVALID_SIGNATURE))
            return@flow
        }
        
        // 2. Verify component SHA-256 digests and file sizes
        if (!staged.verifyFileIntegrity()) {
            storageManager.cleanStaging(staged)
            emit(PackInstallState.Rejected(RejectionReason.CHECKSUM_MISMATCH))
            return@flow
        }
        
        // 3. Security audit of ZIP archive (no path traversal, no executables)
        if (!staged.validateArchiveSecurity()) {
            storageManager.cleanStaging(staged)
            emit(PackInstallState.Rejected(RejectionReason.MALICIOUS_ARCHIVE))
            return@flow
        }
        
        emit(PackInstallState.Indexing)
        databaseMigrator.applyPack(staged)
        
        // 4. Atomic activation via filesystem rename
        storageManager.activatePack(staged, previousActivePack)
        emit(PackInstallState.Active)
    }
}
```

### 4.4 Repository Pattern with Hybrid Search

```kotlin
interface PlaceRepository {
    suspend fun getPlace(placeId: PlaceId): Place?
    suspend fun searchPlaces(query: String, filters: SearchFilters): List<Place>
    fun observeNearbyPlaces(location: GeoPoint?, radius: Double?): Flow<List<Place>>
    suspend fun getPlaceWithClaims(placeId: PlaceId): PlaceDetail
    fun getPlaceCategories(): Flow<List<PlaceCategory>>
}

class LocalPlaceRepository(
    private val placeDao: PlaceDao,
    private val searchDao: FtsSearchDao,
    private val vectorSearch: VectorSearchService
) : PlaceRepository {
    
    override suspend fun searchPlaces(query: String, filters: SearchFilters): List<Place> {
        val ftsResults = searchDao.searchPlacesFts(query, filters.toFtsFilter())
        return if (filters.useSemanticSearch) {
            val queryEmbedding = vectorSearch.embedTextQuery(query)
            vectorSearch.rankBySimilarity(queryEmbedding, ftsResults)
        } else {
            ftsResults
        }
    }
}
```

---

## V. ML Runtime Layer

### 5.1 Model Management Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ML RUNTIME ABSTRACTION                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  interface ModelRuntime {                                   │
│      suspend fun loadModel(modelSpec: ModelSpec)           │
│      suspend fun infer(input: ModelInput): ModelOutput     │
│      fun unload()                                          │
│      val capabilities: RuntimeCapabilities                │
│  }                                                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  IMPLEMENTATIONS                                      │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │                                                       │ │
│  │  ┌──────────────────┐  ┌──────────────────────────┐  │ │
│  │  │ MediaPipe Vision │  │ LiteRT-LM                │  │ │
│  │  │ (ImageEmbedder)  │  │ (Gemma 4 E2B / Qwen)     │  │ │
│  │  │                  │  │                          │  │ │
│  │  │ • MobileCLIP-S0  │  │ • Multimodal I/O         │  │ │
│  │  │ • v1 TFLite      │  │ • Conversational QA      │  │ │
│  │  │ • CPU/GPU Del.   │  │ • Grammar-Constrained GBNF│ │
│  │  │ • ~4.1MB model   │  │ • Tier F (>=6GB RAM) only│  │ │
│  │  │ • Critical Path  │  │ • Non-Critical Path      │  │ │
│  │  └──────────────────┘  └──────────────────────────┘  │ │
│  │                                                       │ │
│  │  ┌──────────────────┐  ┌──────────────────────────┐  │ │
│  │  │ ML Kit Text      │  │ sherpa-onnx              │  │ │
│  │  │ Recognition v2   │  │ (IndicConformer)         │  │ │
│  │  │                  │  │                          │  │ │
│  │  │ • Latin/Devanagari│ │ • Hindi/Hinglish ASR     │  │ │
│  │  │ • Signboards/text│  │ • Push-to-talk           │  │ │
│  │  │ • Bundled models │  │ • Tier M+ only           │  │ │
│  │  └──────────────────┘  └──────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Two-Stage Recognition Pipeline

```kotlin
class RecognitionEngine(
    private val imageEmbedder: VisionEmbedder,       // MobileCLIP-S0 (v1) TFLite via MediaPipe
    private val geometricVerifier: GeometricMatcher, // XFeat INT8
    private val vectorSearch: VectorSearch,          // sqlite-vec
    private val calibrator: OutputCalibrator,
    private val geoPriorService: GeoPriorService
) {
    suspend fun recognize(image: CapturedImage, locationContext: LocationContext?): RecognitionResult {
        // 1. Image normalization
        val normalized = image.normalize()
        if (normalized.isLowQuality) {
            return RecognitionResult.Error(ErrorReason.IMAGE_TOO_BLURRY)
        }
        
        // 2. Stage 1: Global MRL feature embedding
        val queryEmbedding = imageEmbedder.embed(normalized)
        
        // 3. KNN candidate search via sqlite-vec
        val candidates = vectorSearch.knnSearch(queryEmbedding, k = 10)
        val geoAdjusted = geoPriorService.apply(candidates, locationContext)
        val placeScores = aggregateScores(geoAdjusted)
        
        // 4. Score calibration & lookalike check
        val topMatch = placeScores.firstOrNull() ?: return RecognitionResult.Unknown
        val runnerUp = placeScores.getOrNull(1)
        val margin = topMatch.score - (runnerUp?.score ?: 0.0)
        
        // Fast path: high score and wide margin
        if (topMatch.score >= calibrator.acceptThreshold && margin >= calibrator.minMargin) {
            return RecognitionResult.Candidates(listOf(topMatch.toCandidate()))
        }
        
        // Ambiguous path: close runner-up (e.g. Nalanda Temple 3 vs Monastery 1)
        if (margin < calibrator.minMargin) {
            val verified = geometricVerifier.verify(
                queryImage = normalized,
                candidatePlaces = listOf(topMatch.placeId, runnerUp!!.placeId)
            )
            if (verified.inliers >= calibrator.minInliers) {
                return RecognitionResult.Candidates(listOf(verified.topCandidate))
            }
        }
        
        // Explicit clean abstention
        return RecognitionResult.Unknown
    }
}
```

### 5.3 Device Tier Negotiation (The Accordion Model)

```kotlin
enum class DeviceTier {
    ENTRY {    // Tier E (<4GB RAM)
        val maxModelSize = 50L * 1024 * 1024
        val supportsOptionalLLM = false
        val supportsOfflineASR = false
    },
    MID {      // Tier M (4GB–6GB RAM)
        val maxModelSize = 300L * 1024 * 1024
        val supportsOptionalLLM = false
        val supportsOfflineASR = true  // sherpa-onnx IndicConformer
    },
    FLAGSHIP { // Tier F (>=6GB RAM, NPU present)
        val maxModelSize = 2500L * 1024 * 1024
        val supportsOptionalLLM = true  // Gemma 4 E2B via LiteRT-LM
        val supportsOfflineASR = true
    }
}

class DeviceTierManager(private val context: Context) {
    fun detectTier(): DeviceTier {
        val memoryInfo = ActivityManager.MemoryInfo()
        (context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager).getMemoryInfo(memoryInfo)
        val totalMem = memoryInfo.totalMem
        
        return when {
            totalMem >= 6L * 1024 * 1024 * 1024 -> DeviceTier.FLAGSHIP
            totalMem >= 4L * 1024 * 1024 * 1024 -> DeviceTier.MID
            else -> DeviceTier.ENTRY
        }
    }
}
```

---

## VI. Security & Privacy Architecture

### 6.1 Pack Cryptography & Android Keystore

```
PACK SIGNING (Publisher Pipeline)
┌──────────────────────────────────────────┐
│ 1. Canonical manifest.cjson (RFC 8785)   │
│ 2. SHA-256 digest calculated per file    │
│ 3. Detached Ed25519 signature generated  │
│ 4. Output: .twpkg ZIP archive            │
└──────────────────────────────────────────┘

PACK VERIFICATION (Device Runtime)
┌──────────────────────────────────────────┐
│ 1. Read bundled public key from assets   │
│ 2. Verify detached manifest.ed25519      │
│ 3. If invalid -> ABORT & PURGE STAGING   │
│ 4. Validate SHA-256 for all payload files│
│ 5. Path traversal / zip-slip verification│
│ 6. Verify all assets have license entries│
│ 7. Atomic rename to active directory     │
└──────────────────────────────────────────┘
```

**Android Keystore Integration:** Public keys are pinned in the app binary. Trust store rotations are delivered via signed manifest updates verified against existing root keys.

### 6.2 Privacy Boundary & Zero-Telemetry Contract

```
┌────────────────────────────────────────────────────────┐
│                   PRIVACY BOUNDARY                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  DEFAULT BEHAVIOR (Zero consent needed):               │
│  ✗ Zero network calls in critical path                 │
│  ✗ Zero photo or camera frame uploads                 │
│  ✗ Zero GPS coordinates sent off-device                │
│  ✗ Zero audio streaming to cloud                      │
│  ✗ Zero analytics or behavioral tracking              │
│                                                        │
│  OPT-IN BEHAVIOR (Requires explicit UI consent):       │
│  ✓ Aggregated crash logs (PII stripped)               │
│  ✓ Gap beacon (coarse geographic region request)       │
│                                                        │
│  LOCAL ONLY (Never leaves private app sandbox):        │
│  ✓ Saved journal entries and travel notes              │
│  ✓ Captured scan photos (stored in private cache)     │
│  ✓ Transcribed voice queries                          │
│  ✓ Local search history                                │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## VII. Offline Map & Navigation Layer

### 7.1 MapLibre & PMTiles Architecture

```kotlin
class OfflineMapManager(
    private val mapLibreMap: MapLibreMap,
    private val packManager: PackManager
) {
    fun initializeMap(activePack: ActivePack) {
        val pmtilesSource = activePack.getMapComponent("bihar_circuit")
            ?: return  // Map tiles not installed: show offline POI list view
        
        // Load local PMTiles file directly without running an HTTP tile server
        val style = Style.Builder()
            .withSource(
                VectorSource(
                    id = "trueway-pmtiles",
                    tiles = listOf("pmtiles://${pmtilesSource.localPath}")
                )
            )
            .withLayer(
                LineLayer("roads", "trueway-pmtiles")
                    .withSourceLayer("roads")
                    .lineColor("#6366F1")
            )
        mapLibreMap.setStyle(style)
    }
}
```

**PMTiles** is a single-file archive format for tiled vector data, allowing MapLibre Native to seek vector tiles directly from disk with zero server overhead.

---

## VIII. Deployment & Distribution Strategy

### 8.1 Google Play App Delivery Strategy

```
┌──────────────────────────────────────────────────────────┐
│                GOOGLE PLAY DISTRIBUTION                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Base AAB (< 200MB):                                     │
│  ├── App code, Compose UI, Domain logic                 │
│  ├── Prebuilt sqlite-vec native libraries (arm64-v8a)   │
│  ├── MobileCLIP-S0 v1 TFLite model (~4.1MB)            │
│  ├── Default UI strings and iconography                  │
│  └── Bundled publisher public key                        │
│                                                          │
│  Play Asset Delivery (On-Demand Feature Modules):       │
│  ├── sherpa-onnx Hindi ASR model (~200MB)                │
│  ├── ML Kit offline script dictionaries                  │
│  └── Gemma 4 E2B LiteRT-LM model (~2GB, Tier F only)    │
│                                                          │
│  User-Initiated Regional Downloads (.twpkg):             │
│  ├── Regional knowledge pack (5–50MB)                   │
│  ├── Regional PMTiles map pack (25–100MB)                │
│  └── Curated audio narration pack (30–150MB)             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Offline Peer Relay (Nearby Connections)

```kotlin
class PackRelayManager(
    private val nearbyClient: NearbyConnectionsClient,
    private val packVerifier: PackVerifier
) {
    suspend fun advertisePack(pack: ActivePack) {
        nearbyClient.startAdvertising(
            serviceId = "com.trueway.packrelay",
            strategy = Strategy.P2P_CLUSTER
        )
    }
    
    suspend fun receivePack(endpointId: String): Flow<PackTransferProgress> = flow {
        val receivedFile = nearbyClient.receivePayload(endpointId)
        // Receiver independently verifies Ed25519 signature & SHA-256 hashes
        val verification = packVerifier.verify(receivedFile)
        if (verification.isValid) {
            emit(PackTransferProgress.Verified(receivedFile))
        } else {
            emit(PackTransferProgress.Rejected(verification.reason))
        }
    }
}
```

---

## IX. Master Technology Stack Summary

| Layer | Component | Size / Resource Impact | Critical Path? |
| :--- | :--- | :--- | :--- |
| **Language** | Kotlin 2.x | Standard JVM bytecode | **Yes** |
| **UI Toolkit** | Jetpack Compose + Material 3 | Direct rendering pipeline | **Yes** |
| **Navigation** | Compose Navigation (Safe Args) | Zero overhead | **Yes** |
| **Camera** | CameraX (Preview + ImageCapture) | ~2MB native library | **Yes** |
| **Vision Model** | MobileCLIP-S0 (v1) TFLite (MediaPipe) | ~4.1MB (vision_encoder.tflite) | **Yes** |
| **Geometric Verifier**| XFeat INT8 Micro-RANSAC | ~3.8MB (Weights) | Candidate (P1 Gated) |
| **Vector Engine** | Flat Brute-Force Retrieval (TWVEC001 / FloatArray) | Zero native overhead | **Yes (v1 active; sqlite-vec P1 Gated)** |
| **Database** | Room + SQLite FTS5 | Platform SQLite | **Yes** |
| **Maps** | MapLibre Native + PMTiles | ~15MB native library | No (Fallback to list) |
| **ASR (Speech)** | sherpa-onnx (IndicConformer) | ~200MB (Optional module) | No (Fallback to text) |
| **LLM (Reasoning)** | Gemma 4 E2B (LiteRT-LM) | ~2GB RAM (Tier F only) | No (Fallback to cards) |
| **P2P Relay** | Google Nearby Connections API | API surface only | No (P1 Feature) |
| **Pack Crypto** | Ed25519 Detached Signature | <1KB runtime | **Yes** |

---

## X. Performance Constraints & Release Gates

| Metric | Target Specification | Validation Mechanism |
| :--- | :--- | :--- |
| **Cold Startup Time** | $<2.0\text{ s}$ to interactive UI | Automated CI benchmark on entry device |
| **Recognition Latency** | P50 $<2.5\text{ s}$, P95 $<6.0\text{ s}$ | Instrumented CameraX capture pipeline tests |
| **Search Query Latency**| $<100\text{ ms}$ over 1,000 POIs | SQLite FTS5 benchmark |
| **Pack Activation** | $<30\text{ s}$ for 100MB pack | Verification and unpack integration test |
| **Peak Heap Memory** | $<300\text{ MB}$ (without LLM) | Android Memory Profiler automated assertion |
| **Battery Consumption**| Target envelope set after field baselines | Field measurement protocol |
| **Offline Isolation** | **Zero network requests** in critical path | Packet interception test in `RADIO-OFF` mode |

---

## XI. Architecture Decision Records (ADR Summary)

* **ADR-001 (ADR-0004):** *Flat Vector Retrieval for v1; `sqlite-vec` Gated for P1.* At 50–500 POI scale, in-memory zero-copy binary vector retrieval (`TWVEC001`) executes in $<1\text{ ms}$; `sqlite-vec` remains a proposed/gated upgrade.
* **ADR-002 (ADR-0003):** *Two-Stage Vision Architecture.* MobileCLIP-S0 (v1) via MediaPipe ImageEmbedder for global candidate ranking paired with candidate geometric verifier for micro-geometric lookalike disambiguation.
* **ADR-003 (ADR-0001):** *LiteRT & ONNX Runtime Mobile.* Deploy models via robust edge runtimes with direct XNNPACK and GPU execution provider support; avoid deprecated NNAPI.
* **ADR-004 (ADR-0005):** *PMTiles for Offline Vector Maps.* Single-file archive format enabling MapLibre Native to render offline maps with zero tile-server processes.
* **ADR-005 (ADR-0006):** *Ed25519 for Pack Signing.* Detached 64-byte signature over canonical JSON manifest; unverified archives are purged immediately.
* **ADR-006 (ADR-0007):** *Offline Peer Relay via Nearby Connections.* Enables zero-internet device-to-device pack sharing with independent recipient signature verification (Wi-Fi Aware NAN is a research alternative).
* **ADR-007 (ADR-0008):** *Database Isolation for User Data.* Publisher packs (`places.sqlite`) are replaceable, while user journals (`user_journal.sqlite`) remain strictly isolated.

---

## XII. Offline Verification Test Protocol

Before any build is promoted to Beta or Release, it must pass the **Fully Offline Release Protocol**:

1. Install APK on a factory-reset Android test device via ADB.
2. Download region pack `in-bihar-buddhist-circuit.twpkg`.
3. Switch device into **Airplane Mode (`RADIO-OFF`)** with Wi-Fi, Cellular, and Bluetooth disabled.
4. Attach an external network proxy monitor; assert **0 network packets transmitted**.
5. Execute end-to-end user journeys:
   * Launch app $\rightarrow$ UI renders immediately.
   * Search *"Nalanda"* in English and Hindi $\rightarrow$ correct cards display.
   * Open place detail card $\rightarrow$ source citations and claim badges render.
   * Point camera at test target $\rightarrow$ recognition accepts or cleanly abstains.
   * Save entry in journal $\rightarrow$ entry persists across app restarts.
6. **Pass Condition:** 100% of critical paths succeed; zero network egress.
