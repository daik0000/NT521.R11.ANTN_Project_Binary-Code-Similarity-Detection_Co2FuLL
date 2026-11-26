
/* WARNING: Removing unreachable block (ram,0x00401bb6) */
/* WARNING: Removing unreachable block (ram,0x00401a91) */
/* WARNING: Removing unreachable block (ram,0x00401944) */
/* WARNING: Removing unreachable block (ram,0x004016bc) */
/* WARNING: Removing unreachable block (ram,0x0040181f) */
/* WARNING: Removing unreachable block (ram,0x004018a6) */
/* WARNING: Removing unreachable block (ram,0x00401c4b) */
/* WARNING: Removing unreachable block (ram,0x0040171f) */
/* WARNING: Removing unreachable block (ram,0x00401c29) */
/* WARNING: Removing unreachable block (ram,0x0040199f) */
/* WARNING: Removing unreachable block (ram,0x00401c57) */
/* WARNING: Removing unreachable block (ram,0x00401b2b) */
/* WARNING: Removing unreachable block (ram,0x00401c63) */
/* WARNING: Removing unreachable block (ram,0x00401c11) */
/* WARNING: Removing unreachable block (ram,0x00401c82) */

int classify(int param_1)

{
  int local_20;
  int local_1c;
  
  if (param_1 < 0) {
    puts("classify: negative value");
    local_1c = -1;
  }
  else if (param_1 % 2 == 0) {
    puts("classify: even value");
    local_1c = param_1 / 2;
  }
  else {
    puts("classify: odd value");
    local_1c = param_1 * 3 + 1;
  }
  for (local_20 = 0; local_20 < param_1 && local_20 < 8; local_20 = local_20 + 1) {
    local_1c = local_1c + local_20;
  }
  return local_1c;
}

