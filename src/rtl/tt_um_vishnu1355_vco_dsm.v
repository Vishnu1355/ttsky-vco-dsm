/*
 * Copyright (c) 2026 Vishnu
 * SPDX-License-Identifier: Apache-2.0
 *
 * Tile top: pseudo-differential ring-VCO delta-sigma ADC.
 *   Analog: ring_pair_tt (two matched 15-stage current-starved rings). ua[0] = Vin+, ua[1] = Vin-.
 *   Digital: the original vco_dsm_digital with Option A (cubic corrector k3 = 2^-5 - 2^-7, backend.v).
 */
`default_nettype none
module tt_um_vishnu1355_vco_dsm (
`ifdef USE_POWER_PINS
    inout  wire       VPWR,
    inout  wire       VGND,
`endif
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    inout  wire [7:0] ua,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
  wire [14:0] tapP, tapN;
  ring_pair_tt u_rings (
`ifdef USE_POWER_PINS
    .VDPWR(VPWR), .VGND(VGND),
`endif
    .vinp(ua[0]), .vinn(ua[1]), .tapP(tapP), .tapN(tapN));
  vco_dsm_digital u_dig (
    .clk(clk), .rst_n(rst_n), .ena(ena),
    .tapP_a(tapP), .tapN_a(tapN),
    .ui_in(ui_in), .uio_in(uio_in),
    .uo_out(uo_out), .uio_out(uio_out), .uio_oe(uio_oe));
endmodule
`default_nettype wire
