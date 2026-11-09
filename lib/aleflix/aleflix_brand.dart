/// Aleflix brand constants.
///
/// Aleflix is a rebrand of Moonfin (https://github.com/Moonfin-Client/Moonfin-Core).
/// Only what a user sees or installs is renamed: internal identifiers such as
/// the `moonfin` Dart package, the `org.moonfin.androidtv` Kotlin namespace,
/// method channel names and the Moonbase plugin's `/Moonfin/...` server routes
/// stay as upstream ships them, so upstream fixes keep merging cleanly.
/// Fork-specific values live here instead of being scattered through
/// upstream files.
library;

class AleflixBrand {
  const AleflixBrand._();

  static const String appName = 'Aleflix';

  /// The project Aleflix is built on, credited in About as GPL-2.0 requires.
  static const String upstreamName = 'Moonfin';
  static const String upstreamUrl =
      'https://github.com/Moonfin-Client/Moonfin-Core';

  static const String repoOwner = 'alejandrok5';
  static const String repoName = 'aleflix';
  static const String repoUrl = 'https://github.com/$repoOwner/$repoName';
  static const String issuesUrl = '$repoUrl/issues';
  static const String licenseUrl = '$repoUrl/blob/main/LICENSE';
  static const String privacyPolicyUrl = '$repoUrl/blob/main/PRIVACY_POLICY.md';

  /// GitHub API path the in-app update check reads.
  static const String latestReleaseApiPath =
      '/repos/$repoOwner/$repoName/releases/latest';
  static const String latestReleaseUrl = '$repoUrl/releases/latest';

  /// URL scheme for deep links (aleflix://...). Must match the intent filter
  /// in android/app/src/main/AndroidManifest.xml.
  static const String deepLinkScheme = 'aleflix';

  /// Upstream hard-codes navy and teal colors for its cyan theme on the
  /// sign-in screens and detail tabs, keyed on `ThemeRegistry.moonfinId`.
  /// Aleflix Noir took over that id but styles those screens from its theme
  /// tokens, so those checks read this instead. A getter, not a const, so the
  /// upstream branches don't turn into dead-code warnings.
  static bool get usesUpstreamMoonfinStyling => false;
}
