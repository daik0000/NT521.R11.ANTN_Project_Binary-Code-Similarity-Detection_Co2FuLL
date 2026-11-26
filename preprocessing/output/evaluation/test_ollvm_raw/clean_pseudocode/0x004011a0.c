
void greet(undefined8 param_1)

{
  char *pcVar1;
  char *pcVar2;
  bool bVar3;
  undefined1 auStack_38 [8];
  char *local_30;
  char *local_28;
  int local_1c;
  undefined8 local_18;
  int local_10;
  byte local_a;
  byte local_9;
  
  local_a = (x * (x + -1) & 1U) == 0;
  local_9 = y < 10;
  local_10 = -0x41222767;
  pcVar1 = auStack_38;
  local_18 = param_1;
  do {
    while( true ) {
      while( true ) {
        while (local_1c = local_10, local_10 == -0x5ea276cd) {
          pcVar2 = pcVar1 + -0x50;
          *(undefined8 *)(pcVar1 + -0x10) = local_18;
          pcVar1[-0x58] = -0x5b;
          pcVar1[-0x57] = '\x12';
          pcVar1[-0x56] = '@';
          pcVar1[-0x55] = '\0';
          pcVar1[-0x54] = '\0';
          pcVar1[-0x53] = '\0';
          pcVar1[-0x52] = '\0';
          pcVar1[-0x51] = '\0';
          local_28 = pcVar2;
          snprintf(pcVar2,0x40,"Hello, %s!",*(undefined8 *)(pcVar1 + -0x10));
          pcVar1[-0x58] = -0x46;
          pcVar1[-0x57] = '\x12';
          pcVar1[-0x56] = '@';
          pcVar1[-0x55] = '\0';
          pcVar1[-0x54] = '\0';
          pcVar1[-0x53] = '\0';
          pcVar1[-0x52] = '\0';
          pcVar1[-0x51] = '\0';
          printf("%s\n");
          bVar3 = (x * (x + -1) & 1U) == 0;
          local_10 = 0x4167b0fb;
          pcVar1 = pcVar2;
          if (bVar3 != y < 10 || bVar3 && y < 10) {
            local_10 = 0x62493309;
          }
        }
        if (local_10 != -0x41222767) break;
        local_10 = 0x4167b0fb;
        if (((local_a & local_9 | local_a ^ local_9) & 1) != 0) {
          local_10 = -0x5ea276cd;
        }
      }
      if (local_10 != 0x4167b0fb) break;
      pcVar2 = pcVar1 + -0x50;
      *(undefined8 *)(pcVar1 + -0x10) = local_18;
      pcVar1[-0x58] = 'v';
      pcVar1[-0x57] = '\x13';
      pcVar1[-0x56] = '@';
      pcVar1[-0x55] = '\0';
      pcVar1[-0x54] = '\0';
      pcVar1[-0x53] = '\0';
      pcVar1[-0x52] = '\0';
      pcVar1[-0x51] = '\0';
      local_30 = pcVar2;
      snprintf(pcVar2,0x40,"Hello, %s!",*(undefined8 *)(pcVar1 + -0x10));
      pcVar1[-0x58] = -0x75;
      pcVar1[-0x57] = '\x13';
      pcVar1[-0x56] = '@';
      pcVar1[-0x55] = '\0';
      pcVar1[-0x54] = '\0';
      pcVar1[-0x53] = '\0';
      pcVar1[-0x52] = '\0';
      pcVar1[-0x51] = '\0';
      printf("%s\n",local_30);
      local_10 = -0x5ea276cd;
      pcVar1 = pcVar2;
    }
  } while (local_10 != 0x62493309);
  return;
}

