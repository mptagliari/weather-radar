# SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
# SPDX-License-Identifier: GPL-3.0-or-later
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -O2
.DEFAULT_GOAL := test
test_ctl: test.c azctl.c azctl.h
	$(CC) $(CFLAGS) -o $@ test.c azctl.c -lm
test_sup: test_sup.c azsup.c azsup.h azctl.c azctl.h as5048a.c as5048a.h
	$(CC) $(CFLAGS) -o $@ test_sup.c azsup.c azctl.c as5048a.c -lm
test: test_ctl test_sup
	./test_ctl
	./test_sup
clean:
	rm -f test_ctl test_sup
.PHONY: test clean
