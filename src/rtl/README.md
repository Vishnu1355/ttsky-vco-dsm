Hardened sources of the tile (the GDS in gds/ was built from these with LibreLane 3.0.17):
- tt_um_vishnu1355_vco_dsm.v : tile top (ring_pair_tt + vco_dsm_digital)
- vco_dsm_digital.v, ring_sync.v, phase_dec.v, front_end.v, backend.v, out_if.v : digital (backend.v: Option A,
  cubic corrector k3 = 2^-5 - 2^-7)
- ring_pair_tt.v : black-box view of the analog macro (layout and reference netlist in analog/)
src/project.v (one level up) is the port-only stub TinyTapeout compiles for a custom-GDS tile.
