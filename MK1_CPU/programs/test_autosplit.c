/* Auto-split test: function spans I2C + computation domains.
 * The compiler splits read_and_compute into:
 *   read_and_compute_p1() — reads temp via I2C, returns it
 *   read_and_compute_p2(temp) — does computation and outputs
 * Tests Phase 7 auto function splitting with 1 live variable.
 * Expected: out(temp), out(temp*2+1) — temp is RTC temperature.
 */

void read_and_compute(unsigned char dummy) {
    unsigned char temp;
    temp = rtc_read_temp();
    /* ── domain boundary: I2C above, computation below ── */
    out(temp);
    unsigned char result;
    result = temp + temp + 1;
    out(result);
}

void main() {
    i2c_init();
    read_and_compute(0);
    out(42);
    halt();
}
