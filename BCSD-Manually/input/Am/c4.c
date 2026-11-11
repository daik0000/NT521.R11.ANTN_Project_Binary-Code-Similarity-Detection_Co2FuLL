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

// a2ps-4.14_gcc-8.2.0_x86_64_O2_a2ps.elf.strip@0x41dcb0
__int64 __fastcall sub_41DCB0(__int64 a1, _IO_FILE *a2)
{
  _QWORD *v3; // r12
  unsigned __int64 v4; // rbp
  char *v5; // rax
  _QWORD *v6; // rbx
  __int64 v7; // rsi

  v3 = (a1 + 16);
  v4 = 0;
  v5 = dcgettext(domainname: nullptr, msgid: "Known Prologues", category: 5);
  fputs(s: v5, stream: a2);
  _IO_putc(c: 10, fp: a2);
  v6 = sub_439DE0(a1: *v3, a2: ".pro");
  if ( v6[5] != 0 )
  {
    do
    {
      v7 = *(v6[6] + 8 * v4++);
      sub_41DAB0(a1: v3, a2: v7, a3: a2, a4: "Prologue \"%s\":\n", &sub_434C70);
    }
    while ( v4 < v6[5] );
  }
  return sub_439FF0(ptr: v6);
}
