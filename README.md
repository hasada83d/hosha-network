# hosha-network （歩車ネットワーク）
[![PyPI version](https://badge.fury.io/py/hosha-network.svg)](https://pypi.org/project/hosha-network/)

A Python library to construct detailed pedestrian-vehicle layered networks from macro-level road data.

マクロレベルな道路データから，歩行者と車両の詳細な動態を表現する歩車分離ネットワークを構築する Python ライブラリです．

## Overview 概要
**hosha-network** is a Python library for constructing a micro network that expresses the detailed dynamics of pedestrians and vehicles from a macro road network consisting of undirected links and intersection nodes. By extending intersections to add entrance/exit nodes and transition links, it creates a directed network divided into layers for pedestrians and vehicles.

**hosha-network** は，無向リンクと交差点ノードからなるマクロな街路ネットワークから，歩行者と車両の詳細な動きを表現できるミクロなネットワークを構築するための Python ライブラリです．交差点を拡張して遷移リンクや出入口ノードを挿入し，歩行者と車両のレイヤーに分かれた有向ネットワークを作成します．

 <img src="[https://github.com/user-attachments/assets/85dcd9b9-1ee4-45f2-937a-35f261517985](https://github.com/user-attachments/assets/3fb8c462-8ae1-442b-8d5a-a5ea7ae09f17)" width="50%" />

## Features 特徴

- 🚶‍♂️🚗 Separate layers for pedestrians and vehicles: Sidewalks are generated on both sides of vehicle lanes, enabling independent analysis for pedestrians and vehicles.
 
　　歩行者と車両のレイヤー分離：車道の両外側に歩行空間を設けることで，歩行者と車両を別レイヤーで扱い，それぞれの移動特性に基づいた解析が可能になります. 
  
- 🚥 Vehicle Turning movement representation: Transition links for vehicle right-turn, left-turn, and straight movement are inserted to represent detailed behavior at intersections.
 
　　車両の遷移動作の明示：直進・右左折・Uターンを表す遷移リンクを交差点に挿入し，車両の交差点内の詳細な動作を再現します. 
  
- 🚸 Pedestrian crossing movement representation: Crossing links for pedestrians are placed around vehicular transitions, clearly capturing pedestrian crossing behavior.
 
　　歩行者の横断行動の明示：車両の遷移リンクの外側に歩行者用の横断リンクを設け，横断行動を明確に表現します. 
  
- 📍 Midlink segmentation: Road segments are divided at their midpoints, enabling precise modeling of trip origins and destinations even along road sections.

　　中点での道路分割：歩行空間・車道リンクは中点で分割され，交差点以外の街路上でも正確な出発・到着（OD）表現が可能になります. 

## Citation 引用
- Hasada, H., Flexible Foundational Tools for Identifying Detailed Pedestrian and Vehicle Movements Based on Street Structure (preprint).  
  羽佐田紘之, 街路構造に基づいて歩行者・車両の詳細な移動を推定する柔軟な基盤技術の開発 (preprint).

## Acknowledgment 謝辞
This library includes the results of Cross-ministerial Strategic Innovation Promotion Program (SIP) 3rd Phase, “Development of Smart Mobility Platform” promoted by Council for Science, Technology and Innovation, Cabinet Office. （Project Management Agency：New Energy and Industrial Technology Development Organization (NEDO) (Project Code JPNP23023))

<img src="https://github.com/user-attachments/assets/80e29de7-1e28-43b5-bab1-aef8f11690b1" width="100px"> 

本ライブラリには，内閣府総合科学技術・イノベーション会議の下で推進する「戦略的イノベーション創造プログラム(SIP)第３期／スマートモビリティプラットフォームの構築」（研究推進法人：国立研究開発法人新エネルギー・産業技術総合開発機構）(NEDO管理番号：JPNP23023)の成果が含まれています．

## References 参考文献
- 羽佐田紘之, 池谷風馬, 鳥海梓, 本間裕大, and 大口敬. 2025. “歩車ネットワークの構築と「安心とこてくゾーン」の設定手法理論の検討.” In 第71回土木計画学研究発表会・講演集.

---
## Installation インストール
```bash
pip install hosha-network
```

## Usage 使い方

```python
from hosha_network import develop_hosha_network

develop_hosha_network(link_df, node_df, output_dir="./output")
```

## Function 関数

Function `develop_hosha_network()` generates a layered pedestrian-vehicle network from macro-level road data in [GMNS format](https://github.com/zephyr-data-specs/GMNS).

関数`develop_hosha_network()` は，[GMNS フォーマット](https://github.com/zephyr-data-specs/GMNS)のマクロ道路データから歩車分離ネットワークを構築します. 

**Parameters 引数:**

English
- `link_df`: DataFrame with columns: `link_id`, `from_node_id`, `to_node_id`, `length`  (follows GMNS format)
- `node_df`: DataFrame with columns: `node_id`, `x_coord`, `y_coord`  (follows GMNS format with EPSG:4326)
- `output_dir`: Output directory for saving results.

Other optional keyword arguments can be used for fine-tuning the construction process.

日本語
- `link_df`: `link_id`, `from_node_id`, `to_node_id`, `length` を含むデータフレーム (GMNS フォーマットに準拠). 
- `node_df`: `node_id`, `x_coord`, `y_coord`を含むデータフレーム (GMNS フォーマットに準拠、EPSG:4326のみ対応). 
- `output_dir`: 結果を保存する出力先ディレクトリ. 

他のオプションのキーワード引数を使用して，構築方法を調整することも可能です. 
