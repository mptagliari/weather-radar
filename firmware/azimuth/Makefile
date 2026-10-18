# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -O2
test: test.c azctl.c azctl.h
	$(CC) $(CFLAGS) -o $@ test.c azctl.c -lm
	./$@
clean:
	rm -f test
.PHONY: clean
