"""
KalaCart Phase 7 — Digital Craft Museum Service Layer.
Preserves centuries of intangible cultural craftsmanship through 3D artifacts,
360° exhibition rooms, multilingual audio narrations, timelines, and live marketplace cross-linking.
"""

from typing import List, Optional, Dict, Any
from app.models.museum import (
    MuseumCollection,
    GalleryRoom,
    MuseumArtifact,
    AudioGuide,
    CraftTimelineEvent,
    MasterArtisanBio,
    MuseumCrossLinkResponse,
    XRArtifactSessionResponse,
)

# ── Sample Realistic Data Store ──────────────────────────────────────

_AUDIO_GUIDES_DATA: Dict[str, List[AudioGuide]] = {
    "art-dhokra-001": [
        AudioGuide(
            id="audio-dhokra-en",
            artifact_id="art-dhokra-001",
            language_code="en",
            language_name="English",
            narrator_name="Dr. Shashi Shekhar (National Museum Curator)",
            narration_title="The Lost-Wax Secrets of Bastar Dhokra",
            transcript="You are observing the Sacred Bull Nandi, sculpted using the 4,000-year-old cire-perdue lost wax casting method. Originating during the Indus Valley civilization, this molten brass technique allows no two sculptures to ever be identical. Master artisan Sukmati Mandavi channels five generations of tribal lore in every twisted brass filament.",
            audio_stream_url="https://assets.kalacart.in/audio/guides/dhokra_nandi_en.mp3",
            duration_seconds=115,
            is_master_artisan_voice=False,
        ),
        AudioGuide(
            id="audio-dhokra-hi",
            artifact_id="art-dhokra-001",
            language_code="hi",
            language_name="Hindi",
            narrator_name="Sukmati Mandavi (Master Dhokra Sculptor)",
            narration_title="बस्तर की ढोकरा धातु शिल्प परंपरा",
            transcript="यह नंदी मूर्ति मधुमक्खी के मोम और मिट्टी के सांचे से बनाई गई है। जब पिघला हुआ पीतल सांचे में जाता है, तो मोम पिघलकर बाहर निकल जाता है। यह शिल्प हमारे पुरखों की अमर धरोहर है।",
            audio_stream_url="https://assets.kalacart.in/audio/guides/dhokra_nandi_hi.mp3",
            duration_seconds=98,
            is_master_artisan_voice=True,
        ),
        AudioGuide(
            id="audio-dhokra-bn",
            artifact_id="art-dhokra-001",
            language_code="bn",
            language_name="Bengali",
            narrator_name="Ananya Roy",
            narration_title="বস্তারের ঐতিহ্যবাহী ডোকরা শিল্প",
            transcript="এই অপূর্ব ব্রাস নন্দী মূর্তিটি চার হাজার বছরের প্রাচীন মোম গলানো পদ্ধতিতে নির্মিত। প্রতিটি খাঁজে রয়েছে ভারতীয় লোকশিল্পের গভীর ইতিহাস।",
            audio_stream_url="https://assets.kalacart.in/audio/guides/dhokra_nandi_bn.mp3",
            duration_seconds=105,
            is_master_artisan_voice=False,
        )
    ],
    "art-pashmina-002": [
        AudioGuide(
            id="audio-pashmina-en",
            artifact_id="art-pashmina-002",
            language_code="en",
            language_name="English",
            narrator_name="Mirza Ghulam Qadir (Kashmir Heritage Guild)",
            narration_title="Royal Sozni Embroidery on Kashmiri Pashmina",
            transcript="Woven from the microscopic underfleece of Changthangi mountain goats grazing at 14,000 feet in Ladakh, this royal shawl features needlework so fine that both faces are indistinguishable. Known as Jamawar needle craft, a single master artisan worked on this centerpiece for 18 months.",
            audio_stream_url="https://assets.kalacart.in/audio/guides/pashmina_jamawar_en.mp3",
            duration_seconds=130,
            is_master_artisan_voice=True,
        ),
        AudioGuide(
            id="audio-pashmina-hi",
            artifact_id="art-pashmina-002",
            language_code="hi",
            language_name="Hindi",
            narrator_name="Kashmir Craft Trust",
            narration_title="शाही कश्मीरी पश्मीना और सोज़नी कढ़ाई",
            transcript="लद्दाख की चांगथांगी बकरियों की दुर्लभ ऊन से बुनी यह पश्मीना शॉल मुगल काल की कलात्मक भव्यता को दर्शाती है।",
            audio_stream_url="https://assets.kalacart.in/audio/guides/pashmina_jamawar_hi.mp3",
            duration_seconds=110,
            is_master_artisan_voice=False,
        )
    ],
    "art-ajrakh-003": [
        AudioGuide(
            id="audio-ajrakh-en",
            artifact_id="art-ajrakh-003",
            language_code="en",
            language_name="English",
            narrator_name="Dr. Ismail Khatri (Padma Shri Master Artisan)",
            narration_title="16 Stages of Sacred Indigo & Madder Ajrakh",
            transcript="Ajrakh, rooted in the Arabic word Azrak meaning blue, represents the universe. The stars, geometry, and river waters of Dhamadka come alive through natural indigo, pomegranate rind, and iron-fermented mud resist printing.",
            audio_stream_url="https://assets.kalacart.in/audio/guides/ajrakh_khatri_en.mp3",
            duration_seconds=125,
            is_master_artisan_voice=True,
        )
    ]
}

_TIMELINES_DATA: Dict[str, List[CraftTimelineEvent]] = {
    "DHOKRA": [
        CraftTimelineEvent(
            era="Harappan Bronze Age",
            approximate_year="2500 BCE",
            title="Indus Valley Dancing Girl",
            description="First archaeological evidence of cire-perdue lost wax metal casting unearthed at Mohenjo-daro.",
            dynasty_or_patron="Indus Valley Civilization",
            innovation="Clay core lost-wax casting technique"
        ),
        CraftTimelineEvent(
            era="Medieval Tribal Guilds",
            approximate_year="1100 CE",
            title="Bastar & Bankura Bell-Metal Guilds",
            description="Tribal metalsmith clans establish forest kilns for ritual totems, deity palanquins, and measuring bowls.",
            dynasty_or_patron="Kakatiya & Gond Monarchs",
            innovation="Twisted beeswax filament surface filigree"
        ),
        CraftTimelineEvent(
            era="GI Tag & Modern Renaissance",
            approximate_year="2008 - Present",
            title="Geographical Indication Protection",
            description="Bastar and Bengal Dhokra receive formal GI tags. KalaCart establishes digital 3D archives.",
            dynasty_or_patron="Government of India & KalaCart",
            innovation="Direct-to-consumer digital twin certification"
        )
    ],
    "PASHMINA": [
        CraftTimelineEvent(
            era="15th Century Kashmir",
            approximate_year="1420 CE",
            title="Sultan Zain-ul-Abidin's Royal Weavery",
            description="The enlightened king invites master weavers from Turkestan to establish Srinagar's royal ateliers.",
            dynasty_or_patron="Shah Mir Dynasty",
            innovation="Introduction of wooden twill tapestry looms"
        ),
        CraftTimelineEvent(
            era="Mughal Golden Age",
            approximate_year="1605 CE",
            title="Emperor Jahangir's Floral Jamawar",
            description="Court painters illustrate botanical motifs for royal doshala shawls, establishing global luxury prestige.",
            dynasty_or_patron="Mughal Empire",
            innovation="Sozni double-sided needle embroidery"
        ),
        CraftTimelineEvent(
            era="21st Century Authenticity",
            approximate_year="2022 - Present",
            title="GI Micro-DNA Authentication",
            description="Lab-tested micron purity (<15 microns) and blockchain GI tags prevent synthetic imitation.",
            dynasty_or_patron="Kashmir Craft Quality Council",
            innovation="NFC & AR museum authentication"
        )
    ],
    "AJRAKH": [
        CraftTimelineEvent(
            era="Ancient Mesopotamian Trade",
            approximate_year="2000 BCE",
            title="Indigo Resist Dyeworks of Indus",
            description="Textile fragments dyed with natural indigo and madder root traded along the ancient spice and silk routes.",
            dynasty_or_patron="Sindh & Kutch Coastal Traders",
            innovation="Natural iron and fermented jaggery dabu resists"
        ),
        CraftTimelineEvent(
            era="Rao Khengarji I Patronage",
            approximate_year="1548 CE",
            title="Khatri Community Settlement in Dhamadka",
            description="The King of Kutch grants royal patronage and water rights to Khatri master dyers.",
            dynasty_or_patron="Jadeja Dynasty of Kutch",
            innovation="16-step dual-sided block printing sync"
        )
    ]
}

_ARTIFACTS_DATA: List[MuseumArtifact] = [
    MuseumArtifact(
        id="art-dhokra-001",
        collection_id="coll-sacred-metals",
        gallery_room_id="room-bastar-tribal",
        artifact_code="KC-MUS-DHK-001",
        title="Ceremonial Sacred Nandi of Bastar",
        craft_category="Dhokra Bell Metal",
        origin_district="Bastar",
        origin_state="Chhattisgarh",
        historical_period="18th Century CE (Traditional Continuation)",
        estimated_creation_year="c. 1780 CE / Contemporary Lineage",
        medium_and_materials="Lost-wax cast brass, beeswax core, riverbed alluvial clay, mustard seed oil patina",
        dimension_specs="34 cm (H) x 48 cm (L) x 22 cm (W) — 8.4 kg",
        description="A masterwork of tribal lost-wax bell metal casting representing Nandi, the sacred bull vahana of Lord Shiva. The hollow torso is adorned with intricately coiled brass filigree wires resembling sacred tribal spiral cosmology.",
        historical_significance="Direct physical descendant of the Mohenjo-daro bronze casting lineage. Created without reusable molds, meaning this exact physical topology is unique in the world.",
        master_artisan_name="Sukmati Mandavi & Ancestors",
        master_artisan_bio="Sukmati Mandavi is a 5th generation Dhokra sculptor from Jagdalpur, Chhattisgarh, recipient of the National Master Craftsperson Award.",
        master_artisan_awards=["National Master Craftsperson Award", "State Shilp Guru Honor"],
        model_3d_glb_url="https://assets.kalacart.in/models/museum/dhokra_nandi_3d.glb",
        model_3d_usdz_url="https://assets.kalacart.in/models/museum/dhokra_nandi_3d.usdz",
        thumbnail_image_url="https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800&auto=format&fit=crop&q=80",
        multi_angle_images=[
            "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582562124811-c09040d0a901?w=800&auto=format&fit=crop&q=80"
        ],
        xr_ar_supported=True,
        gi_tag_registered=True,
        preservation_status="Pristine Heritage",
        linked_product_ids=["prod-dhokra-nandi-01", "prod-dhokra-lamp-02"],
        audio_guides=_AUDIO_GUIDES_DATA.get("art-dhokra-001", []),
        timeline=_TIMELINES_DATA.get("DHOKRA", []),
        artisan_details=MasterArtisanBio(
            name="Sukmati Mandavi",
            generation=5,
            birthplace="Jagdalpur, Bastar, Chhattisgarh",
            active_years="1998 - Present",
            awards=["National Master Craftsperson Award", "State Shilp Guru Honor"],
            quote="When fire kisses the clay, our ancestors whisper through the brass.",
            photograph_url="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&auto=format&fit=crop&q=80",
            heritage_lineage="Ghadwa Metalsmith Clan of Central India"
        )
    ),
    MuseumArtifact(
        id="art-pashmina-002",
        collection_id="coll-royal-textiles",
        gallery_room_id="room-kashmir-durbar",
        artifact_code="KC-MUS-PSH-002",
        title="Royal Jamawar Kani Pashmina Shawl",
        craft_category="Kashmir Pashmina Weaving",
        origin_district="Srinagar",
        origin_state="Jammu and Kashmir",
        historical_period="Late Mughal Era (Patronized by Court Weavers)",
        estimated_creation_year="c. 1820 CE / Heirloom Master Re-creation",
        medium_and_materials="100% Grade-A Changthangi Cashmere wool (12.5 micron), vegetable madder, walnut husk & saffron dye",
        dimension_specs="200 cm x 100 cm — 210 grams",
        description="Handwoven on traditional Kashmiri wooden twill looms using over 150 individual wooden needle bobbins (Kani). The paisley floral kaleidoscope depicts the Mughal gardens of Shalimar Bagh.",
        historical_significance="Took 18 months of uninterrupted handwork by two master weavers. Certified by the Craft Development Institute under GI Registration No. 46.",
        master_artisan_name="Mirza Ghulam Qadir",
        master_artisan_bio="Mirza Ghulam Qadir is a 6th generation Kani weaver whose ancestral lineage produced royal shawls for Maharaja Ranjit Singh.",
        master_artisan_awards=["Padma Shri Nominee", "Sant Kabir Award"],
        model_3d_glb_url="https://assets.kalacart.in/models/museum/pashmina_shawl_3d.glb",
        model_3d_usdz_url="https://assets.kalacart.in/models/museum/pashmina_shawl_3d.usdz",
        thumbnail_image_url="https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=800&auto=format&fit=crop&q=80",
        multi_angle_images=[
            "https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=800&auto=format&fit=crop&q=80"
        ],
        xr_ar_supported=True,
        gi_tag_registered=True,
        preservation_status="Pristine Heritage",
        linked_product_ids=["prod-pashmina-kani-01", "prod-pashmina-stole-02"],
        audio_guides=_AUDIO_GUIDES_DATA.get("art-pashmina-002", []),
        timeline=_TIMELINES_DATA.get("PASHMINA", []),
        artisan_details=MasterArtisanBio(
            name="Mirza Ghulam Qadir",
            generation=6,
            birthplace="Kanihama, Kashmir",
            active_years="1982 - Present",
            awards=["Sant Kabir Award", "National Master Award"],
            quote="Pashmina is not fabric; it is warm mountain wind captured in silk-soft wool.",
            photograph_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80",
            heritage_lineage="Royal Srinagar Kani Weavers Guild"
        )
    ),
    MuseumArtifact(
        id="art-ajrakh-003",
        collection_id="coll-royal-textiles",
        gallery_room_id="room-kutch-courtyard",
        artifact_code="KC-MUS-AJK-003",
        title="Cosmic Star Ajrakh 16-Stage Wall Tapestry",
        craft_category="Ajrakh Block Printing",
        origin_district="Kachchh",
        origin_state="Gujarat",
        historical_period="Kutch Princely State Tradition",
        estimated_creation_year="c. 1910 CE / Contemporary Revival",
        medium_and_materials="Handspun wild organic cotton, pure Indigofera tinctoria, Rubia cordifolia (Indian madder), tamarind seed gum",
        dimension_specs="280 cm x 180 cm — 650 grams",
        description="A monumental 16-stage hand-block printed textile featuring symmetrical celestial star lattices. Printed identically on both faces using carved teakwood blocks aligned to sub-millimeter precision.",
        historical_significance="Ajrakh is sacred to the Maldhari pastoralist community of the Rann of Kutch. The blue symbolizes the infinite cosmos and the crimson signifies earth's volcanic vitality.",
        master_artisan_name="Dr. Ismail Mohammad Khatri",
        master_artisan_bio="Dr. Ismail Khatri is a world-renowned Khatri master artisan awarded an honorary doctorate by the University of Leicester for reviving natural vegetable dyes.",
        master_artisan_awards=["Padma Shri", "Honorary Doctorate in Arts", "UNESCO Seal of Excellence"],
        model_3d_glb_url="https://assets.kalacart.in/models/museum/ajrakh_tapestry_3d.glb",
        model_3d_usdz_url="https://assets.kalacart.in/models/museum/ajrakh_tapestry_3d.usdz",
        thumbnail_image_url="https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=800&auto=format&fit=crop&q=80",
        multi_angle_images=[
            "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=800&auto=format&fit=crop&q=80"
        ],
        xr_ar_supported=True,
        gi_tag_registered=True,
        preservation_status="Pristine Heritage",
        linked_product_ids=["prod-ajrakh-dupatta-01", "prod-ajrakh-bedspread-02"],
        audio_guides=_AUDIO_GUIDES_DATA.get("art-ajrakh-003", []),
        timeline=_TIMELINES_DATA.get("AJRAKH", []),
        artisan_details=MasterArtisanBio(
            name="Dr. Ismail Mohammad Khatri",
            generation=9,
            birthplace="Dhamadka, Kutch, Gujarat",
            active_years="1975 - Present",
            awards=["Padma Shri", "UNESCO Seal of Excellence"],
            quote="Our colors live and breathe with the river, the sun, and the desert stars.",
            photograph_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&auto=format&fit=crop&q=80",
            heritage_lineage="Khatri Dyers Guild of Dhamadka & Ajrakhpur"
        )
    ),
    MuseumArtifact(
        id="art-bluepottery-004",
        collection_id="coll-sacred-metals",
        gallery_room_id="room-jaipur-palace",
        artifact_code="KC-MUS-BLP-004",
        title="Royal Jaipur Cobalt Blue Glazed Urn",
        craft_category="Jaipur Blue Pottery",
        origin_district="Jaipur",
        origin_state="Rajasthan",
        historical_period="Sawai Ram Singh II Era (1835–1880 CE)",
        estimated_creation_year="c. 1875 CE",
        medium_and_materials="Quartz stone powder, Fuller's earth (Multani Mitti), glass cullet, natural gum, cobalt oxide blue glaze (No clay used)",
        dimension_specs="55 cm (H) x 32 cm (Diameter) — 4.2 kg",
        description="A turquoise and deep cobalt urn fired in low-temperature wood kilns. Unlike traditional pottery, Jaipur Blue Pottery is made without clay, utilizing Egyptian paste methods refined during the Silk Road era.",
        historical_significance="Commissioned during the reign of Maharaja Sawai Ram Singh II, who sent Rajasthani artisans to Delhi to master Persian turquoise glazing.",
        master_artisan_name="Kripal Singh Shekhawat & Disciples",
        master_artisan_bio="Padma Shri Kripal Singh Shekhawat was the revivalist pioneer of modern Jaipur Blue Pottery, inventing 25 new mineral glaze pigments.",
        master_artisan_awards=["Padma Shri", "Shilp Guru"],
        model_3d_glb_url="https://assets.kalacart.in/models/museum/blue_pottery_urn_3d.glb",
        model_3d_usdz_url="https://assets.kalacart.in/models/museum/blue_pottery_urn_3d.usdz",
        thumbnail_image_url="https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=800&auto=format&fit=crop&q=80",
        multi_angle_images=[
            "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=800&auto=format&fit=crop&q=80"
        ],
        xr_ar_supported=True,
        gi_tag_registered=True,
        preservation_status="Pristine Heritage",
        linked_product_ids=["prod-bluepottery-vase-01"],
        audio_guides=[],
        timeline=[],
        artisan_details=MasterArtisanBio(
            name="Kripal Kumbh Guild",
            generation=4,
            birthplace="Jaipur, Rajasthan",
            active_years="1960 - Present",
            awards=["Padma Shri Legacy", "National Award"],
            quote="Quartz holds the crystal light of Rajasthan's royal palaces.",
            photograph_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&auto=format&fit=crop&q=80",
            heritage_lineage="Royal Jaipur Ceramic Masters"
        )
    )
]

_GALLERY_ROOMS_DATA: List[GalleryRoom] = [
    GalleryRoom(
        id="room-bastar-tribal",
        collection_id="coll-sacred-metals",
        room_code="ROOM-BASTAR",
        room_name="Bastar Sacred Bronze & Forest Foundry",
        architectural_theme="Tribal Sal Forest Courtyard with Fire Hearth",
        panorama_360_url="https://assets.kalacart.in/panoramas/bastar_sal_forest_360.jpg",
        ambient_audio_url="https://assets.kalacart.in/audio/ambient/forest_hearth_chimes.mp3",
        lighting_preset="FirelightCharcoalWarm",
        virtual_hall_capacity=500,
        artifacts_count=1,
        artifacts=[_ARTIFACTS_DATA[0]]
    ),
    GalleryRoom(
        id="room-kashmir-durbar",
        collection_id="coll-royal-textiles",
        room_code="ROOM-KASHMIR",
        room_name="Pari Mahal Royal Silk & Wool Pavilion",
        architectural_theme="Carved Pinjrakari Walnut Wood & Dal Lake View",
        panorama_360_url="https://assets.kalacart.in/panoramas/pari_mahal_360.jpg",
        ambient_audio_url="https://assets.kalacart.in/audio/ambient/santoor_spring_breeze.mp3",
        lighting_preset="MistyHimalayanMorning",
        virtual_hall_capacity=600,
        artifacts_count=1,
        artifacts=[_ARTIFACTS_DATA[1]]
    ),
    GalleryRoom(
        id="room-kutch-courtyard",
        collection_id="coll-royal-textiles",
        room_code="ROOM-KUTCH",
        room_name="Kutch Desert Celestial Dyers Court",
        architectural_theme="White Rann Moonlit Bhunga with Mud Mirror Lippan Art",
        panorama_360_url="https://assets.kalacart.in/panoramas/kutch_bhunga_360.jpg",
        ambient_audio_url="https://assets.kalacart.in/audio/ambient/desert_wind_morchang.mp3",
        lighting_preset="DesertStarlightIndigo",
        virtual_hall_capacity=500,
        artifacts_count=1,
        artifacts=[_ARTIFACTS_DATA[2]]
    ),
    GalleryRoom(
        id="room-jaipur-palace",
        collection_id="coll-sacred-metals",
        room_code="ROOM-JAIPUR",
        room_name="City Palace Cobalt Glaze Gallery",
        architectural_theme="Pink City Jharokha Marble Lattice Pavilion",
        panorama_360_url="https://assets.kalacart.in/panoramas/jaipur_jharokha_360.jpg",
        ambient_audio_url="https://assets.kalacart.in/audio/ambient/sarangi_court_music.mp3",
        lighting_preset="GoldenHourWarmth",
        virtual_hall_capacity=750,
        artifacts_count=1,
        artifacts=[_ARTIFACTS_DATA[3]]
    )
]

_COLLECTIONS_DATA: List[MuseumCollection] = [
    MuseumCollection(
        id="coll-sacred-metals",
        collection_code="COL-METALS",
        title="Sacred Bronzes & Ancient Metalware of India",
        subtitle="4,000 Years from the Indus Valley Dancing Girl to Bastar Lost-Wax Foundry",
        description="An extraordinary curation of Indian metallurgical masterworks: sacred Dhokra icons, Bidriware silver inlay, Chola bronze icons, and Moradabad brass repoussé.",
        curator_name="KalaCart National Heritage Board",
        cover_image_url="https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=800&auto=format&fit=crop&q=80",
        banner_image_url="https://images.unsplash.com/photo-1582562124811-c09040d0a901?w=1600&auto=format&fit=crop&q=80",
        historical_era="2500 BCE – Contemporary Living Heritage",
        display_order=1,
        is_featured=True,
        artifact_count=2,
        gallery_rooms=[_GALLERY_ROOMS_DATA[0], _GALLERY_ROOMS_DATA[3]]
    ),
    MuseumCollection(
        id="coll-royal-textiles",
        collection_code="COL-TEXTILES",
        title="Royal Looms: Imperial Weaves & Sacred Dyes",
        subtitle="The Golden Threads of Banarasi, Kashmiri Pashmina, and Kutch Ajrakh",
        description="A sensory pilgrimage through India's imperial textile corridors: needle-fine Cashmere shawls, warp-weft silk brocades, and multi-stage vegetable dye cosmic prints.",
        curator_name="Craft Council of India & KalaCart",
        cover_image_url="https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=800&auto=format&fit=crop&q=80",
        banner_image_url="https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=1600&auto=format&fit=crop&q=80",
        historical_era="1400 CE – Present",
        display_order=2,
        is_featured=True,
        artifact_count=2,
        gallery_rooms=[_GALLERY_ROOMS_DATA[1], _GALLERY_ROOMS_DATA[2]]
    )
]


class MuseumService:
    @staticmethod
    def list_collections() -> List[MuseumCollection]:
        return _COLLECTIONS_DATA

    @staticmethod
    def get_collection_by_id(collection_id: str) -> Optional[MuseumCollection]:
        for col in _COLLECTIONS_DATA:
            if col.id == collection_id or col.collection_code.lower() == collection_id.lower():
                return col
        return None

    @staticmethod
    def list_gallery_rooms() -> List[GalleryRoom]:
        return _GALLERY_ROOMS_DATA

    @staticmethod
    def get_gallery_room_by_id(room_id: str) -> Optional[GalleryRoom]:
        for room in _GALLERY_ROOMS_DATA:
            if room.id == room_id or room.room_code.lower() == room_id.lower():
                return room
        return None

    @staticmethod
    def list_artifacts(
        craft_category: Optional[str] = None,
        state: Optional[str] = None,
        collection_id: Optional[str] = None
    ) -> List[MuseumArtifact]:
        res = _ARTIFACTS_DATA
        if craft_category:
            res = [a for a in res if craft_category.lower() in a.craft_category.lower()]
        if state:
            res = [a for a in res if a.origin_state.lower() == state.lower()]
        if collection_id:
            res = [a for a in res if a.collection_id == collection_id]
        return res

    @staticmethod
    def get_artifact_by_id(artifact_id: str) -> Optional[MuseumArtifact]:
        for a in _ARTIFACTS_DATA:
            if a.id == artifact_id or a.artifact_code.lower() == artifact_id.lower():
                return a
        return None

    @staticmethod
    def get_audio_guides(artifact_id: str, language_code: Optional[str] = None) -> List[AudioGuide]:
        guides = _AUDIO_GUIDES_DATA.get(artifact_id, [])
        if language_code:
            guides = [g for g in guides if g.language_code.lower() == language_code.lower()]
        return guides

    @staticmethod
    def get_craft_timeline(craft_code: str) -> List[CraftTimelineEvent]:
        code = craft_code.upper()
        if code in _TIMELINES_DATA:
            return _TIMELINES_DATA[code]
        # Fallback search by substring
        for k, v in _TIMELINES_DATA.items():
            if k in code or code in k:
                return v
        return []

    @staticmethod
    def get_xr_session(artifact_id: str) -> Optional[XRArtifactSessionResponse]:
        art = MuseumService.get_artifact_by_id(artifact_id)
        if not art:
            return None
        return XRArtifactSessionResponse(
            artifact_id=art.id,
            title=art.title,
            model_3d_glb_url=art.model_3d_glb_url,
            model_3d_usdz_url=art.model_3d_usdz_url,
            scale_factor=1.0,
            initial_rotation=[0.0, 45.0, 0.0],
            ar_placement_mode="surface_horizontal",
            audio_narration_url=art.audio_guides[0].audio_stream_url if art.audio_guides else None,
            recommended_lighting="museum_spotlight"
        )

    @staticmethod
    def cross_link_artifact_to_products(artifact_id: str) -> Optional[MuseumCrossLinkResponse]:
        art = MuseumService.get_artifact_by_id(artifact_id)
        if not art:
            return None

        sample_marketplace_products = [
            {
                "product_id": f"prod-{art.craft_category.lower().replace(' ', '-')}-01",
                "title": f"Authentic Handcrafted {art.craft_category} Piece",
                "artisan_name": art.master_artisan_name or "Verified Master Artisan",
                "price_inr": 4850.0,
                "rating": 4.9,
                "in_stock": True,
                "gi_certified": True,
                "thumbnail": art.thumbnail_image_url,
                "badge": "GI Tagged Living Heritage"
            },
            {
                "product_id": f"prod-{art.craft_category.lower().replace(' ', '-')}-02",
                "title": f"Master Edition {art.craft_category} Collectible",
                "artisan_name": art.master_artisan_name or "National Awardee Artisan",
                "price_inr": 12200.0,
                "rating": 5.0,
                "in_stock": True,
                "gi_certified": True,
                "thumbnail": art.thumbnail_image_url,
                "badge": "Master Collector Line"
            }
        ]

        return MuseumCrossLinkResponse(
            artifact_id=art.id,
            artifact_title=art.title,
            craft_category=art.craft_category,
            origin_district=art.origin_district,
            origin_state=art.origin_state,
            linked_marketplace_products=sample_marketplace_products,
            educational_note=f"Buying verified {art.craft_category} products directly sustains master artisan families in {art.origin_district}, {art.origin_state} and ensures traditional technique preservation."
        )

    @staticmethod
    def cross_link_product_to_museum(product_id: str) -> Dict[str, Any]:
        # Cross link search by product id or category
        matched_artifact = _ARTIFACTS_DATA[0]
        if "pashmina" in product_id.lower() or "shawl" in product_id.lower():
            matched_artifact = _ARTIFACTS_DATA[1]
        elif "ajrakh" in product_id.lower() or "block" in product_id.lower():
            matched_artifact = _ARTIFACTS_DATA[2]
        elif "pottery" in product_id.lower() or "blue" in product_id.lower():
            matched_artifact = _ARTIFACTS_DATA[3]

        return {
            "product_id": product_id,
            "museum_heritage_verified": True,
            "matched_museum_artifact": {
                "artifact_id": matched_artifact.id,
                "artifact_code": matched_artifact.artifact_code,
                "title": matched_artifact.title,
                "historical_period": matched_artifact.historical_period,
                "craft_category": matched_artifact.craft_category,
                "origin_state": matched_artifact.origin_state,
                "museum_collection_name": "Sacred Bronzes & Imperial Corridors",
                "model_3d_glb_url": matched_artifact.model_3d_glb_url,
                "audio_narration_count": len(matched_artifact.audio_guides),
            },
            "lineage_certificate": "Authenticated by KalaCart Digital Craft Museum & National Heritage Board"
        }
