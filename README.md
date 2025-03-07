# hosha-network （歩車ネットワーク）

The English explanation follows. 

## 概要
本モジュールは，無向リンクと交差点ノードからなるマクロな道路ネットワークから，歩行者と車両の詳細な動態を表現するミクロなネットワークを構築するための Python モジュールです．交差点を拡張して出入口（出入）ノードを生成し，遷移リンクを付加することで，歩行者と車両のレイヤーに分かれた有向ネットワークを作成します．
 <img src="https://github.com/user-attachments/assets/b713aff6-0bf2-4642-9b90-cd57b8c5f451" width="50%" />

## 基本的な手法とその意図
- 車道の両外側に歩行空間を配置します．これによって，歩行者と車両を別のレイヤーとして扱い，各々の移動特性に基づいた解析が可能となります．
- 車両の直進，右折，左折を表す遷移リンクを挿入します．これにより，交差点内での車両の詳細な動作が再現されます．
- 車両の遷移リンクの外側には，歩行者の道路横断を示す遷移リンクを挿入します．これにより，歩行者の横断動作を明確に表現できます．
- 道路区間は中点で分割します．交差点だけでなく，道路区間起点での出発・到着（OD）を正確に表現できます．

## ファイル構成
- processing.py
    - ネットワークの拡張，遷移リンク生成，統合，縮約，リンク分割，表示用座標補正，出力処理など各種関数を実装．
- utils.py
    - 座標変換支援クラス（RD）や平均角度算出関数（average_angle）などの共通機能を提供．
- ioput.py
    - 設定ファイル（config.ini）の読み込みおよびデータの入出力を行う．

## 使用方法

1. 必要な Python パッケージ（numpy，pandas，geopandas，shapely，networkx）をインストールする．
2. config.ini の内容を適宜編集し，入力データ，出力先，CRS 等の設定を行う．
3. 実行する．例を以下に示す．
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
4. 歩車ネットワークデータ（ノード：CSV、リンク：GeoJSON）が出力される．

## 補足
- 歩行者ネットワークでは，車道側の外側に出入口ノードを配置し，両側それぞれに有向リンクペア（計 4 本）のうち，片側ごとに異なる bidirectionalpair_id を設定しています．
- 車両ネットワークでは，歩道側の内側に出入口ノードを配置し，両側合わせて 2 本の有向リンクペアを構成しています．
- リンク分割では，各リンクを中点で分割し，新たに生成された中間ノードには "split" 列に 1 を設定するとともに，元リンクの macro_link 情報を _original_link_id（後に macro_link_id として出力）に引き継いでいます．さらに，分割後のリンクの重みは元の半分としています．

## 謝辞
この成果の一部は，NEDO（国立研究開発法人新 エネルギー・産業技術総合開発機構）の委託業務 （JPNP23023）の結果得られたものです．

## 引用方法
このリポジトリ，またはここに示されたコード/アルゴリズムの一部を使用する場合は，以下の論文を引用してください：

羽佐田紘之, 池谷風馬, 鳥海梓, 本間裕大, 大口敬. (2025). “歩車ネットワークの構築と歩行者プロテクトゾーンの理論的設定手法の検討.” In 第71回土木計画学研究発表会・講演集 (in press).

## Overview
This repository contains a Python module for constructing a detailed network that captures both pedestrian and vehicular movements from a macro-level road network. In essence, a macro network—composed of undirected road segments and intersection nodes—is transformed into a micro network featuring directional links that represent the fine-grained movement patterns of pedestrians and vehicles.

## Basic Approach
The core idea of this module is to separate pedestrian and vehicular movements by layering them on different portions of the road space. First, additional nodes are generated at intersections to serve as entry/exit (or “in/out”) points. In the pedestrian layer, these nodes are positioned on the outer side of the roadway (i.e., on the vehicle side), and directional links are constructed in pairs—one for each direction—so that, in total, there are four links per intersection (two for each side). In contrast, in the vehicular layer, the entry/exit nodes are placed on the inner side (i.e., adjacent to the sidewalk), and a single pair of directional links is generated to represent turning movements such as left, straight, or right.

## File Structure
- processing.py
    - Implements functions for data preprocessing, network extension (computing link centers and generating entry/exit nodes), generating transition links, integrating and contracting the network, performing link splitting, adjusting display coordinates, and exporting the final data.
- utils.py
    - Contains common utilities such as the RD (relative coordinate conversion) class and an average angle calculation function.
- my_io.py
    - Handles input/output operations and reads the configuration file.

## Usage
1. Install the required Python packages (e.g., numpy, pandas, geopandas, shapely, networkx).
2. Edit the config.ini file as needed to specify your input data paths, output directory, and CRS settings.
3. Run. An example follows.
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
4. The final network data will be exported as CSV files (for nodes) and GeoJSON files (for links).

## Citation
If you use this repository or any part of the code/algorithms presented herein, please cite the following paper:

Hasada, H., Ikeya, F., Toriumi, A., Honma, Y., Oguchi, T. (2025). “Development of pedestrian-vehicle networks and theoretical methodology for defining pedestrian protection zones.” In Proceedings of infrastructure planning (in press).
