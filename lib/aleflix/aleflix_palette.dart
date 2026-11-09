/// The Aleflix Noir palette, for places upstream paints with fixed colors
/// instead of reading the active theme (loading overlays, the screensaver,
/// avatar fallbacks). Keep in step with
/// packages/design/lib/src/theme/themes/moonfin_theme_spec.dart.
library;

import 'dart:ui';

class AleflixPalette {
  const AleflixPalette._();

  static const Color noir = Color(0xFF0E0D0C);
  static const Color surface = Color(0xFF1A1816);
  static const Color champagne = Color(0xFFC8A96A);
  static const Color champagneLight = Color(0xFFE6D3A8);
  static const Color bronze = Color(0xFF8A7A5E);
  static const Color ivory = Color(0xFFF4EFE6);
  static const Color muted = Color(0xFF9A948A);
}
