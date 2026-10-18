/* SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/* AS5048A SPI frame helpers (16-bit frames, even parity in bit 15).
 * Reads are pipelined: the answer to a command arrives in the next frame. */
#ifndef AS5048A_H
#define AS5048A_H

#include <stdbool.h>
#include <stdint.h>

/* Command frame that reads the angle register (0x3FFF), parity included. */
uint16_t as5048a_read_angle_cmd(void);
/* Decode a response frame. False on parity error or the error flag (bit 14). */
bool as5048a_decode(uint16_t frame, uint16_t *counts);

#endif
