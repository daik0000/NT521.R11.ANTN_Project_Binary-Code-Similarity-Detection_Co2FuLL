
undefined8 duplicate_message(undefined8 param_1)

{
  char *pcVar1;
  char *pcVar2;
  size_t *psVar3;
  undefined8 *puVar4;
  size_t sVar5;
  void *pvVar6;
  size_t **ppsVar7;
  bool bVar8;
  size_t *local_58;
  undefined8 *local_50;
  undefined8 *local_48;
  size_t *local_40;
  undefined8 *local_38;
  undefined8 *local_30;
  int local_24;
  undefined8 local_20;
  int local_18;
  bool local_12;
  bool local_11;
  undefined8 local_10;
  
  local_20 = param_1;
  local_12 = (x_13 * (x_13 + -1) & 1U) == 0;
  local_11 = y_14 < 10;
  local_18 = -0x62d3e926;
  ppsVar7 = &local_58;
  do {
    while( true ) {
      while( true ) {
        while (local_24 = local_18, local_18 == -0x62d3e926) {
          local_18 = -0x295e2caa;
          if (((local_12 & local_11 | local_12 ^ local_11) & 1U) != 0) {
            local_18 = -0x6104ab7d;
          }
        }
        if (local_18 != -0x6104ab7d) break;
        local_38 = ppsVar7 + -2;
        local_40 = (size_t *)(ppsVar7 + -4);
        local_30 = ppsVar7 + -6;
        *local_38 = local_20;
        ppsVar7[-7] = (size_t *)0x401d8e;
        sVar5 = strlen((char *)*local_38);
        psVar3 = local_40;
        *local_40 = sVar5;
        sVar5 = *psVar3;
        ppsVar7[-7] = (size_t *)0x401db5;
        pvVar6 = malloc(-(-1 - sVar5));
        puVar4 = local_30;
        psVar3 = local_40;
        *local_30 = pvVar6;
        pvVar6 = (void *)*puVar4;
        sVar5 = *psVar3;
        ppsVar7[-7] = (size_t *)0x401de5;
        memset(pvVar6,0,-(-1 - sVar5));
        pcVar1 = (char *)*local_30;
        pcVar2 = (char *)*local_38;
        ppsVar7[-7] = (size_t *)0x401df8;
        strcpy(pcVar1,pcVar2);
        local_10 = *local_30;
        bVar8 = (x_13 * (x_13 + -1) & 1U) != 0;
        local_18 = -0x295e2caa;
        if (bVar8 != 9 < y_14 || !bVar8 && 9 >= y_14) {
          local_18 = -0x1c05e2ab;
        }
        ppsVar7 = ppsVar7 + -6;
      }
      if (local_18 != -0x295e2caa) break;
      local_48 = ppsVar7 + -2;
      local_58 = (size_t *)(ppsVar7 + -4);
      local_50 = ppsVar7 + -6;
      *local_48 = local_20;
      ppsVar7[-7] = (size_t *)0x401ecc;
      sVar5 = strlen((char *)*local_48);
      psVar3 = local_58;
      *local_58 = sVar5;
      sVar5 = *psVar3;
      ppsVar7[-7] = (size_t *)0x401efc;
      pvVar6 = malloc(sVar5 + 1);
      puVar4 = local_50;
      psVar3 = local_58;
      *local_50 = pvVar6;
      pvVar6 = (void *)*puVar4;
      sVar5 = *psVar3;
      ppsVar7[-7] = (size_t *)0x401f2c;
      memset(pvVar6,0,-(-1 - sVar5));
      pcVar1 = (char *)*local_50;
      pcVar2 = (char *)*local_48;
      ppsVar7[-7] = (size_t *)0x401f3f;
      strcpy(pcVar1,pcVar2);
      local_18 = -0x6104ab7d;
      ppsVar7 = ppsVar7 + -6;
    }
  } while (local_18 != -0x1c05e2ab);
  return local_10;
}

