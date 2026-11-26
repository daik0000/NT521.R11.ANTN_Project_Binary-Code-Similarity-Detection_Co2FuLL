
int classify(int param_1)

{
  bool bVar1;
  byte local_25;
  int local_24;
  int local_20;
  int local_1c;
  byte local_d;
  int local_c;
  
  local_1c = 0;
  local_24 = 0x4335ff95;
  while( true ) {
    while( true ) {
      while( true ) {
        while( true ) {
          while( true ) {
            while( true ) {
              while( true ) {
                while( true ) {
                  while (local_24 == -0x7df2ee13) {
                    local_20 = local_20 + 1;
                    bVar1 = (x_11 * (x_11 + -1) & 1U) == 0;
                    local_24 = 0x38c8ce97;
                    if (bVar1 != y_12 < 10 || bVar1 && y_12 < 10) {
                      local_24 = 0x2d1a058d;
                    }
                  }
                  if (local_24 != -0x68f93200) break;
                  puts("classify: odd value");
                  local_1c = param_1 * 3 + 1;
                  local_24 = 0x3409a5e3;
                }
                if (local_24 != -0x58ba5469) break;
                local_24 = -0x2af1ebb2;
              }
              if (local_24 != -0x537b3489) break;
              local_24 = -0x68f93200;
              if (param_1 % 2 == 0) {
                local_24 = 0xb530f1c;
              }
            }
            if (local_24 != -0x3056de01) break;
            local_d = local_20 < param_1;
            bVar1 = (x_11 * (x_11 + -1) & 1U) == 0;
            local_24 = 0x320664cf;
            if (bVar1 && y_12 < 10 || bVar1 != y_12 < 10) {
              local_24 = -0x2bbacd90;
            }
          }
          if (local_24 != -0x2eb7f135) break;
          bVar1 = (x_11 * (x_11 + -1) & 1U) == 0;
          local_24 = 0x4d50a38a;
          if (bVar1 && y_12 < 10 || bVar1 != y_12 < 10) {
            local_24 = 0x22143486;
          }
        }
        if (local_24 != -0x2bbacd90) break;
        local_24 = -0x75ed105;
        if ((local_d & 1) != 0) {
          local_24 = -0xdeeef2a;
        }
        local_25 = 0;
      }
      if (local_24 != -0x2af1ebb2) break;
      bVar1 = (x_11 * (x_11 + -1) & 1U) != 0;
      local_24 = -0x58ba5469;
      if (bVar1 != 9 < y_12 || !bVar1 && 9 >= y_12) {
        local_24 = 0x630f70f2;
      }
    }
    if (local_24 == -0x18693d92) break;
    if (local_24 == -0x101b7a7b) {
      local_c = local_1c;
      bVar1 = (x_11 * (x_11 + -1) & 1U) == 0;
      local_24 = 0x6bce72b2;
      if (bVar1 && y_12 < 10 || bVar1 != y_12 < 10) {
        local_24 = -0x18693d92;
      }
    }
    else if (local_24 == -0xdeeef2a) {
      local_25 = local_20 < 8;
      local_24 = -0x75ed105;
    }
    else if (local_24 == -0x75ed105) {
      local_24 = 0x78cb89b1;
      if ((local_25 & 1) != 0) {
        local_24 = 0x6d96e70b;
      }
    }
    else if (local_24 == -0x24ead9d) {
      bVar1 = (x_11 * (x_11 + -1) & 1U) == 0;
      local_24 = 0x38c8ce97;
      if (bVar1 != y_12 < 10 || bVar1 && y_12 < 10) {
        local_24 = -0x7df2ee13;
      }
    }
    else if (local_24 == 0xb530f1c) {
      puts("classify: even value");
      local_1c = param_1 / 2;
      local_24 = 0x3409a5e3;
    }
    else if (local_24 == 0x22143486) {
      puts("classify: negative value");
      local_1c = -1;
      bVar1 = (x_11 * (x_11 + -1) & 1U) == 0;
      local_24 = 0x4d50a38a;
      if (bVar1 && y_12 < 10 || bVar1 != y_12 < 10) {
        local_24 = 0x32fc1b9f;
      }
    }
    else if (local_24 == 0x2423080f) {
      local_20 = 0;
      local_24 = 0x74920393;
    }
    else if (local_24 == 0x2d1a058d) {
      local_24 = 0x74920393;
    }
    else if (local_24 == 0x320664cf) {
      local_24 = -0x3056de01;
    }
    else if (local_24 == 0x32fc1b9f) {
      local_24 = 0x2423080f;
    }
    else if (local_24 == 0x3409a5e3) {
      bVar1 = (x_11 * (x_11 + -1) & 1U) != 0;
      local_24 = -0x58ba5469;
      if (bVar1 != 9 < y_12 || !bVar1 && 9 >= y_12) {
        local_24 = -0x2af1ebb2;
      }
    }
    else if (local_24 == 0x38c8ce97) {
      local_20 = local_20 + 1;
      local_24 = -0x7df2ee13;
    }
    else if (local_24 == 0x4335ff95) {
      local_24 = -0x537b3489;
      if (param_1 < 0) {
        local_24 = -0x2eb7f135;
      }
    }
    else if (local_24 == 0x4d50a38a) {
      puts("classify: negative value");
      local_1c = -1;
      local_24 = 0x22143486;
    }
    else if (local_24 == 0x630f70f2) {
      local_24 = 0x2423080f;
    }
    else if (local_24 == 0x6bce72b2) {
      local_24 = -0x101b7a7b;
    }
    else if (local_24 == 0x6d96e70b) {
      local_1c = local_1c + local_20;
      local_24 = -0x24ead9d;
    }
    else if (local_24 == 0x74920393) {
      bVar1 = (x_11 * (x_11 + -1) & 1U) == 0;
      local_24 = 0x320664cf;
      if (bVar1 != y_12 < 10 || bVar1 && y_12 < 10) {
        local_24 = -0x3056de01;
      }
    }
    else if ((local_24 == 0x78cb89b1) &&
            (bVar1 = (x_11 * (x_11 + -1) & 1U) != 0, local_24 = 0x6bce72b2,
            bVar1 != 9 < y_12 || !bVar1 && 9 >= y_12)) {
      local_24 = -0x101b7a7b;
    }
  }
  return local_c;
}

