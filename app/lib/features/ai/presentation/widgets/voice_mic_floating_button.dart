import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../domain/ai_models.dart';
import 'voice_assistant_modal.dart';

class VoiceMicFloatingButton extends StatelessWidget {
  final bool isArtisanMode;
  final Function(VoiceIntentResult)? onIntentExtracted;

  const VoiceMicFloatingButton({
    super.key,
    this.isArtisanMode = false,
    this.onIntentExtracted,
  });

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton(
      heroTag: 'voice_ai_fab',
      backgroundColor: AppColors.primary,
      foregroundColor: Colors.white,
      elevation: 4,
      onPressed: () async {
        final result = await VoiceAssistantModal.show(
          context,
          isArtisanMode: isArtisanMode,
        );
        if (result != null) {
          onIntentExtracted?.call(result);
        }
      },
      child: const Icon(Icons.mic, size: 26),
    );
  }
}
