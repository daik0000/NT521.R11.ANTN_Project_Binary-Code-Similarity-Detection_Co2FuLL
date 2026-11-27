# Stage-0 evaluation (design §8.3)

| Tiêu chí | Bản clean (baseline) | Bản obfuscated trước xử lý | Sau xử lý | Pass? |
|---|---|---|---|---|
| Số imports tĩnh tìm được (import hiding: test_hidden) | 7 | 2 | 9 (sau recover) | ✅ |
| Strings đọc được (/8 literal, OLLVM -sobf) | 8 | 0 | 8 (sau recover) | ✅ |
| Pseudocode có cấu trúc rõ (greet/classify/duplicate_message) | ✅ | ❌ (dispatcher/state) | ✅ | ✅ |
| File entropy | 1.94 | 3.44 | 3.44 (CFF không đổi entropy) | ✅ |
| Entropy sau unpack (test_ollvm_upx) | — | 7.13 | 3.44 | ✅ |

## Per-sample

| Sample | Status | Signals | Entropy (→ after unpack) | Unpack | Static imports | Recovered APIs | Literals static → after | Flattened funcs | Patches | Opaque globals | Time (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| test_clean | bypassed |  | 1.9351 | — | 7 | — | 8 → 8 | — | 0 | 0 | 0.07 |
| test_clean_O0 | normalized |  | 2.0334 → 2.0334 | none | 8 | — | 8 → 8 | — | 0 | 0 | 14.38 |
| test_ollvm | normalized | cff_pattern, bcf_pattern | 3.4424 → 3.4424 | none | 8 | — | 8 → 8 | greet, classify, duplicate_message | 36 | 6 | 15.18 |
| test_ollvm_sobf | normalized | cff_pattern, bcf_pattern | 3.0237 → 3.0237 | none | 8 | — | 0 → 8 | classify | 19 | 2 | 15.16 |
| test_ollvm_upx | normalized | high_entropy, few_imports, packer_signature | 7.132 → 3.4424 | upx | 0 | — | 2 → 2 | greet, classify, duplicate_message | 36 | 6 | 14.86 |
| test_hidden | normalized | few_imports | 1.9589 → 1.9589 | none | 2 | free, malloc, memset, puts, snprintf, strcpy, strlen | 0 → 0 | — | 0 | 0 | 14.19 |

## Pseudocode per function (lines / if / loops / while(true) / state consts / BCF refs)

| Function | clean -O0 | OLLVM raw | OLLVM deobf | -sobf deobf | UPX deobf | same calls as clean? |
|---|---|---|---|---|---|---|
| greet | 9 / 0 / 0 / 0 / 0 / 0 | 82 / 4 / 4 / 2 / 4 / 7 | 17 / 0 / 0 / 0 / 0 / 0 | 9 / 0 / 0 / 0 / 0 / 0 | 17 / 0 / 0 / 0 / 0 / 0 | ✅ |
| classify | 21 / 2 / 1 / 0 / 0 / 0 | 170 / 40 / 9 / 8 / 28 / 40 | 21 / 2 / 1 / 0 / 0 / 0 | 21 / 2 / 1 / 0 / 0 / 0 | 21 / 2 / 1 / 0 / 0 / 0 | ✅ |
| duplicate_message | 10 / 0 / 0 / 0 / 0 / 0 | 90 / 4 / 4 / 2 / 12 / 7 | 35 / 0 / 0 / 0 / 0 / 0 | 10 / 0 / 0 / 0 / 0 / 0 | 35 / 0 / 0 / 0 / 0 / 0 | ✅ |

test_hidden pseudocode uses recovered import labels: ptr_free, ptr_malloc, ptr_memset, ptr_puts, ptr_snprintf, ptr_strcpy, ptr_strlen
