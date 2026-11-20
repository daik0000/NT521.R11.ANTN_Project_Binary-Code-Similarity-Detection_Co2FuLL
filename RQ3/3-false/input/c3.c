// binutils-2.30_clang-4.0_arm_32_O2_objdump.elf.strip@0x7267c
int __fastcall sub_7267C(char *a1, int *a2)
{
  unsigned int v2; 
  int v4; 
  int v5; 
  int v6; 
  unsigned int v7; 
  unsigned int v8; 
  int v9; 
  int v10; 
  unsigned int *v11; 
  int v12; 
  int v13; 
  int v14; 
  int v15; 
  unsigned int v16; 
  int v17; 
  unsigned int *v18; 
  int v19; 
  unsigned int v20; 
  unsigned int *v21; 
  int v22; 
  int v23; 
  unsigned int i; 
  int v25; 
  int *v26; 
  int v27; 
  int v28; 
  FILE *v29; 
  char *v30; 
  const char *v31; 
  int v32; 
  const char *j; 
  int v34; 
  unsigned int *v35; 
  int v36; 
  char *v37; 
  int v38; 
  int v39; 
  unsigned int *v40; 
  int v41; 
  int v42; 
  char *v43; 
  int v44; 
  int v45; 
  unsigned int *v46; 
  int v47; 
  int v48; 
  unsigned int *v49; 
  int v50; 
  int v51; 
  int v52; 
  int v53; 
  int v54; 
  bool v55; 
  int v56; 
  int v57; 
  int v58; 
  int v59; 
  _DWORD *v60; 
  int v61; 
  bool v62; 
  int v64; 
  int v65; 
  char *v66; 
  FILE *stream; 
  FILE *streama; 
  int v69; 
  int v70; 
  _DWORD v71[18]; 
  char format; 
  _BYTE v73[3]; 

  v2 = 0;
  v4 = a1;
  v71[0] = 0;
  v71[2] = 0;
  v71[4] = 0;
  v71[6] = 0;
  v71[8] = 0;
  v71[10] = 0;
  v71[12] = 0;
  v71[14] = 0;
  v71[16] = 0;
  do
  {
    while ( *a1 == 37 )
    {
      v11 = (a1 + 1);
      v10 = a1[1];
      if ( v10 == 37 )
      {
        a1 += 2;
      }
      else
      {
        if ( v10 == 48 )
        {
          v12 = -1;
        }
        else
        {
          v12 = -1;
          if ( (*(dword_1572A8 + 2 * v10) & 4) != 0 && a1[2] == 36 )
          {
            v11 = (a1 + 3);
            v12 = v10 - 49;
          }
        }
        v69 = v12;
        do
        {
          v14 = *v11++;
          v13 = v14;
        }
        while ( memchr(s: "-+ #0'I", c: v14, n: 8u) != nullptr );
        if ( v13 == 42 )
        {
          v15 = *v11;
          if ( v15 == 48 )
          {
            v16 = v2;
            if ( v2 >= 9 )
              goto LABEL_185;
          }
          else if ( (*(dword_1572A8 + 2 * v15) & 4) != 0 )
          {
            if ( v11[1] == 36 )
            {
              v16 = v15 - 49;
              v11 += 2;
            }
            else
            {
              v16 = v2;
            }
            if ( v16 >= 9 )
LABEL_185:
              sub_71440(
                a1: "bfd.c",
                a2: 980,
                a3: "unsigned int _bfd_doprnt_scan(const char *, union _bfd_doprnt_args *)");
          }
          else
          {
            v16 = v2;
            if ( v2 >= 9 )
              goto LABEL_185;
          }
          v71[2 * v16] = 1;
          ++v2;
          v13 = *v11;
        }
        else
        {
          --v11;
          while ( (*(dword_1572A8 + 2 * v13) & 4) != 0 )
          {
            v17 = *++v11;
            v13 = v17;
          }
        }
        if ( v13 == 46 )
        {
          v18 = v11 + 1;
          v13 = v11[1];
          if ( v13 == 42 )
          {
            v18 = v11 + 2;
            v19 = v11[2];
            if ( v19 == 48 )
            {
              v20 = v2;
              if ( v2 >= 9 )
                goto LABEL_186;
            }
            else if ( (*(dword_1572A8 + 2 * v19) & 4) != 0 )
            {
              v20 = v2;
              if ( v11[3] == 36 )
              {
                v18 = v11 + 4;
                v20 = v19 - 49;
              }
              if ( v20 >= 9 )
LABEL_186:
                sub_71440(
                  a1: "bfd.c",
                  a2: 1005,
                  a3: "unsigned int _bfd_doprnt_scan(const char *, union _bfd_doprnt_args *)");
            }
            else
            {
              v20 = v2;
              if ( v2 >= 9 )
                goto LABEL_186;
            }
            v71[2 * v20] = 1;
            ++v2;
            v13 = *v18;
          }
          else if ( (*(dword_1572A8 + 2 * v13) & 4) != 0 )
          {
            v21 = v11 + 2;
            do
            {
              v22 = *v21++;
              v13 = v22;
            }
            while ( (*(dword_1572A8 + 2 * v22) & 4) != 0 );
            v18 = v21 - 1;
          }
        }
        else
        {
          v18 = v11;
        }
        stream = v4;
        if ( memchr(s: &dword_72DC0, c: v13, n: 4u) != nullptr )
        {
          v6 = 0;
          v5 = 0;
          while ( 1 )
          {
            switch ( v13 )
            {
              case 'L':
                v5 = 2;
                break;
              case 'h':
                v6 = 1;
                break;
              case 'l':
                ++v5;
                break;
              default:
                v65 = 4;
                goto LABEL_181;
            }
            v23 = *++v18;
            v13 = v23;
            if ( memchr(s: &dword_72DC0, c: v23, n: 4u) == nullptr )
              goto LABEL_4;
          }
        }
        v5 = 0;
        v6 = 0;
LABEL_4:
        v7 = v69;
        if ( v69 < 0 )
          v7 = v2;
        v8 = v7;
        v9 = 6;
        switch ( v13 )
        {
          case 'A':
          case 'B':
          case 'p':
          case 's':
            goto LABEL_18;
          case 'E':
          case 'G':
          case 'e':
          case 'f':
          case 'g':
            v9 = 5;
            if ( v5 == 0 )
              v9 = 4;
            goto LABEL_18;
          case 'X':
          case 'c':
          case 'd':
          case 'i':
          case 'o':
          case 'u':
          case 'x':
            v9 = 1;
            if ( v6 != 0 )
            {
LABEL_18:
              if ( v7 >= 9 )
                goto LABEL_184;
            }
            else
            {
              v9 = 3;
              if ( *(v18 - 1) == 76 )
                v5 = 1;
              if ( v5 == 1 )
                v9 = 2;
              if ( v5 == 0 )
                v9 = 1;
              if ( v7 >= 9 )
              {
LABEL_184:
                v65 = 83;
LABEL_181:
                sub_71440(
                  a1: "bfd.c",
                  a2: v65 | 0x400,
                  a3: "unsigned int _bfd_doprnt_scan(const char *, union _bfd_doprnt_args *)");
              }
            }
            a1 = (v18 + 1);
            v4 = stream;
            v71[2 * v8] = v9;
            ++v2;
            break;
          default:
            v65 = 79;
            goto LABEL_181;
        }
      }
    }
    if ( *a1 == 0 )
      break;
    a1 = strchr(s: a1, c: 37);
  }
  while ( a1 != nullptr );
  if ( v2 != 0 )
  {
    for ( i = 0; i < v2; ++i )
    {
      switch ( v71[2 * i] )
      {
        case 1:
        case 2:
        case 6:
          v25 = *a2++;
          v71[2 * i] = v25;
          break;
        case 3:
        case 4:
        case 5:
          v26 = ((a2 + 7) & 0xFFFFFFF8);
          v27 = v26[1];
          v28 = *v26;
          a2 = v26 + 2;
          v71[2 * i] = v28;
          v71[2 * i + 1] = v27;
          break;
        default:
          sub_71440(a1: "bfd.c", a2: 1157, a3: "void error_handler_internal(const char *, va_list)");
      }
    }
  }
  fflush(stream: stdout);
  if ( dword_16C798 != 0 )
    fprintf(stream: stderr, format: "%s: ", dword_16C798);
  else
    fwrite(ptr: "BFD: ", size: 5u, n: 1u, s: stderr);
  v29 = stderr;
  v30 = v73;
  v70 = 0;
LABEL_87:
  while ( 2 )
  {
    for ( j = (v4 + 3); ; j += 2 )
    {
      if ( *(j - 3) == 0 )
        goto LABEL_176;
      if ( *(j - 3) != 37 )
      {
        v43 = strchr(s: j - 3, c: 37);
        if ( v43 != nullptr )
          v44 = fprintf(stream: v29, format: "%.*s", v43 - (j - 3), j - 3);
        else
          v44 = fprintf(stream: v29, format: &dword_73054, j - 3);
        v4 = &j[v44 - 3];
        if ( v44 == -1 )
          goto LABEL_176;
        goto LABEL_87;
      }
      v34 = *(j - 2);
      if ( v34 != 37 )
        break;
      fputc(c: 37, stream: v29);
    }
    streama = v29;
    format = 37;
    v35 = (j - 2);
    v36 = -1;
    if ( v34 == 48 )
    {
      v34 = 48;
    }
    else if ( (*(dword_1572A8 + 2 * v34) & 4) != 0 && *(j - 1) == 36 )
    {
      v36 = v34 - 49;
      v35 = j;
      v34 = *j;
    }
    v37 = v30;
    if ( memchr(s: "-+ #0'I", c: v34, n: 8u) != nullptr )
    {
      do
      {
        *v37++ = v34;
        v38 = *++v35;
        v34 = v38;
      }
      while ( memchr(s: "-+ #0'I", c: v38, n: 8u) != nullptr );
    }
    if ( v34 == 42 )
    {
      v40 = v35 + 1;
      v39 = v35[1];
      if ( v39 == 48 )
      {
        v41 = v70;
      }
      else if ( (*(dword_1572A8 + 2 * v39) & 4) != 0 )
      {
        v41 = v70;
        if ( v35[2] == 36 )
        {
          v40 = v35 + 3;
          v41 = v39 - 49;
        }
      }
      else
      {
        v41 = v70;
      }
      v45 = v71[2 * v41];
      if ( v45 < 0 )
        v45 = -v45;
      v37 += sprintf(s: v37, format: &dword_730C0, v45);
      ++v70;
      v34 = *v40;
    }
    else
    {
      while ( (*(dword_1572A8 + 2 * v34) & 4) != 0 )
      {
        *v37++ = v34;
        v42 = *++v35;
        v34 = v42;
      }
      v40 = v35;
    }
    v66 = v30;
    if ( v34 == 46 )
    {
      *v37++ = 46;
      v46 = v40 + 1;
      v34 = v40[1];
      if ( v34 == 42 )
      {
        v46 = v40 + 2;
        v47 = v40[2];
        if ( v47 == 48 )
        {
          v48 = v70;
        }
        else if ( (*(dword_1572A8 + 2 * v47) & 4) != 0 )
        {
          v48 = v70;
          if ( v40[3] == 36 )
          {
            v46 = v40 + 4;
            v48 = v47 - 49;
          }
        }
        else
        {
          v48 = v70;
        }
        v51 = v71[2 * v48];
        if ( v51 < 0 )
          v51 = -v51;
        v37 += sprintf(s: v37, format: &dword_730C0, v51);
        ++v70;
        v34 = *v46;
      }
      else if ( (*(dword_1572A8 + 2 * v34) & 4) != 0 )
      {
        v49 = v40 + 2;
        do
        {
          *v37++ = v34;
          v50 = *v49++;
          v34 = v50;
        }
        while ( (*(dword_1572A8 + 2 * v50) & 4) != 0 );
        v46 = v49 - 1;
      }
    }
    else
    {
      v46 = v40;
    }
    if ( memchr(s: &dword_72DC0, c: v34, n: 4u) != nullptr )
    {
      v52 = 0;
      v53 = 0;
      while ( 1 )
      {
        switch ( v34 )
        {
          case 'L':
            v52 = 2;
            break;
          case 'h':
            v53 = 1;
            break;
          case 'l':
            ++v52;
            break;
          default:
            v64 = 7;
            goto LABEL_178;
        }
        *v37++ = v34;
        v54 = *++v46;
        LOBYTE(v34) = v54;
        if ( memchr(s: &dword_73234, c: v54, n: 4u) == nullptr )
          goto LABEL_145;
      }
    }
    v53 = 0;
    v52 = 0;
LABEL_145:
    *v37 = v34;
    v37[1] = 0;
    if ( v36 < 0 )
      v36 = v70;
    v4 = (v46 + 1);
    switch ( *v46 )
    {
      case 'A':
        v56 = v71[2 * v36];
        if ( v56 == 0 )
        {
          v64 = 114;
LABEL_178:
          sub_71440(a1: "bfd.c", a2: v64 | 0x300, a3: "int _bfd_doprnt(FILE *, const char *, union _bfd_doprnt_args *)");
        }
        v57 = *(v56 + 148);
        v29 = streama;
        v30 = v66;
        if ( v57 == 0 )
          goto LABEL_174;
        v58 = *(*(v57 + 4) + 4);
        if ( v58 == 2 )
        {
          v60 = *(v56 + 140);
          v62 = v60 == nullptr;
          if ( v60 != nullptr )
          {
            v60 = v60[9];
            v62 = v60 == nullptr;
          }
          if ( !v62 )
            goto LABEL_85;
LABEL_174:
          v32 = fprintf(stream: v29, format: "%s", *v56);
          goto LABEL_175;
        }
        if ( v58 != 5 )
          goto LABEL_174;
        v59 = *(v56 + 140);
        if ( *(v59 + 124) == 0 || (*(v56 + 23) & 2) != 0 )
          goto LABEL_174;
        v60 = (v59 + 116);
LABEL_85:
        v31 = *v56;
        if ( *v60 != 0 )
          v32 = fprintf(stream: streama, format: "%s[%s]", v31);
        else
          v32 = fprintf(stream: streama, format: "%s", v31);
LABEL_175:
        ++v70;
        if ( v32 != -1 )
          continue;
LABEL_176:
        fputc(c: 10, stream: stderr);
        return fflush(stream: stderr);
      case 'B':
        v56 = v71[2 * v36];
        if ( v56 == 0 )
          sub_71440(a1: "bfd.c", a2: 908, a3: "int _bfd_doprnt(FILE *, const char *, union _bfd_doprnt_args *)");
        v61 = *(v56 + 140);
        v29 = streama;
        v30 = v66;
        if ( v61 == 0 || (*(v61 + 44) & 1) != 0 )
          goto LABEL_174;
        v32 = fprintf(stream: streama, format: "%s(%s)", *v61);
        goto LABEL_175;
      case 'E':
      case 'G':
      case 'e':
      case 'f':
      case 'g':
        v29 = streama;
        v32 = fprintf(stream: streama, &format, v71[2 * v36], v71[2 * v36 + 1]);
        goto LABEL_153;
      case 'X':
      case 'c':
      case 'd':
      case 'i':
      case 'o':
      case 'u':
      case 'x':
        if ( v53 != 0 )
          goto LABEL_151;
        if ( *(v46 - 1) == 76 )
        {
          v30 = v66;
          *(v37 - 1) = 108;
        }
        else
        {
          v30 = v66;
          v55 = v52 == 1;
          if ( v52 != 1 )
            v55 = v52 == 0;
          if ( !v55 )
          {
            v29 = streama;
            v32 = fprintf(stream: streama, &format, v71[2 * v36], v71[2 * v36 + 1]);
            goto LABEL_175;
          }
        }
        v29 = streama;
        v32 = fprintf(stream: streama, &format, v71[2 * v36]);
        goto LABEL_175;
      case 'p':
      case 's':
LABEL_151:
        v29 = streama;
        v32 = fprintf(stream: streama, &format, v71[2 * v36]);
LABEL_153:
        v30 = v66;
        goto LABEL_175;
      default:
        v64 = 150;
        goto LABEL_178;
    }
  }
}
~~~

// binutils-2.30_clang-7.0_x86_32_O0_ranlib.elf.strip@0x805a5c0
unsigned int __cdecl sub_805A5C0(char *a1, int a2)
{
  int v3; 
  unsigned int v4; 
  unsigned int v5; 
  int v6; 
  int v7; 
  int v8; 
  int v9; 
  unsigned int v10; 
  char *sa; 

  v10 = 0;
  while ( *a1 != 0 )
  {
    if ( *a1 == 37 )
    {
      if ( a1[1] == 37 )
      {
        a1 += 2;
      }
      else
      {
        v9 = 0;
        v8 = 0;
        sa = a1 + 1;
        v7 = -1;
        if ( *sa != 48 && (word_8167F5C[*sa] & 4) != 0 && sa[1] == 36 )
        {
          v7 = *sa - 49;
          sa += 2;
        }
        while ( strchr(s: "-+ #0'I", c: *sa) != nullptr )
          ++sa;
        if ( *sa == 42 )
        {
          ++sa;
          v5 = v10;
          if ( *sa != 48 && (word_8167F5C[*sa] & 4) != 0 && sa[1] == 36 )
          {
            v5 = *sa - 49;
            sa += 2;
          }
          if ( v5 >= 9 )
            sub_8058740(
              a1: "bfd.c",
              a2: 980,
              a3: "unsigned int _bfd_doprnt_scan(const char *, union _bfd_doprnt_args *)");
          *(12 * v5 + a2) = 1;
          ++v10;
        }
        else
        {
          while ( (word_8167F5C[*sa] & 4) != 0 )
            ++sa;
        }
        if ( *sa == 46 )
        {
          if ( *++sa == 42 )
          {
            ++sa;
            v4 = v10;
            if ( *sa != 48 && (word_8167F5C[*sa] & 4) != 0 && sa[1] == 36 )
            {
              v4 = *sa - 49;
              sa += 2;
            }
            if ( v4 >= 9 )
              sub_8058740(
                a1: "bfd.c",
                a2: 1005,
                a3: "unsigned int _bfd_doprnt_scan(const char *, union _bfd_doprnt_args *)");
            *(12 * v4 + a2) = 1;
            ++v10;
          }
          else
          {
            while ( (word_8167F5C[*sa] & 4) != 0 )
              ++sa;
          }
        }
        while ( strchr(s: "hlL", c: *sa) != nullptr )
        {
          v3 = *sa;
          switch ( v3 )
          {
            case 'L':
              v9 = 2;
              break;
            case 'h':
              v8 = 1;
              break;
            case 'l':
              ++v9;
              break;
            default:
              sub_8058740(
                a1: "bfd.c",
                a2: 1028,
                a3: "unsigned int _bfd_doprnt_scan(const char *, union _bfd_doprnt_args *)");
          }
          ++sa;
        }
        a1 = sa + 1;
        if ( v7 < 0 )
          v7 = v10;
        switch ( *(a1 - 1) )
        {
          case 'A':
          case 'B':
          case 'p':
          case 's':
            v6 = 6;
            break;
          case 'E':
          case 'G':
          case 'e':
          case 'f':
          case 'g':
            if ( v9 != 0 )
              v6 = 5;
            else
              v6 = 4;
            break;
          case 'X':
          case 'c':
          case 'd':
          case 'i':
          case 'o':
          case 'u':
          case 'x':
            if ( v8 != 0 )
            {
              v6 = 1;
            }
            else
            {
              if ( *(a1 - 2) == 76 )
                v9 = 1;
              if ( v9 != 0 )
              {
                if ( v9 == 1 )
                  v6 = 2;
                else
                  v6 = 3;
              }
              else
              {
                v6 = 1;
              }
            }
            break;
          default:
            sub_8058740(
              a1: "bfd.c",
              a2: 1103,
              a3: "unsigned int _bfd_doprnt_scan(const char *, union _bfd_doprnt_args *)");
        }
        if ( v7 >= 9 )
          sub_8058740(
            a1: "bfd.c",
            a2: 1107,
            a3: "unsigned int _bfd_doprnt_scan(const char *, union _bfd_doprnt_args *)");
        *(12 * v7 + a2) = v6;
        ++v10;
      }
    }
    else
    {
      a1 = strchr(s: a1, c: 37);
      if ( a1 == nullptr )
        return v10;
    }
  }
  return v10;
}
