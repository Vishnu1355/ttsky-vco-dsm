/*
 * Copyright (c) 2026 Vishnu
 * SPDX-License-Identifier: Apache-2.0
 *
 * Port list of the hardened analog/mixed-signal tile (black box for Tiny Tapeout).
 * Contents: pseudo-differential pair of 15-stage ring VCOs (ua[0] = Vin+, ua[1] = Vin-) + the ring-VCO
 * delta-sigma digital back end (sinc2 /64, shift-add droop fix, cubic corrector k3 = 2^-5 - 2^-7). Layout: gds/, lef/.
 */
`default_nettype none
module tt_um_vishnu1355_vco_dsm (
    input  wire       VGND,
    input  wire       VPWR,     // 1.8 V (VDPWR)
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
endmodule
