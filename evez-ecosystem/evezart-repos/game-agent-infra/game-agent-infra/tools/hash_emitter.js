#!/usr/bin/env node
/**
 * Node.js Canonical Hash Emitter — B1 Cross-Runtime Companion
 *
 * Purpose: Reads JSON files and emits SHA-256 hashes using the same
 * canonicalization rules as the Python implementation:
 * - NFC string normalization (Unicode Canonical Composed)
 * - sort_keys: true (all object keys sorted lexicographically)
 * - compact JSON (no extra whitespace)
 * - UTF-8 encoding
 * - "sha256:" prefix on hash
 *
 * Usage: node hash_emitter.js file1.json file2.json ...
 */

"use strict";

const { createHash } = require("crypto");
const { readFileSync } = require("fs");

// ─── Canonicalization helpers ──────────────────────────────────────────────────

function normalizeStrings(obj) {
    if (typeof obj === "string") {
        return obj.normalize("NFC");
    }
    if (Array.isArray(obj)) {
        return obj.map(normalizeStrings);
    }
    if (obj !== null && typeof obj === "object") {
        const out = {};
        for (const key of Object.keys(obj).sort()) {
            out[key] = normalizeStrings(obj[key]);
        }
        return out;
    }
    return obj;
}

function canonicalJson(obj) {
    const normalized = normalizeStrings(obj);
    const jsonStr = JSON.stringify(normalized);
    return Buffer.from(jsonStr, "utf-8");
}

function sha256(data) {
    return "sha256:" + createHash("sha256").update(data).digest("hex");
}

// ─── Main hash routine ─────────────────────────────────────────────────────────

function hashFile(filePath) {
    try {
        const rawJson = readFileSync(filePath, "utf-8");
        const obj = JSON.parse(rawJson);
        const hash = sha256(canonicalJson(obj));
        return { hash, error: null };
    } catch (err) {
        return { hash: null, error: err.message };
    }
}

// ─── CLI ───────────────────────────────────────────────────────────────────────

function main() {
    const args = process.argv.slice(2);

    if (args.length === 0) {
        console.error("Usage: node hash_emitter.js <file1.json> [file2.json ...]");
        process.exit(1);
    }

    const results = {};
    for (const filePath of args) {
        results[filePath] = hashFile(filePath);
    }

    console.log(JSON.stringify(results, null, 2));
}

if (require.main === module) {
    main();
}

module.exports = {
    normalizeStrings,
    canonicalJson,
    sha256,
    hashFile,
};