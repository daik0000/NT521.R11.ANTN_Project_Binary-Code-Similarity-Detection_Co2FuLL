
char * duplicate_message(char *param_1)

{
  size_t sVar1;
  char *__dest;
  
  sVar1 = strlen(param_1);
  __dest = (char *)malloc(sVar1 + 1);
  memset(__dest,0,sVar1 + 1);
  strcpy(__dest,param_1);
  return __dest;
}

