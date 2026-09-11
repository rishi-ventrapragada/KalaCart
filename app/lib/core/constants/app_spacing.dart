import 'package:flutter/material.dart';

class AppSpacing {
  AppSpacing._();

  static const double xxs = 2.0;
  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 12.0;
  static const double base = 16.0;
  static const double lg = 20.0;
  static const double xl = 24.0;
  static const double xxl = 32.0;
  static const double xxxl = 40.0;
  static const double huge = 48.0;

  // EdgeInsets helpers
  static const EdgeInsets paddingAllXs = EdgeInsets.all(xs);
  static const EdgeInsets paddingAllSm = EdgeInsets.all(sm);
  static const EdgeInsets paddingAllMd = EdgeInsets.all(md);
  static const EdgeInsets paddingAllBase = EdgeInsets.all(base);
  static const EdgeInsets paddingAllLg = EdgeInsets.all(lg);
  static const EdgeInsets paddingAllXl = EdgeInsets.all(xl);

  static const EdgeInsets paddingHSm = EdgeInsets.symmetric(horizontal: sm);
  static const EdgeInsets paddingHBase = EdgeInsets.symmetric(horizontal: base);
  static const EdgeInsets paddingHLg = EdgeInsets.symmetric(horizontal: lg);
  static const EdgeInsets paddingHXl = EdgeInsets.symmetric(horizontal: xl);

  static const EdgeInsets paddingVSm = EdgeInsets.symmetric(vertical: sm);
  static const EdgeInsets paddingVBase = EdgeInsets.symmetric(vertical: base);
  static const EdgeInsets paddingVLg = EdgeInsets.symmetric(vertical: lg);

  // SizedBox gaps
  static const SizedBox gapH4 = SizedBox(width: xs);
  static const SizedBox gapH6 = SizedBox(width: 6.0);
  static const SizedBox gapH8 = SizedBox(width: sm);
  static const SizedBox gapH10 = SizedBox(width: 10.0);
  static const SizedBox gapH12 = SizedBox(width: md);
  static const SizedBox gapH16 = SizedBox(width: base);
  static const SizedBox gapH24 = SizedBox(width: xl);

  static const SizedBox gapV2 = SizedBox(height: xxs);
  static const SizedBox gapV4 = SizedBox(height: xs);
  static const SizedBox gapV6 = SizedBox(height: 6.0);
  static const SizedBox gapV8 = SizedBox(height: sm);
  static const SizedBox gapV12 = SizedBox(height: md);
  static const SizedBox gapV16 = SizedBox(height: base);
  static const SizedBox gapV20 = SizedBox(height: lg);
  static const SizedBox gapV24 = SizedBox(height: xl);
  static const SizedBox gapV32 = SizedBox(height: xxl);
}
