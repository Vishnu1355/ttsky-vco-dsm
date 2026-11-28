// phase_dec.v -- bubble-tolerant phase decoder for a 15-stage single-ended inverter ring.
// Tap s[i] = output of stage i (stage i drives stage i+1, stage 14 drives stage 0).
// t = s ^ 15'b010101010101010 turns the ring state into a rotating thermometer code:
//   phase 0..15 : ones fill from t[0] upward (count c = phase)
//   phase 16..29: zeros fill from t[0] upward (phase = 30 - c)
// Count-based (popcount) decoding tolerates bubbles; the polarity (which end holds the ones)
// is a 3-vs-3 vote of the two ends, so one bubble at t[0] cannot flip it.
`default_nettype none
module phase_dec (
  input  wire [14:0] s,
  output wire [4:0]  ph          // 0..29
);
  wire [14:0] t = s ^ 15'b010101010101010;
  wire [3:0] c = t[0]+t[1]+t[2]+t[3]+t[4]+t[5]+t[6]+t[7]+t[8]+t[9]+t[10]+t[11]+t[12]+t[13]+t[14];
  wire [1:0] lo = t[0] + t[1] + t[2];
  wire [1:0] hi = t[12] + t[13] + t[14];
  wire low_end = (lo >= hi);                        // ones sit at the low end
  assign ph = (c == 4'd0) ? 5'd0 : low_end ? {1'b0, c} : (5'd30 - {1'b0, c});
endmodule
`default_nettype wire
