
/* WARNING: Removing unreachable block (ram,0x00401553) */
/* WARNING: Removing unreachable block (ram,0x004014fe) */
/* WARNING: Removing unreachable block (ram,0x00401718) */
/* WARNING: Removing unreachable block (ram,0x00401641) */
/* WARNING: Removing unreachable block (ram,0x004016d5) */

int classify(int param_1)

{
  int local_18;
  int local_14;
  
  if (param_1 < 0) {
    puts(&DAT_00404080);
    local_14 = -1;
  }
  else if (param_1 % 2 == 0) {
    puts(&DAT_004040a0);
    local_14 = param_1 / 2;
  }
  else {
    puts(&DAT_004040c0);
    local_14 = param_1 * 3 + 1;
  }
  for (local_18 = 0; local_18 < param_1 && local_18 < 8; local_18 = local_18 + 1) {
    local_14 = local_14 + local_18;
  }
  return local_14;
}

