/* SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/* Host tests: a crude plant (command -> rate with a first-order lag and a
 * dead zone) closes the loop around the controller. Not a model of the real
 * wiper motor; it checks control logic, not tuning. */
#include "azctl.h"

#include <math.h>
#include <stdio.h>

static int fails, checks;

#define CHECK(cond, msg) do { checks++; if (!(cond)) { fails++; \
    printf("FAIL %s\n", msg); } else printf("ok   %s\n", msg); } while (0)

static az_config_t cfg(double start, double end)
{
    return (az_config_t){ .start_deg = start, .end_deg = end, .rate_dps = 4.0,
        .park_deg = 270.0, .kp = 0.05, .ki = 0.04, .kpos = 0.5, .max_cmd = 1.0,
        .max_rate_dps = 20.0 };
}

typedef struct { double az, rate; } plant_t;

static void plant_step(plant_t *p, double cmd, double dt)
{
    const double gain = 25.0;          /* deg/s at full command */
    double u = fabs(cmd) < 0.03 ? 0.0 : cmd; /* dead zone */
    p->rate += (gain * u - p->rate) * (dt / 0.15);
    p->az = az_wrap360(p->az + p->rate * dt);
}

static void run(az_ctl_t *c, plant_t *p, double secs, double *lo, double *hi, double *unwrapped_min)
{
    const double dt = 0.01;
    double rel = 0.0;
    for (double t = 0; t < secs; t += dt) {
        double cmd = az_update(c, p->az, dt);
        double before = p->az;
        plant_step(p, cmd, dt);
        rel += az_diff(p->az, before);
        if (lo && rel < *lo) *lo = rel;
        if (hi && rel > *hi) *hi = rel;
        if (unwrapped_min) *unwrapped_min = rel;
    }
}

int main(void)
{
    CHECK(fabs(az_wrap360(-10.0) - 350.0) < 1e-9, "wrap360 negative");
    CHECK(fabs(az_diff(5.0, 355.0) - 10.0) < 1e-9, "diff across north");
    CHECK(az_in_sector(10.0, 340.0, 30.0), "sector spanning north contains 10");
    CHECK(!az_in_sector(200.0, 340.0, 30.0), "sector spanning north excludes 200");

    az_ctl_t c;
    az_config_t bad = cfg(200, 320);
    bad.rate_dps = 0;
    CHECK(!az_init(&c, &bad), "rejects zero rate");
    bad = cfg(200, 200);
    CHECK(!az_init(&c, &bad), "rejects empty sector");
    bad = cfg(200, 320);
    bad.max_rate_dps = 1.0;
    CHECK(!az_init(&c, &bad), "rejects slew limit below scan rate");

    /* Sector scan stays inside limits and reverses at both ends. */
    az_config_t g = cfg(200, 320);
    CHECK(az_init(&c, &g), "init sector");
    plant_t p = { .az = 250.0 };
    az_set_sector(&c);
    double lo = 0, hi = 0;
    run(&c, &p, 140.0, &lo, &hi, NULL);
    double a0 = 250.0;
    CHECK(a0 + hi <= 320.0 + 2.0 && a0 + lo >= 200.0 - 2.0, "sector overshoot within 2 deg");
    CHECK(hi > 60.0 && lo < -40.0, "sector reaches both limits (reverses)");

    /* Constant rate mid-sector. */
    az_set_sector(&c);
    p = (plant_t){ .az = 240.0 };
    c = (az_ctl_t){0}; az_init(&c, &g); az_set_sector(&c);
    run(&c, &p, 10.0, NULL, NULL, NULL);        /* settle */
    double s = p.az; run(&c, &p, 10.0, NULL, NULL, NULL);
    double rate = az_diff(p.az, s) / 10.0;
    CHECK(fabs(rate - 4.0) < 0.3, "mid-sector rate within 0.3 deg/s of 4.0");

    /* Stare converges and holds. */
    az_init(&c, &g); p = (plant_t){ .az = 100.0 };
    az_set_stare(&c, 250.0);
    run(&c, &p, 40.0, NULL, NULL, NULL);
    CHECK(fabs(az_diff(p.az, 250.0)) < 0.3, "stare converges within 0.3 deg");

    /* Park takes the short way across north. */
    az_init(&c, &g); p = (plant_t){ .az = 350.0 };
    az_config_t g2 = g; g2.park_deg = 10.0; az_init(&c, &g2);
    az_set_park(&c);
    double rel = 0;
    for (double t = 0; t < 10; t += 0.01) {
        double cmd = az_update(&c, p.az, 0.01);
        double b = p.az; plant_step(&p, cmd, 0.01); rel += az_diff(p.az, b);
    }
    CHECK(rel > 0 && rel < 40.0 && fabs(az_diff(p.az, 10.0)) < 0.5, "park crosses north the short way");

    /* Outside the sector, the controller returns to it. */
    az_init(&c, &g); p = (plant_t){ .az = 100.0 };
    az_set_sector(&c);
    run(&c, &p, 30.0, NULL, NULL, NULL);
    CHECK(az_in_sector(p.az, 198.0, 322.0), "outside start returns into the sector");

    printf("\n%d/%d checks passed\n", checks - fails, checks);
    return fails ? 1 : 0;
}
