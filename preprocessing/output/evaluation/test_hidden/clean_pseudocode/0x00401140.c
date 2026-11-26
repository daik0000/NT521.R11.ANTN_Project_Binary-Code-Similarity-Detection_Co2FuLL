
bool main(void)

{
  int iVar1;
  undefined1 local_38 [32];
  undefined8 local_18;
  undefined4 local_c;
  
  local_c = 0;
  iVar1 = resolve_all();
  if (iVar1 == 0) {
    decode(enc_msg1);
    (*(code *)ptr_puts)(enc_msg1);
    local_18 = copy_secret();
    (*(code *)ptr_puts)(local_18);
    decode(enc_fmt);
    (*(code *)ptr_snprintf)(local_38,0x20,enc_fmt,0x2a);
    (*(code *)ptr_puts)(local_38);
    (*(code *)ptr_free)(local_18);
  }
  return iVar1 != 0;
}

