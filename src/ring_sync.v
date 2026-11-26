// ring_sync.v -- 2-flop synchronizers for the 30 asynchronous ring taps (15 per ring).
`default_nettype none
module ring_sync (
  input  wire        clk, rst_n,
  input  wire [14:0] tapP_a, tapN_a,      // asynchronous ring stage outputs
  output reg  [14:0] tapP, tapN           // synchronized
);
  reg [14:0] p1, n1;
  always @(posedge clk or negedge rst_n)
    if (!rst_n) begin p1 <= 0; n1 <= 0; tapP <= 0; tapN <= 0; end
    else        begin p1 <= tapP_a; n1 <= tapN_a; tapP <= p1; tapN <= n1; end
endmodule
`default_nettype wire
