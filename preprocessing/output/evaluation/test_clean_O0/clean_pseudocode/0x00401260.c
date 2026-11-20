
int classify(int param_1)

{
  int local_14;
  int local_10;
  
  if (param_1 < 0) {
    puts("classify: negative value");
    local_10 = -1;
  }
  else if (param_1 % 2 == 0) {
    puts("classify: even value");
    local_10 = param_1 / 2;
  }
  else {
    puts("classify: odd value");
    local_10 = param_1 * 3 + 1;
  }
  for (local_14 = 0; local_14 < param_1 && local_14 < 8; local_14 = local_14 + 1) {
    local_10 = local_14 + local_10;
  }
  return local_10;
}

