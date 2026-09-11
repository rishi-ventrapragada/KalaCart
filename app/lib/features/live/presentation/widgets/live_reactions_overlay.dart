import 'package:flutter/material.dart';
import '../../domain/live_session_model.dart';

class LiveReactionsOverlay extends StatelessWidget {
  final List<LiveReaction> reactions;

  const LiveReactionsOverlay({
    super.key,
    required this.reactions,
  });

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Stack(
        children: reactions.map((reaction) {
          return _AnimatedReactionBubble(
            key: ValueKey(reaction.id),
            reaction: reaction,
          );
        }).toList(),
      ),
    );
  }
}

class _AnimatedReactionBubble extends StatefulWidget {
  final LiveReaction reaction;

  const _AnimatedReactionBubble({
    super.key,
    required this.reaction,
  });

  @override
  State<_AnimatedReactionBubble> createState() => _AnimatedReactionBubbleState();
}

class _AnimatedReactionBubbleState extends State<_AnimatedReactionBubble> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _translateY;
  late Animation<double> _opacity;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );

    _translateY = Tween<double>(begin: 0, end: -220).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );

    _opacity = Tween<double>(begin: 1.0, end: 0.0).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.6, 1.0, curve: Curves.easeIn)),
    );

    _scale = Tween<double>(begin: 0.6, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.0, 0.3, curve: Curves.elasticOut)),
    );

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Positioned(
          bottom: 110 - _translateY.value,
          right: 24 + widget.reaction.xOffset,
          child: Opacity(
            opacity: _opacity.value,
            child: Transform.scale(
              scale: _scale.value,
              child: child,
            ),
          ),
        );
      },
      child: _buildReactionIcon(widget.reaction.type),
    );
  }

  Widget _buildReactionIcon(LiveReactionType type) {
    switch (type) {
      case LiveReactionType.heart:
        return const Icon(Icons.favorite, color: Color(0xFFFF2D55), size: 32);
      case LiveReactionType.fire:
        return const Icon(Icons.local_fire_department, color: Color(0xFFFF9500), size: 32);
      case LiveReactionType.clap:
        return const Text('👏', style: TextStyle(fontSize: 28));
      case LiveReactionType.namaste:
        return const Text('🙏', style: TextStyle(fontSize: 28));
      case LiveReactionType.star:
        return const Icon(Icons.star_rounded, color: Color(0xFFFFCC00), size: 32);
    }
  }
}
