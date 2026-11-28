// out_if.v -- presents each 16-bit sample on the 8 uo_out pins as two bytes, slow enough for the
// demo board's RP2040 to capture: high byte for 32 clocks, then low byte for 32 clocks.
//   uio_out[5] byte_sel : 0 = high byte on uo_out, 1 = low byte
//   uio_out[6] frame    : toggles once per new sample (capture on each edge)
//   uio_out[7] sat      : 1 if the current sample was clipped at full scale
// Modes (ui_in[7:6]): 00 ADC word | 01 ring P phase (bring-up) | 10 ramp test pattern | 11 raw difference code d
`default_nettype none
module out_if (
  input  wire              clk, rst_n,
  input  wire [1:0]        mode,
  input  wire signed [15:0] word_in,
  input  wire              word_valid,
  input  wire [4:0]        phP,
  input  wire signed [5:0] d,
  output reg  [7:0]        uo,
  output wire              byte_sel, frame, sat
);
  reg [15:0] word; reg [4:0] cnt; reg fr, bs, st;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin word <= 0; cnt <= 0; fr <= 0; bs <= 0; st <= 0; end
    else begin
      cnt <= cnt + 1'b1;
      if (cnt == 5'd31) bs <= 1'b1;
      if (word_valid) begin
        word <= (mode == 2'b10) ? word + 1'b1 : word_in;
        st   <= (word_in == 16'sh7FFF) || (word_in == -16'sh7FFF);
        fr <= ~fr; bs <= 1'b0; cnt <= 0;
      end
    end
  end
  always @* begin
    case (mode)
      2'b01:   uo = {3'b000, phP};
      2'b11:   uo = {2'b00, d};
      default: uo = bs ? word[7:0] : word[15:8];
    endcase
  end
  assign byte_sel = bs; assign frame = fr; assign sat = st;
endmodule
`default_nettype wire
