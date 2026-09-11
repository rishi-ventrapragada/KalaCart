import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../../seller/data/seller_repository.dart';
import '../data/live_repository.dart';
import '../domain/live_session_model.dart';

class SellerScheduleLiveScreen extends ConsumerStatefulWidget {
  const SellerScheduleLiveScreen({super.key});

  @override
  ConsumerState<SellerScheduleLiveScreen> createState() => _SellerScheduleLiveScreenState();
}

class _SellerScheduleLiveScreenState extends ConsumerState<SellerScheduleLiveScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController(text: 'Live Workshop: Master Pottery Throwing & Glaze Demo');
  final _descController = TextEditingController(text: 'Join us live as we throw blue quartz clay and showcase new GI certified pieces.');
  final _coverUrlController = TextEditingController(text: 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61');

  final Set<String> _selectedProductIds = {'prod-001', 'prod-004'};
  DateTime _scheduledDate = DateTime.now().add(const Duration(days: 1));
  TimeOfDay _scheduledTime = const TimeOfDay(hour: 18, minute: 30);
  bool _startImmediately = true;

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    _coverUrlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sellerProducts = ref.watch(sellerProductsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Schedule Live Stream'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: AppSpacing.paddingAllBase,
          children: [
            // Header Info Box
            Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: AppColors.primaryContainer.withValues(alpha: 0.3),
                borderRadius: AppRadius.borderMd,
                border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.sensors_rounded, color: AppColors.primary, size: 28),
                  AppSpacing.gapH12,
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Live Artisan Commerce', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        Text('Broadcast your craftsmanship in real-time, demonstrate techniques, and sell live to buyers worldwide.', style: TextStyle(fontSize: 12, height: 1.3)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            AppSpacing.gapV20,

            // Live Title
            Text('Session Title', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
            AppSpacing.gapV6,
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(
                hintText: 'e.g. Traditional Zari Brocade Weaving Masterclass',
                prefixIcon: Icon(Icons.title),
              ),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Please enter a title' : null,
            ),
            AppSpacing.gapV16,

            // Description
            Text('Workshop Description', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
            AppSpacing.gapV6,
            TextFormField(
              controller: _descController,
              maxLines: 3,
              decoration: const InputDecoration(
                hintText: 'What techniques and products will you show during this live stream?',
              ),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Please enter a description' : null,
            ),
            AppSpacing.gapV16,

            // Cover Image URL
            Text('Cover Photo URL', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
            AppSpacing.gapV6,
            TextFormField(
              controller: _coverUrlController,
              decoration: const InputDecoration(
                hintText: 'https://...',
                prefixIcon: Icon(Icons.image_outlined),
              ),
            ),
            AppSpacing.gapV20,

            // Schedule Mode
            Row(
              children: [
                Expanded(
                  child: ChoiceChip(
                    label: const Center(child: Text('Start Immediately', style: TextStyle(fontWeight: FontWeight.bold))),
                    selected: _startImmediately,
                    onSelected: (selected) {
                      if (selected) setState(() => _startImmediately = true);
                    },
                  ),
                ),
                AppSpacing.gapH12,
                Expanded(
                  child: ChoiceChip(
                    label: const Center(child: Text('Schedule for Later', style: TextStyle(fontWeight: FontWeight.bold))),
                    selected: !_startImmediately,
                    onSelected: (selected) {
                      if (selected) setState(() => _startImmediately = false);
                    },
                  ),
                ),
              ],
            ),

            if (!_startImmediately) ...[
              AppSpacing.gapV16,
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.calendar_today, size: 16),
                      label: Text('${_scheduledDate.day}/${_scheduledDate.month}/${_scheduledDate.year}'),
                      onPressed: _pickDate,
                    ),
                  ),
                  AppSpacing.gapH12,
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.access_time, size: 16),
                      label: Text(_scheduledTime.format(context)),
                      onPressed: _pickTime,
                    ),
                  ),
                ],
              ),
            ],
            AppSpacing.gapV24,

            // Select Products to Feature in Live
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Select Showcase Products (${_selectedProductIds.length})', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                TextButton(
                  onPressed: () {
                    setState(() {
                      if (_selectedProductIds.length == sellerProducts.length) {
                        _selectedProductIds.clear();
                      } else {
                        _selectedProductIds.addAll(sellerProducts.map((p) => p.id));
                      }
                    });
                  },
                  child: Text(_selectedProductIds.length == sellerProducts.length ? 'Clear All' : 'Select All'),
                ),
              ],
            ),
            AppSpacing.gapV8,

            ...sellerProducts.map((product) {
              final isSelected = _selectedProductIds.contains(product.id);
              return Card(
                elevation: isSelected ? 2 : 0,
                color: isSelected ? AppColors.primaryContainer.withValues(alpha: 0.2) : null,
                shape: RoundedRectangleBorder(
                  borderRadius: AppRadius.borderMd,
                  side: BorderSide(
                    color: isSelected ? AppColors.primary : Colors.grey.shade300,
                    width: isSelected ? 1.5 : 1,
                  ),
                ),
                margin: const EdgeInsets.only(bottom: 8),
                child: CheckboxListTile(
                  value: isSelected,
                  activeColor: AppColors.primary,
                  onChanged: (val) {
                    setState(() {
                      if (val == true) {
                        _selectedProductIds.add(product.id);
                      } else {
                        _selectedProductIds.remove(product.id);
                      }
                    });
                  },
                  secondary: ClipRRect(
                    borderRadius: AppRadius.borderSm,
                    child: Container(
                      width: 48,
                      height: 48,
                      color: AppColors.primaryContainer.withValues(alpha: 0.5),
                      child: const Icon(Icons.palette_outlined, color: AppColors.primary),
                    ),
                  ),
                  title: Text(product.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  subtitle: Text('₹${product.retailPrice.toStringAsFixed(0)} · ${product.category}', style: const TextStyle(fontSize: 11)),
                ),
              );
            }),

            AppSpacing.gapV24,

            // Action CTA
            AppButton(
              label: _startImmediately ? 'Go Live Now' : 'Save & Schedule Live',
              icon: _startImmediately ? Icons.videocam : Icons.schedule,
              onPressed: _handleSubmit,
            ),
            AppSpacing.gapV24,
          ],
        ),
      ),
    );
  }

  void _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _scheduledDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 90)),
    );
    if (picked != null) {
      setState(() => _scheduledDate = picked);
    }
  }

  void _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _scheduledTime,
    );
    if (picked != null) {
      setState(() => _scheduledTime = picked);
    }
  }

  void _handleSubmit() {
    if (!_formKey.currentState!.validate()) return;

    final sellerProducts = ref.read(sellerProductsProvider);
    final selectedProductsList = sellerProducts
        .where((p) => _selectedProductIds.contains(p.id))
        .map((p) => LiveProductItem(
              id: p.id,
              title: p.title,
              price: p.retailPrice,
              wholesalePrice: p.wholesaleTiers.isNotEmpty ? p.wholesaleTiers.first.pricePerUnit : null,
              imageUrl: 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61',
              craftType: p.category,
              isPinned: p.id == _selectedProductIds.firstOrNull,
            ))
        .toList();

    final newSession = LiveSessionModel(
      id: 'live-${DateTime.now().millisecondsSinceEpoch}',
      artisanId: 'art-seller-me',
      artisanName: 'Dr. Kripal Kumbh Studio',
      artisanAvatar: 'https://images.unsplash.com/photo-1544717305-2782549b5136',
      craftCluster: 'Jaipur Blue Pottery Guild',
      region: 'Jaipur, Rajasthan',
      title: _titleController.text.trim(),
      description: _descController.text.trim(),
      coverImageUrl: _coverUrlController.text.trim().isNotEmpty
          ? _coverUrlController.text.trim()
          : 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61',
      status: _startImmediately ? LiveStreamStatus.live : LiveStreamStatus.scheduled,
      scheduledAt: _startImmediately ? null : _scheduledDate,
      viewerCount: _startImmediately ? 14 : 0,
      likesCount: 0,
      products: selectedProductsList,
      pinnedProductId: selectedProductsList.firstOrNull?.id,
    );

    ref.read(liveSessionsProvider.notifier).addSession(newSession);

    if (_startImmediately) {
      context.pushReplacement('/seller/live/${newSession.id}');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Live workshop scheduled! Notification alert configured for your followers.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      context.pop();
    }
  }
}
