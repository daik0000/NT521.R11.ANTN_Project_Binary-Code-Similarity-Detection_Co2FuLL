// a2ps-4.14_clang-6.0_arm_32_O0_a2ps.elf.strip@0x66e08
int __fastcall sub_66E08(int a1, void (__fastcall *a2)(_DWORD))
{
  unsigned int i; // [sp+Ch] [bp-Ch]

  if ( a2 != nullptr )
  {
    for ( i = 0; i < *(a1 + 20); ++i )
      a2(a1: *(*(a1 + 24) + 4 * i));
  }
  *(a1 + 20) = 0;
  return a1;
}

// a2ps-4.14_gcc-8.2.0_arm_32_O0_a2ps.elf.strip@0x5ff68
int __fastcall sub_5FF68(int result, int (__fastcall *a2)(_DWORD))
{
  int v3; // [sp+4h] [bp-10h]
  unsigned int i; // [sp+Ch] [bp-8h]

  v3 = result;
  if ( a2 != nullptr )
  {
    for ( i = 0; i < *(v3 + 20); ++i )
      result = a2(a1: *(*(v3 + 24) + 4 * i));
  }
  *(v3 + 20) = 0;
  return result;
}
