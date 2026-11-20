
void decode(byte *param_1)

{
  byte *local_10;
  
  for (local_10 = param_1; *local_10 != 0x5a; local_10 = local_10 + 1) {
    *local_10 = *local_10 ^ 0x5a;
  }
  *local_10 = 0;
  return;
}

