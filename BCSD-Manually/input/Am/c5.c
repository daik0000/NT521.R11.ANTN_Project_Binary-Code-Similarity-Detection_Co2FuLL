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

// recutils-1.7_clang-4.0_x86_32_O0_librec.so.1.0.0.elf.strip@0x1e050
int __cdecl rec_sex_ast_node_reset(int a1)
{
  unsigned int i; // [esp+Ch] [ebp-Ch]

  for ( i = 0; i < *(a1 + 36); ++i )
    rec_sex_ast_node_reset(a1: *(a1 + 4 * i + 24));
  *(a1 + 12) = 0;
  return a1;
}
