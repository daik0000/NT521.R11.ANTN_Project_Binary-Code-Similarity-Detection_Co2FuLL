
void _datadiv_decode6065282123340875853(void)

{
  bool bVar1;
  uint local_84;
  uint local_74;
  uint local_64;
  uint local_54;
  uint local_44;
  uint local_34;
  uint local_24;
  uint local_14;
  uint local_4;
  
  local_4 = 0;
  do {
    (&DAT_00404050)[(int)local_4] =
         (~(&DAT_00404050)[(int)local_4] & 0x56 | (&DAT_00404050)[(int)local_4] & 0xa9) ^ 0xe4;
    bVar1 = local_4 < 10;
    local_4 = local_4 + 1;
  } while (bVar1);
  local_14 = 0;
  do {
    (&DAT_0040405b)[(int)local_14] =
         ~(&DAT_0040405b)[(int)local_14] & 0xee | (&DAT_0040405b)[(int)local_14] & 0x11;
    bVar1 = local_14 < 3;
    local_14 = local_14 + 1;
  } while (bVar1);
  local_24 = 0;
  do {
    (&DAT_00404060)[(int)local_24] =
         (~(&DAT_00404060)[(int)local_24] & 0xa8 | (&DAT_00404060)[(int)local_24] & 0x57) ^ 6;
    bVar1 = local_24 < 0x13;
    local_24 = local_24 + 1;
  } while (bVar1);
  local_34 = 0;
  do {
    (&DAT_00404080)[(int)local_34] =
         (~(&DAT_00404080)[(int)local_34] & 0x75 | (&DAT_00404080)[(int)local_34] & 0x8a) ^ 0x5c;
    bVar1 = local_34 < 0x18;
    local_34 = local_34 + 1;
  } while (bVar1);
  local_44 = 0;
  do {
    (&DAT_004040a0)[(int)local_44] =
         (~(&DAT_004040a0)[(int)local_44] & 0xef | (&DAT_004040a0)[(int)local_44] & 0x10) ^ 0x7e;
    bVar1 = local_44 < 0x14;
    local_44 = local_44 + 1;
  } while (bVar1);
  local_54 = 0;
  do {
    (&DAT_004040c0)[(int)local_54] =
         (~(&DAT_004040c0)[(int)local_54] & 0x79 | (&DAT_004040c0)[(int)local_54] & 0x86) ^ 0xf1;
    bVar1 = local_54 < 0x13;
    local_54 = local_54 + 1;
  } while (bVar1);
  local_64 = 0;
  do {
    (&DAT_004040d4)[(int)local_64] =
         ~(&DAT_004040d4)[(int)local_64] & 0xd6 | (&DAT_004040d4)[(int)local_64] & 0x29;
    bVar1 = local_64 < 6;
    local_64 = local_64 + 1;
  } while (bVar1);
  local_74 = 0;
  do {
    (&DAT_004040e0)[(int)local_74] =
         (~(&DAT_004040e0)[(int)local_74] & 0xad | (&DAT_004040e0)[(int)local_74] & 0x52) ^ 0x43;
    bVar1 = local_74 < 0x20;
    local_74 = local_74 + 1;
  } while (bVar1);
  local_84 = 0;
  do {
    (&DAT_00404110)[(int)local_84] =
         ~(&DAT_00404110)[(int)local_84] & 0x47 | (&DAT_00404110)[(int)local_84] & 0xb8;
    bVar1 = local_84 < 0x1a;
    local_84 = local_84 + 1;
  } while (bVar1);
  return;
}

