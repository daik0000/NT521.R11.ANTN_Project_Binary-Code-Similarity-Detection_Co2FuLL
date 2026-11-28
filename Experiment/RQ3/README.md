# RQ3 - Đánh giá tính hợp lý của giải thích từ LLM 
## I. 10 cặp random LLM đánh giá đúng
Chọn 5 cặp dương và 5 cặp âm random để phân tích: 
- Dương:
    - `a2ps-4.14_clang-4.0_x86_32_O1_a2ps.elf.strip@0x804e3d0` và `a2ps-4.14_clang-7.0_x86_64_O1_a2ps.elf.strip@0x406e30`
    - `a2ps-4.14_clang-6.0_arm_32_O0_a2ps.elf.strip@0x66e08` và `a2ps-4.14_gcc-8.2.0_arm_32_O0_a2ps.elf.strip@0x5ff68`
    - `a2ps-4.14_clang-6.0_x86_32_O3_a2ps.elf.strip@0x807f3e0` và `a2ps-4.14_clang-7.0_x86_32_O3_a2ps.elf.strip@0x807dcf0`
    - `a2ps-4.14_gcc-4.9.4_arm_32_O3_a2ps.elf.strip@0x26214` và `a2ps-4.14_gcc-8.2.0_arm_64_O3_a2ps.elf.strip@0x416150`
    - `a2ps-4.14_gcc-4.9.4_x86_32_O2_a2ps.elf.strip@0x807be20` và `a2ps-4.14_clang-7.0_arm_32_O1_a2ps.elf.strip@0x40bf4`

- Âm:
    - `a2ps-4.14_clang-4.0_x86_32_O1_a2ps.elf.strip@0x804e3d0` và `a2ps-4.14_gcc-4.9.4_x86_32_O0_a2ps.elf.strip@0x80859a6`
    - `a2ps-4.14_clang-4.0_x86_32_O1_a2ps.elf.strip@0x804e3d0` và `a2ps-4.14_clang-4.0_arm_64_O0_a2ps.elf.strip@0x4517a0`
    - `a2ps-4.14_clang-4.0_x86_32_O1_a2ps.elf.strip@0x804e3d0` và `gsl-2.5_gcc-6.4.0_arm_32_O0_libgsl.so.23.1.0.elf.strip@0xc0cc8`
    - `a2ps-4.14_clang-4.0_x86_32_O1_a2ps.elf.strip@0x804e3d0` và `a2ps-4.14_gcc-8.2.0_x86_64_O2_a2ps.elf.strip@0x41dcb0`
    - `a2ps-4.14_clang-6.0_arm_32_O0_a2ps.elf.strip@0x66e08` và `recutils-1.7_clang-4.0_x86_32_O0_librec.so.1.0.0.elf.strip@0x1e050`

### Kết quả:
Giải thích của LLM
- Đối với cặp dương: liệt kê được các hành động chung của 2 hàm, tuy nhiên nhìn chung chưa phân tích sâu được các hành động chung đó là gì, ở đâu, ...  -> đúng nhưng chưa đủ 
- Đối với cặp âm: chỉ ra flow riêng biệt của 2 hàm, từ đó đánh giá nó khác nhau -> hợp lý 

### Ví dụ: 
### a. Cặp dương `a2ps-4.14_clang-4.0_x86_32_O1_a2ps.elf.strip@0x804e3d0` và `a2ps-4.14_clang-7.0_x86_64_O1_a2ps.elf.strip@0x406e30`

#### Raw pseudocode của từng hàm

Code A:

```c
int sub_804E3D0(int a1, int a2, int a3)
{
    if (*(a1 + 20) != 0) {
        v5 = 0;
        LOBYTE(a3) = 1;
        do {
            LOBYTE(a3) = sub_804E490(
                a1: a2,
                a2: *(*(a1 + 24) + 4 * v5++)
            ) & a3;
        } while (v5 < *(a1 + 20));
    } else {
        LOBYTE(a3) = 1;
    }
    return a3;
}
```

Code B:

```c
__int64 sub_406E30(__int64 a1, __int64 a2)
{
    if (*(a2 + 40) != 0) {
        LOBYTE(v2) = 1;
        v5 = 0;
        do {
            LOBYTE(v2) = sub_406F00(
                a1,
                a2: *(*(a2 + 48) + 8 * v5++)
            ) & v2;
        } while (v5 < *(a2 + 40));
    } else {
        LOBYTE(v2) = 1;
    }
    return v2;
}
```

#### High-level pseudocode chung

```c
bool check_all(Context *ctx, Checker checker)
{
    bool result = true;

    for (unsigned int i = 0; i < ctx->count; ++i)
        result = checker(ctx, ctx->items[i]) && result;

    return result;
}
```

Cả hai hàm đều duyệt các phần tử trong một container, gọi một hàm kiểm tra trên
từng phần tử và AND kết quả kiểm tra vào biến tích lũy. Nếu container rỗng,
hàm trả về `true` vì biến tích lũy được khởi tạo bằng `1`.

#### Giải thích của LLM

> Both codes iterate over a list of elements, calling a function (`sub_804E490` in Code A and `sub_406F00` in Code B) with specific arguments and performing a bitwise AND operation. The structure, logic, and operations are identical, suggesting they are compiled from the same source code with different variable names and offsets due to compilation settings.

#### Nhận xét về giải thích của LLM

- LLM đã liệt kê đúng các hành động chung: duyệt danh sách, gọi hàm trên từng
  phần tử và thực hiện phép AND. Đối chiếu với raw pseudocode, Code A dùng
  `sub_804E490(...) & a3`, còn Code B dùng `sub_406F00(...) & v2`; đây chính là
  thao tác cập nhật kết quả trong high-level pseudocode.
- Kết luận hai hàm có cùng logic là đúng. Các khác biệt về tên hàm, offset và
  kích thước bước truy cập (`4 * v5` ở Code A, `8 * v5` ở Code B) phù hợp với
  khác biệt kiến trúc và cách biên dịch.
- Tuy nhiên, giải thích chưa phân tích cụ thể các hành động đó nằm ở đâu và
  tương ứng với thành phần nào: chưa nêu `*(a1 + 20)`/`*(a2 + 40)` là số phần
  tử, `*(a1 + 24)`/`*(a2 + 48)` là mảng phần tử, chưa chỉ ra việc khởi tạo kết
  quả bằng `1`, trường hợp container rỗng và cách `v5++` duyệt qua từng phần tử.
  Vì vậy giải thích đúng nhưng chưa đủ sâu.

### b. Cặp âm `a2ps-4.14_clang-4.0_x86_32_O1_a2ps.elf.strip@0x804e3d0` và `a2ps-4.14_gcc-4.9.4_x86_32_O0_a2ps.elf.strip@0x80859a6`

#### Raw pseudocode của từng hàm

Code A:

```c
int sub_804E3D0(int a1, int a2, int a3)
{
    if (*(a1 + 20) != 0) {
        v5 = 0;
        LOBYTE(a3) = 1;
        do {
            LOBYTE(a3) = sub_804E490(
                a1: a2,
                a2: *(*(a1 + 24) + 4 * v5++)
            ) & a3;
        } while (v5 < *(a1 + 20));
    } else {
        LOBYTE(a3) = 1;
    }
    return a3;
}
```

Code B:

```c
int sub_80859A6(int a1, int a2)
{
    if (*(a1 + 20) != *(a2 + 20))
        return 0;

    for (i = 0; *(a1 + 20) > i; ++i) {
        if ((*(a1 + 32))(
                a1: *(4 * i + *(a1 + 24)),
                a2: *(4 * i + *(a2 + 24))) != 0)
            return 0;
    }

    return 1;
}
```

#### High-level pseudocode của từng hàm

Code A:

```c
bool check_all(Context *ctx, Checker checker)
{
    bool result = true;
    for (unsigned int i = 0; i < ctx->count; ++i)
        result = checker(ctx, ctx->items[i]) && result;
    return result;
}
```

Code B:

```c
bool contexts_equal(Context *left, Context *right)
{
    if (left->count != right->count)
        return false;

    for (unsigned int i = 0; i < left->count; ++i) {
        if (left->compare(left->items[i], right->items[i]) != 0)
            return false;
    }

    return true;
}
```

Code A xử lý một context: gọi `checker` trên từng phần tử và AND toàn bộ kết
quả. Code B xử lý hai context: trước tiên so sánh số lượng phần tử, sau đó gọi
`compare` trên từng cặp phần tử tương ứng và dừng ngay khi phát hiện khác nhau.

#### Giải thích của LLM

> Code A iterates over an array, applying a function to each element and updating a result variable, while Code B checks if two structures have the same size and then compares corresponding elements using a function. The logic, operations, and purposes of the two codes are different, indicating they are from different source codes.

#### Nhận xét về giải thích của LLM

- LLM đã chỉ ra đúng flow riêng biệt của hai hàm. Với Code A, nhận xét
  “iterates over an array, applying a function to each element and updating a
  result variable” khớp với vòng lặp, lời gọi `sub_804E490` và phép AND cập nhật
  `a3` trong raw pseudocode.
- Với Code B, nhận xét “checks if two structures have the same size and then
  compares corresponding elements” khớp với điều kiện
  `*(a1 + 20) != *(a2 + 20)`, vòng lặp theo chỉ số `i` và lời gọi comparator với
  hai phần tử cùng vị trí. Nhánh trả về `0` ngay khi comparator khác `0` cũng
  thể hiện rõ đây là phép so sánh hai cấu trúc, không phải phép kiểm tra độc
  lập trên một danh sách.
- Vì vậy kết luận hai hàm khác logic là hợp lý: Code A nhận một context và tổng
  hợp các kết quả Boolean; Code B nhận hai context và kiểm tra chúng có tương
  đương hay không. Tuy nhiên, giải thích vẫn có thể chi tiết hơn nếu nêu rõ
  phép AND trong Code A và điều kiện dừng sớm trong Code B.


## II. 3 cặp LLM đánh giá sai 
- `binutils-2.30_clang-4.0_arm_32_O2_objdump.elf.strip@0x7267c` và `binutils-2.30_clang-6.0_arm_32_O0_addr2line.elf.strip@0x18860`
- `a2ps-4.14_gcc-7.3.0_arm_64_O3_a2ps.elf.strip@0x416a10` và `a2ps-4.14_gcc-6.4.0_arm_64_O3_a2ps.elf.strip@0x4189e0`
- `binutils-2.30_clang-4.0_arm_32_O2_objdump.elf.strip@0x7267c` và `binutils-2.30_clang-7.0_x86_32_O0_ranlib.elf.strip@0x805a5c0`

### Nhận xét input: 
- Cả 3 cặp này đều có label là NO nhưng được LLM đánh giá là YES 
- Raw pseudocode của 2/3 cặp đều rất dài 
- Flow logic: một hàm chứa các hành động của hàm còn lại và thực thi thêm các hành động khác 


### Nhận xét giải thích của LLM 

- LLM nhận diện đúng một số đoạn hoặc thao tác bề mặt tương tự giữa hai hàm, chẳng hạn cùng duyệt chuỗi, cùng xử lý format string, cùng cấp phát bộ nhớ hoặc cùng cập nhật bảng/cache. Tuy nhiên, LLM đã suy diễn rằng một phần logic chung đồng nghĩa với việc toàn bộ hai hàm có cùng logic nguồn.
- LLM chưa đối chiếu đầy đủ flow của từng hàm: kiểu và số lượng tham số, dữ liệu đầu vào được đọc, giá trị trả về, các nhánh điều khiển và side effect quan sát được. Vì vậy, nó bỏ qua sự khác nhau về vai trò chính của hàm, ví dụ một hàm xử lý output hoặc error còn hàm kia chỉ scan dữ liệu, hoặc một hàm quản lý stream còn hàm kia quản lý buffer/object.
- Do tập trung vào keyword và các đoạn code tương tự thay vì toàn bộ control flow, LLM đã đánh giá một phase chung hoặc một pattern quản lý dữ liệu như đại diện cho cả hàm. Đây là nguyên nhân chung dẫn đến việc cả ba cặp đều bị kết luận nhầm là `YES`; để đánh giá đúng cần so sánh toàn bộ input, output, mục đích và side effect của hai hàm.


### Ví dụ

#### Cặp c1

`binutils-2.30_clang-4.0_arm_32_O2_objdump.elf.strip@0x7267c` và
`binutils-2.30_clang-6.0_arm_32_O0_addr2line.elf.strip@0x18860`

#### Raw pseudocode của từng hàm

Raw pseudocode khá dài, được giữ nguyên và tham chiếu tại
[`3-false/input/c1.c`](3-false/input/c1.c):

- Code A: `sub_7267C`
- Code B: `sub_18860`

#### High-level pseudocode của từng hàm

Code A — `sub_7267C`:

```c
int handle_error(const char *format, va_list arguments)
{
    TypeInfo types[9] = {};
    unsigned int argument_count = scan_format_and_record_types(format, types);

    load_arguments(arguments, types, argument_count);

    fflush(stdout);
    print_prefix_and_formatted_message(stderr, format, types);
    return fflush(stderr);
}
```

Hàm phân tích format string để xác định kiểu đối số, lấy các đối số từ
`va_list`, in thông báo lỗi ra `stderr` và flush các stream.

Code B — `sub_18860`:

```c
int format_output(FILE *stream, const char *format, Argument *arguments)
{
    unsigned int argument_index = 0;
    int written = 0;

    while (*format != '\0') {
        if (*format != '%') {
            written += print_literal_until_percent(stream, format);
            format = next_percent(format);
            continue;
        }

        FormatSpec spec = parse_flags_width_precision_and_length(&format);
        int count = print_conversion(stream, spec,
                                     arguments, &argument_index);
        if (count < 0)
            return -1;

        written += count;
    }

    return written;
}
```

Hàm nhận một stream, format string và mảng đối số; phân tích từng conversion,
định dạng rồi ghi kết quả vào stream. Hàm trả về số ký tự đã ghi hoặc `-1`
khi có lỗi I/O.

#### Giải thích của LLM

> Both code snippets are functionally similar, handling formatted string processing and argument parsing. They both use `fprintf` for output and handle format specifiers, including width, precision, and type specifiers. The structure and logic of the loops, conditionals, and argument handling are consistent, indicating they are likely compiled from the same source code, possibly with minor differences in implementation details due to different compilation settings.

#### Nhận xét giải thích của LLM

- LLM nhận diện đúng một số điểm tương đồng: cả hai cùng xử lý format string,
  phân tích argument/format specifier, xử lý width và precision, đồng thời có
  các nhánh lặp và gọi hàm output như `fprintf`. Điều này đối chiếu được với
  hai high-level pseudocode: Code A có phase scan format và in thông báo; Code B
  parse conversion rồi ghi kết quả ra stream.
- Tuy nhiên, LLM chưa phân biệt đầy đủ hợp đồng và vai trò của hai hàm. Code A
  là error handler: ngoài scan format còn đọc `va_list`, in tiền tố/thông báo
  lỗi ra `stderr`, flush `stdout/stderr` và trả về trạng thái flush. Code B
  là formatter/output routine: nhận `FILE *`, định dạng từng conversion, đếm
  số ký tự đã ghi và trả về `-1` nếu output thất bại.
- Vì vậy, việc cả hai có một phần logic xử lý format chung không chứng minh toàn
  bộ control flow, input/output và side effect giống nhau. LLM đã đánh đồng
  tương đồng cục bộ với cùng source, đúng với nhận xét phía trên về việc chỉ
  tập trung vào keyword và một phase chung. Đối chiếu toàn bộ hàm cho thấy kết
  luận đúng là `NO` (label `0`), không phải `YES`.
