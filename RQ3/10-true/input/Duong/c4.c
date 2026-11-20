// a2ps-4.14_gcc-4.9.4_arm_32_O3_a2ps.elf.strip@0x26214
_BYTE *__fastcall sub_26214(_BYTE *result)
{
  _BYTE *v1; // r6
  int v2; // r5
  int v3; // r3
  _BYTE *v4; // r2
  int v5; // r5
  int v6; // r3
  int v7; // r2
  int *v8; // r1
  int v9; // r1
  char v10; // r3
  int v11; // r7

  v1 = result;
  v2 = dword_724AC;
  if ( dword_724AC == 0 )
  {
    result = sub_4F9A0(a1: 4);
    *result = 0;
    result[1] = 0;
    result[2] = 0;
    dword_724B4 = 0;
    result[3] = 0;
    dword_724AC = result;
    dword_724B0 = 1;
    v2 = result;
    goto LABEL_9;
  }
  v3 = dword_724B4;
  if ( dword_724B0 - 1 > dword_724B4 )
  {
LABEL_3:
    v4 = *(v2 + 4 * v3);
    v5 = v2 + 4 * v3;
    if ( v4 == v1 )
      return result;
    if ( v4 != nullptr )
    {
      v6 = dword_724B8;
      v7 = dword_724C0;
      *dword_724B8 = byte_724BC;
      *(*v5 + 8) = v6;
      *(*v5 + 16) = v7;
    }
    goto LABEL_6;
  }
  v11 = dword_724B0 + 8;
  v2 = sub_4F9B8(a1: dword_724AC, a2: 4 * (dword_724B0 + 8));
  dword_724AC = v2;
  result = memset(s: (v2 + 4 * dword_724B0), c: 0, n: 0x20u);
  dword_724B0 = v11;
  if ( v2 != 0 )
  {
LABEL_9:
    v3 = dword_724B4;
    goto LABEL_3;
  }
  if ( v1 != nullptr )
  {
    v5 = 4 * dword_724B4;
LABEL_6:
    *v5 = v1;
    result = *(v1 + 4);
    dword_72BE8 = *(v1 + 2);
    v8 = *v5;
    dword_724B8 = dword_72BE8;
    v9 = *v8;
    dword_724C0 = result;
    dword_724C4 = v9;
    v10 = *dword_72BE8;
    dword_724C8 = 1;
    byte_724BC = v10;
  }
  return result;
}

// a2ps-4.14_gcc-8.2.0_arm_64_O3_a2ps.elf.strip@0x416150
char *__fastcall sub_416150(__int64 a1)
{
  __int64 v2; // x2
  char *result; // x0
  __int64 v4; // x1
  int v5; // w3
  char *v6; // x0
  int v7; // w1
  char v8; // w2
  __int64 v9; // x21
  __int64 v10; // x1
  _QWORD *v11; // x1
  int v12; // w0

  if ( qword_46B7B8 == 0 )
  {
    v12 = sub_43E3F8(a1: 8);
    v2 = v12;
    qword_46B7B8 = v12;
    qword_46B7C0 = 0;
    *v12 = 0;
    qword_46B7E0 = 1;
    goto LABEL_3;
  }
  v2 = qword_46B7B8 + 8 * qword_46B7C0;
  if ( qword_46B7E0 - 1 > qword_46B7C0 )
  {
LABEL_3:
    result = *v2;
    if ( *v2 == a1 )
      return result;
    if ( result != nullptr )
    {
      v4 = qword_46B7C8;
      v5 = dword_46B7EC;
      *qword_46B7C8 = byte_46B7E8;
      v6 = *v2;
      *(v6 + 2) = v4;
      *(v6 + 7) = v5;
    }
    goto LABEL_6;
  }
  v9 = qword_46B7E0 + 8;
  result = sub_43E408();
  v10 = qword_46B7E0;
  qword_46B7B8 = result;
  qword_46B7E0 = v9;
  v11 = (result + 8 * v10);
  *v11 = 0;
  v11[1] = 0;
  v11[2] = 0;
  v11[3] = 0;
  v11[4] = 0;
  v11[5] = 0;
  v11[6] = 0;
  v11[7] = 0;
  if ( result != 0 )
  {
    v2 = result + 8 * qword_46B7C0;
    goto LABEL_3;
  }
  if ( a1 != 0 )
  {
    v2 = 8 * qword_46B7C0;
LABEL_6:
    result = *(a1 + 16);
    *v2 = a1;
    qword_46C550 = result;
    qword_46B7F0 = *a1;
    v7 = *(a1 + 28);
    v8 = *result;
    qword_46B7C8 = result;
    byte_46B7E8 = v8;
    dword_46B7EC = v7;
  }
  return result;
}
