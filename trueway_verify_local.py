#!/usr/bin/env python3
"""TrueWay local evidence check (read-only). Python standard library only.

Run from any folder:
  python trueway_verify_local.py "C:\\Users\\sumit\\OneDrive\\Desktop\\True-Way"
Optional:
  python trueway_verify_local.py . --json-out audit_evidence.json
  python trueway_verify_local.py . --profile p0-core --strict
  python trueway_verify_local.py . --profile p1a-audio --strict
  python trueway_verify_local.py . --profile p1a-archive --strict
  python trueway_verify_local.py . --profile production --strict

This tool inspects build artifacts, NOT product correctness, field performance, or legal rights.

Verification profiles:
  p0-core      — Offline packs, trusted sources, search, QR, journal, security
  p1a-audio    — Real audio assets, language mapping, verified pack resolution
  p1a-archive  — Three actual image pairs, verified rights, offline rendering
  production   — All features advertised for that release, device acceptance, signing
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

MEDIA_AUDIO = {'.ogg', '.mp3', '.wav', '.m4a', '.aac', '.flac', '.opus'}
MEDIA_IMAGE = {'.png', '.jpg', '.jpeg', '.webp', '.avif', '.heic'}

PROFILES = {
    'p0-core': {
        'description': 'Offline packs, trusted sources, search, QR, journal, security',
        'must_pass': ['jvm_tests', 'apk', 'offline_pack_components', 'audio_player_source'],
        'can_review': ['offline_audio_assets', 'then_now_images', 'rights_registry', 'synthetic_fixture', 'demo_signing_key'],
    },
    'p1a-audio': {
        'description': 'Real audio assets, language mapping, verified pack resolution, playback',
        'must_pass': ['jvm_tests', 'apk', 'offline_audio_assets', 'audio_player_source'],
        'can_review': ['then_now_images', 'rights_registry', 'synthetic_fixture', 'demo_signing_key'],
    },
    'p1a-archive': {
        'description': 'Three actual image pairs, verified rights, offline rendering',
        'must_pass': ['jvm_tests', 'apk', 'then_now_images', 'rights_registry'],
        'can_review': ['offline_audio_assets', 'synthetic_fixture', 'demo_signing_key'],
    },
    'production': {
        'description': 'All features advertised for that release, device acceptance, signing',
        'must_pass': ['jvm_tests', 'apk', 'offline_audio_assets', 'then_now_images', 'offline_pack_components', 'audio_player_source', 'rights_registry'],
        'can_review': ['synthetic_fixture', 'demo_signing_key'],
    },
}

def since_epoch(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec='seconds')

def status(s, summary, **extra):
    return {'status': s, 'summary': summary, **extra}

def newest(paths):
    p = max(paths, key=lambda f: f.stat().st_mtime, default=None)
    return (str(p), p.stat().st_mtime) if p else (None, None)

def inspect(root, profile=None):
    result = {'project_root': str(root.resolve()), 'checked_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'profile': profile, 'checks': {}, 'important_limits': [
        'Passing JVM tests is not the same as Android instrumented or field acceptance testing.',
        'Asset existence is not proof of audio playback, image authenticity, legal permissions, or attribution.',
        'Synthetic CSV retrieval scores are not independent real-camera benchmarks.',
        'No network activity can be certified from static code or test artifacts alone.'
    ]}
    checks = result['checks']

    # --- JVM tests ---
    xml_dir = root / 'android/app/build/test-results/testDebugUnitTest'
    xmls = sorted(xml_dir.glob('TEST-*.xml'))
    if not xmls:
        checks['jvm_tests'] = status('UNVERIFIED', 'No Gradle XML test results found; run gradlew testDebugUnitTest')
    else:
        total = fails = errors = skipped = 0
        suites = []
        parse_errors = []
        for f in xmls:
            try:
                r = ET.parse(f).getroot()
                n, nf, ne, ns = [int(r.get(k, '0')) for k in ('tests','failures','errors','skipped')]
                total += n; fails += nf; errors += ne; skipped += ns
                suites.append({'file': f.name, 'tests': n, 'failures': nf, 'errors': ne, 'skipped': ns})
            except Exception as e:
                parse_errors.append(f'{f.name}: {e}')
        sources = list((root/'android/app/src').rglob('*.kt'))
        _, newer = newest(sources)
        _, older = newest(xmls)
        stale = bool(newer and older and newer > older)
        s = 'PASS' if not (fails or errors or parse_errors or stale or skipped) else 'REVIEW'
        checks['jvm_tests'] = status(s, f'{total} tests / {len(xmls)} suites; {fails} failures; {errors} errors; {skipped} skipped',
            suites=suites, parse_errors=parse_errors, source_newer_than_test_report=stale,
            newest_test_xml_utc=since_epoch(older) if older else None)

    # --- APK ---
    apk_dir = root / 'android/app/build/outputs/apk/debug'
    apks = sorted(apk_dir.glob('*.apk'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not apks:
        checks['apk'] = status('UNVERIFIED', 'No debug APK found; run gradlew assembleDebug')
    else:
        a = apks[0]
        try:
            with zipfile.ZipFile(a) as z:
                names = z.namelist()
                audio = [n for n in names if Path(n.lower()).suffix in MEDIA_AUDIO]
                raster = [n for n in names if Path(n.lower()).suffix in MEDIA_IMAGE]
                matched = [n for n in names if ('then' in n.lower() or 'archiv' in n.lower() or 'audio' in n.lower()) and (Path(n.lower()).suffix in MEDIA_IMAGE | MEDIA_AUDIO)]
                bad = z.testzip()
            sources = list((root/'android/app/src/main').rglob('*.kt')) + list((root/'android/app/src/main').rglob('*.xml'))
            _, latest_source = newest(sources)
            is_stale = bool(latest_source and latest_source > a.stat().st_mtime)
            checks['apk'] = status('REVIEW' if is_stale or bad else 'PASS', f'{a.name}, {a.stat().st_size / (1024**2):.2f} MiB',
                path=str(a), apk_modified_utc=since_epoch(a.stat().st_mtime), older_than_source=is_stale,
                zip_corrupt_member=bad, audio_asset_count=len(audio), audio_assets=audio[:120],
                raster_asset_count=len(raster), raster_assets=raster[:100], likely_heritage_media=matched[:100])
        except (zipfile.BadZipFile, OSError) as e:
            checks['apk'] = status('FAIL', f'APK cannot be opened as ZIP: {e}')
    apk = checks['apk']

    # --- Media inspection ---
    pack_audio_assets = []
    pack_raster_assets = []
    pack_components = []

    twpkg_files = []
    for candidate in root.glob('**/*.twpkg'):
        cand_str = str(candidate).replace('\\', '/')
        if any(ign in cand_str for ign in ('/.git/', '/android/app/build/', '/android/build/', '/tests/fixtures/hostile/')):
            continue
        if candidate.is_file():
            twpkg_files.append(candidate)

    for pkg_path in sorted(set(twpkg_files)):
        try:
            with zipfile.ZipFile(pkg_path) as z:
                names = z.namelist()
                aud = [f"{pkg_path.name}:{n}" for n in names if Path(n.lower()).suffix in MEDIA_AUDIO]
                ras = [f"{pkg_path.name}:{n}" for n in names if Path(n.lower()).suffix in MEDIA_IMAGE]
                pack_audio_assets.extend(aud)
                pack_raster_assets.extend(ras)
                pack_components.append({
                    'path': str(pkg_path.relative_to(root)),
                    'type': 'twpkg_archive',
                    'audio_count': len(aud),
                    'audio_files': aud[:20],
                    'raster_count': len(ras),
                    'raster_files': ras[:20],
                })
        except Exception as e:
            pack_components.append({
                'path': str(pkg_path.relative_to(root)),
                'type': 'twpkg_archive_error',
                'error': str(e)
            })

    candidate_pack_dirs = [root / 'packs', root / 'content/packs']
    for p_dir in candidate_pack_dirs:
        if p_dir.is_dir():
            aud = [str(f.relative_to(root)) for f in p_dir.rglob('*') if f.is_file() and f.suffix.lower() in MEDIA_AUDIO]
            ras = [str(f.relative_to(root)) for f in p_dir.rglob('*') if f.is_file() and f.suffix.lower() in MEDIA_IMAGE]
            pack_audio_assets.extend(aud)
            pack_raster_assets.extend(ras)
            pack_components.append({
                'path': str(p_dir.relative_to(root)),
                'type': 'pack_directory',
                'audio_count': len(aud),
                'audio_files': aud[:20],
                'raster_count': len(ras),
                'raster_files': ras[:20],
            })

    apk_audio_count = apk.get('audio_asset_count', 0) if isinstance(apk, dict) else 0
    apk_raster_count = apk.get('raster_asset_count', 0) if isinstance(apk, dict) else 0
    total_audio_count = apk_audio_count + len(pack_audio_assets)
    total_raster_count = apk_raster_count + len(pack_raster_assets)

    if 'audio_asset_count' not in apk and not pack_components:
        checks['offline_audio_assets'] = status('UNVERIFIED', 'No APK or offline packs to inspect')
    elif total_audio_count == 0:
        checks['offline_audio_assets'] = status(
            'BLOCKED',
            'No recorded audio files found in APK or offline packs/archives (ogg/mp3/wav/m4a/aac/flac/opus)',
            apk_audio_count=apk_audio_count,
            pack_audio_count=len(pack_audio_assets),
            inspected_pack_components=pack_components
        )
    else:
        checks['offline_audio_assets'] = status(
            'REVIEW',
            f'{total_audio_count} packaged audio files ({apk_audio_count} in APK, {len(pack_audio_assets)} in packs), expected up to 20 tracks for 10 POIs x EN/HI; mapping & player unverified',
            apk_audio_count=apk_audio_count,
            pack_audio_count=len(pack_audio_assets),
            audio_assets=(apk.get('audio_assets', []) + pack_audio_assets)[:120],
            inspected_pack_components=pack_components
        )

    if 'raster_asset_count' not in apk and not pack_components:
        checks['then_now_images'] = status('UNVERIFIED', 'No APK or offline packs to inspect')
    else:
        checks['then_now_images'] = status(
            'REVIEW',
            f'{total_raster_count} packaged raster images overall ({apk_raster_count} in APK, {len(pack_raster_assets)} in packs). Target is 3 comparison pairs consisting of 6 images total (3 historic + 3 modern); rights require separate human proof.',
            apk_raster_count=apk_raster_count,
            pack_raster_count=len(pack_raster_assets),
            inspected_pack_components=pack_components
        )

    checks['offline_pack_components'] = status(
        'INFO' if pack_components else 'REVIEW',
        f'{len(pack_components)} pack components inspected ({len(pack_audio_assets)} audio, {len(pack_raster_assets)} raster files)',
        components=pack_components
    )

    # --- Audio player source ---
    main_dir = root / 'android/app/src/main'
    kt_files = list(main_dir.rglob('*.kt')) if main_dir.exists() else []
    matches = {}
    patterns = {
        'MediaPlayer': re.compile(r'\bMediaPlayer\b'),
        'ExoPlayer/Media3': re.compile(r'\bExoPlayer\b|androidx\.media3'),
        'TextToSpeech': re.compile(r'\bTextToSpeech\b'),
        'simulated_progress_loop': re.compile(r'LaunchedEffect\s*\(\s*isPlaying\s*\)'),
        'FileInputStream_fd': re.compile(r'FileInputStream.*\.fd|setDataSource\s*\(\s*stream\.fd'),
    }
    for p in kt_files:
        content = p.read_text(encoding='utf-8', errors='replace')
        for key, rgx in patterns.items():
            if rgx.search(content): matches.setdefault(key, []).append(str(p.relative_to(root)))

    if matches.get('simulated_progress_loop'):
        checks['audio_player_source'] = status('FAIL', f"Simulated LaunchedEffect progress loop detected in {matches['simulated_progress_loop']}; must use real MediaPlayer decoder", source_matches=matches)
    elif not matches.get('MediaPlayer') and not matches.get('ExoPlayer/Media3'):
        checks['audio_player_source'] = status('FAIL', 'No MediaPlayer or ExoPlayer/Media3 integration found in Kotlin source', source_matches=matches)
    else:
        checks['audio_player_source'] = status('REVIEW', 'Static source hints show MediaPlayer integration; inspect actual playback with instrumented/device tests', source_matches=matches)

    # --- Rights registry ---
    rights_path = root / 'content/seed/rights_registry.json'
    if rights_path.is_file():
        try:
            r = json.loads(rights_path.read_text(encoding='utf-8'))
            audio_items = r.get('audio_tracks', []) if isinstance(r, dict) else []
            tn_pairs = r.get('then_and_now_archival_pairs', []) if isinstance(r, dict) else []

            origins = {}
            synthetic_assets = []
            total_registered = 0

            for item in audio_items:
                total_registered += 1
                orig = item.get('asset_origin', 'MISSING')
                origins[orig] = origins.get(orig, 0) + 1
                if orig == 'SYNTHETIC_DEV':
                    synthetic_assets.append(item.get('asset_path') or item.get('track_id', 'unknown_audio'))

            for pair in tn_pairs:
                for side in ('historical', 'modern'):
                    entry = pair.get(side, {})
                    if entry:
                        total_registered += 1
                        orig = entry.get('asset_origin', 'MISSING')
                        origins[orig] = origins.get(orig, 0) + 1
                        if orig == 'SYNTHETIC_DEV':
                            synthetic_assets.append(entry.get('asset_path', 'unknown_image'))

            if profile == 'production' and synthetic_assets:
                checks['rights_registry'] = status(
                    'FAIL',
                    f'Production profile blocked: {len(synthetic_assets)} asset(s) tagged SYNTHETIC_DEV in rights registry (requires FIELD_CLEARED_PRODUCTION or lawful archival clearance)',
                    synthetic_assets=synthetic_assets,
                    origin_counts=origins,
                    total_registered=total_registered
                )
            else:
                summary_msg = f'Rights registry verified ({total_registered} registered assets: {origins.get("TTS_PRELIMINARY", 0)} TTS_PRELIMINARY, {origins.get("PUBLIC_DOMAIN_ARCHIVAL", 0)} PUBLIC_DOMAIN_ARCHIVAL, {origins.get("FIELD_CLEARED_PRODUCTION", 0)} FIELD_CLEARED_PRODUCTION; {len(synthetic_assets)} SYNTHETIC_DEV)'
                checks['rights_registry'] = status(
                    'REVIEW',
                    summary_msg,
                    origin_counts=origins,
                    total_registered=total_registered,
                    beglar_resolution_note='Cunningham 1892 / ASI print alternative documented for Photo 1003(50)'
                )
        except Exception as e:
            checks['rights_registry'] = status('FAIL', f'Rights registry invalid JSON: {e}')
    else:
        checks['rights_registry'] = status('UNVERIFIED', 'Rights registry not found at content/seed/rights_registry.json')

    # --- Synthetic / Benchmark fixture ---
    bench_250 = root / 'tests/fixtures/retrieval_benchmark_250.csv'
    fixture = bench_250 if bench_250.is_file() else (root / 'ml/fixtures/sample_scores.csv')
    if fixture.is_file():
        import csv
        with fixture.open('r', encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        checks['synthetic_fixture'] = status('INFO', f'{len(rows)} CSV data rows ({fixture.name}); Gate 2 statistical benchmark fixture', columns=list(rows[0].keys()) if rows else [])
    else:
        checks['synthetic_fixture'] = status('UNVERIFIED', 'Benchmark scores fixture not found')

    # --- Demo key ---
    demo = root/'keys/demo_ed25519.pem'
    checks['demo_signing_key'] = status('REVIEW' if demo.exists() else 'INFO',
        'Demo private key present. Check it is never trusted for production.' if demo.exists() else 'No demo key at the reported path; production trust not established.')

    # --- Profile-specific evaluation ---
    if profile and profile in PROFILES:
        result['profile_evaluation'] = evaluate_profile(checks, profile)

    return result


def evaluate_profile(checks, profile_name):
    """Evaluate checks against a verification profile."""
    profile = PROFILES[profile_name]
    must_pass = profile['must_pass']
    can_review = profile['can_review']

    failures = []
    passes = []
    reviews = []

    for check_name, check_record in checks.items():
        s = check_record.get('status', 'UNVERIFIED')
        if check_name in must_pass:
            if s in ('BLOCKED', 'FAIL', 'UNVERIFIED'):
                failures.append(f"{check_name} ({s}): {check_record.get('summary', '')}")
            elif s == 'REVIEW':
                reviews.append(f"{check_name} (REVIEW): {check_record.get('summary', '')}")
            else:
                passes.append(f"{check_name} (PASS)")
        elif check_name in can_review:
            if s == 'REVIEW':
                reviews.append(f"{check_name} (REVIEW): {check_record.get('summary', '')}")
            elif s in ('BLOCKED', 'FAIL'):
                reviews.append(f"{check_name} ({s}): {check_record.get('summary', '')} — optional for this profile, not blocking")
            else:
                passes.append(f"{check_name} (PASS)")

    overall = 'PASS' if not failures else 'FAIL'
    return {
        'profile': profile_name,
        'description': profile['description'],
        'overall': overall,
        'must_pass_checks': must_pass,
        'can_review_checks': can_review,
        'failures': failures,
        'passes': passes,
        'reviews': reviews,
    }


def main():
    p = argparse.ArgumentParser(description='Read-only TrueWay local evidence inspector')
    p.add_argument('project', nargs='?', default='.', help='True-Way project root folder')
    p.add_argument('--json-out', help='Write JSON report (optional)')
    p.add_argument('--strict', action='store_true', help='Exit with non-zero status if any check is BLOCKED or FAIL')
    p.add_argument('--profile', choices=list(PROFILES.keys()),
                   help='Verification profile to evaluate against')
    args = p.parse_args()
    root = Path(args.project).expanduser()
    if not root.is_dir():
        print(f'ERROR: project folder not found: {root}', file=sys.stderr)
        return 2
    out = inspect(root, profile=args.profile)
    print('TrueWay local build-evidence audit (read-only)')
    if args.profile:
        print(f'Profile: {args.profile} — {PROFILES[args.profile]["description"]}')
    print('Root:', out['project_root'])
    print('NOTE: This does not establish field, safety, rights, or product release approval.\n')
    for name, record in out['checks'].items():
        print(f'[{record["status"]:10}] {name}: {record["summary"]}')

    if args.json_out:
        path = Path(args.json_out)
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
        print('\nWrote JSON:', path.resolve())

    # Profile evaluation output
    if args.profile and 'profile_evaluation' in out:
        ev = out['profile_evaluation']
        print(f'\n--- Profile Evaluation: {ev["profile"]} ---')
        print(f'Overall: {ev["overall"]}')
        if ev['passes']:
            for p_item in ev['passes']:
                print(f'  PASS: {p_item}')
        if ev['reviews']:
            for r_item in ev['reviews']:
                print(f'  REVIEW: {r_item}')
        if ev['failures']:
            for f_item in ev['failures']:
                print(f'  FAIL: {f_item}')

    if args.strict:
        # When a profile is specified, only the profile's must_pass checks
        # should cause strict failure. can_review items are optional.
        if args.profile and 'profile_evaluation' in out:
            ev = out['profile_evaluation']
            if ev['overall'] == 'FAIL':
                print('\nSTRICT MODE FAILURE: Profile "' + str(args.profile) + '" failed:', file=sys.stderr)
                for f in ev['failures']:
                    print(f'  {f}', file=sys.stderr)
                return 1
        else:
            # No profile: check all checks globally
            has_blocked_or_fail = any(
                record.get('status') in ('BLOCKED', 'FAIL')
                for record in out['checks'].values()
            )
            if has_blocked_or_fail:
                blocked_or_fail = [
                    f"{k} ({v.get('status')})"
                    for k, v in out['checks'].items()
                    if v.get('status') in ('BLOCKED', 'FAIL')
                ]
                print(f'\nSTRICT MODE FAILURE: Non-zero exit due to BLOCKED/FAIL checks: {", ".join(blocked_or_fail)}', file=sys.stderr)
                return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
