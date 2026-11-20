
/* WARNING: Removing unreachable block (ram,0x0040125e) */
/* WARNING: Removing unreachable block (ram,0x0040132a) */
/* WARNING: Removing unreachable block (ram,0x0040133e) */

void greet(undefined8 param_1)

{
  char acStack_88 [64];
  undefined8 local_48;
  char *local_28;
  undefined8 local_18;
  undefined1 local_a;
  undefined1 local_9;
  
  local_9 = 1;
  local_a = 1;
  local_28 = acStack_88;
  local_18 = param_1;
  local_48 = param_1;
  snprintf(local_28,0x40,"Hello, %s!",param_1);
  printf("%s\n");
  return;
}

