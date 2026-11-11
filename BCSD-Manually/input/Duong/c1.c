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

// a2ps-4.14_clang-7.0_x86_64_O1_a2ps.elf.strip@0x406e30
__int64 __fastcall sub_406E30(__int64 a1, __int64 a2)
{
  unsigned int v2; // ebp
  unsigned __int64 v5; // rbx

  if ( *(a2 + 40) != 0 )
  {
    LOBYTE(v2) = 1;
    v5 = 0;
    do
      LOBYTE(v2) = sub_406F00(a1, a2: *(*(a2 + 48) + 8 * v5++)) & v2;
    while ( v5 < *(a2 + 40) );
  }
  else
  {
    LOBYTE(v2) = 1;
  }
  return v2;
}
