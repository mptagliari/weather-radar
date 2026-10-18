/* SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/* Azimuth sector-scan controller core (issue #11).
 *
 * Hardware independent: feed it the antenna-axis angle, get back a signed
 * motor command in [-1, 1] for the H-bridge. All angles are degrees,
 * clockwise from true north, in [0, 360). Time is seconds.
 */
#ifndef AZCTL_H
#define AZCTL_H

#include <stdbool.h>

typedef enum { AZ_PARK, AZ_STARE, AZ_SECTOR } az_mode_t;

typedef struct {
    double start_deg;      /* sector limit, clockwise start */
    double end_deg;        /* sector limit, clockwise end   */
    double rate_dps;       /* scan rate, degrees per second (> 0) */
    double park_deg;       /* safe parking azimuth */
    double kp, ki;         /* PI gains on rate error (command per deg/s) */
    double kpos;           /* position gain (deg/s per deg) used for stare/park */
    double max_cmd;        /* command clamp, 0..1 */
    double max_rate_dps;   /* hard slew limit for stare/park moves */
} az_config_t;

typedef struct {
    az_config_t cfg;
    az_mode_t mode;
    double target_deg;     /* stare target */
    int dir;               /* +1 clockwise, -1 counter-clockwise (sector) */
    double prev_deg;       /* last measured angle */
    double rate_meas;      /* filtered measured rate, deg/s */
    double integ;          /* PI integrator */
    bool have_prev;
} az_ctl_t;

/* Wrap any angle to [0, 360). */
double az_wrap360(double deg);
/* Shortest signed difference a - b in (-180, 180]. */
double az_diff(double a, double b);
/* Fraction-safe: true if angle lies within [start, end] travelling clockwise. */
bool az_in_sector(double deg, double start, double end);

/* Returns false if the configuration is invalid (non-positive rate, etc.). */
bool az_init(az_ctl_t *c, const az_config_t *cfg);
void az_set_park(az_ctl_t *c);
void az_set_stare(az_ctl_t *c, double deg);
void az_set_sector(az_ctl_t *c);

/* One control step: measured angle, time step. Returns motor command in
 * [-max_cmd, max_cmd]; positive is clockwise. */
double az_update(az_ctl_t *c, double meas_deg, double dt);

#endif
