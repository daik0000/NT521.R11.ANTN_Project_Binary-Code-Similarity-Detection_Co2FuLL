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

// gsl-2.5_gcc-6.4.0_arm_32_O0_libgsl.so.23.1.0.elf.strip@0xc0cc8
unsigned int __fastcall gsl_histogram_max_bin(int a1)
{
  int v1; // r2
  int v4; // [sp+8h] [bp-1Ch]
  int v5; // [sp+Ch] [bp-18h]
  unsigned int v6; // [sp+10h] [bp-14h]
  unsigned int i; // [sp+14h] [bp-10h]

  v6 = 0;
  v4 = **(a1 + 8);
  v5 = *(*(a1 + 8) + 4);
  for ( i = 0; *a1 > i; ++i )
  {
    if ( sub_3842F0(
           a1: *(*(a1 + 8) + 8 * i),
           a2: *(*(a1 + 8) + 8 * i + 4),
           a3: v4,
           a4: v5) != 0 )
    {
      v1 = *(a1 + 8);
      v4 = *(v1 + 8 * i);
      v5 = *(v1 + 8 * i + 4);
      v6 = i;
    }
  }
  return v6;
}
