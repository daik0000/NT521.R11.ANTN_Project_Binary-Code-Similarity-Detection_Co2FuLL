
uint compute(int param_1,int param_2)

{
  uint uVar1;
  uint *__ptr;
  
  __ptr = (uint *)malloc(8);
  *__ptr = param_1 + param_2;
  __ptr[1] = param_1 * param_2;
  printf(&DAT_00404060,(ulong)*__ptr,(ulong)__ptr[1]);
  uVar1 = *__ptr;
  free(__ptr);
  return uVar1;
}

