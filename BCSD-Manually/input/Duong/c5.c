// a2ps-4.14_gcc-4.9.4_x86_32_O2_a2ps.elf.strip@0x807be20
int __cdecl sub_807BE20(int a1, int a2)
{
  int v2; // ebx

  v2 = 0;
  if ( *(a1 + 20) == 0 )
    return -1;
  while ( (*(a1 + 32))(a1: *(*(a1 + 24) + 4 * v2), a2) != 0 )
  {
    if ( *(a1 + 20) <= ++v2 )
      return -1;
  }
  return v2;
}

// a2ps-4.14_clang-7.0_arm_32_O1_a2ps.elf.strip@0x40bf4
int __fastcall sub_40BF4(int a1, int a2)
{
  int v3; // r4
  int v5; // r7

  v3 = -1;
  if ( *(a1 + 20) != 0 )
  {
    v5 = 0;
    while ( (*(a1 + 32))(a1: *(*(a1 + 24) + 4 * v5), a2) != 0 )
    {
      if ( ++v5 >= *(a1 + 20) )
        return v3;
    }
    return v5;
  }
  return v3;
}
