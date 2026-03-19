# ==============================================================================
# 🛠️ BITNET 1.58b VIVADO BLOCK DESIGN AUTOMATION 
# ==============================================================================

# 1. Set the path to your generated HLS IP and update catalog
set ip_repo_path "../Vitis_HLS/bitnet_hls_workspace/solution1/impl/ip"
set_property ip_repo_paths $ip_repo_path [current_project]
update_ip_catalog

# 2. Create the Block Design
create_bd_design "design_1"

# 3. Instantiate and configure the Zynq Processing System (ARM Cortex-A9)
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external "FIXED_IO, DDR" apply_board_preset "1" Master "Disable" Slave "Disable" }  [get_bd_cells processing_system7_0]

# Enable AXI HP0 port for high-speed, direct-to-memory DMA transfers
set_property -dict [list CONFIG.PCW_USE_S_AXI_HP0 {1}] [get_bd_cells processing_system7_0]

# 4. Instantiate and configure the AXI Direct Memory Access (DMA)
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 axi_dma_0

# Disable Scatter-Gather, set buffer width to 26, and force 1024-bit (128-byte) data widths 
# to handle the massive parallel feature ingestion.
set_property -dict [list \
    CONFIG.c_include_sg {0} \
    CONFIG.c_sg_length_width {26} \
    CONFIG.c_m_axis_mm2s_tdata_width {1024} \
    CONFIG.c_s_axis_s2mm_tdata_width {1024} \
    CONFIG.c_m_axi_mm2s_data_width {1024} \
    CONFIG.c_m_axi_s2mm_data_width {1024} \
] [get_bd_cells axi_dma_0]

# 5. Instantiate your custom BitNet Accelerator IP (Data-Driven / ap_ctrl_none)
create_bd_cell -type ip -vlnv mts:hls:BitNet_LLM:1.0 BitNet_LLM_0

# 6. Instantiate the TLAST Injector (Subset Converter) for the S2MM channel
create_bd_cell -type ip -vlnv xilinx.com:ip:axis_subset_converter:1.1 tlast_injector
set_property -dict [list \
    CONFIG.M_HAS_TLAST {1} \
    CONFIG.TLAST_REMAP {1'b1} \
    CONFIG.S_TDATA_NUM_BYTES {128} \
    CONFIG.M_TDATA_NUM_BYTES {128} \
] [get_bd_cells tlast_injector]

# 7. Wire the AXI4-Stream Data Paths
# DMA (MM2S) -> BitNet IP -> TLAST Injector -> DMA (S2MM)
connect_bd_intf_net [get_bd_intf_pins axi_dma_0/M_AXIS_MM2S] [get_bd_intf_pins -of_objects [get_bd_cells BitNet_LLM_0] -filter {MODE==Slave && VLNV=~*axis*}]
connect_bd_intf_net [get_bd_intf_pins -of_objects [get_bd_cells BitNet_LLM_0] -filter {MODE==Master && VLNV=~*axis*}] [get_bd_intf_pins tlast_injector/S_AXIS]
connect_bd_intf_net [get_bd_intf_pins tlast_injector/M_AXIS] [get_bd_intf_pins axi_dma_0/S_AXIS_S2MM]

# 8. Run Connection Automation for AXI-Lite (Control) and AXI-MM (Memory)
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config { Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} Master {/processing_system7_0/M_AXI_GP0} Slave {/axi_dma_0/S_AXI_LITE} ddr_seg {Auto} intc_ip {New AXI Interconnect} master_apm {0}}  [get_bd_intf_pins axi_dma_0/S_AXI_LITE]
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config { Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} Master {/axi_dma_0/M_AXI_MM2S} Slave {/processing_system7_0/S_AXI_HP0} ddr_seg {Auto} intc_ip {New AXI Interconnect} master_apm {0}}  [get_bd_intf_pins processing_system7_0/S_AXI_HP0]
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config { Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} Master {/axi_dma_0/M_AXI_S2MM} Slave {/processing_system7_0/S_AXI_HP0} ddr_seg {Auto} intc_ip {New AXI Interconnect} master_apm {0}}  [get_bd_intf_pins axi_dma_0/M_AXI_S2MM]

# 9. Manually connect Clocks and Resets for the Data-Driven IP and Injector
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] [get_bd_pins BitNet_LLM_0/ap_clk]
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] [get_bd_pins tlast_injector/aclk]

set rst_net [get_bd_nets -of_objects [get_bd_pins axi_dma_0/axi_resetn]]
connect_bd_net -net $rst_net [get_bd_pins BitNet_LLM_0/ap_rst_n]
connect_bd_net -net $rst_net [get_bd_pins tlast_injector/aresetn]

# 10. Clean up, Validate, and Save
regenerate_bd_layout
validate_bd_design
save_bd_design



puts "======================================================================"
puts "✅ SUCCESS: BitNet Hardware Architecture successfully built!"
puts "======================================================================"