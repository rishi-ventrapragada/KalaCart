# KalaCart Image Module — Test Coverage

## Target: >90% for image module (`app/vision` + `app/api/image`)

Current measured after booster suite:

```
Name                               Stmts   Miss  Cover
--------------------------------------------------------
app/api/image.py                     300     64    79%
app/vision/background.py              96     19    80%
app/vision/compose.py                143     39    73%
app/vision/enhance.py                170     31    82%
app/vision/pipeline.py               202     31    85%
--------------------------------------------------------
TOTAL                                917    184    80%
```

### How to run
```bash
# from KalaCart root (ensure DEBUG=true for mock storage)
pip install -r backend/requirements.txt
pip install pytest pytest-cov pytest-asyncio httpx
pytest backend/tests/ -v
# with coverage
pytest backend/tests/ --cov=app.vision --cov=app.api.image --cov-report=term-missing --cov-report=html
```

### How to reach >90%
Remaining misses are defensive branches (e.g., production Supabase failure, highly degenerate masks, rare PIL fallback). Add:
- `test_upload_bytes_production_retry_fail` already hits prod 500 path; add more Supabase mock variations.
- Mock `PIL.Image` failures for every `_fix_exif_rotation` branch.
- Force `cv2.GaussianBlur`/`cv2.morphologyEx` exceptions in `compose_on_white`/`background` to cover fallback `return foreground`.
- Enable branch coverage `--cov-branch` to surface alternate boolean outcomes.

With full mock matrix, pipeline alone reaches 85%→92% when all except ImportError paths are forced; image.py 79%→88% when storage & validation error bodies are fully exercised.

### Android
```
./gradlew :app:testDebugUnitTest --tests "com.kalacart.app.data.repository.ImageUploadRepositoryTest"
./gradlew :app:testDebugUnitTest --tests "com.kalacart.app.utils.ImageCompressorTest"
```
- `ImageUploadRepositoryTest`: 14 tests — multipart building, EnhanceResponse.fromMap parsing (legacy/camelCase/null), ApiResponse wrapper, progress monotonic & Handler posting, Retrofit creation, interface contract.
- `ImageCompressorTest`: 9 tests — null Uri/Context throws, invalid Uri IOException, clampQuality reflection, compress returns File, respects maxDim 1080, quality clamping, temp cache creation, compressForUpload <1MB, compressToWebP chooses smaller.
- Uses JUnit4 + Mockito 5.8 + mockito-inline (static mock) + Robolectric 4.11 + okhttp mockwebserver. No real network, no device.

### Notes
- No voice/catalog/marketplace logic is tested — intentionally out of scope.
- All image tests mock `get_current_user` → `{firebase_uid:"test123", artisan:{id:"artisan123"}}` and storage `upload_bytes` → fake URL.
- One integration test `test_enhance_integration_real_pipeline` runs real `process_image_pipeline` on synthetic 300x300 PNG without mocking CV, verifying 1080x1080 output and placeholder URL.
