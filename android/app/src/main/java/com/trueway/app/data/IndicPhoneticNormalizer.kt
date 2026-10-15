package com.trueway.app.data

/**
 * Phonetic normalization for bilingual Indic monument names and queries (F003 Search Polish).
 * Maps spelling variants (e.g. Mahabodhi / Mahabodi, Nalanda / Nalandā, Suvarnabhandar / Sonbhandar)
 * to a canonical phonetic search skeleton.
 */
object IndicPhoneticNormalizer {

    private val rules = listOf(
        "chh" to "c", "ch" to "c", "sh" to "s",
        "bh" to "b", "dh" to "d", "gh" to "g",
        "jh" to "j", "kh" to "k", "ph" to "p", "th" to "t",
        "aa" to "a", "ee" to "i", "oo" to "u",
        "ai" to "e", "au" to "o", "ou" to "o",
        "ks" to "k", "gy" to "g", "jna" to "gya",
        "sw" to "s", "sv" to "s", "v" to "w", "z" to "j", "q" to "k"
    )

    private val diacriticMap = mapOf(
        'ā' to "a", 'ī' to "i", 'ū' to "u", 'ṛ' to "ri", 'ṝ' to "ri",
        'ṅ' to "n", 'ñ' to "n", 'ṭ' to "t", 'ḍ' to "d", 'ṇ' to "n",
        'ś' to "s", 'ṣ' to "s", 'ḥ' to "h", 'ṃ' to "m", 'ṁ' to "m"
    )

    private val nonWordRegex = Regex("[^a-z0-9\\u0900-\\u097f\\s]")
    private val devanagariRegex = Regex("[\\u0900-\\u097f]")
    private val trailingVowelRegex = Regex("[aeiou]+$")
    private val duplicateCharRegex = Regex("(.)\\1+")

    fun toSkeleton(input: String): String {
        if (input.isBlank()) return ""
        val lowered = buildString(input.length) {
            for (ch in input.lowercase()) {
                append(diacriticMap[ch] ?: ch)
            }
        }
        val cleaned = nonWordRegex.replace(lowered, " ")
        val tokens = mutableListOf<String>()
        for (rawTok in cleaned.split(Regex("\\s+")).filter { it.isNotEmpty() }) {
            if (devanagariRegex.containsMatchIn(rawTok)) {
                tokens.add(rawTok)
                continue
            }
            var tok = rawTok
                .replace(Regex("^swarna"), "son")
                .replace(Regex("^suvarna"), "son")
                .replace(Regex("^gijjha"), "griddha")
            for ((src, dst) in rules) {
                tok = tok.replace(src, dst)
            }
            if (tok.length > 2) {
                val head = tok.substring(0, 1)
                val tail = trailingVowelRegex.replace(tok.substring(1), "")
                    .replace('o', 'u')
                    .replace('e', 'i')
                tok = head + tail
            }
            tok = duplicateCharRegex.replace(tok, "$1")
            if (tok.isNotEmpty()) tokens.add(tok)
        }
        val joinedLatin = tokens.filter { !devanagariRegex.containsMatchIn(it) }.joinToString("")
        if (tokens.size > 1 && joinedLatin.isNotEmpty()) {
            tokens.add(joinedLatin)
        }
        return tokens.joinToString(" ")
    }
}
