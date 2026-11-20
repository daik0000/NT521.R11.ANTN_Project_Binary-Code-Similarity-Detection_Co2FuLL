
undefined8 copy_secret(void)

{
  long lVar1;
  undefined8 uVar2;
  
  decode(enc_msg2);
  lVar1 = (*(code *)ptr_strlen)(enc_msg2);
  uVar2 = (*(code *)ptr_malloc)(lVar1 + 1);
  (*(code *)ptr_memset)(uVar2,0,lVar1 + 1);
  (*(code *)ptr_strcpy)(uVar2,enc_msg2);
  return uVar2;
}

