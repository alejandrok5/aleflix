# Maintaining the Aleflix fork

Aleflix renames only what a user sees or installs. Internal identifiers stay exactly as upstream ships them, so Moonfin's frequent commits keep merging with few conflicts.

## Ground rules

- **Never rename internal identifiers.** The `moonfin` Dart package and `package:moonfin/...` imports, the `org.moonfin.androidtv` Kotlin namespace, class names such as `MoonfinApplication`, method channel names (`org.moonfin.androidtv/...`), preference keys, enum names such as `VisualThemeId.moonfin`, and the Moonbase plugin's `/Moonfin/...` server routes all stay.
- **Fork values live in [`lib/aleflix/aleflix_brand.dart`](lib/aleflix/aleflix_brand.dart).** Prefer referencing `AleflixBrand` over editing literals across upstream files.
- **Replace asset contents, not asset paths.** `assets/icons/moonfin_logo.svg` and `assets/images/logo_and_text.png` keep their names, so no upstream Dart has to change.
- Translations are rewritten by a script, never by hand.

## Where the brand lives

| Area | Change | Files |
|------|--------|-------|
| App ID and name | `com.aleflix.app`, "Aleflix" (beta: `.beta`, "Aleflix Beta") | `android/app/build.gradle.kts` |
| Firebase | Plugin not applied; Moonfin's `google-services.json` removed | `android/app/build.gradle.kts` |
| Deep links | `aleflix://` (Dart also accepts `moonfin://` for tvOS) | `AndroidManifest.xml`, `MainActivity.kt`, `deep_link_service.dart` |
| Launcher icon | Adaptive foreground, themed monochrome, legacy PNGs | `res/mipmap-*`, `res/mipmap-anydpi-v26/ic_launcher.xml`, `res/drawable/ic_launcher_monochrome_inset.xml` |
| Splash | The Ridge, in the Android 12+ splash and the pre-12 launch window | `res/drawable-xxxhdpi/aleflix_splash.png`, `res/values*-v31/styles.xml`, `res/drawable*/launch_background.xml` |
| TV banner | 320 x 180 | `res/drawable-nodpi/aleflix_tv_banner.png` |
| In-app logo | The Howl + "Aleflix" in Fraunces | `assets/icons/moonfin_logo.svg`, `assets/images/logo_and_text.png`, `assets/icons/app_icon.png` |
| Strings | "Moonfin" to "Aleflix" in every ARB value (see below) | `lib/l10n/*.arb`, generated `app_localizations*.dart` |
| Theme | Aleflix Noir replaces the cyan Moonfin theme under the same `moonfin` id | `packages/design/lib/src/theme/themes/moonfin_theme_spec.dart` |
| Theme picker | Neon Pulse and 8-bit Hero unregistered | `theme_registry.dart`, `setup_wizard_screen.dart` |
| Title font | `ThemeSpec.displayFontFamily` (new) feeds display, headline and titleLarge | `theme_spec.dart`, `lib/ui/theme/app_theme.dart` |
| Fonts | Inter and Fraunces static instances | `assets/fonts/`, `pubspec.yaml` |
| Focus ring | New `AppTheme.champagne`, default for Noir | `preference_constants.dart`, `user_preferences.dart`, `app_theme_controller.dart` |
| Loading animation | Champagne moon phases by default; spinner and runner retinted | `loading_animation_widget.dart`, `user_preferences.dart` |
| About screen | Fork links; Discord and donation tiles replaced by a Moonfin credit | `about_category_screen.dart` |
| Update check | This repo's GitHub releases | `app_update_service.dart` |
| Server dashboard name | "Aleflix for Android" / "Aleflix for Android TV" | `lib/di/injection.dart`, `device_profile_builder.dart` |
| Public downloads folder | `Downloads/Aleflix` | `MediaStoreHelper.kt` |

## Releases and updates

Installed copies check this repository's GitHub releases under **Settings → About → Check for updates** (sideloaded builds only, see `DISTRIBUTION_CHANNEL`). Phone installs take the asset without `tv` in its name; TV installs take the one with it.

- **Version:** Moonfin's version plus the Aleflix revision in `aleflix.properties`: Moonfin 3.0.0 + revision 1 = **3.0.0.1**. Gradle appends the revision to the version name (end of `android/app/build.gradle.kts`); version codes stay Moonfin's.
- **Publishing:** `.github/workflows/aleflix-release.yml` publishes a release whenever a push to `main` changes `aleflix.properties` or `pubspec.yaml`, and skips versions already released. For an Aleflix-only release, bump `revision` and push.
- **Signing:** every release is signed with the Aleflix key (SHA-256 `d972c469…271340`); Android refuses an update signed with anything else. The key lives outside the repo in `~/.aleflix-signing/` (keep a backup) and in the `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_TYPE`, `ANDROID_STORE_PASSWORD`, `ANDROID_KEY_ALIAS` and `ANDROID_KEY_PASSWORD` secrets. Local release builds read `android/app/release.keystore` + `android/keystore.properties` (both gitignored).
- **Building locally:** `scripts/aleflix/build_release.sh [all|mobile|tv]` writes `dist/Aleflix_Android_v<version>.apk` and `dist/Aleflix_AndroidTV_v<version>.apk`.

## Following Moonfin automatically

`.github/workflows/aleflix-sync.yml` runs daily. When Moonfin publishes a release it:

1. merges it (`scripts/aleflix/sync_upstream.sh`): translation conflicts take Moonfin's side and the rebrand re-runs; Moonfin's workflow files stay out of the fork; the revision resets to 1;
2. checks it: `flutter analyze`, then the test gate (`scripts/aleflix/compare_tests.py`: no test may fail on Aleflix that passes on that Moonfin release, apart from `scripts/aleflix/expected-test-differences.txt`), then a release build;
3. fast-forwards `main` and runs the release workflow.

Anything that fails stops before `main` changes, and GitHub emails the failed run. A conflict outside the translations needs the manual merge below. Pushing Moonfin's history needs the `SYNC_TOKEN` secret (fine-grained token for this repository with Contents and Workflows read/write), because Moonfin's commits touch workflow files and the built-in Actions token may not push those.

Moonfin's own workflows are disabled in this fork (Actions → each workflow → Disable), so they don't run here.

## Merging upstream

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

On conflicts:

1. **`lib/l10n/`**: take upstream's side, then re-apply the rebrand and regenerate.
   ```bash
   git checkout --theirs lib/l10n
   python3 scripts/aleflix/rebrand_strings.py
   flutter gen-l10n
   ```
2. **Binary assets** (icons, banner, logo): keep ours (`git checkout --ours <file>`), or regenerate them (below).
3. **Everything else**: resolve by hand. The table above lists every file Aleflix touches.

After every merge, even a clean one, run the string script, since upstream may have added new strings that mention Moonfin:

```bash
python3 scripts/aleflix/rebrand_strings.py --check || { python3 scripts/aleflix/rebrand_strings.py && flutter gen-l10n; }
grep -rn "'Moonfin for Android" lib   # should print nothing
```

## Regenerating brand assets

The marks are vector files in `branding/source/` (Recraft V4.1 output). `scripts/aleflix/build_assets.py` derives every Android and Flutter asset from them:

```bash
uv venv /tmp/aleflix-brand && uv pip install --python /tmp/aleflix-brand resvg-py pillow
/tmp/aleflix-brand/bin/python scripts/aleflix/build_assets.py --preview /tmp/aleflix-preview
```

## Not rebranded yet

These platforms still carry Moonfin's identity, because the fork targets Android first: iOS, tvOS, macOS, Windows (`msix_config` in `pubspec.yaml`), Linux and web.
