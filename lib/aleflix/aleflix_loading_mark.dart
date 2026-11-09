import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import 'aleflix_palette.dart';

const _orbitsPerCycle = 3;

/// The Aleflix loading mark: the wolf-and-moon logo held still while a
/// moonlight halo breathes behind it and a champagne arc circles the disc.
///
/// Stands in for upstream's spinning Moonfin logo
/// (`LoadingAnimationImage.moonfinLogo`, shown as "Aleflix Logo").
class AleflixLoadingMark extends StatefulWidget {
  const AleflixLoadingMark({super.key, required this.size, this.speed = 1.0});

  final double size;

  /// Tempo multiplier from the loading-speed setting; 1.0 orbits once every
  /// 1.6 s and breathes once every 4.8 s.
  final double speed;

  static const _logoAsset = 'assets/icons/moonfin_logo.svg';

  /// Compiles the logo into flutter_svg's cache, so the first loading overlay
  /// shows it at once rather than an empty disc while the SVG is parsed.
  static Future<void> precache() async {
    const loader = SvgAssetLoader(_logoAsset);
    try {
      await svg.cache.putIfAbsent(
        loader.cacheKey(null),
        () => loader.loadBytes(null),
      );
    } catch (_) {
      // Only a warm-up: the widget loads the asset itself either way.
    }
  }

  @override
  State<AleflixLoadingMark> createState() => _AleflixLoadingMarkState();
}

class _AleflixLoadingMarkState extends State<AleflixLoadingMark>
    with SingleTickerProviderStateMixin {
  /// One breath; the arc makes [_orbitsPerCycle] turns in the same time so
  /// the loop joins seamlessly.
  static const _cycleMs = 4800;

  late final AnimationController _controller;

  Duration get _cycle =>
      Duration(milliseconds: (_cycleMs / widget.speed).round());

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: _cycle)..repeat();
  }

  @override
  void didUpdateWidget(covariant AleflixLoadingMark oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.speed != widget.speed) {
      _controller.duration = _cycle;
      if (_controller.isAnimating) _controller.repeat();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = widget.size;
    return SizedBox.square(
      dimension: size,
      child: CustomPaint(
        painter: _HaloOrbitPainter(_controller),
        // The logo never moves, so it rasterizes once on its own layer.
        child: Center(
          child: RepaintBoundary(
            child: SvgPicture.asset(
              AleflixLoadingMark._logoAsset,
              width: size * _HaloOrbitPainter.markFraction,
              height: size * _HaloOrbitPainter.markFraction,
            ),
          ),
        ),
      ),
    );
  }
}

class _HaloOrbitPainter extends CustomPainter {
  _HaloOrbitPainter(this.animation) : super(repaint: animation);

  final Animation<double> animation;

  /// Logo diameter as a fraction of the widget's side.
  static const markFraction = 0.74;
  static const _orbitFraction = 0.45;
  static const _arcSweep = math.pi * 0.62;

  @override
  void paint(Canvas canvas, Size size) {
    final t = animation.value;
    final side = size.shortestSide;
    final center = size.center(Offset.zero);
    // 0 -> 1 -> 0 over the cycle, eased at both ends.
    final breath = 0.5 - 0.5 * math.cos(t * 2 * math.pi);

    // Moonlight halo: lies under the logo's disc, so only the rim glows.
    final haloRadius = side * 0.5;
    final haloAlpha = 0.10 + 0.16 * breath;
    canvas.drawCircle(
      center,
      haloRadius,
      Paint()
        ..shader = RadialGradient(
          colors: [
            AleflixPalette.champagne.withValues(alpha: haloAlpha),
            AleflixPalette.champagne.withValues(alpha: haloAlpha),
            AleflixPalette.champagne.withValues(alpha: 0),
          ],
          stops: const [0, markFraction, 1],
        ).createShader(Rect.fromCircle(center: center, radius: haloRadius)),
    );

    final orbitRadius = side * _orbitFraction;
    final stroke = math.max(1.5, side * 0.016);
    final orbitRect = Rect.fromCircle(center: center, radius: orbitRadius);

    // Faint track the arc runs along.
    canvas.drawCircle(
      center,
      orbitRadius,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = stroke * 0.6
        ..color = AleflixPalette.champagne.withValues(alpha: 0.14),
    );

    // The arc, fading in from its tail to an ivory head.
    final head = -math.pi / 2 + (t * _orbitsPerCycle % 1) * 2 * math.pi;
    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(head - _arcSweep);
    canvas.translate(-center.dx, -center.dy);
    canvas.drawArc(
      orbitRect,
      0,
      _arcSweep,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = stroke
        // Butt caps, and decal tiling below: anything drawn outside the
        // gradient's angle range (a round cap, antialiasing at the tail)
        // would otherwise wrap round and take the ivory head color. The head
        // dot rounds the leading end.
        ..strokeCap = StrokeCap.butt
        ..shader = SweepGradient(
          center: Alignment.center,
          endAngle: _arcSweep,
          tileMode: TileMode.decal,
          colors: [
            AleflixPalette.champagne.withValues(alpha: 0),
            AleflixPalette.champagne,
            AleflixPalette.ivory,
          ],
          stops: const [0, 0.7, 1],
        ).createShader(orbitRect),
    );
    canvas.restore();

    final headPoint =
        center + Offset(math.cos(head), math.sin(head)) * orbitRadius;
    canvas.drawCircle(
      headPoint,
      stroke * 2.2,
      Paint()..color = AleflixPalette.champagne.withValues(alpha: 0.22),
    );
    canvas.drawCircle(
      headPoint,
      stroke * 0.9,
      Paint()..color = AleflixPalette.ivory,
    );
  }

  @override
  bool shouldRepaint(covariant _HaloOrbitPainter oldDelegate) =>
      oldDelegate.animation != animation;
}
