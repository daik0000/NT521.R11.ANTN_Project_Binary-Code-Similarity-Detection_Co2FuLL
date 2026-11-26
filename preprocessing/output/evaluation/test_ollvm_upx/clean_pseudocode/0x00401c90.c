
/* WARNING: Removing unreachable block (ram,0x00401d46) */
/* WARNING: Removing unreachable block (ram,0x00401e7b) */
/* WARNING: Removing unreachable block (ram,0x00401e93) */

undefined8 duplicate_message(char *param_1)

{
  size_t *psVar1;
  undefined8 *puVar2;
  size_t sVar3;
  void *pvVar4;
  undefined8 local_88 [2];
  size_t local_78 [2];
  char *local_68 [5];
  size_t *local_40;
  char **local_38;
  undefined8 *local_30;
  char *local_20;
  undefined1 local_12;
  undefined1 local_11;
  undefined8 local_10;
  
  local_20 = param_1;
  local_12 = 1;
  local_11 = 1;
  local_11 = 1;
  local_12 = 1;
  local_38 = local_68;
  local_40 = local_78;
  local_30 = local_88;
  local_68[0] = param_1;
  sVar3 = strlen(param_1);
  psVar1 = local_40;
  *local_40 = sVar3;
  pvVar4 = malloc(-(-1 - *psVar1));
  puVar2 = local_30;
  psVar1 = local_40;
  *local_30 = pvVar4;
  memset((void *)*puVar2,0,-(-1 - *psVar1));
  strcpy((char *)*local_30,*local_38);
  local_10 = *local_30;
  return *local_30;
}

