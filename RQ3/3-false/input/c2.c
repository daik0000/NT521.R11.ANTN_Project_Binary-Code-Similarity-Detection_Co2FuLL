// a2ps-4.14_gcc-7.3.0_arm_64_O3_a2ps.elf.strip@0x416a10
int __fastcall sub_416A10(FILE *a1)
{
  int v2; 
  int v3; 
  int *v4; 
  int v5; 
  int *v6; 
  _BYTE *v7; 
  char *v8; 
  int v9; 
  _BOOL4 v10;
  int v11; 
  int v12; 
  unsigned int *v13; 
  int v14; 
  int result; 
  int v16; 
  int v17; 
  char v18; 
  int v19; 
  int v20; 
  int v21; 
  _QWORD *v22; 
  int v23; 

  if ( qword_4647B0 != 0 )
  {
    v2 = qword_4647B0 + 8 * qword_4647C0;
    v3 = *v2;
    if ( *v2 != 0 )
    {
      v4 = __errno_location();
      v5 = *v4;
      v6 = v4;
      goto LABEL_4;
    }
    if ( qword_4647C0 >= (qword_4647B8 - 1) )
    {
      v19 = qword_4647B8 + 8;
      v20 = sub_440838();
      v21 = qword_4647B8;
      qword_4647B0 = v20;
      qword_4647B8 = v19;
      v22 = (v20 + 8 * v21);
      v2 = v20 + 8 * qword_4647C0;
      *v22 = 0;
      v22[1] = 0;
      v22[2] = 0;
      v22[3] = 0;
      v22[4] = 0;
      v22[5] = 0;
      v22[6] = 0;
      v22[7] = 0;
    }
  }
  else
  {
    v23 = sub_440828(a1: 8);
    v2 = v23;
    qword_4647B0 = v23;
    qword_4647B8 = 1;
    qword_4647C0 = 0;
    *v23 = 0;
  }
  *v2 = sub_4168D0(a1: qword_4647D8, a2: 0x4000);
  if ( qword_4647B0 == 0 )
  {
    MEMORY[0] = a1;
    __break(0x3E8u);
  }
  v2 = qword_4647B0 + 8 * qword_4647C0;
  v3 = *v2;
  v6 = __errno_location();
  v5 = *v6;
  if ( v3 == 0 )
  {
    MEMORY[0] = a1;
    __break(0x3E8u);
  }
LABEL_4:
  v7 = *(v3 + 8);
  *(v3 + 28) = 0;
  *v7 = 0;
  *(*(v3 + 8) + 1LL) = 0;
  v8 = *(v3 + 8);
  v9 = *v2;
  *(v3 + 16) = v8;
  *(v3 + 40) = 1;
  *(v3 + 56) = 0;
  if ( v3 == v9 )
  {
    v16 = *v3;
    qword_465540 = v8;
    qword_4647D8 = v16;
    v17 = *(v3 + 28);
    qword_4647C8 = v8;
    v18 = *v8;
    dword_4647D4 = v17;
    byte_4647D0 = v18;
    *v3 = a1;
    *(v3 + 52) = 1;
  }
  else
  {
    *v3 = a1;
    *(v3 + 52) = 1;
    *(v3 + 44) = 1;
  }
  v10 = false;
  if ( a1 != nullptr )
  {
    v11 = fileno(stream: a1);
    v12 = isatty(fd: v11);
    v9 = *v2;
    v10 = v12 > 0;
  }
  v13 = *(v9 + 16);
  *(v3 + 36) = v10;
  v14 = *v9;
  *v6 = v5;
  qword_465540 = v13;
  qword_4647D8 = v14;
  qword_4647C8 = v13;
  result = *v13;
  dword_4647D4 = *(v9 + 28);
  byte_4647D0 = result;
  return result;
}
~~~

// a2ps-4.14_gcc-6.4.0_arm_64_O3_a2ps.elf.strip@0x4189e0
int __fastcall sub_4189E0(int a1)
{
  int result; 
  int v3; 
  int v4; 
  int *v5; 
  int v6; 
  int v7; 
  int v8; 
  unsigned int *v9; 
  int v10; 
  int v11; 
  int v12; 
  int v13; 
  int v14; 
  int v15; 

  result = qword_464810;
  if ( qword_464810 == 0 )
  {
    LODWORD(result) = sub_440D60(a1: 8);
    qword_464810 = result;
    result = result;
    *result = 0;
    qword_464818 = 1;
    qword_464820 = 0;
    goto LABEL_10;
  }
  v3 = qword_464820;
  if ( qword_464818 - 1 > qword_464820 )
  {
LABEL_3:
    v4 = *(result + 8 * v3);
    v5 = (result + 8 * v3);
    if ( v4 == a1 )
      return result;
    if ( v4 != 0 )
    {
      v6 = qword_464828;
      v7 = dword_464834;
      *qword_464828 = byte_464830;
      v8 = *v5;
      *(v8 + 16) = v6;
      *(v8 + 28) = v7;
    }
    goto LABEL_6;
  }
  v12 = qword_464818 + 8;
  v13 = sub_440D70();
  v14 = v13;
  v15 = qword_464818;
  qword_464810 = v13;
  qword_464818 = v12;
  result = v13 + 8 * v15;
  *result = 0;
  *(result + 8) = 0;
  *(result + 16) = 0;
  *(result + 24) = 0;
  *(result + 32) = 0;
  *(result + 40) = 0;
  *(result + 48) = 0;
  *(result + 56) = 0;
  if ( v14 != 0 )
  {
    result = v14;
LABEL_10:
    v3 = qword_464820;
    goto LABEL_3;
  }
  if ( a1 != 0 )
  {
    v5 = (8 * qword_464820);
LABEL_6:
    v9 = *(a1 + 16);
    v10 = *a1;
    v11 = *(a1 + 28);
    *v5 = a1;
    qword_465568 = v9;
    qword_464838 = v10;
    qword_464828 = v9;
    result = *v9;
    dword_464834 = v11;
    byte_464830 = result;
  }
  return result;
}
