# -*- coding: utf-8 -*-
"""
Created on Wed May 28 21:11:36 2025

@author: hasada83d
"""

# src/hosha_network/interface.py

import os
import geopandas as gpd
from .processing import (
    preprocess_original_links,
    preprocess_original_nodes,
    branch_network_types,
    process_pedestrian_network,
    process_vehicle_network,
    integrate_vehicle_and_pedestrian_networks,
    finalize_network,
    split_links,
    birdirectionzie_ped_links,
    adjust_display_coordinates,
    export_final_network,
    get_utm_epsg
)

def develop_hosha_network(link_df, node_df, output_dir="./output", **kwargs):
    """
    A user-facing function to construct a pedestrian-vehicle integrated network.

    Parameters:
    - link_df (DataFrame): Link data in GMNS format.
    - node_df (DataFrame): Node data in GMNS format.
    - output_dir (str): Directory where the output files will be saved (default: "./output").
    - **kwargs: Optional keyword arguments for fine-tuning the construction process.

      Optional Keyword Arguments (kwargs):
      - input_crs (str): Coordinate reference system (CRS) of input data (default: "EPSG:4326").
      - output_crs (str): CRS to use for exported output data (default: "EPSG:4326").
      - output_display (bool): Whether to export display-friendly files for visualization (default: False).
      - output_name (str): Prefix for the names of output files (default: "hosha_").

      - contract (bool): Whether to contract the pedestrian network (default: False).
      - left_driving (bool): Whether the network assumes left-hand traffic (default: True).
      - make_uturn (bool): Whether to allow U-turns in vehicle network construction (default: False).
      
      - veh_offset_angle (float): Angular offset (in degrees) when generating vehicle turning links (default: 10).
      - veh_scale (float): Link length scaling factor for vehicle links (default: 0.5).
      - veh_threshold_deg (float): Angular threshold (in degrees) to determine turn connections (default: 45).

      - ped_offset_angle (float): Angular offset (in degrees) when generating pedestrian turning links (default: 10).
      - ped_scale (float): Link length scaling factor for pedestrian links (default: 1.0).
      - ped_threshold_deg (float): Angular threshold (in degrees) to determine pedestrian turn connections (default: 45).
     
    """   
    
    os.makedirs(output_dir, exist_ok=True)

    config = {}
    config["output"]={}
    config["crs"]={}
    config["veh"]={}
    config["ped"]={}
    config["method"]={}
    
    config["crs"]["input_crs"] = kwargs.get("input_crs", "EPSG:4326")  #入力データのCRS（例: "EPSG:4326"）
    config["crs"]["export_crs"] = kwargs.get("output_crs", "EPSG:4326")  #出力データのCRS（例: "EPSG:4326"）
    config["output"]["display"] = kwargs.get("output_display", False)  #表示用データを出力するか（デフォルト: False）
    config["output"]["name"] = kwargs.get("output_name", "hosha_") #出力データの名前
    config["output"]["dir"] = output_dir

    config["method"]["contract"]=kwargs.get("contract",False)

    config["veh"]["offset_angle"]=kwargs.get("veh_offset_angle", 10)
    config["veh"]["scale"]=kwargs.get("veh_scale", 0.5)
    config["veh"]["left_driving"]=kwargs.get("left_driving", True)
    config["veh"]["threshold_deg"]=kwargs.get("veh_threshold_deg", 45)
    config["veh"]["make_uturn"]=kwargs.get("make_uturn",False)
    
    config["ped"]["offset_angle"]=kwargs.get("ped_offset_angle", 10)
    config["ped"]["scale"]=kwargs.get("ped_scale", 1.0)
    config["ped"]["left_driving"]=kwargs.get("left_driving", True)
    config["ped"]["threshold_deg"]=kwargs.get("ped_threshold_deg", 45)

    # --- 前処理 ---
    config["crs"]["projected_crs"] = get_utm_epsg(node_df['y_coord'].median(),node_df['x_coord'].median())
    node_df = gpd.GeoDataFrame(node_df, geometry=gpd.points_from_xy(node_df['x_coord'], node_df['y_coord']),crs=config["crs"]["input_crs"] ).to_crs(config["crs"]["projected_crs"])
    
    processed_link = preprocess_original_links(link_df)
    processed_node = preprocess_original_nodes(node_df, processed_link)

    # --- ネットワーク種別の分岐 ---
    walk_link, walk_node, veh_link, veh_node = branch_network_types(processed_link, processed_node)

    # --- 歩行者ネットワークの構築 ---
    contract_option = "partial" if contract else "none"
    final_ped_nodes, final_ped_links = process_pedestrian_network(walk_link, walk_node, config["method"]["contract"],config)

    # --- 車両ネットワークの構築 ---
    updated_veh_nodes, updated_veh_links = process_vehicle_network(veh_link, veh_node,config)

    # --- 統合と整理 ---
    integrated_nodes, integrated_links = integrate_vehicle_and_pedestrian_networks(
        final_ped_nodes, final_ped_links,
        updated_veh_nodes, updated_veh_links
    )
    final_nodes, final_links = finalize_network(integrated_nodes, integrated_links, processed_link, processed_node)

    # --- リンク分割と歩行者リンク双方向化 ---
    final_nodes, final_links = split_links(final_nodes, final_links)
    final_nodes, final_links = birdirectionzie_ped_links(final_nodes, final_links)

    # --- エクスポート（raw） ---
    config["output"]["suffix"] = ""
    export_final_network(final_nodes, final_links, node_df, link_df, config)

    # --- 表示用出力（オプション） ---
    if config["output"]["display"]:
        config["output"]["suffix"] = "_display"
        display_nodes = adjust_display_coordinates(final_nodes, processed_node, scale_factor=10)
        export_final_network(display_nodes, final_links, node_df, link_df, config)

    # --- 統計出力 ---
    #print("【歩行者ネットワーク】ノード:", final_ped_nodes.shape[0], "リンク:", final_ped_links.shape[0])
    #print("【車両ネットワーク】ノード:", updated_veh_nodes.shape[0], "リンク:", updated_veh_links.shape[0])
    print("【構築ネットワーク】ノード:", final_nodes.shape[0], "リンク:", final_links.shape[0])

