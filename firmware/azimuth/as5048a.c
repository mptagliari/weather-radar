/* SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#include "as5048a.h"

static bool even_parity_ok(uint16_t v)
{
    v ^= v >> 8; v ^= v >> 4; v ^= v >> 2; v ^= v >> 1;
    return (v & 1u) == 0u;
}

uint16_t as5048a_read_angle_cmd(void)
{
    uint16_t cmd = 0x4000u | 0x3FFFu; /* read bit + angle register */
    return even_parity_ok(cmd) ? cmd : (uint16_t)(cmd | 0x8000u);
}

bool as5048a_decode(uint16_t frame, uint16_t *counts)
{
    if (!even_parity_ok(frame) || (frame & 0x4000u))
        return false;
    *counts = frame & 0x3FFFu;
    return true;
}
