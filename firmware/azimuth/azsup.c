/* SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#include "azsup.h"

#include <math.h>

double az_counts_to_deg(uint16_t counts, double zero_offset_deg, bool invert)
{
    double d = (double)(counts % AZ_AS5048A_COUNTS) * 360.0 / AZ_AS5048A_COUNTS;
    if (invert)
        d = 360.0 - d;
    return az_wrap360(d + zero_offset_deg);
}

bool az_sup_init(az_sup_t *s, const az_config_t *cfg, const az_sup_config_t *sc,
                 const az_hal_t *hal)
{
    if (!s || !sc || !hal || !hal->read_counts || !hal->set_motor ||
        !hal->read_current_a || sc->ramp_per_s <= 0.0 ||
        sc->encoder_fail_limit < 1 || sc->max_dt_s <= 0.0)
        return false;
    *s = (az_sup_t){ .cfg = *sc, .hal = *hal };
    if (!az_init(&s->ctl, cfg))
        return false;
    s->hal.set_motor(s->hal.ctx, 0.0);
    return true;
}

static az_fault_t latch(az_sup_t *s, az_fault_t f)
{
    s->fault = f;
    s->cmd_out = 0.0;
    s->hal.set_motor(s->hal.ctx, 0.0);
    return f;
}

az_fault_t az_sup_tick(az_sup_t *s, double dt)
{
    const az_sup_config_t *c = &s->cfg;

    if (s->fault != AZ_FAULT_NONE) {
        s->hal.set_motor(s->hal.ctx, 0.0);
        return s->fault;
    }
    if (dt <= 0.0 || dt > c->max_dt_s)
        return latch(s, AZ_FAULT_TIMING);

    uint16_t counts = 0;
    if (!s->hal.read_counts(s->hal.ctx, &counts) || counts >= AZ_AS5048A_COUNTS) {
        if (++s->bad_reads >= c->encoder_fail_limit)
            return latch(s, AZ_FAULT_ENCODER);
        /* Tolerate an isolated bad read: hold the last command this tick. */
        s->hal.set_motor(s->hal.ctx, s->cmd_out);
        return AZ_FAULT_NONE;
    }
    s->bad_reads = 0;

    double prev = s->angle_deg;
    s->angle_deg = az_counts_to_deg(counts, c->zero_offset_deg, c->invert);
    s->rate_dps = az_diff(s->angle_deg, prev) / dt;

    double want = az_update(&s->ctl, s->angle_deg, dt);

    /* Ramp the command: protects the gearbox from reversal shocks. */
    double step = c->ramp_per_s * dt;
    double d = want - s->cmd_out;
    s->cmd_out += d > step ? step : (d < -step ? -step : d);

    /* Stall: driving hard but the antenna is not moving. */
    if (fabs(s->cmd_out) > c->stall_cmd && fabs(s->rate_dps) < c->stall_min_dps)
        s->stall_t += dt;
    else
        s->stall_t = 0.0;
    if (s->stall_t >= c->stall_time_s)
        return latch(s, AZ_FAULT_STALL);

    if (fabs(s->hal.read_current_a(s->hal.ctx)) > c->current_limit_a)
        s->over_t += dt;
    else
        s->over_t = 0.0;
    if (s->over_t >= c->current_time_s)
        return latch(s, AZ_FAULT_OVERCURRENT);

    s->hal.set_motor(s->hal.ctx, s->cmd_out);
    return AZ_FAULT_NONE;
}

void az_sup_clear_fault(az_sup_t *s)
{
    s->fault = AZ_FAULT_NONE;
    s->bad_reads = 0;
    s->stall_t = s->over_t = 0.0;
    s->cmd_out = 0.0;
    az_set_park(&s->ctl);
}
