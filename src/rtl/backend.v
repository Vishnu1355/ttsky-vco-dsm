// backend.v -- minimal back end for a 1x2 TinyTapeout tile (lean3 + correction bypass).
//   d_in (6 b, 50 MHz) -> 2 integrators (18 b) -> every 64 clocks, on ONE adder + ONE register R:
//   2 combs -> droop comp y = 1.375 w[n-1] - 0.1875 (w[n] + w[n-2]) -> |y| -> y^2, y^3 (shift-add)
//   -> out = y + k3 y^3 + k2 y^2  (k3 hard-wired 2^-5 - 2^-7 on p3 [Option A, retuned for the SKY130 ring_pair; was 2^-3 - 2^-7]; k2 = two cfg terms)
// Bit-exact with lean3_golden.py.  Sequence: 2 + 5 + 1 + 32 + 4 + 1 = 45 of 64 clocks.
`default_nettype none
module backend #(parameter B = 18, parameter F = 16) (
  input  wire              clk, rst_n,
  input  wire signed [5:0] d_in,
  input  wire [4:0]        c2_t1, c2_t2,        // {en, neg, off[2:0]} : p2 >> (4+off)
  input  wire              bypass,              // 1 = output the flattened word, no correction
  output reg  signed [15:0] out,
  output reg               out_valid
);
  reg  signed [B-1:0] i1, i2, cd0, cd1, R, wh0, wh1;
  wire signed [B-1:0] i1n = i1 + {{(B-6){d_in[5]}}, d_in};
  wire signed [B-1:0] i2n = i2 + i1n;
  reg  [5:0] ph; reg [3:0] st; reg [3:0] cnt; reg sgn;
  reg  [F-1:0] a, b, p2; reg [F:0] acc;
  localparam S_IDLE=0, S_C1=1, S_T=2, S_H=3, S_Y1=4, S_Y2=5, S_Y3=6, S_ABS=7,
             S_M1=8, S_M2=9, S_A1=10, S_A2=11, S_A3=12, S_A4=13, S_OUT=14;
  wire [F-1:0] p3 = acc[F-1:0];
  wire [F-1:0] u1 = p2 >> (4 + c2_t1[2:0]);
  wire [F-1:0] u2 = p2 >> (4 + c2_t2[2:0]);
  reg  signed [B-1:0] opa, opb; reg sub;
  wire signed [B-1:0] res = sub ? opa - opb : opa + opb;
  always @* begin
    opa = R; opb = 0; sub = 0;
    case (st)
      S_IDLE: begin opa = i2n; opb = cd0; sub = 1; end        // comb 1 (latched when ph==63)
      S_C1:   begin opb = cd1; sub = 1; end                   // comb 2 -> R = w
      S_T:    begin opb = wh1; end                            // t = w + w[n-2]
      S_H:    begin opa = R >>> 3; opb = R >>> 4; end         // h = 3/16 t
      S_Y1:   begin opa = wh1; opb = R; sub = 1; end          // (wh1 now = w[n-1]) - h
      S_Y2:   begin opb = wh1 >>> 2; end
      S_Y3:   begin opb = wh1 >>> 3; end                      // y
      S_ABS:  begin opa = 0; opb = R; sub = 1; end
      S_M1, S_M2: begin opa = {{(B-F-1){1'b0}}, acc}; opb = b[0] ? {{(B-F){1'b0}}, a} : 0; end
      S_A1:   begin opb = bypass ? 0 : {{(B-F){1'b0}}, p3 >> 5}; sub = sgn; end   // Option A: k3 = 2^-5 - 2^-7
      S_A2:   begin opb = bypass ? 0 : {{(B-F){1'b0}}, p3 >> 7}; sub = ~sgn; end
      S_A3:   begin opb = (c2_t1[4] && !bypass) ? {{(B-F){1'b0}}, u1} : 0; sub = c2_t1[3]; end
      S_A4:   begin opb = (c2_t2[4] && !bypass) ? {{(B-F){1'b0}}, u2} : 0; sub = c2_t2[3]; end
      default: ;
    endcase
  end
  localparam signed [B-1:0] SATP = (1 <<< 15) - 1;
  wire signed [B-1:0] mag  = R[B-1] ? res : R;                // valid in S_ABS
  wire [F-1:0] magc = (mag > $signed({{(B-F){1'b0}}, {F{1'b1}}})) ? {F{1'b1}} : mag[F-1:0];
  wire signed [B-1:0] satR = (R > SATP) ? SATP : (R < -SATP) ? -SATP : R;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      i1<=0; i2<=0; cd0<=0; cd1<=0; R<=0; wh0<=0; wh1<=0; ph<=0; st<=S_IDLE; cnt<=0; sgn<=0;
      a<=0; b<=0; p2<=0; acc<=0; out<=0; out_valid<=0;
    end else begin
      i1<=i1n; i2<=i2n; ph<=ph+1'b1; out_valid<=1'b0;
      case (st)
        S_IDLE: if (ph == 6'd63) begin R <= res; cd0 <= i2n; st <= S_C1; end
        S_C1:  begin R <= res; cd1 <= R; st <= S_T; end
        S_T:   begin R <= res; wh1 <= wh0; wh0 <= R; st <= S_H; end
        S_H:   begin R <= res; st <= S_Y1; end
        S_Y1:  begin R <= res; st <= S_Y2; end
        S_Y2:  begin R <= res; st <= S_Y3; end
        S_Y3:  begin R <= res; st <= S_ABS; end
        S_ABS: begin sgn <= R[B-1]; a <= magc; b <= magc; acc <= 0; cnt <= 0; st <= S_M1; end
        S_M1:  begin acc <= res[F:0] >> 1; b <= b >> 1; cnt <= cnt + 1'b1;
                 if (cnt == F-1) begin p2 <= res[F:1]; b <= res[F:1]; acc <= 0; cnt <= 0; st <= S_M2; end end
        S_M2:  begin acc <= res[F:0] >> 1; b <= b >> 1; cnt <= cnt + 1'b1; if (cnt == F-1) st <= S_A1; end
        S_A1:  begin R <= res; st <= S_A2; end
        S_A2:  begin R <= res; st <= S_A3; end
        S_A3:  begin R <= res; st <= S_A4; end
        S_A4:  begin R <= res; st <= S_OUT; end
        S_OUT: begin out <= satR[15:0]; out_valid <= 1'b1; st <= S_IDLE; end
        default: st <= S_IDLE;
      endcase
    end
  end
endmodule
`default_nettype wire
