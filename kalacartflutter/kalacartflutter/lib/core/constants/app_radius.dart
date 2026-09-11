import 'package:flutter/material.dart';

class AppRadius {
  AppRadius._();

  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 12.0;
  static const double lg = 16.0;
  static const double xl = 24.0;
  static const double full = 999.0;

  static const Radius radiusXs = Radius.circular(xs);
  static const Radius radiusSm = Radius.circular(sm);
  static const Radius radiusMd = Radius.circular(md);
  static const Radius radiusLg = Radius.circular(lg);
  static const Radius radiusXl = Radius.circular(xl);

  static const BorderRadius borderXs = BorderRadius.all(radiusXs);
  static const BorderRadius borderSm = BorderRadius.all(radiusSm);
  static const BorderRadius borderMd = BorderRadius.all(radiusMd);
  static const BorderRadius borderLg = BorderRadius.all(radiusLg);
  static const BorderRadius borderXl = BorderRadius.all(radiusXl);
  static const BorderRadius borderFull = BorderRadius.all(Radius.circular(full));
  static const BorderRadius borderPill = borderFull;

  static const RoundedRectangleBorder shapeSm = RoundedRectangleBorder(borderRadius: borderSm);
  static const RoundedRectangleBorder shapeMd = RoundedRectangleBorder(borderRadius: borderMd);
  static const RoundedRectangleBorder shapeLg = RoundedRectangleBorder(borderRadius: borderLg);
  static const RoundedRectangleBorder shapeXl = RoundedRectangleBorder(borderRadius: borderXl);
  static const RoundedRectangleBorder shapePill = RoundedRectangleBorder(borderRadius: borderFull);
}
