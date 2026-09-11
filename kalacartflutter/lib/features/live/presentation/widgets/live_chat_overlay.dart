import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../domain/live_session_model.dart';

class LiveChatOverlay extends StatelessWidget {
  final List<LiveComment> comments;
  final ScrollController scrollController;

  const LiveChatOverlay({
    super.key,
    required this.comments,
    required this.scrollController,
  });

  @override
  Widget build(BuildContext context) {
    return ShaderMask(
      shaderCallback: (Rect bounds) {
        return const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.transparent, Colors.white, Colors.white],
          stops: [0.0, 0.25, 1.0],
        ).createShader(bounds);
      },
      blendMode: BlendMode.dstIn,
      child: ListView.builder(
        controller: scrollController,
        padding: const EdgeInsets.only(left: 12, right: 80, bottom: 8, top: 20),
        itemCount: comments.length,
        itemBuilder: (context, index) {
          final comment = comments[index];
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: comment.isSystem
                      ? AppColors.primary.withValues(alpha: 0.75)
                      : Colors.black.withValues(alpha: 0.55),
                  borderRadius: AppRadius.borderMd,
                  border: comment.isArtisan
                      ? Border.all(color: AppColors.secondary, width: 1.2)
                      : null,
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (!comment.isSystem) ...[
                      CircleAvatar(
                        radius: 9,
                        backgroundImage: NetworkImage(comment.userAvatar),
                      ),
                      AppSpacing.gapH6,
                    ],
                    Flexible(
                      child: RichText(
                        text: TextSpan(
                          children: [
                            if (comment.isArtisan)
                              const WidgetSpan(
                                alignment: PlaceholderAlignment.middle,
                                child: Padding(
                                  padding: EdgeInsets.only(right: 4),
                                  child: Icon(Icons.verified, size: 12, color: AppColors.secondary),
                                ),
                              ),
                            TextSpan(
                              text: '${comment.userName}: ',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: comment.isArtisan
                                    ? AppColors.secondaryContainer
                                    : (comment.isSystem ? Colors.white : Colors.white70),
                              ),
                            ),
                            TextSpan(
                              text: comment.text,
                              style: const TextStyle(
                                fontSize: 12,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
