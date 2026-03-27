# =========================================================
# Vivado BitNet System Builder Script
# =========================================================

# 1. Project Configuration
set project_name "BitNet_Vivado"
set part_name "xc7z010clg400-1"
# Point this to the directory where v++ exported your IP ZIP/folder
set ip_repo_path "./Vitis_HLS/src/build" 

# 2. Create Project
create_project $project_name ./$project_name -part $part_name -force

# 3. Add Custom IP Repository
set_property ip_repo_paths $ip_repo_path [current_project]
update_ip_catalog

# 4. Create Block Design
create_bd_design "design_1"

# 5. Instantiate Zynq Processing System (PS)
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0

# Apply Basic Zynq Automation (DDR and Fixed IO)
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external "FIXED_IO, DDR" apply_board_preset "1" Master "Disable" Slave "Disable" }  [get_bd_cells processing_system7_0]

# 6. Instantiate your custom BitNet IP (UPDATED VLNV)
create_bd_cell -type ip -vlnv mts:zynq_ai:bitnet_llm:1.1 bitnet_llm_0

# 7. Apply Connection Automation
# This wires the Zynq's Master AXI port to your IP's Slave AXI port and handles the 100MHz clock mapping
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config { Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} Master {/processing_system7_0/M_AXI_GP0} Slave {/bitnet_llm_0/s_axi_control} ddr_seg {Auto} intc_ip {New AXI Interconnect} master_apm {0}}  [get_bd_intf_pins bitnet_llm_0/s_axi_control]

# 8. Clean up layout
regenerate_bd_layout
save_bd_design

# 9. Create HDL Wrapper
set bd_file [get_files ./$project_name/$project_name.srcs/sources_1/bd/design_1/design_1.bd]
make_wrapper -files $bd_file -top
add_files -norecurse ./$project_name/$project_name.gen/sources_1/bd/design_1/hdl/design_1_wrapper.v

# Set top-level module
set_property top design_1_wrapper [current_fileset]
update_compile_order -fileset sources_1

puts "========================================================="
puts "SUCCESS: Vivado Block Design built and wrapper generated!"
puts "========================================================="
