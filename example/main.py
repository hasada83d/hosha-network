#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
main.py
-------
本ファイルは、プロジェクトの実行エントリーポイントです。

【処理の流れ】
1. ライブラリのインポート
2. コンフィグ (config.ini) を読み込み、io.py の関数を用いてデータの読み込みと CRS 変換を実施
3. オリジナルデータの前処理（リンク・ノード）
4. ネットワーク種別の分岐（歩行者・車両）
5. 歩行者ネットワークの全体処理（リンク中心計算＋新規ノード生成＋ターンリンク生成＋縮約・抽出）
6. 車両ネットワークの全体処理（リンク中心計算＋新規ノード生成＋ターンリンク生成＋統合）
7. 両ネットワークの統合
8. リンクを分割
9.  表示用ノードの座標補正および最終データのエクスポート  
   ※ 統合ネットワーク（integrated_nodes, integrated_links）に対して、  
      補正前（raw）と補正後（display）の両方を出力する。
"""

import sys
sys.path.append(r"..\..\hosha-network")

# --- ステップ1: ライブラリのインポート ---
import os
from ioput import load_config, load_input_data  
from processing import (
    preprocess_original_links,
    preprocess_original_nodes,
    branch_network_types,
    process_pedestrian_network,
    process_vehicle_network,
    integrate_vehicle_and_pedestrian_networks,
    adjust_display_coordinates,
    finalize_network,
    split_links,
    export_final_network,
    birdirectionzie_ped_links
)

def main():
    # --- ステップ2: コンフィグの読み込みおよびデータの読み込み ---
    config = load_config(r"..\input\config.ini")
    ori_link, ori_node = load_input_data(config)
    
    # --- ステップ3: オリジナルデータの前処理 ---
    processed_link = preprocess_original_links(ori_link)
    processed_node = preprocess_original_nodes(ori_node, processed_link)
    
    # --- ステップ4: ネットワーク種別の分岐 ---
    walk_link, walk_node, veh_link, veh_node = branch_network_types(processed_link, processed_node)
    
    # --- ステップ5: 歩行者ネットワークの全体処理 ---
    final_ped_nodes, final_ped_links = process_pedestrian_network(walk_link, walk_node,contract="none")
    
    # --- ステップ6: 車両ネットワークの全体処理 ---
    updated_veh_nodes, updated_veh_links = process_vehicle_network(veh_link, veh_node)
    
    # --- ステップ7: 両ネットワークの統合 ---
    integrated_nodes, integrated_links = integrate_vehicle_and_pedestrian_networks(final_ped_nodes, final_ped_links, updated_veh_nodes, updated_veh_links)
    final_nodes, final_links = finalize_network(integrated_nodes, integrated_links, processed_link, processed_node)
    
    # --- ステップ8: リンクを分割 ---
    final_nodes, final_links = split_links(final_nodes, final_links)
    
    # --- ステップ9: 歩行者ネットワークを双方向に ---
    final_nodes, final_links = birdirectionzie_ped_links(final_nodes, final_links)
    
    # --- ステップ10: 表示用ノードの座標補正および最終データのエクスポート ---
    # 補正前の raw データをエクスポート
    export_final_network(final_nodes, final_links, config, suffix="raw")
    # 補正後の表示用データを作成してエクスポート
    display_nodes = adjust_display_coordinates(final_nodes, processed_node, scale_factor=10)
    export_final_network(display_nodes, final_links, config, suffix="display")
    
    # 結果確認用出力
    print("【歩行者ネットワーク（縮約後）】")
    print("最終ノード数:", final_ped_nodes.shape[0])
    print("最終リンク数:", final_ped_links.shape[0])
    
    print("\n【車両ネットワーク】")
    print("更新後ノード数（車両）:", updated_veh_nodes.shape[0])
    print("更新後リンク数（車両）:", updated_veh_links.shape[0])
    
    print("\n【統合ネットワーク】")
    print("統合後ノード数:", integrated_nodes.shape[0])
    print("統合後リンク数:", integrated_links.shape[0])

if __name__ == "__main__":
    main()
