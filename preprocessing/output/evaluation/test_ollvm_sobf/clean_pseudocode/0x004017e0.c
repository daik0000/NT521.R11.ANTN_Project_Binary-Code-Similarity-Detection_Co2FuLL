
undefined8 main(int param_1)

{
  uint uVar1;
  uint uVar2;
  void *__ptr;
  
  greet(&DAT_004040d4);
  uVar1 = compute(6,7);
  uVar2 = classify(-(-param_1 - uVar1));
  __ptr = (void *)duplicate_message(&DAT_004040e0);
  printf(&DAT_00404110,(ulong)uVar1,(ulong)uVar2,__ptr);
  free(__ptr);
  return 0;
}

