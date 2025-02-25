# hosha-network

The English explanation follows. 

## 概要
本モジュールは、無向リンクと交差点ノードからなるマクロな道路ネットワークを基盤とし、そこから歩行者と車両の詳細な動態を表現するミクロなネットワークを構築するための Python モジュールである。具体的には、交差点を拡張して出入口（出入）ノードを生成し、各層ごとに有向リンク（遷移リンク）を付加することで、歩行者と車両の移動を個別に解析可能なネットワークを作成する。さらに、各リンクは中点で分割され、リンクの重みは分割後に半分に調整され、双方向リンクは別々の識別子が付与される。

## 基本的な手法とその意図
- まず、車道の両外側に歩行空間を配置する。これにより、歩行者と車両を別のレイヤーとして扱い、各々の移動特性に基づいた解析が可能となる。
- 次に、交差点を拡張し、車両の直進、右折、左折を表す遷移リンクを挿入する。これにより、交差点内での車両の詳細な動作が再現される。
- さらに、交差点を拡張することで、車両の遷移リンクの外側に、歩行者がどの道路を横断するかを示す遷移リンクを挿入する。これにより、歩行者の横断動作を明確に表現する。
- また、道路区間は中点で分割することで、交差点だけでなく、道路区間起点での出発・到着（OD）を正確に表現できるようにしている。

## ファイル構成
- main.py
    - 全体の処理パイプライン（前処理、層分離、各ネットワークの拡張、リンク分割、座標補正、出力）を実行するエントリーポイント。
- processing.py
    - ネットワークの拡張、遷移リンク生成、統合、縮約、リンク分割、表示用座標補正、出力処理など各種関数を実装。
- utils.py
    - 座標変換支援クラス（RD）や平均角度算出関数（average_angle）などの共通機能を提供。
- my_io.py
    - 設定ファイル（config.ini）の読み込みおよびデータの入出力を行う。
- config.ini
    - 入力データパス、出力ディレクトリ、座標系などの設定ファイル。

## 使用方法

必要な Python パッケージ（pandas、numpy、geopandas、networkx、shapely など）をインストールする。
config.ini の内容を適宜編集し、入力データ、出力先、CRS 等の設定を行う。
```python:main.py
# --- ステップ1: ライブラリのインポート ---
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
    export_final_network
)

def main():
    # --- ステップ2: コンフィグの読み込みおよびデータの読み込み ---
    config = load_config("your config path")
    ori_link, ori_node = load_input_data(config)
    
    # --- ステップ3: オリジナルデータの前処理 ---
    processed_link = preprocess_original_links(ori_link)
    processed_node = preprocess_original_nodes(ori_node, processed_link)
    
    # --- ステップ4: ネットワーク種別の分岐 ---
    walk_link, walk_node, veh_link, veh_node = branch_network_types(processed_link, processed_node)
    
    # --- ステップ5: 歩行者ネットワークの全体処理 ---
    final_ped_nodes, final_ped_links = process_pedestrian_network(walk_link, walk_node)
    
    # --- ステップ6: 車両ネットワークの全体処理 ---
    updated_veh_nodes, updated_veh_links = process_vehicle_network(veh_link, veh_node)
    
    # --- ステップ7: 両ネットワークの統合 ---
    integrated_nodes, integrated_links = integrate_vehicle_and_pedestrian_networks(final_ped_nodes, final_ped_links, updated_veh_nodes, updated_veh_links)
    final_nodes, final_links = finalize_network(integrated_nodes, integrated_links, processed_link, processed_node)
    
    # --- ステップ8: リンクを分割 ---
    final_nodes, final_links = split_links(final_nodes, final_links)
    
    # --- ステップ9: 表示用ノードの座標補正および最終データのエクスポート ---
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
```
これにより、最終的なネットワークデータ（ノード：CSV、リンク：GeoJSON）が出力される。

## 補足
- 歩行者ネットワークでは、車道側の外側に出入口ノードを配置し、両側それぞれに有向リンクペア（計 4 本）のうち、片側ごとに異なる bidirectionalpair_id を設定する。
- 車両ネットワークでは、歩道側の内側に出入口ノードを配置し、両側合わせて 2 本の有向リンクペアを構成する。
- リンク分割では、各リンクを中点で分割し、新たに生成された中間ノードには "split" 列に 1 を設定するとともに、元リンクの macro_link 情報を _original_link_id（後に macro_link_id として出力）に引き継ぐ。さらに、分割後のリンクの重みは元の半分となる。

## 謝辞
この成果の一部は，NEDO（国立研究開発法人新 エネルギー・産業技術総合開発機構）の委託業務 （JPNP23023）の結果得られたものです．

## 引用方法
このリポジトリ、またはここに示されたコード/アルゴリズムの一部を使用する場合は、以下の論文を引用してください：
羽佐田紘之, 池谷風馬, 鳥海梓, 本間裕大, 大口敬. (2025). “歩車ネットワークの構築と歩行者プロテクトゾーンの理論的設定手法の検討.” In 第71回土木計画学研究発表会・講演集 (in press).

## Overview
This repository contains a Python module for constructing a detailed network that captures both pedestrian and vehicular movements from a macro-level road network. In essence, a macro network—composed of undirected road segments and intersection nodes—is transformed into a micro network featuring directional links that represent the fine-grained movement patterns of pedestrians and vehicles.

## Basic Approach
The core idea of this module is to separate pedestrian and vehicular movements by layering them on different portions of the road space. First, additional nodes are generated at intersections to serve as entry/exit (or “in/out”) points. In the pedestrian layer, these nodes are positioned on the outer side of the roadway (i.e., on the vehicle side), and directional links are constructed in pairs—one for each direction—so that, in total, there are four links per intersection (two for each side). In contrast, in the vehicular layer, the entry/exit nodes are placed on the inner side (i.e., adjacent to the sidewalk), and a single pair of directional links is generated to represent turning movements such as left, straight, or right. Furthermore, each road segment is split at its midpoint to accurately represent origin–destination (OD) pairs that originate from the road segments rather than the intersections.

## File Structure
- main.py
    - The entry point for running the entire processing pipeline, including preprocessing, network extension, link splitting, coordinate adjustment, and final export.
- processing.py
    - Implements functions for data preprocessing, network extension (computing link centers and generating entry/exit nodes), generating transition links, integrating and contracting the network, performing link splitting, adjusting display coordinates, and exporting the final data.
- utils.py
    - Contains common utilities such as the RD (relative coordinate conversion) class and an average angle calculation function.
- my_io.py
    - Handles input/output operations and reads the configuration file.
- config.ini
    - Contains settings for input data paths, output directories, coordinate reference systems (CRS), etc.

## Usage
Install the required Python packages (e.g., pandas, numpy, geopandas, networkx, shapely).
Edit the config.ini file as needed to specify your input data paths, output directory, and CRS settings.

```python:main.py
# --- Step 1: Import libraries ---
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
    export_final_network
)
def main():
    # --- Step 2: Load configuration and input data ---
    config = load_config(r"..\input\config.ini")
    ori_link, ori_node = load_input_data(config)
    
    # --- Step 3: Preprocess original data ---
    processed_link = preprocess_original_links(ori_link)
    processed_node = preprocess_original_nodes(ori_node, processed_link)
    
    # --- Step 4: Separate network types (pedestrian and vehicular) ---
    walk_link, walk_node, veh_link, veh_node = branch_network_types(processed_link, processed_node)
    
    # --- Step 5: Process pedestrian network ---
    final_ped_nodes, final_ped_links = process_pedestrian_network(walk_link, walk_node)
    
    # --- Step 6: Process vehicular network ---
    updated_veh_nodes, updated_veh_links = process_vehicle_network(veh_link, veh_node)
    
    # --- Step 7: Integrate both networks ---
    integrated_nodes, integrated_links = integrate_vehicle_and_pedestrian_networks(
        final_ped_nodes, final_ped_links, updated_veh_nodes, updated_veh_links
    )
    final_nodes, final_links = finalize_network(integrated_nodes, integrated_links, processed_link, processed_node)
    
    # --- Step 8: Split links ---
    final_nodes, final_links = split_links(final_nodes, final_links)
    
    # --- Step 9: Adjust display coordinates and export final data ---
    # Export raw data (before coordinate adjustment)
    export_final_network(final_nodes, final_links, config, suffix="raw")
    # Create display data by adjusting node coordinates and export it
    display_nodes = adjust_display_coordinates(final_nodes, processed_node, scale_factor=10)
    export_final_network(display_nodes, final_links, config, suffix="display")
    
    # Print results for verification
    print("【Pedestrian Network (After Contraction)】")
    print("Final number of nodes:", final_ped_nodes.shape[0])
    print("Final number of links:", final_ped_links.shape[0])
    
    print("\n【Vehicular Network】")
    print("Updated number of vehicular nodes:", updated_veh_nodes.shape[0])
    print("Updated number of vehicular links:", updated_veh_links.shape[0])
    
    print("\n【Integrated Network】")
    print("Number of nodes after integration:", integrated_nodes.shape[0])
    print("Number of links after integration:", integrated_links.shape[0])

if __name__ == "__main__":
    main()
```
The final network data will be exported as CSV files (for nodes) and GeoJSON files (for links).

## Citation
If you use this repository or any part of the code/algorithms presented herein, please cite the following paper:
Hasada, H., Ikeya, F., Toriumi, A., Honma, Y., Oguchi, T. (2025). “Development of pedestrian-vehicle networks and theoretical methodology for defining pedestrian protection zones.” In Proceedings of infrastructure planning (in press).
