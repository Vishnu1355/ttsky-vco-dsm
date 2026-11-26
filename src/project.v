// project.v -- TinyTapeout top level (1x2 analog tile, 2 analog pins). Structural only:
// the two rings are a custom analog block; everything else is the vco_dsm_digital macro.
//   ua[0] = Vin+   ua[1] = Vin-
// Rename tt_um_vco_dsm to tt_um_<github-username>_vco_dsm before submission (must match info.yaml).
`default_nettype none
module tt_um_vco_dsm (
  input  wire [7:0] ui_in, output wire [7:0] uo_out,
  input  wire [7:0] uio_in, output wire [7:0] uio_out, output wire [7:0] uio_oe,
  inout  wire [7:0] ua,
  input  wire ena, clk, rst_n
);
  wire [14:0] tapP, tapN;
  ring_pair u_rings (.vinp(ua[0]), .vinn(ua[1]), .tapP(tapP), .tapN(tapN));   // analog (to be designed)
  vco_dsm_digital u_dig (.clk(clk), .rst_n(rst_n), .ena(ena), .tapP_a(tapP), .tapN_a(tapN),
                         .ui_in(ui_in), .uio_in(uio_in), .uo_out(uo_out), .uio_out(uio_out), .uio_oe(uio_oe));
endmodule

// Black box for the analog ring pair: two 15-stage current-starved rings, each tuned by its own input.
// Tap order must match phase_dec.v: tap[i] = output of stage i, stage i drives stage i+1.
(* blackbox *)
module ring_pair (inout wire vinp, inout wire vinn, output wire [14:0] tapP, output wire [14:0] tapN);
endmodule
`default_nettype wire
