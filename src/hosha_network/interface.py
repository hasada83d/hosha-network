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
    export_final_network
)

def develop_hosha_network(link_df, node_df, crs, output_dir="./output", contract=False,**kwargs):
    """
    歩車ネットワークを構築するユーザー用関数。

    Parameters:
    - link_df (DataFrame): GMNS形式のリンクデータ
    - node_df (DataFrame): GMNS形式のノードデータ
    - crs (str) : 入力データのCRS（例: "EPSG:4326"）
    - output_dir (str): 結果出力先フォルダ
    - contract (bool): 歩行者ネットワークの縮約を行うか（デフォルト: False）
    - export_display (bool): 
    """
    
    export_crs = kwargs.get("export_crs", "EPSG:4326")  #出力データのCRS（例: "EPSG:4326"）
    export_display = kwargs.get("export_display", False)  #表示用データを出力するか（デフォルト: False）
    export_name = kwargs.get("export_name", "hosha_") #出力データの名前
    
    os.makedirs(output_dir, exist_ok=True)

    config = {}
    config["output"]={}
    config["crs"]={}
    config["output"]["dir"] = output_dir
    config["output"]["name"] = export_name
    config["crs"]["input_crs"] = crs 
    config["crs"]["export_crs"] = export_crs

    # --- 前処理 ---
    processed_link = preprocess_original_links(link_df)
    processed_node = preprocess_original_nodes(node_df, processed_link)

    # --- ネットワーク種別の分岐 ---
    walk_link, walk_node, veh_link, veh_node = branch_network_types(processed_link, processed_node)

    # --- 歩行者ネットワークの構築 ---
    contract_option = "partial" if contract else "none"
    final_ped_nodes, final_ped_links = process_pedestrian_network(walk_link, walk_node, contract=contract_option)

    # --- 車両ネットワークの構築 ---
    updated_veh_nodes, updated_veh_links = process_vehicle_network(veh_link, veh_node)

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
    if export_display:
        config["output"]["suffix"] = "_display"
        display_nodes = adjust_display_coordinates(final_nodes, processed_node, scale_factor=10)
        export_final_network(display_nodes, final_links, node_df, link_df, config)

    # --- 統計出力 ---
    #print("【歩行者ネットワーク】ノード:", final_ped_nodes.shape[0], "リンク:", final_ped_links.shape[0])
    #print("【車両ネットワーク】ノード:", updated_veh_nodes.shape[0], "リンク:", updated_veh_links.shape[0])
    print("【構築ネットワーク】ノード:", final_nodes.shape[0], "リンク:", final_links.shape[0])

