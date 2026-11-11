// a2ps-4.14_clang-4.0_x86_32_O1_a2ps.elf.strip@0x804e3d0
int __usercall sub_804E3D0@<eax>(int a1@<edx>, int a2@<ecx>, int a3@<ebx>)
{
  unsigned int v5; // ebp

  if ( *(a1 + 20) != 0 )
  {
    v5 = 0;
    LOBYTE(a3) = 1;
    do
      LOBYTE(a3) = sub_804E490(a1: a2, a2: *(*(a1 + 24) + 4 * v5++)) & a3;
    while ( v5 < *(a1 + 20) );
  }
  else
  {
    LOBYTE(a3) = 1;
  }
  return a3;
}

// a2ps-4.14_gcc-4.9.4_x86_32_O0_a2ps.elf.strip@0x80859a6
int __cdecl sub_80859A6(int a1, int a2)
{
  unsigned int i; // [esp+Ch] [ebp-Ch]

  if ( *(a1 + 20) != *(a2 + 20) )
    return 0;
  for ( i = 0; *(a1 + 20) > i; ++i )
  {
    if ( (*(a1 + 32))(
           a1: *(4 * i + *(a1 + 24)),
           a2: *(4 * i + *(a2 + 24))) != 0 )
      return 0;
  }
  return 1;
}
