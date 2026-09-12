class SupabaseConfig {
  static const String supabaseUrl = 'https://imprsuvtgqxepwzimqmc.supabase.co';
  /// Supabase publishable key. Safe to ship in the client -- it carries no
  /// privileges of its own and RLS is the boundary, exactly as the legacy anon
  /// key was.
  ///
  /// Replaces the legacy `anon` JWT. The legacy anon and service_role keys are
  /// both signed by one shared JWT secret and can only be disabled together, so
  /// the exposed service_role key could not be revoked while the app still used
  /// the legacy anon key. Moving the client to this key unblocks disabling both.
  /// Supabase also removes legacy JWT API keys at the end of 2026.
  static const String supabasePublishableKey =
      'sb_publishable_knkWRgPGlMOSU6XX31Kgbg_MlGxUzon';

  // Storage Buckets
  static const String bucketProducts = 'products';
  static const String bucketProductImages = 'product_images';
  static const String bucketProfileImages = 'profile_images';
  static const String bucketChatMedia = 'chat-media';
}
