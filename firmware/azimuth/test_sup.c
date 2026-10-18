/* SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/* Host tests for the supervisor, using a fake HAL with injectable faults. */
#include "as5048a.h"
#include "azsup.h"

#include <math.h>
#include <stdio.h>

static int fails, checks;
#define CHECK(cond, msg) do { checks++; if (!(cond)) { fails++; \
    printf("FAIL %s\n", msg); } else printf("ok   %s\n", msg); } while (0)

typedef struct {
    double az, rate;           /* plant state */
    double motor;              /* last command applied */
    double current;
    bool enc_ok, frozen;       /* encoder failure / frozen plant (stall) */
} fake_t;

static bool f_read(void *x, uint16_t *c)
{
    fake_t *f = x;
    if (!f->enc_ok) return false;
    *c = (uint16_t)(f->az * AZ_AS5048A_COUNTS / 360.0) % AZ_AS5048A_COUNTS;
    return true;
}
static void f_motor(void *x, double cmd) { ((fake_t *)x)->motor = cmd; }
static double f_cur(void *x) { return ((fake_t *)x)->current; }

static void plant(fake_t *f, double dt)
{
    if (f->frozen) { f->rate = 0; return; }
    double u = fabs(f->motor) < 0.03 ? 0.0 : f->motor;
    f->rate += (25.0 * u - f->rate) * (dt / 0.15);
    f->az = az_wrap360(f->az + f->rate * dt);
}

static az_config_t ccfg(void)
{
    return (az_config_t){ .start_deg = 200, .end_deg = 320, .rate_dps = 4.0,
        .park_deg = 270, .kp = 0.05, .ki = 0.04, .kpos = 0.5, .max_cmd = 1.0,
        .max_rate_dps = 20.0 };
}
static az_sup_config_t scfg(void)
{
    return (az_sup_config_t){ .ramp_per_s = 4.0, .encoder_fail_limit = 3,
        .stall_cmd = 0.3, .stall_min_dps = 0.3, .stall_time_s = 1.0,
        .current_limit_a = 15.0, .current_time_s = 0.2, .max_dt_s = 0.05 };
}

static void setup(az_sup_t *s, fake_t *f, double az)
{
    *f = (fake_t){ .az = az, .enc_ok = true };
    az_hal_t h = { f_read, f_motor, f_cur, f };
    az_config_t cc = ccfg(); az_sup_config_t sc = scfg();
    az_sup_init(s, &cc, &sc, &h);
}

static az_fault_t run(az_sup_t *s, fake_t *f, double secs)
{
    az_fault_t r = AZ_FAULT_NONE;
    for (double t = 0; t < secs && r == AZ_FAULT_NONE; t += 0.01) {
        r = az_sup_tick(s, 0.01);
        plant(f, 0.01);
    }
    return r;
}

int main(void)
{
    CHECK(fabs(az_counts_to_deg(0, 0, false)) < 1e-9, "counts 0 -> 0 deg");
    CHECK(fabs(az_counts_to_deg(8192, 0, false) - 180.0) < 1e-9, "counts 8192 -> 180 deg");
    CHECK(fabs(az_counts_to_deg(4096, 0, true) - 270.0) < 1e-9, "inverted encoder");
    CHECK(fabs(az_counts_to_deg(0, -10, false) - 350.0) < 1e-9, "zero offset wraps");

    /* AS5048A framing. */
    CHECK(as5048a_read_angle_cmd() == 0xFFFF, "angle read command is 0xFFFF");
    uint16_t cnt = 0;
    CHECK(as5048a_decode(0xA000, &cnt) && cnt == 0x2000, "decode valid frame (parity bit set)");
    CHECK(!as5048a_decode(0x2000, &cnt), "reject odd-parity frame");
    CHECK(!as5048a_decode(0x6000, &cnt), "reject frame with error flag");
    CHECK(as5048a_decode(0x8001, &cnt) && cnt == 1, "decode frame using parity bit");

    az_sup_t s; fake_t f; az_hal_t h = { f_read, f_motor, f_cur, &f };
    az_config_t cc = ccfg(); az_sup_config_t sc = scfg();
    sc.ramp_per_s = 0;
    CHECK(!az_sup_init(&s, &cc, &sc, &h), "rejects zero ramp");

    /* Normal operation: no fault, command ramps (never jumps). */
    setup(&s, &f, 100.0);
    az_set_stare(&s.ctl, 150.0);
    az_sup_tick(&s, 0.01);
    CHECK(fabs(f.motor) <= 0.04 + 1e-9, "first command limited by ramp");
    CHECK(run(&s, &f, 30.0) == AZ_FAULT_NONE && fabs(az_diff(f.az, 150.0)) < 0.5,
          "healthy stare reaches target, no fault");

    /* Isolated bad read is tolerated; persistent loss faults and cuts power. */
    setup(&s, &f, 100.0); az_set_stare(&s.ctl, 150.0);
    run(&s, &f, 1.0);
    f.enc_ok = false; az_sup_tick(&s, 0.01); f.enc_ok = true;
    CHECK(az_sup_tick(&s, 0.01) == AZ_FAULT_NONE && s.bad_reads == 0, "single bad read tolerated");
    f.enc_ok = false;
    CHECK(run(&s, &f, 0.5) == AZ_FAULT_ENCODER && f.motor == 0.0, "encoder loss faults, motor off");
    CHECK(az_sup_tick(&s, 0.01) == AZ_FAULT_ENCODER && f.motor == 0.0, "fault is latched");

    /* Stall. */
    setup(&s, &f, 100.0); az_set_stare(&s.ctl, 250.0);
    f.frozen = true;
    CHECK(run(&s, &f, 10.0) == AZ_FAULT_STALL && f.motor == 0.0, "stall detected, motor off");

    /* Over-current. */
    setup(&s, &f, 100.0); az_set_stare(&s.ctl, 150.0);
    f.current = 30.0;
    CHECK(run(&s, &f, 2.0) == AZ_FAULT_OVERCURRENT && f.motor == 0.0, "over-current detected");

    /* Brief current spike below the allowed time does not fault. */
    setup(&s, &f, 100.0); az_set_stare(&s.ctl, 150.0);
    f.current = 30.0; run(&s, &f, 0.1); f.current = 2.0;
    CHECK(run(&s, &f, 2.0) == AZ_FAULT_NONE, "short current spike tolerated");

    /* Late tick. */
    setup(&s, &f, 100.0);
    CHECK(az_sup_tick(&s, 0.5) == AZ_FAULT_TIMING && f.motor == 0.0, "late tick faults");

    /* Clearing a fault returns to park, motor stays off until healthy. */
    setup(&s, &f, 100.0); f.enc_ok = false; run(&s, &f, 0.5);
    f.enc_ok = true; az_sup_clear_fault(&s);
    CHECK(s.fault == AZ_FAULT_NONE && s.ctl.mode == AZ_PARK && s.cmd_out == 0.0,
          "clear fault resets to park");

    printf("\n%d/%d checks passed\n", checks - fails, checks);
    return fails ? 1 : 0;
}
