# hosha-network （歩車ネットワーク）
A Python library to construct detailed pedestrian-vehicle layered networks from macro-level road data.

マクロレベルな道路データから，歩行者と車両の詳細な動態を表現する歩車分離ネットワークを構築する Python ライブラリです．

## Overview 概要
**hosha-network** is a Python module for constructing a micro network that expresses the detailed dynamics of pedestrians and vehicles from a macro road network consisting of undirected links and intersection nodes. By extending intersections to generate entrance/exit nodes and adding transition links, it creates a directed network divided into layers for pedestrians and vehicles.

hosha-networkは，無向リンクと交差点ノードからなるマクロな街路ネットワークから，歩行者と車両の詳細な動態を表現するミクロなネットワークを構築するための Python モジュールです．交差点を拡張して出入口ノードを生成し，遷移リンクを付加することで，歩行者と車両のレイヤーに分かれた有向ネットワークを作成します．

 <img src="https://github.com/user-attachments/assets/b713aff6-0bf2-4642-9b90-cd57b8c5f451" width="50%" />

## Features 特徴

- 🚶‍♂️ Separate layers for pedestrians and vehicles: Sidewalks are generated on both sides of vehicle lanes, enabling independent analysis for pedestrians and vehicles.
 
　　歩行空間のレイヤー分離：車道の両外側に歩行空間を設けることで，歩行者と車両を別レイヤーで扱い，それぞれの移動特性に基づいた解析が可能になります. 
  
- 🔁 Vehicle Turning movement representation: Transition links for vehicle right-turn, left-turn, and straight movement are inserted to represent detailed behavior at intersections.
 
　　車両の遷移動作の明示：直進・右左折を表す遷移リンクを交差点に挿入し，車両の交差点内の詳細な動作を再現します. 
  
- 🚸 Pedestrian crossing movement representation: Crossing links for pedestrians are placed around vehicular transitions, clearly capturing pedestrian crossing behavior.
 
　　歩行者の横断行動の明示：車両の遷移リンクの外側に歩行者用の横断リンクを設け，横断行動を明確に表現します. 
  
- 📍 Midlink segmentation: Road segments are divided at their midpoints, enabling precise modeling of trip origins and destinations even along road sections.

　　中点での道路分割：歩行空間・車道リンクは中点で分割され，交差点以外の道路区間でも正確な出発・到着（OD）表現が可能になります. 

## Citation 引用
Coming soon!

## Acknowledgment 謝辞
この成果は，NEDO（国立研究開発法人新 エネルギー・産業技術総合開発機構）の委託業務 （JPNP23023）の結果得られたものです．

## References 参考文献
- 羽佐田紘之, 池谷風馬, 鳥海梓, 本間裕大, and 大口敬. 2025. “歩車ネットワークの構築と「安心とこてくゾーン」の設定手法理論の検討.” In 第71回土木計画学研究発表会・講演集.

---
## Installation インストール
Coming soon!
<!-- 
```bash
pip install hosha-network
```
-->

## Usage 使い方

```python
from hosha_network import develop_hosha_network

develop_hosha_network(link_gdf, node_df, crs, output_dir, contract=False, export_display=True)
```

## Function: `develop_hosha_network()` 関数の説明

This function generates a layered pedestrian-vehicle network from macro-level road data in GMNS format, assuming a planar (Cartesian) coordinate system such as UTM.

本関数は、平面直交座標系（例: UTM）を前提として，GMNS形式のマクロ道路データから歩車分離ネットワークを構築します. 

**Parameters 引数:**

English
- `link_gdf`: GeoDataFrame with columns: `link_id`, `from_node_id`, to_node_id`, `geometry`  (follows [GMNS format](https://github.com/zephyr-data-specs/GMNS))
- `node_df`: DataFrame with columns: `node_id`, `x_coord, `y_coord`  (follows [GMNS format](https://github.com/zephyr-data-specs/GMNS))
- `crs`: Coordinate Reference System (EPSG code). The module currently supports only planar (Cartesian) coordinate systems such as UTM.
- `output_dir`: Output directory for saving results.
- `contract`: Whether to contract intermediate nodes (default: False).
- `export_display`: Whether to export scaled coordinate data for visualization (default: True).

日本語
- `link_gdf`: `link_id`, `from_node_id`, to_node_id`, `geometry` を含む GeoDataFrame ([GMNS フォーマット](https://github.com/zephyr-data-specs/GMNS)に準拠). 
- `node_df`: `node_id`, `x_coord, `y_coord`を含む DataFrame ([GMNS フォーマット](https://github.com/zephyr-data-specs/GMNS)に準拠). 
- `crs`: 使用する座標系（EPSGコード）. 本モジュールは平面直交座標系のみ対応しています. 
- `output_dir`: 結果を保存する出力先ディレクトリ. 
- `contract`: 中間ノードの縮約を実行するか（デフォルト: False）. 
- `export_display`: 表示用のスケーリング出力も行うか（デフォルト: True）. 

