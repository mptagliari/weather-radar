/* SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#include "azctl.h"

#include <math.h>

/* Overshoot of a sector limit treated as a reversal rather than a recovery. */
#define AZ_REVERSE_WINDOW_DEG 10.0

static double clamp(double x, double lo, double hi)
{
    return x < lo ? lo : (x > hi ? hi : x);
}

double az_wrap360(double deg)
{
    double r = fmod(deg, 360.0);
    return r < 0.0 ? r + 360.0 : r;
}

double az_diff(double a, double b)
{
    double d = az_wrap360(a - b);
    return d > 180.0 ? d - 360.0 : d;
}

bool az_in_sector(double deg, double start, double end)
{
    double span = az_wrap360(end - start);
    double off = az_wrap360(deg - start);
    return off <= span;
}

bool az_init(az_ctl_t *c, const az_config_t *cfg)
{
    if (!c || !cfg || cfg->rate_dps <= 0.0 || cfg->max_cmd <= 0.0 ||
        cfg->max_cmd > 1.0 || cfg->max_rate_dps < cfg->rate_dps)
        return false;
    double span = az_wrap360(cfg->end_deg - cfg->start_deg);
    if (span <= 0.0 || span >= 360.0)
        return false;
    *c = (az_ctl_t){ .cfg = *cfg, .mode = AZ_PARK, .dir = +1 };
    c->target_deg = az_wrap360(cfg->park_deg);
    return true;
}

static void reset_loop(az_ctl_t *c)
{
    c->integ = 0.0;
    c->have_prev = false;
}

void az_set_park(az_ctl_t *c)
{
    c->mode = AZ_PARK;
    c->target_deg = az_wrap360(c->cfg.park_deg);
    reset_loop(c);
}

void az_set_stare(az_ctl_t *c, double deg)
{
    c->mode = AZ_STARE;
    c->target_deg = az_wrap360(deg);
    reset_loop(c);
}

void az_set_sector(az_ctl_t *c)
{
    c->mode = AZ_SECTOR;
    reset_loop(c);
}

/* Desired signed rate (deg/s) for the current mode and angle. */
static double desired_rate(az_ctl_t *c, double meas)
{
    const az_config_t *g = &c->cfg;

    if (c->mode == AZ_SECTOR) {
        if (!az_in_sector(meas, g->start_deg, g->end_deg)) {
            /* Outside the sector: head for the nearer limit, never beyond. */
            double ds = fabs(az_diff(meas, g->start_deg));
            double de = fabs(az_diff(meas, g->end_deg));
            /* A small overshoot of the limit we were heading for is a normal
             * reversal, not a recovery: keep scanning the other way. */
            if (c->dir > 0 && de < AZ_REVERSE_WINDOW_DEG && de <= ds) {
                c->dir = -1;
                return c->dir * g->rate_dps;
            }
            if (c->dir < 0 && ds < AZ_REVERSE_WINDOW_DEG && ds <= de) {
                c->dir = +1;
                return c->dir * g->rate_dps;
            }
            c->target_deg = ds < de ? g->start_deg : g->end_deg;
        } else {
            double to_end = az_wrap360(g->end_deg - meas);
            double to_start = az_wrap360(meas - g->start_deg);
            if (c->dir > 0 && to_end <= 0.0)
                c->dir = -1;
            else if (c->dir < 0 && to_start <= 0.0)
                c->dir = +1;
            return c->dir * g->rate_dps;
        }
    }
    /* Park, stare, or returning to the sector: proportional move, slew limited. */
    return clamp(g->kpos * az_diff(c->target_deg, meas),
                 -g->max_rate_dps, g->max_rate_dps);
}

double az_update(az_ctl_t *c, double meas_deg, double dt)
{
    const az_config_t *g = &c->cfg;
    double meas = az_wrap360(meas_deg);

    if (dt <= 0.0)
        return 0.0;
    if (c->have_prev) {
        double r = az_diff(meas, c->prev_deg) / dt;
        c->rate_meas += 0.3 * (r - c->rate_meas); /* light smoothing of encoder steps */
    } else {
        c->rate_meas = 0.0;
    }
    c->prev_deg = meas;
    c->have_prev = true;

    double want = desired_rate(c, meas);
    double err = want - c->rate_meas;

    /* Conditional integration: stop winding up when the output is saturated. */
    double cmd = g->kp * err + c->integ;
    if (fabs(cmd) < g->max_cmd || (cmd > 0) != (err > 0))
        c->integ += g->ki * err * dt;
    c->integ = clamp(c->integ, -g->max_cmd, g->max_cmd);

    cmd = g->kp * err + c->integ;

    /* Stop cleanly on the target instead of dithering around it. */
    if (c->mode != AZ_SECTOR && fabs(az_diff(c->target_deg, meas)) < 0.05) {
        c->integ = 0.0;
        return 0.0;
    }
    return clamp(cmd, -g->max_cmd, g->max_cmd);
}
