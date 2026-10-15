package com.trueway.app.touchpoint

import org.bouncycastle.crypto.generators.Ed25519KeyPairGenerator
import org.bouncycastle.crypto.params.Ed25519KeyGenerationParameters
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters
import org.bouncycastle.crypto.signers.Ed25519Signer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.SecureRandom
import java.util.Base64

/**
 * Touchpoint acceptance (TOUCH-033…036, §29.2) with REAL Ed25519 — Python
 * fixtures signed by `tests/fixtures/qr/make_demo_touchpoint.py` plus a
 * JVM-generated round-trip. No mocked crypto anywhere.
 */
class TouchpointTest {

    private fun res(name: String): String =
        javaClass.classLoader?.getResourceAsStream("qr/$name")!!
            .bufferedReader().readText()

    private fun envelopeParts(name: String): Pair<ByteArray, ByteArray> {
        val o = org.json.JSONObject(res(name))
        fun b64(s: String): ByteArray {
            var p = s.trim()
            repeat((4 - p.length % 4) % 4) { p += "=" }
            return Base64.getUrlDecoder().decode(p)
        }
        return b64(o.getString("c")) to b64(o.getString("s"))
    }

    private fun trust() = TouchpointVerifier.parseTrustStore(res("trust_store.json"))

    @Test
    fun validDemoEnvelopeVerifiesAndResolves() {
        val (c, s) = envelopeParts("demo_touchpoint_envelope.json")
        val r = TouchpointVerifier.verify(c, s, trust())
        assertTrue(r is TouchpointResult.Valid)
        assertEquals("in-bihar-nalanda-museum", (r as TouchpointResult.Valid).payload.placeId)
    }

    @Test
    fun qrUriFormParsesToSamePayload() {
        val text = res("demo_touchpoint_qr.txt")
        val parts = TouchpointParser.parseQrText(text)
            ?: throw AssertionError("QR URI rejected")
        val r = TouchpointVerifier.verify(parts.first, parts.second, trust())
        assertTrue(r is TouchpointResult.Valid)
    }

    @Test
    fun forgedSignatureRejected() {
        val (c, s) = envelopeParts("forged_touchpoint_envelope.json")
        val r = TouchpointVerifier.verify(c, s, trust())
        assertEquals(TouchpointReject.BAD_SIGNATURE, (r as TouchpointResult.Invalid).reason)
    }

    @Test
    fun expiredRejected() {
        val (c, s) = envelopeParts("expired_touchpoint_envelope.json")
        // expires_at=2020: any later clock must reject.
        val r = TouchpointVerifier.verify(c, s, trust(), nowMs = 1_700_000_000_000L)
        assertEquals(TouchpointReject.EXPIRED, (r as TouchpointResult.Invalid).reason)
    }

    @Test
    fun unknownIssuerRejected() {
        val (c, s) = envelopeParts("unknownissuer_touchpoint_envelope.json")
        val r = TouchpointVerifier.verify(c, s, trust())
        assertEquals(TouchpointReject.UNKNOWN_ISSUER, (r as TouchpointResult.Invalid).reason)
    }

    @Test
    fun arbitraryUrlsAndGarbageAreNeverTouched() {
        assertEquals(null, TouchpointParser.parseQrText("https://evil.example/qr?id=1"))
        assertEquals(null, TouchpointParser.parseQrText("WIFI:S:cafe;T:WPA;P:secret;;"))
        assertEquals(null, TouchpointParser.parseQrText("tw://place/v1/onlyonepart"))
        assertEquals(null, TouchpointParser.parseQrText("tw://other/v9/abc.def"))
    }

    @Test
    fun authenticatedButUninstalledPlaceIsHonestUnknown() {
        // Fresh JVM keypair: sign a payload for a place outside the corpus.
        val gen = Ed25519KeyPairGenerator()
        gen.init(Ed25519KeyGenerationParameters(SecureRandom()))
        val kp = gen.generateKeyPair()
        val priv = kp.private as Ed25519PrivateKeyParameters
        val pub = (kp.public as org.bouncycastle.crypto.params.Ed25519PublicKeyParameters).encoded
        val canonical = """{"expires_at":null,"human_label":"Nowhere","issued_at":"2026-10-10T00:00:00Z","issuer_id":"test","key_id":"k1","pack_id":"p","place_id":"no-such-place","site_serial":null,"touchpoint_id":"t1"}"""
            .toByteArray()
        val signer = Ed25519Signer()
        signer.init(true, priv)
        signer.update(canonical, 0, canonical.size)
        val sig = signer.generateSignature()
        val r = TouchpointVerifier.verify(
            canonical, sig, listOf(TrustedIssuer("test", "k1", pub)),
        )
        assertTrue(r is TouchpointResult.ValidUnknownPlace)
    }

    @Test
    fun loadTrustStoreLoadsFromPackDir() {
        val tempDir = java.nio.file.Files.createTempDirectory("test-touch-trust").toFile()
        try {
            val json = """
            {
              "issuers": [
                {
                  "issuer_id": "test.issuer",
                  "key_id": "key-rot-1",
                  "pubkey_b64u": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                  "status": "ACTIVE"
                }
              ]
            }
            """.trimIndent()
            java.io.File(tempDir, "touch_issuers.json").writeText(json)

            val issuers = TouchpointVerifier.loadTrustStore(context = null, packDir = tempDir)
            assertEquals(1, issuers.size)
            assertEquals("test.issuer", issuers[0].issuerId)
            assertEquals("key-rot-1", issuers[0].keyId)
            assertEquals(32, issuers[0].pubkey.size)
        } finally {
            tempDir.deleteRecursively()
        }
    }

    @Test
    fun loadTrustStoreLoadsFromPackContentDir() {
        val tempDir = java.nio.file.Files.createTempDirectory("test-touch-trust-content").toFile()
        try {
            val contentDir = java.io.File(tempDir, "content").apply { mkdirs() }
            val json = """
            {
              "issuers": [
                {
                  "issuer_id": "regional.asi",
                  "key_id": "asi-bihar-2026",
                  "pubkey_b64u": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                  "status": "ACTIVE"
                }
              ]
            }
            """.trimIndent()
            java.io.File(contentDir, "touch_issuers.json").writeText(json)

            val issuers = TouchpointVerifier.loadTrustStore(context = null, packDir = tempDir)
            assertEquals(1, issuers.size)
            assertEquals("regional.asi", issuers[0].issuerId)
            assertEquals("asi-bihar-2026", issuers[0].keyId)
        } finally {
            tempDir.deleteRecursively()
        }
    }

    @Test
    fun loadTrustStoreEmptyOnNullOrEmptyDir() {
        val tempDir = java.nio.file.Files.createTempDirectory("test-touch-trust-empty").toFile()
        try {
            val issuers = TouchpointVerifier.loadTrustStore(context = null, packDir = tempDir)
            assertTrue(issuers.isEmpty())
        } finally {
            tempDir.deleteRecursively()
        }
    }

    @Test
    fun bundledAssetsTouchIssuersMatchesFixtureTrustStore() {
        val assetCandidates = listOf(
            java.io.File("src/main/assets/touch_issuers.json"),
            java.io.File("android/app/src/main/assets/touch_issuers.json"),
            java.io.File("../app/src/main/assets/touch_issuers.json"),
        )
        val assetFile = assetCandidates.firstOrNull { it.isFile }
        if (assetFile != null) {
            val bundledIssuers = TouchpointVerifier.parseTrustStore(assetFile.readText())
            val fixtureIssuers = trust()
            assertEquals(fixtureIssuers.size, bundledIssuers.size)
            assertEquals(fixtureIssuers[0].issuerId, bundledIssuers[0].issuerId)
            assertEquals(fixtureIssuers[0].keyId, bundledIssuers[0].keyId)
            org.junit.Assert.assertArrayEquals(
                "Bundled assets/touch_issuers.json public key must match QR fixture trust_store.json",
                fixtureIssuers[0].pubkey,
                bundledIssuers[0].pubkey,
            )
        }
    }
}
