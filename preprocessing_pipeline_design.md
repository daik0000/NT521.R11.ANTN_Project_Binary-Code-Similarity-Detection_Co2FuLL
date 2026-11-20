# Binary Normalization Pre-processing Pipeline
## Design Specification for Co2FuLL Enhancement

> **Mục tiêu:** Thêm một stage tiền xử lý độc lập trước pipeline Co2FuLL gốc, giúp phục hồi binary bị obfuscate về dạng "clean enough" để Candidate Retrieval và LLM Verification hoạt động hiệu quả. Không chỉnh sửa bất kỳ file nào trong repo Co2FuLL gốc.

---

## 1. Vị trí trong repo

```
Co2FuLL-public/              ← repo gốc, KHÔNG CHỈNH SỬA
│
preprocessing/               ← toàn bộ code mới nằm ở đây
│
├── README.md                ← file này
├── requirements.txt
├── setup.sh                 ← script cài môi trường
│
├── detect.py                ← 0.1 Obfuscation Signal Check
├── unpack.py                ← 0.2a Packing Recovery
├── recover_imports.py       ← 0.2b Import & String Recovery
├── deobfuscate_cfg.py       ← 0.2c CFG Deobfuscation (Ghidra wrapper)
├── run_pipeline.py          ← entry point: chạy toàn bộ stage 0
│
├── ghidra_scripts/
│   └── deobfuscate_headless.py  ← Ghidra headless script (CFG deobfuscation)
│
├── qiling_scripts/
│   ├── dump_unpacked.py     ← Qiling: OEP detect + memory dump
│   └── hook_imports.py      ← Qiling: hook GetProcAddress/LoadLibrary
│
└── output/                  ← thư mục output (tự tạo khi chạy)
    └── <binary_name>/
        ├── normalized.bin       ← binary sau unpack (nếu có)
        ├── recovered_imports.json
        ├── recovered_strings.json
        └── clean_pseudocode/
            └── <func_addr>.c    ← pseudocode đã deobfuscate
```

---

## 2. Tổng quan pipeline

```
[Input: Binary file (.exe / ELF / .dll)]
         │
         ▼
┌─────────────────────────────────────┐
│  STEP 0.1 — Obfuscation Detection   │  (~2ms, không tốn kém)
│                                     │
│  Kiểm tra các signal:               │
│  • File entropy > 7.0               │
│  • Số lượng imports tĩnh < 5        │
│  • Tỉ lệ printable strings thấp     │
│  • CFF dispatcher pattern           │
│                                     │
│  Output: is_obfuscated (bool)       │
└──────────────┬──────────────────────┘
               │
        ┌──────┴───────┐
        │ Obfuscated?  │
        └──────┬───────┘
     NO        │        YES
     │         │         │
     ▼         │         ▼
  [BYPASS]     │  ┌──────────────────────────────┐
  Pass binary  │  │ STEP 0.2a — Unpack           │
  thẳng vào    │  │                              │
  Co2FuLL      │  │ • Thử UPX unpack             │
               │  │ • Nếu fail → Qiling emulate  │
               │  │   → detect OEP               │
               │  │   → dump memory tại OEP      │
               │  │                              │
               │  │ Output: normalized.bin       │
               │  │ (= input binary nếu ko packed│
               │  └──────────────┬───────────────┘
               │                 │
               │                 ▼
               │  ┌──────────────────────────────┐
               │  │ STEP 0.2b — Import & String  │
               │  │            Recovery          │
               │  │                              │
               │  │ • FLOSS: extract encoded str │
               │  │ • Qiling: hook API resolution│
               │  │   GetProcAddress/LoadLibrary │
               │  │   dlopen/dlsym (Linux)       │
               │  │                              │
               │  │ Output:                      │
               │  │  recovered_imports.json      │
               │  │  recovered_strings.json      │
               │  └──────────────┬───────────────┘
               │                 │
               │                 ▼
               │  ┌──────────────────────────────┐
               │  │ STEP 0.2c — CFG Deobfuscation│
               │  │                              │
               │  │ • Ghidra headless +          │
               │  │   Python script:             │
               │  │   - Unflatten CFF (OLLVM)    │
               │  │   - Remove BCF/opaque preds  │
               │  │   - Export decompiled code   │
               │  │                              │
               │  │ Output:                      │
               │  │  clean pseudocode per func   │
               │  └──────────────┬───────────────┘
               │                 │
               └────────┬────────┘
                        ▼
         ┌──────────────────────────────┐
         │  STEP 0.3 — Feed to Co2FuLL  │
         │                              │
         │ • Merge recovered_imports    │
         │   vào feature extraction     │
         │ • Merge recovered_strings    │
         │ • Re-build Dependency Graph  │
         │ • Pass clean pseudocode      │
         │   thay thế output Ghidra gốc│
         └──────────────────────────────┘
                        │
                        ▼
            [Co2FuLL Pipeline gốc]
            ① Candidate Retrieval
            ② LLM Verification
```

---

## 3. Đầu vào và Đầu ra

### Input
| Thành phần | Mô tả |
|---|---|
| `binary_path` | Đường dẫn tới file binary cần phân tích (PE/ELF) |
| `arch` | Kiến trúc: `x86`, `x86_64`, `arm`, `arm64`, `mips` |
| `os_type` | `windows` hoặc `linux` |
| `rootfs_path` | Đường dẫn tới rootfs cho Qiling (Windows/Linux) |

### Output
| File | Mô tả | Dùng ở đâu trong Co2FuLL |
|---|---|---|
| `normalized.bin` | Binary sau khi unpack (nếu bị packed) | Thay thế input cho Ghidra |
| `recovered_imports.json` | Dict `{addr: "API_name"}` recover được | Bổ sung vào DG construction |
| `recovered_strings.json` | List strings decrypt được | Bổ sung vào DG construction |
| `clean_pseudocode/<addr>.c` | Pseudocode sau deobfuscate per function | Thay thế pseudocode cho LLM |

---

## 4. Môi trường và Dependencies

### 4.1 Yêu cầu hệ thống
- OS: Ubuntu 20.04+ hoặc Kali Linux
- Python: 3.9+
- Java: 17+ (bắt buộc cho Ghidra)
- RAM: tối thiểu 8GB (Qiling emulation + Ghidra headless)

### 4.2 Python packages

```txt
# requirements.txt
qiling>=1.4.6
flare-floss>=3.0.0
pefile>=2023.2.7
pyelftools>=0.29
capstone>=5.0.0
unicorn>=2.0.0
lief>=0.14.0
z3-solver>=4.12.0
click>=8.1.0
tqdm>=4.65.0
```

### 4.3 External tools

| Tool | Version | Link | Ghi chú |
|---|---|---|---|
| **Ghidra** | 11.x | https://ghidra-sre.org | Free, NSA. Cần Java 17+ |
| UPX | 4.x | https://github.com/upx/upx | `apt install upx-ucl` |
| FLOSS | 3.x | https://github.com/mandiant/flare-floss | `pip install flare-floss` |
| Qiling rootfs | - | https://github.com/qilingframework/rootfs | Cần để emulate Windows/Linux |

> **Lưu ý Ghidra:** Ghidra không cần license. Download bản release từ https://ghidra-sre.org, giải nén, trỏ `GHIDRA_HOME` vào thư mục đó là dùng được headless ngay.

### 4.4 Setup script

```bash
#!/bin/bash
# setup.sh

echo "[*] Cài Java 17 (bắt buộc cho Ghidra)..."
sudo apt-get install -y openjdk-17-jdk

echo "[*] Download Ghidra..."
GHIDRA_VERSION="11.1.2"
GHIDRA_URL="https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VERSION}_build/ghidra_${GHIDRA_VERSION}_PUBLIC_20240709.zip"
wget -q "$GHIDRA_URL" -O /tmp/ghidra.zip
unzip -q /tmp/ghidra.zip -d ./tools/
export GHIDRA_HOME="$(pwd)/tools/ghidra_${GHIDRA_VERSION}_PUBLIC"
echo "export GHIDRA_HOME=$GHIDRA_HOME" >> ~/.bashrc

echo "[*] Cài Python packages..."
pip install -r requirements.txt

echo "[*] Cài UPX..."
sudo apt-get install -y upx-ucl

echo "[*] Cài FLOSS..."
pip install flare-floss

echo "[*] Download Qiling rootfs..."
git clone https://github.com/qilingframework/rootfs.git ./qiling_rootfs

echo "[*] Done. Kiểm tra GHIDRA_HOME trong config.py trước khi chạy."
```

---

## 5. Mô tả chi tiết từng module

### 5.1 `detect.py` — Obfuscation Signal Check

**Mục đích:** Phân loại nhanh binary có dấu hiệu obfuscation không. Nếu không → bypass toàn bộ stage 0.

**Logic:**

```python
def check_obfuscation_signals(binary_path: str) -> bool:
    """
    Trả về True nếu binary có dấu hiệu obfuscation.
    Dùng kết hợp nhiều heuristic, không cần 100% chính xác.
    Mục tiêu: false negative thấp (không bỏ sót obfuscated binary).
    """
    signals = []

    # Signal 1: File entropy
    # Binary clean thường có entropy 5.0–6.5
    # Packed binary thường > 7.0
    entropy = calc_file_entropy(binary_path)
    signals.append(("high_entropy", entropy > 7.0))

    # Signal 2: Import count thấp
    # Binary thực dùng ít nhất 10–20 imports
    # Nhóm 2 (import hiding) thường chỉ có LoadLibrary + GetProcAddress
    import_count = count_static_imports(binary_path)
    signals.append(("few_imports", import_count < 5))

    # Signal 3: Tỉ lệ printable strings thấp
    # Binary clean thường có nhiều strings đọc được
    # Packed/encrypted binary hầu như không có
    string_density = calc_string_density(binary_path)
    signals.append(("low_strings", string_density < 0.05))

    # Signal 4: CFF pattern — dispatcher + switch variable
    # Phát hiện qua pattern matching trên disassembly (capstone)
    has_cff = detect_cff_pattern(binary_path)
    signals.append(("cff_pattern", has_cff))

    # Nếu có BẤT KỲ signal nào → xử lý
    return any(flag for _, flag in signals)
```

**Lưu ý:** Độ chính xác detection không cần cao — sai về phía false positive (chạy thừa stage 0 trên binary clean) thì có overhead nhỏ, nhưng không sai kết quả. Sai về false negative (bỏ qua binary obfuscated) thì nguy hiểm hơn.

---

### 5.2 `unpack.py` — Packing Recovery (Nhóm 1)

**Mục đích:** Giải nén binary bị packed, lấy về binary thực chứa code gốc.

**Strategy:**

```
1. Thử UPX unpack (nhanh, không cần emulation)
   → upx -d -o normalized.bin input.bin
   → Nếu thành công: done

2. Nếu UPX fail (custom packer):
   → Dùng Qiling emulate quá trình unpack
   → Monitor memory writes (unpacker ghi code vào RAM)
   → Detect OEP: khi execution jump đến vùng memory
     mới được ghi (không phải stub gốc)
   → Dump memory tại OEP → normalized.bin
```

**File:** `qiling_scripts/dump_unpacked.py`

```python
from qiling import Qiling
from qiling.const import QL_VERBOSE

def find_oep_and_dump(binary_path, rootfs, output_path):
    ql = Qiling([binary_path], rootfs, verbose=QL_VERBOSE.OFF)

    written_regions = set()

    def track_mem_write(ql, access, addr, size, value):
        written_regions.add((addr, addr + size))

    def check_execution(ql, addr, size):
        # Nếu đang execute vùng vừa được ghi → OEP tìm thấy
        for (start, end) in written_regions:
            if start <= addr < end:
                dump_memory(ql, output_path)
                ql.stop()
                return

    ql.hook_mem_write(track_mem_write)
    ql.hook_code(check_execution)
    ql.run()
```

---

### 5.3 `recover_imports.py` — Import & String Recovery (Nhóm 2)

**Mục đích:** Recover imports bị hidden và strings bị encrypt.

**Part A — String recovery với FLOSS:**

```python
import subprocess

def recover_strings_floss(binary_path) -> list[str]:
    """
    Chạy FLOSS để extract encoded strings.
    FLOSS emulate các hàm nhỏ, không cần OS context đầy đủ.
    """
    result = subprocess.run(
        ["floss", "--no-static-strings", binary_path],
        capture_output=True, text=True
    )
    return parse_floss_output(result.stdout)
```

**Part B — Import recovery với Qiling:**

```python
# qiling_scripts/hook_imports.py

def recover_dynamic_imports(binary_path, rootfs, os_type):
    ql = Qiling([binary_path], rootfs)
    resolved = {}  # addr -> api_name

    def hook_GetProcAddress(ql):
        api_name = read_string_arg(ql, arg_index=1)
        return_addr = get_caller_addr(ql)
        resolved[return_addr] = api_name

    def hook_LoadLibrary(ql):
        dll_name = read_string_arg(ql, arg_index=0)
        log_dll_load(dll_name)

    # Windows hooks
    if os_type == "windows":
        ql.os.set_api("GetProcAddress", hook_GetProcAddress)
        ql.os.set_api("LoadLibraryA", hook_LoadLibrary)
        ql.os.set_api("LoadLibraryW", hook_LoadLibrary)
    # Linux hooks
    else:
        ql.os.set_api("dlsym", hook_GetProcAddress)
        ql.os.set_api("dlopen", hook_LoadLibrary)

    ql.run()
    return resolved
```

---

### 5.4 `deobfuscate_cfg.py` — CFG Deobfuscation (Nhóm 3)

**Mục đích:** Dùng **Ghidra headless** + Python script để unflatten CFF, remove BCF. Output là pseudocode (Ghidra decompiler output) sạch per function.

**Approach:** Ghidra có chế độ `analyzeHeadless` chạy hoàn toàn không cần GUI, nhận script Python để xử lý binary và export kết quả.

```python
# deobfuscate_cfg.py

import subprocess
import os

GHIDRA_HOME = os.environ.get("GHIDRA_HOME", "./tools/ghidra_11.1.2_PUBLIC")
ANALYZE_HEADLESS = os.path.join(GHIDRA_HOME, "support", "analyzeHeadless")

def run_ghidra_deobfuscate(binary_path, output_dir):
    """
    Chạy Ghidra headless:
      1. Import binary vào Ghidra project tạm
      2. Chạy auto-analysis
      3. Chạy script deobfuscate_headless.py để:
         - Detect và unflatten CFF
         - Remove opaque predicates (BCF)
         - Export decompiled pseudocode per function
    """
    os.makedirs(output_dir, exist_ok=True)

    project_dir = "/tmp/ghidra_projects"
    project_name = f"preproc_{os.path.basename(binary_path)}"
    script_path = os.path.join(
        os.path.dirname(__file__),
        "ghidra_scripts", "deobfuscate_headless.py"
    )

    cmd = [
        ANALYZE_HEADLESS,
        project_dir, project_name,
        "-import", binary_path,
        "-postScript", script_path,
        "-scriptPath", os.path.join(os.path.dirname(__file__), "ghidra_scripts"),
        "-scriptlog", "/tmp/ghidra_script.log",
        "-deleteProject",          # Xóa project tạm sau khi xong
        "-noanalysis",             # Tắt analysis mặc định, dùng script kiểm soát
        "-analyzeHeadless",
    ]

    # Truyền output_dir vào script qua environment variable
    env = os.environ.copy()
    env["GHIDRA_OUTPUT_DIR"] = output_dir

    subprocess.run(cmd, env=env, timeout=600)  # Timeout 10 phút per binary
```

**Ghidra headless script:**

```python
# ghidra_scripts/deobfuscate_headless.py
# Chạy trong Ghidra Python (Jython) context

import os
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.program.model.listing import Function

output_dir = os.environ.get("GHIDRA_OUTPUT_DIR", "/tmp/ghidra_output")
os.makedirs(output_dir, exist_ok=True)

monitor = ConsoleTaskMonitor()
program = getCurrentProgram()

# --- Bước 1: Chạy analysis ---
analyzeAll(program)

# --- Bước 2: Setup Decompiler ---
decomp = DecompInterface()
decomp.openProgram(program)

# --- Bước 3: (Optional) Detect và patch CFF ---
# Nếu dùng thêm script OLLVM-unflattener thì chèn vào đây
# Ví dụ: chạy script detect_dispatcher() rồi patch jump targets

# --- Bước 4: Export pseudocode per function ---
func_manager = program.getFunctionManager()
funcs = func_manager.getFunctions(True)

for func in funcs:
    try:
        result = decomp.decompileFunction(func, 60, monitor)
        if result and result.decompiledFunction:
            pseudocode = result.decompiledFunction.getC()
            addr = func.getEntryPoint().getOffset()
            out_file = os.path.join(output_dir, f"{addr:#010x}.c")
            with open(out_file, "w") as f:
                f.write(pseudocode)
    except Exception as e:
        print(f"[WARN] Decompile failed for {func.getName()}: {e}")

print(f"[DONE] Exported pseudocode to {output_dir}")
```

> **Ghi chú về CFF unflattening trong Ghidra:**
> Ghidra không có built-in CFF unflattener mạnh như D-810. Có hai hướng bổ sung:
> 1. **Script Python trong Ghidra:** Cộng đồng đã có script [`OllvmDeflat.py`](https://github.com/FFRI/ghidra-deobfuscator) chạy trong Ghidra để unflatten OLLVM CFF — copy vào `ghidra_scripts/` và gọi từ `deobfuscate_headless.py`.
> 2. **angr pre-pass:** Dùng angr để trace execution và patch binary trước khi import vào Ghidra. Output của angr là binary đã được simplify CFG, Ghidra decompile ra kết quả tốt hơn.

---

### 5.5 `run_pipeline.py` — Entry Point

**Mục đích:** Chạy toàn bộ stage 0 cho một binary.

```python
# run_pipeline.py

import click
from detect import check_obfuscation_signals
from unpack import unpack_binary
from recover_imports import recover_strings_floss, recover_dynamic_imports
from deobfuscate_cfg import run_ghidra_deobfuscate
from pathlib import Path
import shutil
import json

@click.command()
@click.argument("binary_path")
@click.option("--arch", default="x86_64")
@click.option("--os-type", default="windows")
@click.option("--rootfs", default="./qiling_rootfs")
@click.option("--output-dir", default="./output")
@click.option("--force", is_flag=True,
              help="Bỏ qua detection, chạy full pipeline")
def main(binary_path, arch, os_type, rootfs, output_dir, force):
    out = Path(output_dir) / Path(binary_path).stem
    out.mkdir(parents=True, exist_ok=True)

    # --- STEP 0.1: Detection ---
    if not force:
        is_obf = check_obfuscation_signals(binary_path)
        if not is_obf:
            print(f"[CLEAN] {binary_path} — bypass preprocessing")
            shutil.copy(binary_path, out / "normalized.bin")
            return
        print(f"[OBFUSCATED] {binary_path} — running normalization")

    # --- STEP 0.2a: Unpack ---
    normalized = unpack_binary(binary_path, out / "normalized.bin")

    # --- STEP 0.2b: Import & String Recovery ---
    strings = recover_strings_floss(str(normalized))
    imports = recover_dynamic_imports(str(normalized), rootfs, os_type)

    with open(out / "recovered_strings.json", "w") as f:
        json.dump(strings, f, indent=2)
    with open(out / "recovered_imports.json", "w") as f:
        json.dump(imports, f, indent=2)

    # --- STEP 0.2c: CFG Deobfuscation ---
    pseudo_dir = out / "clean_pseudocode"
    run_ghidra_deobfuscate(str(normalized), str(pseudo_dir))

    print(f"[DONE] Output saved to: {out}")
    print(f"  normalized binary : {normalized}")
    print(f"  recovered imports : {len(imports)} APIs")
    print(f"  recovered strings : {len(strings)} strings")
    print(f"  clean pseudocode  : {pseudo_dir}")

if __name__ == "__main__":
    main()
```

**Ví dụ sử dụng:**
```bash
# Chạy cho một binary
python run_pipeline.py sample.exe --arch x86_64 --os-type windows

# Chạy batch cho nhiều binary
for f in binaries/*.exe; do
    python run_pipeline.py "$f" --output-dir ./output/
done

# Force chạy dù binary clean (dùng để test)
python run_pipeline.py sample.bin --force
```

---

## 6. Tích hợp với Co2FuLL gốc

Sau khi stage 0 chạy xong, kết quả được feed vào Co2FuLL theo cách sau. **Không sửa code Co2FuLL gốc** — chỉ cần truyền data đã recover vào đúng bước.

### 6.1 Bổ sung recovered imports và strings vào DG construction

```python
# preprocessing/inject_context.py

def merge_recovered_data(ida_features: dict,
                          recovered_imports_path: str,
                          recovered_strings_path: str) -> dict:
    """
    Merge recovered imports/strings vào features dict
    trước khi Co2FuLL build DG.
    """
    import json

    with open(recovered_imports_path) as f:
        extra_imports = json.load(f)
    with open(recovered_strings_path) as f:
        extra_strings = json.load(f)

    ida_features["imports"].update(extra_imports)
    ida_features["strings"].extend(extra_strings)
    return ida_features
```

### 6.2 Thay thế pseudocode cho LLM Verification

```python
# preprocessing/inject_pseudocode.py

def get_clean_pseudocode(func_addr: int,
                          clean_pseudo_dir: str,
                          fallback_func) -> str:
    """
    Ưu tiên dùng pseudocode từ Ghidra deobfuscated nếu có.
    Fallback về pseudocode gốc nếu không.
    """
    import os
    clean_path = os.path.join(
        clean_pseudo_dir, f"{func_addr:#010x}.c"
    )
    if os.path.exists(clean_path):
        with open(clean_path) as f:
            return f.read()
    return fallback_func(func_addr)
```

---

## 7. Phạm vi và Giới hạn

### Những gì pipeline này giải quyết được
| Nhóm | Mô tả | Coverage |
|---|---|---|
| Nhóm 1 | Packing (UPX, custom) | ✅ Tốt |
| Nhóm 2 | Import hiding + String encryption | ✅ Tốt |
| Nhóm 3 | CFF, BCF, Instruction substitution | ⚠️ Tốt với OLLVM/Hikari standard |

### Những gì nằm ngoài scope
| Nhóm | Mô tả | Lý do |
|---|---|---|
| Nhóm 4 | Function fission/fusion | Không có tool tự động recover function boundary |
| Nhóm 5 | VM-based (VMProtect, Themida) | Open research problem, không giải được tổng quát |
| Nhóm 3 custom | Custom CFF (không phải OLLVM-style) | Ghidra script có thể miss nếu dispatcher logic khác |

---

## 8. Kế hoạch test

> **Phạm vi test giai đoạn này:** Chỉ đánh giá khả năng deobfuscate của pre-processing stage — **chưa** chạy pipeline Co2FuLL đầy đủ. Mục tiêu là xác nhận rằng binary sau khi qua stage 0 trông "sạch" hơn trước: imports và strings hiển thị đầy đủ, pseudocode đọc được. Tích hợp với Co2FuLL là bước sau.

### 8.1 Chuẩn bị test binary

Viết một chương trình C nhỏ làm subject, đủ để có imports và string literals làm context feature — tương tự tinh thần BinKit.

**Yêu cầu chương trình C:**
- Gọi ít nhất 3–4 hàm thư viện chuẩn: `printf`, `malloc`, `strcpy`, `strlen`, `memset`
- Có vài string literals có nghĩa (không phải chuỗi rác)
- Có ít nhất 2–3 hàm con để pseudocode per-function có gì để so sánh

**Ví dụ nội dung `test_subject.c`:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void greet(const char *name) {
    char buf[64];
    snprintf(buf, sizeof(buf), "Hello, %s!", name);
    printf("%s\n", buf);
}

int compute(int x, int y) {
    int *tmp = (int *)malloc(sizeof(int) * 2);
    tmp[0] = x + y;
    tmp[1] = x * y;
    printf("sum=%d, product=%d\n", tmp[0], tmp[1]);
    free(tmp);
    return tmp[0];
}

int main(int argc, char *argv[]) {
    greet("BinKit");
    compute(6, 7);
    return 0;
}
```

**Biên dịch 3 bản:**

```bash
# Bản 1: clean (gcc bình thường)
gcc -O2 -o test_clean test_subject.c

# Bản 2: OLLVM obfuscated — dùng clang với OLLVM passes
# (cần toolchain OLLVM hoặc Hikari/obfuscator-llvm fork)
# Áp dụng cả 3 pass: fla (control flow flattening), bcf (bogus control flow), sub (substitution)
clang -mllvm -fla -mllvm -bcf -mllvm -sub -o test_ollvm test_subject.c

# Bản 3: OLLVM + UPX packed
upx --best -o test_ollvm_upx test_ollvm
```

> **Nếu chưa có OLLVM toolchain:** Có thể dùng bản fork công khai:
> - [obfuscator-llvm](https://github.com/obfuscator-llvm/obfuscator) — LLVM 4.0 base, stable
> - [Hikari](https://github.com/HikariObfuscator/Hikari) — LLVM 12 base, hiện đại hơn
> - Docker image có sẵn: `docker pull obfuscator-llvm/obfuscator`

---

### 8.2 Unit test từng module

Chạy từng bước của pipeline độc lập, quan sát output bằng mắt.

**Test detection:**
```bash
# Phải thấy: clean → False, OLLVM → True, packed → True
python -c "
from detect import check_obfuscation_signals
print('clean :', check_obfuscation_signals('tests/test_clean'))
print('ollvm :', check_obfuscation_signals('tests/test_ollvm'))
print('packed:', check_obfuscation_signals('tests/test_ollvm_upx'))
"
```

**Test unpack:**
```bash
# Chạy unpack trên bản packed, kiểm tra output có giống bản ollvm không
python unpack.py tests/test_ollvm_upx --output tests/test_unpacked

# So sánh file size (unpacked phải ~bằng ollvm)
ls -lh tests/test_ollvm tests/test_unpacked

# Kiểm tra binary hợp lệ sau unpack
file tests/test_unpacked
readelf -h tests/test_unpacked   # Linux ELF
```

**Test string recovery:**
```bash
# Với bản clean: strings đọc được tĩnh → floss ít tìm thêm
# Với bản OLLVM: strings bị XOR/encoded → floss recover được nhiều hơn
python -c "
from recover_imports import recover_strings_floss
clean  = recover_strings_floss('tests/test_clean')
obf    = recover_strings_floss('tests/test_ollvm')
print('clean strings :', len(clean),  clean[:3])
print('ollvm strings :', len(obf),    obf[:3])
"
```

**Test CFG deobfuscation (Ghidra headless):**
```bash
# Chạy Ghidra lên cả 2 bản, lưu pseudocode ra file
python run_pipeline.py tests/test_clean  --output-dir ./output/ --force
python run_pipeline.py tests/test_ollvm  --output-dir ./output/ --force

# So sánh pseudocode của hàm compute() ở địa chỉ tương ứng
# Bản clean: pseudocode ngắn gọn, logic rõ
# Bản OLLVM trước deobfuscate: đầy switch/dispatcher, biến state
# Bản OLLVM sau deobfuscate: gần giống bản clean
diff output/test_clean/clean_pseudocode/ output/test_ollvm/clean_pseudocode/
```

---

### 8.3 Tiêu chí đánh giá (quan sát thủ công)

Giai đoạn này chưa có metric tự động — dev tự quan sát và ghi nhận:

| Tiêu chí | Bản clean (baseline) | Bản OLLVM trước xử lý | Bản OLLVM sau xử lý | Pass? |
|---|---|---|---|---|
| Số imports tĩnh tìm được | ≥ 5 | < 5 | ≥ 5 (sau recover) | — |
| Strings đọc được | ≥ 3 | 0–1 | ≥ 3 (sau FLOSS) | — |
| Pseudocode có cấu trúc rõ | ✅ | ❌ (đầy switch) | Gần ✅ | — |
| File entropy | < 7.0 | 6.x | 6.x (CFF không ảnh hưởng entropy) | — |
| Entropy sau unpack (bản packed) | — | — | < 7.0 | — |

> Dev điền vào bảng sau khi chạy và ghi nhận kết quả thực tế.

---

### 8.4 Checklist trước khi bắt đầu dev

- [ ] Cài Java 17: `sudo apt install openjdk-17-jdk`
- [ ] Download và giải nén Ghidra 11.x từ https://ghidra-sre.org
- [ ] Set `GHIDRA_HOME` trỏ đúng vào thư mục Ghidra: `export GHIDRA_HOME=/path/to/ghidra_11.x`
- [ ] Cài UPX: `sudo apt install upx-ucl`
- [ ] Chạy `pip install -r requirements.txt`
- [ ] Chạy `setup.sh` để download Qiling rootfs
- [ ] (Optional) Download script `OllvmDeflat.py` từ https://github.com/FFRI/ghidra-deobfuscator, copy vào `ghidra_scripts/`
- [ ] Kiểm tra Ghidra headless hoạt động:
  ```bash
  $GHIDRA_HOME/support/analyzeHeadless /tmp/test TestProj \
      -import tests/test_clean -deleteProject
  # Phải thấy "INFO  HEADLESS: execution complete" ở cuối log
  ```
- [ ] Kiểm tra Qiling rootfs hoạt động:
  ```bash
  python -c "from qiling import Qiling; \
             ql = Qiling(['tests/test_clean'], './qiling_rootfs/x8664_linux'); \
             ql.run()"
  ```
- [ ] Biên dịch được `test_clean` và `test_ollvm` từ `test_subject.c`
- [ ] Chạy `python run_pipeline.py tests/test_clean` → phải thấy `[CLEAN] bypass`
- [ ] Chạy `python run_pipeline.py tests/test_ollvm` → phải thấy `[OBFUSCATED]` và output files
- [ ] Điền bảng tiêu chí đánh giá (mục 8.3) dựa trên kết quả quan sát thực tế
