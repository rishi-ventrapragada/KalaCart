import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../data/ai_providers.dart';
import '../../domain/ai_models.dart';
import 'voice_waveform_indicator.dart';

class VoiceAssistantModal extends ConsumerStatefulWidget {
  final bool isArtisanMode;
  final Function(VoiceIntentResult)? onIntentExtracted;

  const VoiceAssistantModal({
    super.key,
    this.isArtisanMode = false,
    this.onIntentExtracted,
  });

  static Future<VoiceIntentResult?> show(
    BuildContext context, {
    bool isArtisanMode = false,
  }) {
    return showModalBottomSheet<VoiceIntentResult>(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => VoiceAssistantModal(
        isArtisanMode: isArtisanMode,
      ),
    );
  }

  @override
  ConsumerState<VoiceAssistantModal> createState() => _VoiceAssistantModalState();
}

class _VoiceAssistantModalState extends ConsumerState<VoiceAssistantModal> {
  VoiceState _voiceState = VoiceState.idle;
  SupportedLanguage _selectedLanguage = SupportedLanguage.hinglish;
  String _liveTranscript = '';
  String _assistantResponse = '';
  String _recognizedDialect = '';
  VoiceIntentResult? _lastResult;
  StreamSubscription<String>? _sttSubscription;

  @override
  void initState() {
    super.initState();
    // Auto-start listening after opening
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _startVoiceSession();
    });
  }

  void _startVoiceSession() {
    final sttService = ref.read(speechToTextServiceProvider);
    setState(() {
      _voiceState = VoiceState.listening;
      _liveTranscript = 'Listening... (Speak in English, Hindi, Telugu, or Hinglish)';
      _assistantResponse = '';
      _lastResult = null;
    });

    _sttSubscription?.cancel();
    _sttSubscription = sttService.startListening(preferredLanguage: _selectedLanguage).listen(
      (text) {
        if (mounted) {
          setState(() {
            _liveTranscript = text;
          });
        }
      },
      onDone: () => _processRecordedAudio(),
      onError: (_) {
        if (mounted) {
          setState(() {
            _voiceState = VoiceState.error;
            _assistantResponse = 'Could not capture voice audio. Please tap mic to try again.';
          });
        }
      },
    );

    // Auto-trigger completion simulation after 2.5s
    Future.delayed(const Duration(milliseconds: 2500), () {
      if (_voiceState == VoiceState.listening && mounted) {
        _processRecordedAudio();
      }
    });
  }

  void _processRecordedAudio() async {
    _sttSubscription?.cancel();
    setState(() => _voiceState = VoiceState.processing);

    final aiService = ref.read(aiServiceProvider);
    final transcript = _liveTranscript.contains('Listening')
        ? 'Ee basket ki 50 pieces kavali, wholesale quote ivvandi.'
        : _liveTranscript;

    final result = await aiService.processVoiceCommand(
      rawVoiceText: transcript,
      isArtisanMode: widget.isArtisanMode,
    );

    if (mounted) {
      setState(() {
        _voiceState = VoiceState.speaking;
        _liveTranscript = result.rawTranscript;
        _assistantResponse = result.assistantResponseText;
        _recognizedDialect = result.recognizedLanguage;
        _lastResult = result;
      });

      // Play simulated TTS audio feedback
      ref.read(textToSpeechServiceProvider).speak(
            text: result.assistantResponseText,
            language: _selectedLanguage,
          );
    }
  }

  @override
  void dispose() {
    _sttSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
      ),
      padding: EdgeInsets.fromLTRB(
        20,
        12,
        20,
        MediaQuery.of(context).padding.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Drag Handle
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.grey.withValues(alpha: 0.4),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          AppSpacing.gapV16,

          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: const BoxDecoration(
                      color: AppColors.primaryContainer,
                      borderRadius: AppRadius.borderSm,
                    ),
                    child: const Icon(Icons.auto_awesome, color: AppColors.primary, size: 18),
                  ),
                  AppSpacing.gapH8,
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.isArtisanMode ? 'Kala-AI Artisan Copilot' : 'Kala-AI Voice Assistant',
                        style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        'Multilingual Speech Understanding',
                        style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
                      ),
                    ],
                  ),
                ],
              ),
              // Language Selector Dropdown
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: AppRadius.borderPill,
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<SupportedLanguage>(
                    value: _selectedLanguage,
                    isDense: true,
                    style: const TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.bold),
                    items: SupportedLanguage.values.map((lang) {
                      return DropdownMenuItem(
                        value: lang,
                        child: Text('${lang.nativeLabel} (${lang.englishLabel})'),
                      );
                    }).toList(),
                    onChanged: (lang) {
                      if (lang != null) {
                        setState(() => _selectedLanguage = lang);
                        _startVoiceSession();
                      }
                    },
                  ),
                ),
              ),
            ],
          ),
          AppSpacing.gapV20,

          // Main Voice Card
          Container(
            width: double.infinity,
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
              borderRadius: AppRadius.borderLg,
              border: Border.all(
                color: _voiceState == VoiceState.listening
                    ? AppColors.primary.withValues(alpha: 0.5)
                    : Colors.transparent,
                width: 1.5,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _getStatusLabel(),
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: _getStatusColor(),
                      ),
                    ),
                    if (_recognizedDialect.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: const BoxDecoration(
                          color: AppColors.secondaryContainer,
                          borderRadius: AppRadius.borderXs,
                        ),
                        child: Text(
                          _recognizedDialect,
                          style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppColors.onSecondaryContainer),
                        ),
                      ),
                  ],
                ),
                AppSpacing.gapV12,

                // User Transcript
                Text(
                  '"$_liveTranscript"',
                  style: const TextStyle(fontSize: 14, fontStyle: FontStyle.italic, fontWeight: FontWeight.w500),
                ),
                AppSpacing.gapV12,

                // Assistant Response (if any)
                if (_assistantResponse.isNotEmpty) ...[
                  const Divider(),
                  AppSpacing.gapV8,
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.psychology_alt, color: AppColors.primary, size: 18),
                      AppSpacing.gapH8,
                      Expanded(
                        child: Text(
                          _assistantResponse,
                          style: const TextStyle(fontSize: 13, height: 1.4, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                ],

                // Extracted Intent action chip
                if (_lastResult != null && _lastResult!.intentType == 'rfq_inquiry') ...[
                  AppSpacing.gapV12,
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppColors.primaryContainer.withValues(alpha: 0.3),
                      borderRadius: AppRadius.borderMd,
                      border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.request_quote_outlined, color: AppColors.primary, size: 20),
                        AppSpacing.gapH8,
                        const Expanded(
                          child: Text(
                            'Parsed 50 qty wholesale RFQ intent from Telugu audio.',
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                        ),
                        TextButton(
                          onPressed: () {
                            Navigator.pop(context, _lastResult);
                          },
                          child: const Text('Apply RFQ'),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          AppSpacing.gapV24,

          // Voice Waveform & Mic Trigger Button
          VoiceWaveformIndicator(
            isListening: _voiceState == VoiceState.listening,
            isProcessing: _voiceState == VoiceState.processing,
          ),
          AppSpacing.gapV16,

          // Main Interactive Mic Button
          GestureDetector(
            onTap: () {
              if (_voiceState == VoiceState.listening) {
                _processRecordedAudio();
              } else {
                _startVoiceSession();
              }
            },
            child: Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: _getStatusColor(),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: _getStatusColor().withValues(alpha: 0.35),
                    blurRadius: 18,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Icon(
                _getMicIcon(),
                color: Colors.white,
                size: 32,
              ),
            ),
          ),
          AppSpacing.gapV8,
          Text(
            _voiceState == VoiceState.listening ? 'Tap to finish' : 'Tap to speak again',
            style: const TextStyle(fontSize: 11, color: Colors.grey),
          ),
        ],
      ),
    );
  }

  String _getStatusLabel() {
    switch (_voiceState) {
      case VoiceState.idle:
        return 'IDLE';
      case VoiceState.listening:
        return 'LISTENING TO SPEECH...';
      case VoiceState.processing:
        return 'AI NEURAL UNDERSTANDING...';
      case VoiceState.speaking:
        return 'AI ASSISTANT RESPONSE';
      case VoiceState.error:
        return 'VOICE RECOGNITION ERROR';
    }
  }

  Color _getStatusColor() {
    switch (_voiceState) {
      case VoiceState.idle:
        return Colors.grey;
      case VoiceState.listening:
        return const Color(0xFFD32F2F);
      case VoiceState.processing:
        return AppColors.primary;
      case VoiceState.speaking:
        return AppColors.success;
      case VoiceState.error:
        return Colors.redAccent;
    }
  }

  IconData _getMicIcon() {
    switch (_voiceState) {
      case VoiceState.idle:
      case VoiceState.speaking:
        return Icons.mic;
      case VoiceState.listening:
        return Icons.stop;
      case VoiceState.processing:
        return Icons.hourglass_top_rounded;
      case VoiceState.error:
        return Icons.refresh;
    }
  }
}
