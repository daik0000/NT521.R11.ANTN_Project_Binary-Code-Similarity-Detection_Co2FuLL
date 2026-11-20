// a2ps-4.14_clang-6.0_x86_32_O3_a2ps.elf.strip@0x807f3e0
long double __cdecl sub_807F3E0(int a1, int a2, int a3, int a4, char *a5, int a6)
{
  int v6; // esi
  int v7; // eax
  int v8; // eax
  char *v9; // esi
  int v10; // eax
  int v11; // eax
  float v12; // xmm0_4
  long double result; // fst7
  int v14; // edi
  char *v15; // esi
  int v16; // eax
  FILE *v17; // esi
  char *v18; // eax
  const char *v19; // [esp+8h] [ebp-134h]
  float v20[2]; // [esp+24h] [ebp-118h] BYREF
  char s[272]; // [esp+2Ch] [ebp-110h] BYREF

  v6 = a1;
  v7 = __isoc99_sscanf(a1: a2, a2: "%f%255s", v20, s);
  if ( v7 != 1 )
  {
    if ( v7 == 2 )
    {
      v8 = sub_8078A30(a1, s, a3: off_80911C8, s2: dword_8094368, n: 4u, a6: 0, a7: off_8094350);
      v20[0] = *&dword_8094368[v8] * v20[0];
    }
    else
    {
      v9 = dcgettext(domainname: nullptr, msgid: "invalid argument `%s' for `%s'", category: 5);
      v10 = sub_807A9F0(a1: a2);
      v19 = v9;
      v6 = a1;
      error(status: 1, errnum: 0, format: v19, v10, a1);
    }
  }
  v11 = sub_8078A30(
          a1: "internal conversion",
          s: a5,
          a3: off_80911C8,
          s2: dword_8094368,
          n: 4u,
          a6: 1,
          a7: abort);
  s[0] = 0;
  v12 = v20[0] / *&dword_8094368[v11];
  v20[0] = v12;
  switch ( a6 )
  {
    case 0:
      goto LABEL_34;
    case 1:
      if ( *&a3 <= v12 )
        goto LABEL_34;
      sprintf(s, format: "%.1f%s <= f", *&a3, a5);
      if ( s[0] != 0 )
        goto LABEL_36;
      goto LABEL_33;
    case 2:
      if ( *&a3 < v12 )
        goto LABEL_34;
      sprintf(s, format: "%.1f%s < f", *&a3, a5);
      if ( s[0] != 0 )
        goto LABEL_36;
      goto LABEL_33;
    case 3:
      if ( v12 <= *&a4 )
        goto LABEL_34;
      sprintf(s, format: "f <= %.1f%s", *&a4, a5);
      if ( s[0] != 0 )
        goto LABEL_36;
      goto LABEL_33;
    case 4:
      if ( v12 < *&a4 )
        goto LABEL_34;
      sprintf(s, format: "f <= %.1f%s", *&a4, a5);
      if ( s[0] != 0 )
        goto LABEL_36;
      goto LABEL_33;
    case 5:
      if ( *&a3 <= v12 && v12 <= *&a4 )
        goto LABEL_34;
      sprintf(s, format: "%.1f%s <= f <= %.1f%s", *&a3, a5, *&a4, a5);
      if ( s[0] != 0 )
        goto LABEL_36;
      goto LABEL_33;
    case 6:
      if ( *&a3 < v12 && v12 <= *&a4 )
        goto LABEL_34;
      sprintf(s, format: "%.1f%s < f <= %.1f%s", *&a3, a5, *&a4, a5);
      if ( s[0] != 0 )
        goto LABEL_36;
      goto LABEL_33;
    case 7:
      if ( *&a3 <= v12 && v12 < *&a4 )
        goto LABEL_34;
      sprintf(s, format: "%.1f%s <= f < %.1f%s", *&a3, a5, *&a4, a5);
      if ( s[0] != 0 )
        goto LABEL_36;
      goto LABEL_33;
    case 8:
      if ( *&a3 >= v12 || v12 >= *&a4 )
      {
        sprintf(s, format: "%.1f%s < f < %.1f%s", *&a3, a5, *&a4, a5);
        if ( s[0] != 0 )
        {
LABEL_36:
          v14 = v6;
          v15 = dcgettext(domainname: nullptr, msgid: "invalid argument `%s' for `%s'", category: 5);
          v16 = sub_807A9F0(a1: a2);
          error(status: 0, errnum: 0, format: v15, v16, v14);
          v17 = stderr;
          v18 = dcgettext(domainname: nullptr, msgid: "Valid arguments are floats f such that: %s\n", category: 5);
          fprintf(stream: v17, format: v18, s);
          exit(status: 1);
        }
LABEL_33:
        v12 = v20[0];
      }
LABEL_34:
      v20[1] = v12;
      return v12;
    default:
      abort();
      return result;
  }
}

// a2ps-4.14_clang-7.0_x86_32_O3_a2ps.elf.strip@0x807dcf0
long double __cdecl sub_807DCF0(int a1, int a2, int a3, int a4, char *a5, int a6)
{
  int v6; // esi
  int v7; // eax
  int v8; // eax
  char *v9; // esi
  int v10; // eax
  int v11; // eax
  float v12; // xmm0_4
  char *v13; // eax
  long double result; // fst7
  int v15; // edi
  char *v16; // esi
  int v17; // eax
  FILE *v18; // esi
  char *v19; // eax
  char *format; // [esp+4h] [ebp-138h]
  const char *v21; // [esp+8h] [ebp-134h]
  double v22; // [esp+8h] [ebp-134h]
  double v23; // [esp+14h] [ebp-128h]
  float v24[2]; // [esp+24h] [ebp-118h] BYREF
  char s[272]; // [esp+2Ch] [ebp-110h] BYREF

  v6 = a1;
  v7 = __isoc99_sscanf(a1: a2, a2: "%f%255s", v24, s);
  if ( v7 != 1 )
  {
    if ( v7 == 2 )
    {
      v8 = sub_80774C0(a1, s, a3: off_808F728, s2: dword_809236C, n: 4u, a6: 0, a7: off_8092354);
      v24[0] = *&dword_809236C[v8] * v24[0];
    }
    else
    {
      v9 = dcgettext(domainname: nullptr, msgid: "invalid argument `%s' for `%s'", category: 5);
      v10 = sub_8079450(a1: a2);
      v21 = v9;
      v6 = a1;
      error(status: 1, errnum: 0, format: v21, v10, a1);
    }
  }
  v11 = sub_80774C0(
          a1: "internal conversion",
          s: a5,
          a3: off_808F728,
          s2: dword_809236C,
          n: 4u,
          a6: 1,
          a7: abort);
  s[0] = 0;
  v12 = v24[0] / *&dword_809236C[v11];
  v24[0] = v12;
  switch ( a6 )
  {
    case 0:
      goto LABEL_29;
    case 1:
      if ( *&a3 <= v12 )
        goto LABEL_29;
      sprintf(s, format: "%.1f%s <= f", *&a3, a5);
      goto LABEL_27;
    case 2:
      if ( *&a3 < v12 )
        goto LABEL_29;
      sprintf(s, format: "%.1f%s < f", *&a3, a5);
      goto LABEL_27;
    case 3:
      if ( v12 > *&a4 )
        goto LABEL_13;
      goto LABEL_29;
    case 4:
      if ( v12 < *&a4 )
        goto LABEL_29;
LABEL_13:
      sprintf(s, format: "f <= %.1f%s", *&a4, a5);
      goto LABEL_27;
    case 5:
      if ( *&a3 <= v12 && v12 <= *&a4 )
        goto LABEL_29;
      v13 = a5;
      v23 = *&a4;
      v22 = *&a3;
      format = "%.1f%s <= f <= %.1f%s";
      break;
    case 6:
      if ( *&a3 < v12 && v12 <= *&a4 )
        goto LABEL_29;
      v13 = a5;
      v23 = *&a4;
      v22 = *&a3;
      format = "%.1f%s < f <= %.1f%s";
      break;
    case 7:
      if ( *&a3 <= v12 && v12 < *&a4 )
        goto LABEL_29;
      v13 = a5;
      v23 = *&a4;
      v22 = *&a3;
      format = "%.1f%s <= f < %.1f%s";
      break;
    case 8:
      if ( *&a3 < v12 && v12 < *&a4 )
        goto LABEL_29;
      v13 = a5;
      v23 = *&a4;
      v22 = *&a3;
      format = "%.1f%s < f < %.1f%s";
      break;
    default:
      abort();
      return result;
  }
  sprintf(s, format, v22, v13, v23, v13);
LABEL_27:
  if ( s[0] != 0 )
  {
    v15 = v6;
    v16 = dcgettext(domainname: nullptr, msgid: "invalid argument `%s' for `%s'", category: 5);
    v17 = sub_8079450(a1: a2);
    error(status: 0, errnum: 0, format: v16, v17, v15);
    v18 = stderr;
    v19 = dcgettext(domainname: nullptr, msgid: "Valid arguments are floats f such that: %s\n", category: 5);
    fprintf(stream: v18, format: v19);
    exit(status: 1);
  }
  v12 = v24[0];
LABEL_29:
  v24[1] = v12;
  return v12;
}
