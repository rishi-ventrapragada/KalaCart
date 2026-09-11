import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';

class VoiceWaveformIndicator extends StatefulWidget {
  final bool isListening;
  final bool isProcessing;
  final Color? color;

  const VoiceWaveformIndicator({
    super.key,
    required this.isListening,
    this.isProcessing = false,
    this.color,
  });

  @override
  State<VoiceWaveformIndicator> createState() => _VoiceWaveformIndicatorState();
}

class _VoiceWaveformIndicatorState extends State<VoiceWaveformIndicator> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isListening && !widget.isProcessing) {
      return const SizedBox.shrink();
    }

    final waveColor = widget.color ?? AppColors.primary;

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(5, (index) {
            final delay = index * 0.18;
            final animVal = (_controller.value + delay) % 1.0;
            final height = widget.isProcessing
                ? 8.0 + (animVal * 12.0)
                : 10.0 + ((1.0 - (animVal - 0.5).abs() * 2) * 24.0);

            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 2.5),
              width: 3.5,
              height: height,
              decoration: BoxDecoration(
                color: waveColor,
                borderRadius: BorderRadius.circular(2),
              ),
            );
          }),
        );
      },
    );
  }
}
