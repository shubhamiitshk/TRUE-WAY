package com.trueway.app.pack

import org.bouncycastle.crypto.generators.Ed25519KeyPairGenerator
import org.bouncycastle.crypto.params.Ed25519KeyGenerationParameters
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters
import org.bouncycastle.crypto.signers.Ed25519Signer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files
import java.security.MessageDigest
import java.util.Base64
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * Pack lifecycle gates (F006, ADR-0006, Gate 2 on-device half): real
 * generated `.twpkg` fixtures, real Ed25519 (release path) and the real
 * demo scheme — no mocked crypto, no mocked filesystem.
 */
class PackImporterTest {

    private data class Keys(val priv: Ed25519PrivateKeyParameters, val pub: ByteArray)

    private fun genKeys(): Keys {
        val gen = Ed25519KeyPairGenerator()
        gen.init(Ed25519KeyGenerationParameters(java.security.SecureRandom()))
        val kp = gen.generateKeyPair()
        return Keys(
            kp.private as Ed25519PrivateKeyParameters,
            (kp.public as Ed25519PublicKeyParameters).encoded,
        )
    }

    private fun edSign(priv: Ed25519PrivateKeyParameters, msg: ByteArray): ByteArray {
        val s = Ed25519Signer()
        s.init(true, priv)
        s.update(msg, 0, msg.size)
        return s.generateSignature()
    }

    private fun shaHex(b: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(b).joinToString("") { "%02x".format(it) }

    /** Build a minimal pack zip. sign=null → demo scheme; else Ed25519 with keyId. */
    private fun makePack(
        dir: File,
        name: String,
        version: String = "2026.10.1",
        keyId: String = "pubkey-test-1",
        keys: Keys? = null,
        allowDemoSign: Boolean = true,
        extraEntries: Map<String, ByteArray> = emptyMap(),
        corruptAfterSign: (MutableMap<String, ByteArray>) -> Unit = {},
    ): File {
        val content = "hello-pack".toByteArray()
        val manifest = """{"format":"trueway.pack","schema_version":3,"pack_id":"test-pack","release_version":"$version","publisher_id":"t","signing_key_id":"$keyId","place_count":1,"vision":{"model_id":null,"dim":null,"adapter":false},"files":[{"path":"content/data.bin","bytes":${content.size},"sha256":"${shaHex(content)}"}],"licence_index_path":"L","attribution_index_path":"A","changelog_path":"C","update_policy":{"atomic_activate":true}}"""
        val mbytes = manifest.toByteArray()
        val sig: ByteArray = if (keys != null) {
            edSign(keys.priv, mbytes)
        } else {
            check(allowDemoSign)
            Base64.getEncoder().encode(("DEMO-SIGNATURE:".toByteArray() + MessageDigest.getInstance("SHA-256").digest(mbytes)))
        }
        val items = mutableMapOf(
            "manifest.cjson" to mbytes,
            "manifest.ed25519" to sig,
            "content/data.bin" to content,
        )
        items.putAll(extraEntries)
        corruptAfterSign(items)
        val out = File(dir, name)
        ZipOutputStream(out.outputStream()).use { zos ->
            items.forEach { (n, d) ->
                zos.putNextEntry(ZipEntry(n))
                zos.write(d)
                zos.closeEntry()
            }
        }
        return out
    }

    private fun tempRoot(): File = Files.createTempDirectory("packtest").toFile()

    private class MemStore : ActivePackStore {
        val map = mutableMapOf<String, String>()
        override fun getActive(packId: String) = map[packId]
        override fun setActive(packId: String, version: String) {
            map[packId] = version
        }
        override fun clearActive(packId: String) {
            map.remove(packId)
        }
    }

    @Test
    fun validReleasePackActivates() {
        val root = tempRoot()
        val keys = genKeys()
        val pkg = makePack(root, "v.twpkg", keys = keys)
        val store = MemStore()
        val r = PackImporter.installPackage(
            pkg, File(root, "packs"), mapOf("pubkey-test-1" to keys.pub),
            allowDemo = false, activeStore = store,
        )
        assertTrue(r is PackInstallResult.Active)
        assertEquals("2026.10.1", store.getActive("test-pack"))
        assertTrue(File(root, "packs/test-pack/2026.10.1/manifest.cjson").exists())
        assertTrue(File(root, "packs/test-pack/2026.10.1/content/data.bin").exists())
    }

    @Test
    fun badSignatureRejectedAndNothingActivates() {
        val root = tempRoot()
        val keys = genKeys()
        val pkg = makePack(root, "bad.twpkg", keys = keys,
            corruptAfterSign = {
                val sig = it["manifest.ed25519"]!!.copyOf()
                sig[7] = (sig[7].toInt() xor 0xFF).toByte()
                it["manifest.ed25519"] = sig
            })
        val store = MemStore()
        val r = PackImporter.installPackage(
            pkg, File(root, "packs"), mapOf("pubkey-test-1" to keys.pub),
            allowDemo = false, activeStore = store,
        )
        assertTrue(r is PackInstallResult.Rejected)
        assertEquals(PackReject.BAD_SIGNATURE, (r as PackInstallResult.Rejected).reason)
        assertEquals(null, store.getActive("test-pack"))
        assertFalse(File(root, "packs/test-pack").exists())
    }

    @Test
    fun traversalRejectedWithNoEscape() {
        val root = tempRoot()
        val keys = genKeys()
        val pkg = makePack(root, "trav.twpkg", keys = keys,
            extraEntries = mapOf("../../evil.txt" to "x".toByteArray()))
        // Note: manifest doesn't list evil.txt — path check fires first anyway.
        val r = PackImporter.verifyPackage(
            pkg, mapOf("pubkey-test-1" to keys.pub), allowDemo = false,
        )
        assertTrue(r is PackVerifyResult.Rejected)
        assertEquals(PackReject.UNSAFE_PATH, (r as PackVerifyResult.Rejected).reason)
        assertFalse(File(root, "evil.txt").exists())
    }

    @Test
    fun unknownPublisherRejected() {
        val root = tempRoot()
        val keys = genKeys()
        val pkg = makePack(root, "u.twpkg", keys = keys)
        val r = PackImporter.verifyPackage(pkg, emptyMap(), allowDemo = false)
        assertEquals(PackReject.UNKNOWN_PUBLISHER, (r as PackVerifyResult.Rejected).reason)
    }

    @Test
    fun downgradeRefused() {
        val root = tempRoot()
        val keys = genKeys()
        val pkg = makePack(root, "old.twpkg", version = "2026.10.1", keys = keys)
        val r = PackImporter.verifyPackage(
            pkg, mapOf("pubkey-test-1" to keys.pub), allowDemo = false,
            minSafeVersion = "2026.10.2",
        )
        assertEquals(PackReject.DOWNGRADE, (r as PackVerifyResult.Rejected).reason)
    }

    @Test
    fun failedUpgradeKeepsPreviousPack() {
        val root = tempRoot()
        val keys = genKeys()
        val trust = mapOf("pubkey-test-1" to keys.pub)
        val store = MemStore()
        val packs = File(root, "packs")
        val v1 = makePack(root, "v1.twpkg", version = "2026.10.1", keys = keys)
        assertTrue(
            PackImporter.installPackage(v1, packs, trust, false, activeStore = store)
                is PackInstallResult.Active,
        )
        val v2bad = makePack(root, "v2.twpkg", version = "2026.10.2", keys = keys,
            corruptAfterSign = { it["content/data.bin"] = "tampered!".toByteArray() })
        val r2 = PackImporter.installPackage(v2bad, packs, trust, false, activeStore = store)
        assertTrue(r2 is PackInstallResult.Rejected)
        assertEquals("2026.10.1", store.getActive("test-pack"))
        assertTrue(File(root, "packs/test-pack/2026.10.1/manifest.cjson").exists())
    }

    @Test
    fun demoSchemeGatedByAllowDemo() {
        val root = tempRoot()
        val pkg = makePack(root, "demo.twpkg", keyId = "DEMO-KEY-DO-NOT-SHIP", keys = null)
        val trust = emptyMap<String, ByteArray>()
        val denied = PackImporter.verifyPackage(pkg, trust, allowDemo = false)
        assertEquals(PackReject.BAD_SIGNATURE, (denied as PackVerifyResult.Rejected).reason)
        val allowed = PackImporter.verifyPackage(pkg, trust, allowDemo = true)
        assertTrue(allowed is PackVerifyResult.Ok)
    }

    @Test
    fun unlistedEntryNotInManifestRejected() {
        val root = tempRoot()
        val keys = genKeys()
        // A safe-named extra file (no traversal, not executable) that the signed
        // manifest does not list must still be rejected — a signed pack cannot
        // smuggle unsigned content into the live pack dir.
        val pkg = makePack(root, "extra.twpkg", keys = keys,
            extraEntries = mapOf("content/smuggled.json" to "{}".toByteArray()))
        val r = PackImporter.verifyPackage(
            pkg, mapOf("pubkey-test-1" to keys.pub), allowDemo = false,
        )
        assertTrue(r is PackVerifyResult.Rejected)
        assertEquals(PackReject.UNLISTED_ENTRY, (r as PackVerifyResult.Rejected).reason)
    }

    @Test
    fun reinstallSameVersionKeepsPackReadable() {
        val root = tempRoot()
        val keys = genKeys()
        val trust = mapOf("pubkey-test-1" to keys.pub)
        val store = MemStore()
        val packs = File(root, "packs")
        val v1 = makePack(root, "v1.twpkg", version = "2026.10.1", keys = keys)
        assertTrue(
            PackImporter.installPackage(v1, packs, trust, false, activeStore = store)
                is PackInstallResult.Active,
        )
        // Reinstalling the SAME version must not destroy the live pack.
        val again = makePack(root, "v1again.twpkg", version = "2026.10.1", keys = keys)
        val r = PackImporter.installPackage(again, packs, trust, false, activeStore = store)
        assertTrue(r is PackInstallResult.Active)
        assertEquals("2026.10.1", store.getActive("test-pack"))
        assertTrue(File(root, "packs/test-pack/2026.10.1/manifest.cjson").exists())
        assertTrue(File(root, "packs/test-pack/2026.10.1/content/data.bin").exists())
    }

    @Test
    fun deleteRemovesPackAndPointer() {
        val root = tempRoot()
        val keys = genKeys()
        val pkg = makePack(root, "v.twpkg", keys = keys)
        val store = MemStore()
        val packs = File(root, "packs")
        PackImporter.installPackage(pkg, packs, mapOf("pubkey-test-1" to keys.pub),
            false, activeStore = store)
        assertTrue(PackImporter.deletePack(packs, "test-pack", store))
        assertFalse(File(root, "packs/test-pack").exists())
        assertEquals(null, store.getActive("test-pack"))
    }

    @Test
    fun hostileFixturesAllRejectedOnDevice() {
        val hostileDir = listOf(
            File("../../tests/fixtures/hostile"),
            File("../tests/fixtures/hostile"),
            File("tests/fixtures/hostile"),
        ).firstOrNull { it.isDirectory && File(it, "bad-signature.twpkg").exists() }
            ?: throw AssertionError("hostile fixture directory not found")

        // 1. bad-signature: manifest signature corrupted
        val badSig = PackImporter.verifyPackage(
            File(hostileDir, "bad-signature.twpkg"), emptyMap(), allowDemo = true,
        )
        assertTrue(badSig is PackVerifyResult.Rejected)
        assertEquals(PackReject.BAD_SIGNATURE, (badSig as PackVerifyResult.Rejected).reason)

        // 2. unknown-key: attacker key not recognized
        val unkKey = PackImporter.verifyPackage(
            File(hostileDir, "unknown-key.twpkg"), emptyMap(), allowDemo = true,
        )
        assertTrue(unkKey is PackVerifyResult.Rejected)
        assertEquals(PackReject.UNKNOWN_PUBLISHER, (unkKey as PackVerifyResult.Rejected).reason)

        // 3. truncated-sqlite: SHA-256 / size mismatch on SQLite
        val trunc = PackImporter.verifyPackage(
            File(hostileDir, "truncated-sqlite.twpkg"), emptyMap(), allowDemo = true,
        )
        assertTrue(trunc is PackVerifyResult.Rejected)
        assertEquals(PackReject.DIGEST_MISMATCH, (trunc as PackVerifyResult.Rejected).reason)

        // 4. traversal: path traversal entry in zip
        val trav = PackImporter.verifyPackage(
            File(hostileDir, "traversal.twpkg"), emptyMap(), allowDemo = true,
        )
        assertTrue(trav is PackVerifyResult.Rejected)
        assertEquals(PackReject.UNSAFE_PATH, (trav as PackVerifyResult.Rejected).reason)

        // 5. downgrade: version 2026.10.1 below minSafeVersion 2026.10.2
        val down = PackImporter.verifyPackage(
            File(hostileDir, "downgrade.twpkg"), emptyMap(), allowDemo = true, minSafeVersion = "2026.10.2",
        )
        assertTrue(down is PackVerifyResult.Rejected)
        assertEquals(PackReject.DOWNGRADE, (down as PackVerifyResult.Rejected).reason)

        // 6. forged-prodkey: production-looking key id (not in trust store) with
        // a recomputed demo hash → unknown publisher, never trusted.
        File(hostileDir, "forged-prodkey.twpkg").takeIf { it.exists() }?.let { f ->
            val forged = PackImporter.verifyPackage(f, emptyMap(), allowDemo = true)
            assertTrue(forged is PackVerifyResult.Rejected)
            assertEquals(PackReject.UNKNOWN_PUBLISHER, (forged as PackVerifyResult.Rejected).reason)
        }

        // 7. unlisted-entry: safe-named file absent from the signed manifest.
        File(hostileDir, "unlisted-entry.twpkg").takeIf { it.exists() }?.let { f ->
            val unlisted = PackImporter.verifyPackage(f, emptyMap(), allowDemo = true)
            assertTrue(unlisted is PackVerifyResult.Rejected)
            assertEquals(PackReject.UNLISTED_ENTRY, (unlisted as PackVerifyResult.Rejected).reason)
        }
    }
}
