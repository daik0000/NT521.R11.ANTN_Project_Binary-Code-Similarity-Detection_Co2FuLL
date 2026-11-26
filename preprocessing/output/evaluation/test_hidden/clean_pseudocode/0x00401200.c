
undefined4 resolve_all(void)

{
  long lVar1;
  undefined4 local_c;
  
  decode(enc_libc);
  lVar1 = dlopen(enc_libc,2);
  if (lVar1 == 0) {
    local_c = 0xffffffff;
  }
  else {
    ptr_puts = (undefined *)resolve(lVar1,&enc_puts);
    ptr_malloc = (undefined *)resolve(lVar1,&enc_malloc);
    ptr_free = (undefined *)resolve(lVar1,&enc_free);
    ptr_strlen = (undefined *)resolve(lVar1,&enc_strlen);
    ptr_memset = (undefined *)resolve(lVar1,&enc_memset);
    ptr_strcpy = (undefined *)resolve(lVar1,&enc_strcpy);
    ptr_snprintf = (undefined *)resolve(lVar1,enc_snprintf);
    local_c = 0;
  }
  return local_c;
}

