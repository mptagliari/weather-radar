// SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// ESP32 port of the azimuth drive (issue #11).
// Compiles for esp32dev but has never run on hardware. All pins, the current
// scale and every gain below are placeholders to be set on the bench.
//
// Hardware assumed: AS5048A on SPI (mode 1), BTS7960-class H-bridge
// (RPWM/LPWM + R_EN/L_EN, IS pins to an ADC through a resistor).
#include <Arduino.h>
#include <SPI.h>

extern "C" {
#include "as5048a.h"
#include "azctl.h"
#include "azsup.h"
}

// ---- Placeholders: pins ---------------------------------------------------
static const int PIN_CS = 5;
static const int PIN_RPWM = 25, PIN_LPWM = 26, PIN_EN = 27;
static const int PIN_IS = 34;  // sum of both IS pins through one resistor

// ---- Placeholders: electrical ---------------------------------------------
// BTS7960 current sense is roughly I/8500 per amp; with SENSE_OHMS to ground
// volts = amps / 8500 * ohms. VERIFY on the bench before trusting the limit.
static const float SENSE_OHMS = 1000.0f;
static const float ADC_VREF = 3.3f;
static const int PWM_BITS = 10, PWM_HZ = 20000;

static SPIClass spi(VSPI);
static az_sup_t sup;

static bool read_counts(void *, uint16_t *counts)
{
    // Pipelined: the first frame returns the previous answer, the second ours.
    const uint16_t cmd = as5048a_read_angle_cmd();
    spi.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE1));
    digitalWrite(PIN_CS, LOW);  spi.transfer16(cmd);  digitalWrite(PIN_CS, HIGH);
    delayMicroseconds(1);
    digitalWrite(PIN_CS, LOW);  uint16_t r = spi.transfer16(cmd);  digitalWrite(PIN_CS, HIGH);
    spi.endTransaction();
    return as5048a_decode(r, counts);
}

static void set_motor(void *, double cmd)
{
    const uint32_t full = (1u << PWM_BITS) - 1u;
    uint32_t duty = (uint32_t)(fabs(cmd) * full);
    digitalWrite(PIN_EN, cmd == 0.0 ? LOW : HIGH);
    ledcWrite(0, cmd > 0 ? duty : 0);  // RPWM: clockwise
    ledcWrite(1, cmd < 0 ? duty : 0);  // LPWM: counter-clockwise
}

static double read_current(void *)
{
    float volts = analogReadMilliVolts(PIN_IS) / 1000.0f;
    (void)ADC_VREF;
    return volts / SENSE_OHMS * 8500.0f;
}

void setup()
{
    Serial.begin(115200);
    pinMode(PIN_CS, OUTPUT);  digitalWrite(PIN_CS, HIGH);
    pinMode(PIN_EN, OUTPUT);  digitalWrite(PIN_EN, LOW);  // motor off at boot
    spi.begin();
    ledcSetup(0, PWM_HZ, PWM_BITS);  ledcAttachPin(PIN_RPWM, 0);
    ledcSetup(1, PWM_HZ, PWM_BITS);  ledcAttachPin(PIN_LPWM, 1);

    az_config_t cc = {};
    cc.start_deg = 200; cc.end_deg = 320; cc.rate_dps = 4.0; cc.park_deg = 270;
    cc.kp = 0.05; cc.ki = 0.04; cc.kpos = 0.5; cc.max_cmd = 0.6; cc.max_rate_dps = 10.0;

    az_sup_config_t sc = {};
    sc.zero_offset_deg = 0.0; sc.ramp_per_s = 2.0; sc.encoder_fail_limit = 5;
    sc.stall_cmd = 0.25; sc.stall_min_dps = 0.3; sc.stall_time_s = 1.5;
    sc.current_limit_a = 10.0; sc.current_time_s = 0.3; sc.max_dt_s = 0.05;

    az_hal_t hal = { read_counts, set_motor, read_current, nullptr };
    if (!az_sup_init(&sup, &cc, &sc, &hal)) {
        Serial.println("config rejected; motor stays off");
        for (;;) delay(1000);
    }
    az_set_park(&sup.ctl);  // boot parked; an operator command starts a scan
}

void loop()
{
    static uint32_t last = micros();
    uint32_t now = micros();
    double dt = (now - last) * 1e-6;
    last = now;

    az_fault_t f = az_sup_tick(&sup, dt);
    if (f != AZ_FAULT_NONE) {
        static uint32_t t = 0;
        if (millis() - t > 1000) { t = millis(); Serial.printf("FAULT %d\n", (int)f); }
    }
    if (Serial.available()) {
        switch (Serial.read()) {
        case 's': az_set_sector(&sup.ctl); break;
        case 'p': az_set_park(&sup.ctl); break;
        case 'c': az_sup_clear_fault(&sup); break;
        }
    }
    delay(10);  // ~100 Hz; the supervisor faults on a tick later than max_dt_s
}
