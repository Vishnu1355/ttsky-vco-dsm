// vco_dsm_digital.v -- the complete digital part of the ring-VCO delta-sigma ADC (everything except
// the two analog rings). Hardened as one standard-cell macro and placed next to the rings.
//   ui_in[4:0]  c2_t1  even-order trim term 1 {en, neg, off[2:0]}
//   ui_in[5]    bypass 1 = correction off (flattened, uncorrected output) for on/off A/B tests
//   ui_in[7:6]  mode   00 ADC | 01 ring-P phase | 10 ramp | 11 raw code
//   uio_in[4:0] c2_t2  even-order trim term 2
//   uo_out      data byte; uio_out[5] byte_sel, [6] frame toggle, [7] saturation
`default_nettype none
module vco_dsm_digital (
  input  wire        clk, rst_n, ena,
  input  wire [14:0] tapP_a, tapN_a,
  input  wire [7:0]  ui_in, uio_in,
  output wire [7:0]  uo_out, uio_out, uio_oe
);
  // static configuration, registered once
  reg [4:0] t1, t2; reg byp; reg [1:0] mode;
  always @(posedge clk or negedge rst_n)
    if (!rst_n) begin t1 <= 0; t2 <= 0; byp <= 0; mode <= 0; end
    else begin t1 <= ui_in[4:0]; byp <= ui_in[5]; mode <= ui_in[7:6]; t2 <= uio_in[4:0]; end

  wire [14:0] tapP, tapN;  wire [4:0] phP, phN;  wire signed [5:0] d;
  wire signed [15:0] word; wire word_valid;
  ring_sync u_sync (.clk(clk), .rst_n(rst_n), .tapP_a(tapP_a), .tapN_a(tapN_a), .tapP(tapP), .tapN(tapN));
  phase_dec u_decP (.s(tapP), .ph(phP));
  phase_dec u_decN (.s(tapN), .ph(phN));
  front_end u_fe   (.clk(clk), .rst_n(rst_n), .phP(phP), .phN(phN), .d(d));
  backend   u_be   (.clk(clk), .rst_n(rst_n), .d_in(d), .c2_t1(t1), .c2_t2(t2), .bypass(byp),
                    .out(word), .out_valid(word_valid));
  wire bs, fr, st;
  out_if    u_out  (.clk(clk), .rst_n(rst_n), .mode(mode), .word_in(word), .word_valid(word_valid),
                    .phP(phP), .d(d), .uo(uo_out), .byte_sel(bs), .frame(fr), .sat(st));
  assign uio_out = {st, fr, bs, 5'b00000};
  assign uio_oe  = 8'b1110_0000;
  wire _unused = &{ena, uio_in[7:5], 1'b0};
endmodule
`default_nettype wire
