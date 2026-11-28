// ring_pair_tt -- analog macro: friend's ring_pair (two identical 15-stage symmetric current-starved ring VCOs,
// bias mirror per ring, non-inverting tap buffers) inside a TinyTapeout wrapper (met3 power rails, pin extensions).
// Black box for the digital flow.
(* blackbox *)
module ring_pair_tt (
`ifdef USE_POWER_PINS
  inout  wire        VDPWR,
  inout  wire        VGND,
`endif
  input  wire        vinp,     // Vin+ (ua[0])
  input  wire        vinn,     // Vin- (ua[1])
  output wire [14:0] tapP,     // ring P buffered stage outputs -> ring_sync
  output wire [14:0] tapN      // ring N buffered stage outputs
);
endmodule
