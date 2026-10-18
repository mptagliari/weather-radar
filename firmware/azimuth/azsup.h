/* SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
/* Supervisor around the azimuth controller (issue #11, REQ-015).
 *
 * Owns the hardware boundary (encoder, motor, current sense) through a small
 * HAL, converts raw encoder counts, ramps the motor command, and latches a
 * fault -- motor off -- on encoder loss, stall, over-current or a late tick.
 * The wiper-motor worm gear is expected to hold the antenna when unpowered.
 */
#ifndef AZSUP_H
#define AZSUP_H

#include <stdbool.h>
#include <stdint.h>

#include "azctl.h"

typedef enum {
    AZ_FAULT_NONE = 0,
    AZ_FAULT_ENCODER,     /* read failures or counts out of range */
    AZ_FAULT_STALL,       /* commanded hard, antenna not moving */
    AZ_FAULT_OVERCURRENT, /* motor current above limit for too long */
    AZ_FAULT_TIMING       /* control tick far later than expected */
} az_fault_t;

typedef struct {
    /* Return false on a failed/invalid read. counts is 14-bit (0..16383). */
    bool (*read_counts)(void *ctx, uint16_t *counts);
    void (*set_motor)(void *ctx, double cmd);  /* -1..1, + is clockwise */
    double (*read_current_a)(void *ctx);
    void *ctx;
} az_hal_t;

typedef struct {
    double zero_offset_deg;    /* encoder zero relative to true north */
    bool invert;               /* counts increase counter-clockwise */
    double ramp_per_s;         /* max change of command per second */
    int encoder_fail_limit;    /* consecutive bad reads before fault */
    double stall_cmd;          /* |cmd| above this counts toward a stall */
    double stall_min_dps;      /* below this rate the antenna is "not moving" */
    double stall_time_s;
    double current_limit_a;
    double current_time_s;     /* allowed time above the limit */
    double max_dt_s;           /* tick gap treated as a timing fault */
} az_sup_config_t;

typedef struct {
    az_ctl_t ctl;
    az_hal_t hal;
    az_sup_config_t cfg;
    az_fault_t fault;
    int bad_reads;
    double cmd_out;
    double stall_t, over_t;
    double angle_deg;          /* last valid antenna-axis angle */
    double rate_dps;
} az_sup_t;

#define AZ_AS5048A_COUNTS 16384

double az_counts_to_deg(uint16_t counts, double zero_offset_deg, bool invert);

bool az_sup_init(az_sup_t *s, const az_config_t *cfg, const az_sup_config_t *sc,
                 const az_hal_t *hal);
/* Call at a fixed rate (e.g. 100 Hz) with the elapsed time. Returns the fault. */
az_fault_t az_sup_tick(az_sup_t *s, double dt);
/* Clear a latched fault. Refused (false) while the cause persists is left to
 * the next tick; clearing resets the controller to park mode. */
void az_sup_clear_fault(az_sup_t *s);

#endif
