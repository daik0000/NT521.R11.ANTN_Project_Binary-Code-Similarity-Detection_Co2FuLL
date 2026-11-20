
undefined8 main(int param_1)

{
  uint uVar1;
  uint uVar2;
  void *__ptr;
  
  greet("BinKit");
  uVar1 = compute(6,7);
  uVar2 = classify(uVar1 + param_1);
  __ptr = (void *)duplicate_message("binary code similarity detection");
  printf("result=%d class=%d msg=%s\n",(ulong)uVar1,(ulong)uVar2,__ptr);
  free(__ptr);
  return 0;
}

