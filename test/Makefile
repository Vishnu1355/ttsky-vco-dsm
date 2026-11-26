# cocotb testbench for the digital macro (Icarus Verilog).  Run: make
SIM ?= icarus
TOPLEVEL_LANG = verilog
SRC = ../src
VERILOG_SOURCES = $(SRC)/ring_sync.v $(SRC)/phase_dec.v $(SRC)/front_end.v $(SRC)/backend.v $(SRC)/out_if.v $(SRC)/vco_dsm_digital.v
COCOTB_TOPLEVEL = vco_dsm_digital
COCOTB_TEST_MODULES = test
include $(shell cocotb-config --makefiles)/Makefile.sim
