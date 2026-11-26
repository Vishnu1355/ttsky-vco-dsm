// front_end.v -- subtract the two ring phases first (mod 30), then ONE differentiator.
// d = wrap( (phP - phN) - previous ), wrapped to [-15, 14].  Valid while |fP - fN| < 0.5 cycle/clock.
`default_nettype none
module front_end (
  input  wire              clk, rst_n,
  input  wire [4:0]        phP, phN,
  output reg  signed [5:0] d
);
  wire [5:0] dphi = (phP >= phN) ? ({1'b0, phP} - {1'b0, phN}) : ({1'b0, phP} + 6'd30 - {1'b0, phN});
  reg  [5:0] dphi_d;
  wire signed [6:0] df = $signed({1'b0, dphi}) - $signed({1'b0, dphi_d});
  wire signed [6:0] dw = (df >= 7'sd15) ? df - 7'sd30 : (df < -7'sd15) ? df + 7'sd30 : df;
  always @(posedge clk or negedge rst_n)
    if (!rst_n) begin dphi_d <= 0; d <= 0; end
    else        begin dphi_d <= dphi; d <= dw[5:0]; end
endmodule
`default_nettype wire
