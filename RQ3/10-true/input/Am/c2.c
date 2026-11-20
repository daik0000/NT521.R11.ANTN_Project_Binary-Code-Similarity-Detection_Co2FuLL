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

// a2ps-4.14_clang-4.0_arm_64_O0_a2ps.elf.strip@0x4517a0
__int64 __fastcall sub_4517A0(__int64 a1, __int64 a2)
{
  unsigned __int64 i; // [xsp+0h] [xbp-20h]

  for ( i = 0; i < *(a1 + 40); ++i )
  {
    if ( (*(a1 + 64))(a1: *(*(a1 + 48) + 8 * i), a2) == 0 )
      return i;
  }
  return -1;
}
