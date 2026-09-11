import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/catalog_studio_state.dart';

abstract class CatalogStudioService {
  Future<void> startAiProcessing();
  void addImage(CapturedImageItem image);
  void removeImage(String id);
  void reorderImages(int oldIndex, int newIndex);
  void toggleEnhancedBackground(String id);
  void updateGeneratedData(AiGeneratedCraftData data);
  void resetStudio();
  void selectPresetSample(int index);
}

class MockCatalogStudioRepository extends StateNotifier<CatalogStudioSessionState> implements CatalogStudioService {
  MockCatalogStudioRepository()
      : super(const CatalogStudioSessionState(
          stage: CatalogStudioStage.capture,
          images: [
            CapturedImageItem(
              id: 'img-01',
              label: 'Front View (Glaze & Neck)',
              assetMockPath: 'assets/mock/pottery_front.jpg',
              isPrimary: true,
              isEnhanced: true,
            ),
            CapturedImageItem(
              id: 'img-02',
              label: 'Detail Motif & Cobalt Oxide',
              assetMockPath: 'assets/mock/pottery_detail.jpg',
              isPrimary: false,
              isEnhanced: false,
            ),
            CapturedImageItem(
              id: 'img-03',
              label: 'Base & GI Guild Seal',
              assetMockPath: 'assets/mock/pottery_base.jpg',
              isPrimary: false,
              isEnhanced: false,
            ),
          ],
        ));

  final List<AiGeneratedCraftData> _mockPresets = [
    const AiGeneratedCraftData(
      title: 'Handcrafted Cobalt Floral Jaipur Blue Pottery Amphora Vase',
      description: 'Preserving Rajasthan\'s famed GI-certified ceramic tradition, this amphora vase is shaped without clay using a centuries-old mix of Makrana quartz stone, glass powder, natural gum, and multani mitti. Hand-painted with Persian-Mughal vine motifs using pure cobalt oxide and copper glazes.',
      category: 'Pottery & Terracotta',
      materials: 'Natural Quartz Powder, Fuller\'s Earth (Multani Mitti), Plant Gum, Cobalt & Copper Oxide Glazes',
      craftTechnique: 'Quartz Clay-Free Molding, Low-Fire Kiln Baking, Hand-Lined Glaze Detailing',
      dimensions: '14" Height x 7.5" Diameter (Base: 4.5")',
      weight: '1.45 kg',
      tags: ['#JaipurBluePottery', '#GITagged', '#HandmadeInIndia', '#EcoCeramics', '#HeritageHome'],
      careInstructions: 'Wipe clean with soft damp cloth. Not microwave safe. Avoid abrasive cleaning agents.',
      seoDescription: 'Authentic GI Tagged Jaipur Blue Pottery floral vase handcrafted by master artisans in Kot Jewar, Rajasthan. Free shipping across India.',
      retailPrice: 2450.0,
      wholesalePrice: 1650.0,
      suggestedMoq: 10,
      englishTranslation: 'Handcrafted Cobalt Floral Jaipur Blue Pottery Amphora Vase with authentic GI heritage stamp.',
      hindiTranslation: 'हस्तनिर्मित कोबाल्ट फ्लोरल जयपुर ब्लू पॉटरी फूलदान - पारंपरिक मुल्तानी मिट्टी और क्वार्ट्ज से निर्मित।',
      teluguTranslation: 'చేతితో తయారు చేయబడిన జైపూర్ బ్లూ పాటర్ పువ్వుల జాడీ - సహజ ఖనిజ రంగులతో రూపొందించబడింది.',
      bengaliTranslation: 'হস্তশিল্পজাত জয়পুর ব্লু পটারি ফুলদানি - প্রাকৃতিক খনিজ ও কোবাল্ট গ্লেজ দ্বারা সজ্জিত।',
      marketingCopyShort: 'Bring the royal heritage of Jaipur into your living space with this GI-certified Blue Pottery masterpiece.',
      marketingCopySocial: '✨ Centuries of artistry in your hands! Handcrafted by master artisans in Jaipur using quartz and natural cobalt mineral glazes. Zero clay. 100% timeless. 🏺🇮🇳 #KalaCart #IndianCrafts #JaipurPottery',
      giClusterDetected: 'Jaipur Blue Pottery Cluster (GI Reg #04)',
      authenticityConfidence: 0.98,
    ),
    const AiGeneratedCraftData(
      title: 'Machilipatnam Botanical Teak-Block Kalamkari Handloom Fabric',
      description: 'Authentic Andhra Pradesh hand block-printed textile dyed with myrobalan nuts and natural indigo. The patterns are stamped using hand-carved teakwood blocks and washed in flowing canal waters to fix the organic dyes.',
      category: 'Handloom & Textiles',
      materials: '100% Guntur Organic Cotton, Natural Indigo Leaves, Madder Root, Alum Mordant',
      craftTechnique: 'Teakwood Block Stamping, River Canal Washing, Sun Bleaching',
      dimensions: '44" Width x 5.5 Meters Length',
      weight: '580 grams',
      tags: ['#Kalamkari', '#NaturalDyes', '#PedanaHandloom', '#SustainableFashion', '#VegetableDyed'],
      careInstructions: 'Dry clean for the first 2 washes. Wash separately in cold water with mild detergent.',
      seoDescription: 'Original Pedana Machilipatnam Kalamkari fabric hand block printed with organic vegetable dyes.',
      retailPrice: 3800.0,
      wholesalePrice: 2700.0,
      suggestedMoq: 5,
      englishTranslation: 'Machilipatnam Botanical Teak-Block Kalamkari Handloom Fabric.',
      hindiTranslation: 'मछलीपट्टनम पारंपरिक कलमकारी हाथ से छपा हुआ सूती कपड़ा - प्राकृतिक वानस्पतिक रंगों से रंगा हुआ।',
      teluguTranslation: 'మచిలీపట్నం సహజ రంగుల కలంకారీ చేనేత వస్త్రం - పెడన హస్తకళాకారుల చేతిపని.',
      bengaliTranslation: 'মছলিপত্তনম প্রাকৃতিক রঙের কলমকারী হ্যান্ডলুম টেক্সটাইল।',
      marketingCopyShort: 'Wear the beauty of flowing river canals and organic indigo with genuine Pedana Kalamkari.',
      marketingCopySocial: '🌿 Hand-carved teak blocks + fermented indigo + Krishna river washing = Pure Kalamkari Magic! 🌸✨ #Kalamkari #HandloomIndia #KalaCart',
      giClusterDetected: 'Pedana Kalamkari Cluster, Krishna District (GI Reg #19)',
      authenticityConfidence: 0.96,
    ),
    const AiGeneratedCraftData(
      title: 'Bastar Lost-Wax Bell Metal Tribal Musician Figurine',
      description: '4,000-year-old non-ferrous lost-wax metal casting technique preserved by the Ghadwa tribal guild in Kondagaon, Bastar. Modeled with bees-wax wires and encased in riverbed clay molds.',
      category: 'Brass & Metal Craft',
      materials: 'Recycled Bell Metal (Kansa Alloy), Forest Beeswax, Alluvial River Clay',
      craftTechnique: 'Lost-Wax Casting (Cire Perdue), Beeswax Wirework, Pit Furnace Firing',
      dimensions: '8" Height x 4.5" Width x 3.5" Depth',
      weight: '1.2 kg',
      tags: ['#Dhokra', '#LostWaxCasting', '#BastarArt', '#TribalMetal', '#IndusHeritage'],
      careInstructions: 'Clean with a dry brass polishing cloth. Keep away from humid moisture.',
      seoDescription: 'Authentic Bastar Dhokra lost-wax bell metal figurine handmade in Chhattisgarh tribal clusters.',
      retailPrice: 2950.0,
      wholesalePrice: 2100.0,
      suggestedMoq: 6,
      englishTranslation: 'Bastar Lost-Wax Bell Metal Tribal Musician Figurine.',
      hindiTranslation: 'बस्तर ढोकरा कांस्य धातु की पारंपरिक जनजातीय संगीतकार मूर्ति।',
      teluguTranslation: 'బస్తర్ డోక్రా లోహపు గిరిజన విగ్రహం - కోండగావ్ చేతివృత్తులు.',
      bengaliTranslation: 'বস্তার ডোকরা কাঁসা ও পিতলের আদিবাসী হস্তশিল্প মূর্তি।',
      marketingCopyShort: 'Own a direct descendant of the Indus Valley Civilization\'s Dancing Girl artistry.',
      marketingCopySocial: '🔥 4,000 years of unbroken metallurgical heritage! Every Dhokra piece is 1-of-1 because the clay mold is broken during casting. 🪔✨ #Dhokra #TribalArt #KalaCart',
      giClusterDetected: 'Kondagaon Bastar Dhokra Cluster (GI Reg #83)',
      authenticityConfidence: 0.99,
    ),
  ];

  @override
  void selectPresetSample(int index) {
    if (index >= 0 && index < _mockPresets.length) {
      state = state.copyWith(selectedSamplePresetIndex: index);
    }
  }

  @override
  void addImage(CapturedImageItem image) {
    state = state.copyWith(images: [...state.images, image]);
  }

  @override
  void removeImage(String id) {
    state = state.copyWith(images: state.images.where((i) => i.id != id).toList());
  }

  @override
  void reorderImages(int oldIndex, int newIndex) {
    final list = [...state.images];
    if (oldIndex < newIndex) {
      newIndex -= 1;
    }
    final item = list.removeAt(oldIndex);
    list.insert(newIndex, item);
    state = state.copyWith(images: list);
  }

  @override
  void toggleEnhancedBackground(String id) {
    state = state.copyWith(
      images: state.images.map((img) {
        if (img.id == id) {
          return img.copyWith(isEnhanced: !img.isEnhanced);
        }
        return img;
      }).toList(),
    );
  }

  @override
  void updateGeneratedData(AiGeneratedCraftData data) {
    state = state.copyWith(generatedData: data);
  }

  @override
  void resetStudio() {
    state = const CatalogStudioSessionState(
      stage: CatalogStudioStage.capture,
      images: [],
      generatedData: null,
      progress: 0.0,
      stageMessage: 'Ready to capture craft',
    );
  }

  @override
  Future<void> startAiProcessing() async {
    final presetData = _mockPresets[state.selectedSamplePresetIndex % _mockPresets.length];

    // Stage 1: Analyzing
    state = state.copyWith(
      stage: CatalogStudioStage.analyzing,
      progress: 0.20,
      stageMessage: 'Analyzing craft geometry, lighting & surface motifs...',
    );
    await Future.delayed(const Duration(milliseconds: 650));

    // Stage 2: Identifying
    state = state.copyWith(
      stage: CatalogStudioStage.identifying,
      progress: 0.45,
      stageMessage: 'Matching with Indian GI Cluster Database (${presetData.giClusterDetected})...',
    );
    await Future.delayed(const Duration(milliseconds: 700));

    // Stage 3: Generating
    state = state.copyWith(
      stage: CatalogStudioStage.generating,
      progress: 0.68,
      stageMessage: 'Composing artisan heritage narrative, materials & craft technique...',
    );
    await Future.delayed(const Duration(milliseconds: 700));

    // Stage 4: Translating
    state = state.copyWith(
      stage: CatalogStudioStage.translating,
      progress: 0.85,
      stageMessage: 'Translating craft listing to Hindi, Telugu & Bengali...',
    );
    await Future.delayed(const Duration(milliseconds: 650));

    // Stage 5: Pricing
    state = state.copyWith(
      stage: CatalogStudioStage.pricing,
      progress: 0.95,
      stageMessage: 'Calculating fair artisan retail & wholesale tier recommendations...',
    );
    await Future.delayed(const Duration(milliseconds: 600));

    // Stage 6: Ready
    state = state.copyWith(
      stage: CatalogStudioStage.ready,
      progress: 1.0,
      stageMessage: 'Kala-AI Craft Listing Ready for Artisan Review!',
      generatedData: presetData,
    );
  }
}

final catalogStudioProvider = StateNotifierProvider<MockCatalogStudioRepository, CatalogStudioSessionState>((ref) {
  return MockCatalogStudioRepository();
});
