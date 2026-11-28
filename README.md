# tt_um_vishnu1355_vco_dsm: Ring-VCO Delta-Sigma ADC with on-chip shift-add linearization

TinyTapeout SKY130, analog 1x2 tile, 2 analog pins (ua[0] = Vin+, ua[1] = Vin-). The datasheet is
[docs/info.md](docs/info.md).

| Path | Content |
|---|---|
| `gds/`, `lef/` | Hardened tile (LibreLane 3.0.17, TinyTapeout precheck 17/17) |
| `src/project.v` | Port list for TinyTapeout (custom-GDS stub) |
| `src/rtl/` | Hardened sources: tile top, digital back end, analog black box |
| `analog/` | Ring macro `ring_pair_tt`: GDS, LEF, LVS reference netlist, extracted netlist |
| `test/` | cocotb tests of the digital (bit-exact golden model, post-layout ring curves): `cd test && make` |
