package com.trueway.app.pack

import android.content.Context
import com.trueway.app.R

/** User-facing copy for every importer outcome (blueprint §19.3). */
object PackImportResultLabels {
    fun describe(result: PackInstallResult, context: Context): String = when (result) {
        is PackInstallResult.Active -> context.getString(
            R.string.packs_import_ok,
            result.summary.releaseVersion,
            result.summary.placeCount,
            result.summary.signingKeyId,
        )
        is PackInstallResult.Rejected -> when (result.reason) {
            PackReject.BAD_SIGNATURE -> context.getString(R.string.packs_reject_signature)
            PackReject.UNKNOWN_PUBLISHER ->
                context.getString(R.string.packs_reject_publisher, result.detail)
            PackReject.DIGEST_MISMATCH -> context.getString(R.string.packs_reject_digest)
            PackReject.UNSAFE_PATH ->
                context.getString(R.string.packs_reject_unsafe, result.detail)
            PackReject.UNLISTED_ENTRY ->
                context.getString(R.string.packs_reject_unlisted, result.detail)
            PackReject.DOWNGRADE -> context.getString(R.string.packs_reject_downgrade)
            PackReject.BAD_FORMAT -> context.getString(R.string.packs_reject_format)
            PackReject.TOO_LARGE -> context.getString(R.string.packs_reject_size)
            PackReject.LOW_STORAGE -> context.getString(R.string.packs_reject_storage)
            PackReject.IO_ERROR -> context.getString(R.string.packs_reject_io)
        }
    }
}
