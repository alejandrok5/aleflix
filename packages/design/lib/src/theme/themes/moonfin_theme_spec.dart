import 'package:flutter/material.dart';

import '../theme_spec.dart';

// Aleflix Noir. This is the default theme and keeps upstream's 'moonfin' id
// (ThemeRegistry.moonfinId) so stored preferences, settings sync and every
// moonfinId special case in upstream code carry over without edits.
//
// Warm charcoal ground, ivory type and a single champagne-gold accent, kept
// for state: progress, selection, focus. Focus is shown as a soft gold ring
// and a lift shadow rather than a glow. Titles set in Fraunces, UI in Inter.

const _ground = Color(0xFF0E0D0C); // warm charcoal
const _surface = Color(0xFF1A1816);
const _raised = Color(0xFF24211E);
const _raisedActive = Color(0xFF302C27);
const _hairline = Color(0xFF3A352F);
const _ivory = Color(0xFFF4EFE6);
const _faint = Color(0xFF6B665E);
const _gold = Color(0xFFC8A96A); // champagne
const _goldLight = Color(0xFFE6D3A8);

const moonfinThemeSpec = ThemeSpec(
  id: 'moonfin',
  displayName: 'Aleflix Noir',
  fontFamily: 'Inter',
  displayFontFamily: 'Fraunces',
  colors: ThemeColorTokens(
    background: _ground,
    onBackground: _ivory,
    surface: _surface,
    onSurface: _ivory,
    surfaceVariant: _raised,
    scrim: Color(0xCC0E0D0C),
    accent: _gold,
    onAccent: _ground,
    buttonNormal: _raised,
    buttonFocused: _ivory,
    buttonDisabled: _surface,
    buttonActive: _raisedActive,
    onButtonNormal: _ivory,
    onButtonFocused: _ground,
    onButtonDisabled: _faint,
    inputBackground: Color(0xFF1F1C19),
    inputFocused: Color(0xFF2A2622),
    inputBorder: _hairline,
    inputBorderFocused: _gold,
    rangeTrack: _hairline,
    rangeProgress: _gold,
    rangeThumb: _goldLight,
    seekbarBuffered: Color(0x66F4EFE6),
    badgeBackground: _gold,
    onBadge: _ground,
    badgeUnplayed: _gold,
    badgeWatched: Color(0xFF8E9F7A), // muted sage
    recordingActive: Color(0xFFC4553D), // brick
    recordingScheduled: Color(0xFFD08A4E), // amber
    error: Color(0xFFD9604C),
  ),
  borders: ThemeBorderTokens(
    cardBorder: BorderSide(color: Colors.transparent),
    chipBorder: BorderSide(color: Color(0x40C8A96A)),
    focusBorder: BorderSide(color: _goldLight, width: 2),
    cardRadius: BorderRadius.all(Radius.circular(6)),
    chipRadius: BorderRadius.all(Radius.circular(999)),
    chipBackground: Color(0x14F4EFE6),
    // A lift, not a glow: focused cards rise off the charcoal ground.
    focusGlow: [
      BoxShadow(
        color: Color(0xA6000000),
        blurRadius: 28,
        offset: Offset(0, 10),
      ),
    ],
  ),
);
