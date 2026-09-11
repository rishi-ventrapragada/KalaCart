import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../shared/models/chat_rfq_models.dart';
import '../../ai/presentation/widgets/voice_assistant_modal.dart';
import '../data/rfq_chat_repository.dart';

class BuyerCreateRfqScreen extends ConsumerStatefulWidget {
  const BuyerCreateRfqScreen({super.key});

  @override
  ConsumerState<BuyerCreateRfqScreen> createState() => _BuyerCreateRfqScreenState();
}

class _BuyerCreateRfqScreenState extends ConsumerState<BuyerCreateRfqScreen> {
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _categoryController = TextEditingController(text: 'Pottery & Terracotta');
  final TextEditingController _qtyController = TextEditingController(text: '50');
  final TextEditingController _priceController = TextEditingController(text: '1200');
  final TextEditingController _deadlineController = TextEditingController(text: 'Within 30 Days');
  final TextEditingController _pincodeController = TextEditingController(text: '560038 (Bengaluru)');
  final TextEditingController _notesController = TextEditingController();
  bool _voiceNoteRecorded = false;
  int _attachmentCount = 2;

  @override
  void dispose() {
    _titleController.dispose();
    _categoryController.dispose();
    _qtyController.dispose();
    _priceController.dispose();
    _deadlineController.dispose();
    _pincodeController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final qty = int.tryParse(_qtyController.text) ?? 50;
    final unitPrice = double.tryParse(_priceController.text) ?? 1200;
    final totalBudget = qty * unitPrice;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Post Custom RFQ'),
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          // Header info
          const Text(
            'Request Bespoke Quotes from Master Guilds',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          AppSpacing.gapV4,
          const Text(
            'Enter your craft specifications. Verified master artisans across India will respond with custom pricing and delivery timelines.',
            style: TextStyle(fontSize: 12, color: Colors.grey, height: 1.35),
          ),
          AppSpacing.gapV16,

          TextField(
            controller: _titleController,
            decoration: const InputDecoration(
              labelText: 'Craft / Product Name *',
              hintText: 'e.g. 50 Custom Glazed Blue Pottery Mugs with Logo',
              prefixIcon: Icon(Icons.title),
            ),
          ),
          AppSpacing.gapV12,

          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _categoryController,
                  decoration: const InputDecoration(
                    labelText: 'Category *',
                    prefixIcon: Icon(Icons.category_outlined),
                  ),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: TextField(
                  controller: _qtyController,
                  keyboardType: TextInputType.number,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    labelText: 'Quantity (Units) *',
                    prefixIcon: Icon(Icons.numbers),
                  ),
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,

          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _priceController,
                  keyboardType: TextInputType.number,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    labelText: 'Target Price / Unit (₹) *',
                    prefixIcon: Icon(Icons.currency_rupee),
                  ),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: TextField(
                  controller: _deadlineController,
                  decoration: const InputDecoration(
                    labelText: 'Delivery Timeline *',
                    prefixIcon: Icon(Icons.event_outlined),
                  ),
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,

          TextField(
            controller: _pincodeController,
            decoration: const InputDecoration(
              labelText: 'Destination PIN Code / City *',
              prefixIcon: Icon(Icons.location_on_outlined),
            ),
          ),
          AppSpacing.gapV12,

          TextField(
            controller: _notesController,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Customization & Material Requirements',
              hintText: 'Describe colors, dimensions, motifs, lead-free glazes, packaging type...',
              alignLabelWithHint: true,
            ),
          ),
          AppSpacing.gapV16,

          // Voice Note Simulator
          Container(
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: AppColors.primaryContainer.withValues(alpha: 0.3),
              borderRadius: AppRadius.borderMd,
            ),
            child: Row(
              children: [
                IconButton(
                  icon: Icon(_voiceNoteRecorded ? Icons.check_circle : Icons.mic_rounded, color: AppColors.primary, size: 28),
                  onPressed: () async {
                    final result = await VoiceAssistantModal.show(context, isArtisanMode: false);
                    if (result != null) {
                      setState(() {
                        _voiceNoteRecorded = true;
                        _notesController.text = '${result.rawTranscript}\n\n[Kala-AI Note: ${result.assistantResponseText}]';
                      });
                    }
                  },
                ),
                AppSpacing.gapH8,
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _voiceNoteRecorded ? 'Voice Note Attached (0:42)' : 'Record Audio Note for Artisan',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                      Text(
                        _voiceNoteRecorded ? 'Transcribed in Hindi & English for rural artisans.' : 'Speak in any Indian language. Kala-AI translates for artisans.',
                        style: const TextStyle(fontSize: 10, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          AppSpacing.gapV16,

          // Reference Images / Attachments
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Reference Attachments ($_attachmentCount)', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              TextButton.icon(
                icon: const Icon(Icons.add_photo_alternate_outlined, size: 16),
                label: const Text('Add Reference'),
                onPressed: () {
                  setState(() => _attachmentCount += 1);
                },
              ),
            ],
          ),
          AppSpacing.gapV8,
          SizedBox(
            height: 70,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _attachmentCount,
              separatorBuilder: (_, __) => AppSpacing.gapH8,
              itemBuilder: (context, index) {
                return Container(
                  width: 70,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: AppRadius.borderSm,
                  ),
                  child: Center(
                    child: Icon(Icons.image_outlined, color: Colors.grey.shade600),
                  ),
                );
              },
            ),
          ),
          AppSpacing.gapV24,

          // Total Estimated Target Budget Card
          Container(
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: AppColors.secondaryContainer.withValues(alpha: 0.4),
              borderRadius: AppRadius.borderMd,
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Total Estimated Target Budget:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                Text(CurrencyFormatter.formatINR(totalBudget), style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 16)),
              ],
            ),
          ),
          AppSpacing.gapV24,

          // Submit Button
          SizedBox(
            height: 48,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                shape: AppRadius.shapeMd,
              ),
              icon: const Icon(Icons.send_rounded),
              label: const Text('Broadcast RFQ to Master Guilds', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              onPressed: _submitRfq,
            ),
          ),
          AppSpacing.gapV32,
        ],
      ),
    );
  }

  void _submitRfq() {
    final title = _titleController.text.isNotEmpty ? _titleController.text : '50 Custom Glazed Blue Pottery Mugs';
    final qty = int.tryParse(_qtyController.text) ?? 50;
    final price = double.tryParse(_priceController.text) ?? 1200;

    final newRfq = BuyerRfqSubmission(
      id: 'brfq-${DateTime.now().millisecondsSinceEpoch}',
      title: title,
      category: _categoryController.text,
      quantity: qty,
      targetPricePerUnit: price,
      deliveryRequiredBy: _deadlineController.text,
      destinationPincode: _pincodeController.text,
      customizationNotes: _notesController.text.isNotEmpty ? _notesController.text : 'Custom order specifications submitted.',
      hasVoiceNote: _voiceNoteRecorded,
      status: 'open',
      createdAt: DateTime.now(),
    );

    ref.read(buyerRfqProvider.notifier).submitBuyerRfq(newRfq);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('🎉 RFQ broadcasted to 140+ verified Indian Master Guilds!'),
        behavior: SnackBarBehavior.floating,
      ),
    );
    context.pop();
  }
}
