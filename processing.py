# processing.py
# -*- coding: utf-8 -*-
"""
processing.py
-------------
本ファイルは、オリジナルデータの前処理、ネットワーク拡張（リンク中心計算＋新規ノード生成）、
ターンリンク生成、リンク統合、networkx を用いたノード縮約および最終ネットワーク抽出、
さらに「表示用ノードの座標補正」と「最終データのエクスポート」を実装します。

※ RD クラスおよび average_angle 関数は utils.py に定義しています。
"""

import os
import pandas as pd
import numpy as np
import networkx as nx
from shapely.geometry import LineString, Point
from utils import RD, average_angle

def calc_macro_link(df, s_col="s", t_col="t"):
    """
    指定されたDataFrameに対して、2つのカラム（s_col, t_col）の値を用いてmacro_linkを生成する。
    両者の値が同一の場合は "_" + 値、異なる場合は、小さい方と大きい方を "_" で連結した文字列を返す。
    NaN等がある場合は空文字列を返す。
    
    Parameters:
      df : DataFrame
          入力データ
      s_col : str, optional
          始点となるカラム名（デフォルトは "s"）
      t_col : str, optional
          終点となるカラム名（デフォルトは "t"）
    
    Returns:
      df : DataFrame
          macro_link カラムを追加したDataFrame
    """
    def _calc(row):
        try:
            s_val = int(row[s_col])
            t_val = int(row[t_col])
        except Exception:
            return ""
        if s_val == t_val:
            return "-1"
        else:
            return f"{min(s_val, t_val)}_{max(s_val, t_val)}"
    df["macro_link"] = df.apply(lambda x:_calc(x), axis=1)
    return df

def reorder_macro(macro):
    """
    macro_link の値（例："12345_67890"）を文字列に変換し、"_" で分割したうえで、
    数値として比較して小さい順に並べ替えた文字列を返す。
    分割できない場合や数値変換に失敗した場合は、空文字列を返す。
    """
    try:
        macro_str = str(macro)  # まず文字列に変換する
        parts = macro_str.split("_")
        if len(parts) != 2:
            return ""
        a = int(parts[0])
        b = int(parts[1])
        return f"{min(a, b)}_{max(a, b)}"
    except Exception:
        return ""
    
def access_from_drm(row):
    restriction_mapping = {
        1: "both_B",
        2: "pedestrian",
        3: "pedestrian",
        4: "both_FT",
        5: "both_TF",
        6: "both_FT",
        7: "both_TF",
        8: "both_B",
        0: "both_B"
    }

    # 道路種別コードによる高速道路判定
    vehicle_only_types = {1, 2}  # 高速自動車国道、都市高速

    try:
        restriction_code = int(row["DrmLimitCode"])
    except:
        restriction_code = 0
    try:
        road_type_code = int(row["DrmRoadKindCode"])
    except:
        road_type_code = 0

    # 基本access（歩行者 or 車両 or 両用）
    access = restriction_mapping.get(restriction_code, "both_B")

    # 高速道路は常に vehicle のみ（pedestrian も削除）
    if road_type_code in vehicle_only_types:
        if access == "pedestrian":
            return "none"
        if access.startswith("both"):
            return "vehicle_"+access[5:]
        return "vehicle_B"

    return access

def access_from_undi_gmns(row):
    """
    GMNSフォーマットの行から access 列を作成。
    - directed == False（無向）の場合のみ計算。
    - ped_facility が 'none' → 車両専用
      ped_facility が 'offstreet_path' → 歩行者専用
      その他 → 歩行者・車両共用
    - facility_type に "highway", "motorway" を含む → 車両専用
    - suffix は dir_flag によって決定。。
    """

    # 1) 無向でないなら何もしない
    if row.get("directed", True):
        base = "none"

    # 2) 属性の正規化
    ped = str(row.get("ped_facility", "")).lower()
    facility_type = str(row.get("facility_type", "")).lower()
    try:
        df = int(row.get("dir_flag", 0))
    except:
        df = 0

    # 3) base の決定
    if ped == "none":
        base = "vehicle"
    elif ped == "offstreet_path":
        base = "pedestrian"
    else:
        base = "both"

    # 4) facility_typeによる上書き（highway は車両専用）
    if facility_type in ["highway", "expressway", "motorway"]:
        base = "vehicle"

    # 5) suffix の決定
    if df == 1:
        suffix = "FT"
    elif df == -1:
        suffix = "TF"
    else:
        suffix = "B"

    # 6) access 文字列の生成
    if base == "none":
        return "none"
    if base == "pedestrian":
        return "pedestrian"
    return f"{base}_{suffix}"

# === オリジナルデータ前処理 ===
def preprocess_original_links(ori_link):
    ori_link["id"] = ori_link["link_id"].astype("int64")
    ori_link["s"] = (ori_link["from_node_id"]).astype("int64")
    ori_link["t"] = (ori_link["to_node_id"]).astype("int64")
    duplicate_mask = ori_link["id"].duplicated(keep=False)
    if duplicate_mask.any():
        ori_link.loc[duplicate_mask, "id"] = ori_link.loc[duplicate_mask, "id"]-min(ori_link["id"]) + max(ori_link["id"])
    ori_link["weight"] = ori_link["length"].astype(float).fillna(0)
    ori_link["dummy"] = 0
    ori_link.index = ori_link["id"]
    
    ori_link["access"] = ori_link.apply(lambda x:access_from_undi_gmns(x),axis=1)
    ori_link = calc_macro_link(ori_link, s_col="s", t_col="t")
    return ori_link

def preprocess_original_nodes(ori_node, processed_link):
    ori_node["id"] = ori_node["node_id"].astype("int64")
    ori_node = ori_node.drop_duplicates(subset=["id"])
    valid_ids = set(processed_link["s"].values) | set(processed_link["t"].values)
    ori_node = ori_node[ori_node["id"].isin(valid_ids)]
    ori_node["x"] = ori_node["geometry"].x
    ori_node["y"] = ori_node["geometry"].y
    ori_node["x_display"] = ori_node["geometry"].x
    ori_node["y_display"] = ori_node["geometry"].y
    ori_node["dummy"] = 0
    ori_node["original_id"] = ori_node["id"]
    ori_node["intersection"]=ori_node["id"]
    ori_node.index = ori_node["id"]
    return ori_node

def branch_network_types(processed_link, processed_node):
    """
    入力された processed_link DataFrame（access 属性を含む）と processed_node を
    もとに、歩行者ネットワーク用と車両ネットワーク用に分岐する関数。
    
    具体的には、
      - 歩行者ネットワークには、access が "pedestrian" または "both_～" のリンクを採用。
      - 車両ネットワークには、access が "vehicle_～" または "both_～" のリンクを採用。
    なお、"none" やその他不適格なものは含まれません。
    
    Returns:
      walk_link, walk_node, veh_link, veh_node : 各ネットワーク用の DataFrame
    """
    # 歩行者ネットワーク: access が "pedestrian" もしくは "both" で始まるもの
    walk_mask = (processed_link["access"] == "pedestrian") | \
                (processed_link["access"].str.startswith("both"))
    walk_link = processed_link[walk_mask].copy()

    # 車両ネットワーク: access が "vehicle" で始まるものまたは "both" で始まるもの
    veh_mask = processed_link["access"].str.startswith("vehicle") | \
               (processed_link["access"].str.startswith("both"))
    veh_link = processed_link[veh_mask].copy()

    # 現状、ノードはリンク分割後の参照に利用するので、共通の processed_node をそのまま用いる
    walk_node = processed_node.copy()
    veh_node  = processed_node.copy()

    return walk_link, walk_node, veh_link, veh_node

# === 共通処理：リンク中心座標計算 ===
def compute_link_centers(net_link, net_node):
    """
    各リンクについて、始点と終点の表示座標から中心座標 (center_x, center_y) を計算して返す。
    """
    net_link = net_link.copy()
    net_link["center_x"] = net_link.apply(
        lambda row: (net_node.loc[row["s"], "x_display"] + net_node.loc[row["t"], "x_display"]) / 2,
        axis=1
    )
    net_link["center_y"] = net_link.apply(
        lambda row: (net_node.loc[row["s"], "y_display"] + net_node.loc[row["t"], "y_display"]) / 2,
        axis=1
    )
    return net_link

# === 共通処理：新規ノード生成 ===
def generate_inout_nodes(attribute, nodes_df, link_df, offset_angle=10, scale=1, extra_filter_func=None, new_node_start=0):
    """
    指定された属性（例："intersection"）に基づいて新規 in/out ノードを生成する関数。
    本改修では、各接続リンクの access 属性と、リンク端点（s/t）が base node と一致するかで、
    生成するノードタイプ（in, out）を条件分岐する。
    
    Returns:
      (new_nodes, next_index)
    """
    new_nodes = []
    new_node_index = new_node_start
    unique_vals = nodes_df[attribute].unique()
    for attr_val in unique_vals:
        if attr_val == -1:
            continue
        base_nodes = nodes_df[nodes_df[attribute] == attr_val]
        if base_nodes.empty:
            continue
        base_node = base_nodes.iloc[0]
        base_id = base_node["id"]
        origin_x, origin_y = base_node["x"], base_node["y"]
        RD.set_origin(origin_x, origin_y)
        # base_id に接続しているリンクを抽出
        cond = (link_df["s"] == base_id) | (link_df["t"] == base_id)
        connected_links = link_df[cond]
        if extra_filter_func is not None:
            connected_links = connected_links[extra_filter_func(connected_links)]
        for _, link_row in connected_links.iterrows():
            # そのリンクの access 属性を取得
            access = link_row.get("access", "both_B")
            # 判定用: base node がリンクのどちら側か
            role = None
            if base_id == link_row["s"]:
                role = 1  # base はリンクのノード1側
            elif base_id == link_row["t"]:
                role = 2    # base はリンクのノード2側
            else:
                continue  # どちらにも属さない場合はスキップ
            
            # RD を用いてリンク中心からの極座標 (r, degree) を取得
            cx = link_row["center_x"]
            cy = link_row["center_y"]
            r, degree = RD.getRD(cx, cy)
            
            # 生成対象ノードの判断
            # デフォルトは、何も条件に該当しなければ両方生成する（従来の挙動）
            create_out = True
            create_in = True
            
            if role == 1:
                # ノード1側：リンクの流れが s -> t
                # "both_FT"・"vehicle_FT"の場合、出る側のみ生成；"both_TF"・"vehicle_TF"の場合は生成しない
                if access in {"both_FT", "vehicle_FT"}:
                    create_in = False
                elif access in {"both_TF", "vehicle_TF"}:
                    create_out = False
                # "both_B" や "pedestrian"の場合は、両方生成（従来通り）
            elif role == 2:
                # ノード2側：リンクの流れが s -> t なら、t は着く側
                if access in {"both_FT", "vehicle_FT"}:
                    create_out = False
                elif access in {"both_TF", "vehicle_TF"}:
                    create_in = False
            
            # ※ 万が一 access の値が未定義なら、両方生成
            # 以下、各生成条件に応じてノードを生成
            if create_out:
                # out ノード: 角度 + offset_angle
                out_x, out_y = RD.getXY(scale, degree + offset_angle)
                new_nodes.append({
                    "id": new_node_index,
                    "x": out_x,
                    "y": out_y,
                    "original_id": base_id,
                    "_original_link_id": link_row["id"],
                    "in_out": "out"
                })
                new_node_index += 1
            if create_in:
                # in ノード: 角度 - offset_angle
                in_x, in_y = RD.getXY(scale, degree - offset_angle)
                new_nodes.append({
                    "id": new_node_index,
                    "x": in_x,
                    "y": in_y,
                    "original_id": base_id,
                    "_original_link_id": link_row["id"],
                    "in_out": "in"
                })
                new_node_index += 1
    return new_nodes, new_node_index


def generate_augmented_nodes(net_link, net_node, offset_angle, scale):
    """
    新規ノード生成のみを行う関数。
    "intersection" 属性を持つノードに対して、RD クラスと generate_inout_nodes を利用し、
    ±offset_angle のオフセットを適用した新規 in/out ノードを生成し、元のノードに連結する。
    """
    if "intersection" not in net_node.columns:
        net_node["intersection"] = -1
    new_nodes, _ = generate_inout_nodes(
        attribute="intersection",
        nodes_df=net_node,
        link_df=net_link,
        offset_angle=offset_angle,
        scale=scale,
        extra_filter_func=None,
        new_node_start=0
    )
    if new_nodes:
        new_nodes_df = pd.DataFrame(new_nodes)
    else:
        new_nodes_df = pd.DataFrame(columns=["id", "x", "y", "original_id", "_original_link_id", "in_out"])
    updated_nodes = new_nodes_df
    return updated_nodes

def generate_normal_links(ori_link, augmented_nodes):
    """
    元の道路リンク（マクロネットワーク）の情報をもとに、
    拡張後の出入口ノード（augmented_nodes）から、通常の有向リンクを生成する。
    出入口ノードは "out" と "in" のみを用いる。
    
    Returns:
        normal_links : DataFrame
    """
    links = []
    ii = 0
    for link_id in ori_link["id"].unique():
        original_s = ori_link.loc[ori_link["id"] == link_id, "s"].values[0]
        original_t = ori_link.loc[ori_link["id"] == link_id, "t"].values[0]

        # 出入口ノードの探索（始点："out" ノードのみ）
        candidates_source = augmented_nodes[
            (augmented_nodes["original_id"] == original_s) &
            (augmented_nodes["_original_link_id"] == link_id) &
            (augmented_nodes["in_out"] == "out")
        ]

        # 出入口ノードの探索（終点："in" ノードのみ）
        candidates_target = augmented_nodes[
            (augmented_nodes["original_id"] == original_t) &
            (augmented_nodes["_original_link_id"] == link_id) &
            (augmented_nodes["in_out"] == "in")
        ]

        if not (candidates_source.empty or candidates_target.empty):
            s_node = candidates_source.iloc[0]["id"]
            t_node = candidates_target.iloc[0]["id"]
            
            links.append({
                "id": ii,
                "s": s_node,
                "t": t_node,
                "original_id": link_id,
                "_original_node_id": None,
                "turn": None
            })
            ii += 1
        
        # 出入口ノードの探索（始点："out" ノードのみ）
        candidates_source = augmented_nodes[
            (augmented_nodes["original_id"] == original_t) &
            (augmented_nodes["_original_link_id"] == link_id) &
            (augmented_nodes["in_out"] == "out")
        ]

        # 出入口ノードの探索（終点："in" ノードのみ）
        candidates_target = augmented_nodes[
            (augmented_nodes["original_id"] == original_s) &
            (augmented_nodes["_original_link_id"] == link_id) &
            (augmented_nodes["in_out"] == "in")
        ]

        if not (candidates_source.empty or candidates_target.empty):
            s_node = candidates_source.iloc[0]["id"]
            t_node = candidates_target.iloc[0]["id"]
            
            links.append({
                "id": ii,
                "s": s_node,
                "t": t_node,
                "original_id": link_id,
                "_original_node_id": None,
                "turn": None
            })
            ii += 1
    return pd.DataFrame(links)

# === ターンリンク生成 ===
def generate_turn_links(nodes_df, ori_nodes_df, threshold_deg=45):
    """
    歩行者ネットワーク用のターンリンク生成関数。
    各交差点（nodes_df の original_id ごと）に対して、各ノード i から
    同じ交差点内で _original_link_id が異なる候補 o との角度差を計算し、
    最小の角度差が閾値に関わらず、常にターンリンク（turn="cross"）を生成する。
    
    中心点は、変更前の元のノードデータ (ori_nodes_df) から取得する。
    """
    link_list = []
    link_index = 0 
    threshold_rad = threshold_deg * np.pi / 180.0 
    for orig_id, group in nodes_df.groupby("original_id"):
        if group.shape[0] <= 2:
            continue
        # ここで、元データから中心点を取得する
        if orig_id in ori_nodes_df["id"].values:
            center = (
                ori_nodes_df.loc[ori_nodes_df["id"] == orig_id, "x"].iloc[0],
                ori_nodes_df.loc[ori_nodes_df["id"] == orig_id, "y"].iloc[0]
            )
        else:
            # 万が一、元データに存在しない場合は、グループ内の先頭の値を利用
            center = (group.iloc[0]["x"], group.iloc[0]["y"])
        for i in group.index:
            node_i = group.loc[i]
            angle_i = np.arctan2(node_i["y"] - center[1], node_i["x"] - center[0])
            best_rad = None
            best_o = None
            for j in group.index:
                if i != j:
                    node_j = group.loc[j]
                    angle_j = np.arctan2(node_j["y"] - center[1], node_j["x"] - center[0])
                    diff = np.arctan2(np.sin(angle_j - angle_i), np.cos(angle_j - angle_i))
                    if diff < 0:
                        diff += 2 * np.pi
                    if best_rad is None or diff < best_rad:
                        best_rad = diff
                        best_o = j
            if best_rad is not None and (best_rad < np.pi-threshold_rad):
                link_list.append({
                    "id": link_index,
                    "s": i,
                    "t": best_o,
                    "original_id": orig_id,
                    "turn": "cross"
                })
                link_index += 1
            elif best_rad is not None and (best_rad >= np.pi-threshold_rad):
                link_list.append({
                    "id": link_index,
                    "s": i,
                    "t": best_o,
                    "original_id": orig_id,
                    "turn": "notcross"
                })
                link_index += 1
    return pd.DataFrame(link_list)


def generate_turn_links_veh(nodes_df, ori_nodes_df):
    """
    車両ネットワーク用のターンリンク生成関数。
    各交差点（nodes_df の original_id ごと）で、in ノードと out ノードの全組み合わせに対して、
    中心からの角度差に基づきターン分類する：
    Returns:
      DataFrame（columns: ["id", "s", "t", "original_id", "turn"]）
    """
    link_list = []
    link_index = 0
    for orig_id, group in nodes_df.groupby("original_id"):
        in_nodes = group[group["in_out"] == "in"]
        out_nodes = group[group["in_out"] == "out"]
        if in_nodes.empty or out_nodes.empty:
            continue
        if orig_id in ori_nodes_df["id"].values:
            center = (
                ori_nodes_df.loc[ori_nodes_df["id"] == orig_id, "x"].iloc[0],
                ori_nodes_df.loc[ori_nodes_df["id"] == orig_id, "y"].iloc[0]
            )
        else:
            center = (group.iloc[0]["x"], group.iloc[0]["y"])
        for i, in_node in in_nodes.iterrows():
            angle_in = np.arctan2(in_node["y"] - center[1], in_node["x"] - center[0])
            for j, out_node in out_nodes.iterrows():
                angle_out = np.arctan2(out_node["y"] - center[1], out_node["x"] - center[0])
                diff = np.arctan2(np.sin(angle_out - angle_in), np.cos(angle_out - angle_in))
                if diff < 0:
                    diff += 2 * np.pi
                if diff < 3*np.pi/4:
                    turn = "right"
                elif diff < 5*np.pi/4:
                    turn = "straight"
                else:
                    turn = "left"
                link_list.append({
                    "id": link_index,
                    "s": i,
                    "t": j,
                    "original_id": orig_id,
                    "turn": turn
                })
                link_index += 1
    return pd.DataFrame(link_list)

def integrate_turn_links(existing_links, turn_links):
    """
    既存リンクとターンリンクを統合して返す。
    """
    merged_links = pd.concat([existing_links, turn_links], ignore_index=True)
    merged_links = merged_links.reset_index(drop=True)
    merged_links["id"]=merged_links.index
    return merged_links

# === networkx を用いたノード縮約および最終ネットワーク抽出 ===
def contract_network_nodes(G, pos, nodes_df, ori_nodes_df):
    """
    networkx のグラフ G と各ノードの座標 pos、及びノード情報 nodes_df を用いて、
    ターン属性が "cross" のリンクを対象にノード縮約を行う。
    縮約後の座標は、対象ノードの original_id（交差点基準）の座標を中心とし、
    各端点との角度の二等分角上に、両端からの距離の平均を半径とした点とする。
    """
    for u, v, data in list(G.edges(data=True)):
        if (data.get("turn", "") != "cross"):
            continue
        if nodes_df.loc[u, "_original_link_id"] == nodes_df.loc[v, "_original_link_id"]:
            continue
        if nodes_df.loc[u, "in_out"] == nodes_df.loc[v, "in_out"]:
            continue
        orig_id = nodes_df.loc[u, "original_id"]
        if orig_id in ori_nodes_df["id"].values:
            center = (ori_nodes_df.loc[orig_id, "x"], ori_nodes_df.loc[orig_id, "y"])
        else:
            center = pos[list(pos.keys())[u]]
        xs, ys = pos[list(pos.keys())[u]]
        xt, yt = pos[list(pos.keys())[v]]
        angle_u = np.arctan2(ys - center[1], xs - center[0])
        angle_v = np.arctan2(yt - center[1], xt - center[0])
        bisector = average_angle(angle_u, angle_v)
        r_u = np.hypot(xs - center[0], ys - center[1])
        r_v = np.hypot(xt - center[0], yt - center[1])
        R = (r_u + r_v) / 2.0
        new_x = center[0] + R * np.cos(bisector)
        new_y = center[1] + R * np.sin(bisector)
        new_coord = (new_x, new_y)
        #print(u,v)
        #print(u in list(G.nodes))
        #print(v in list(G.nodes))
        G = nx.contracted_nodes(G, u, v, self_loops=False)
        pos[u] = new_coord
        #if v in pos:
        #    del pos[v]
    return G, pos

def extract_network_from_graph(G, pos):
    """
    contracted G と pos 辞書から最終的なノード・リンク情報を抽出する。
    
    Returns:
      final_nodes : DataFrame（"id", "x", "y"）
      final_links : DataFrame（"s", "t", "id", "turn"）
    """
    nodes_list = []
    for node, coord in pos.items():
        nodes_list.append({
            "id": node,
            "x": coord[0],
            "y": coord[1]
        })
    final_nodes = pd.DataFrame(nodes_list)
    
    links_list = []
    for u, v, data in G.edges(data=True):
        links_list.append({
            "s": u,
            "t": v,
            "id": data.get("id", None),
            "turn": data.get("turn", "")
        })
    final_links = pd.DataFrame(links_list)
    
    final_nodes =final_nodes[final_nodes["id"].isin(set(final_links["s"].values)|set(final_links["t"].values))]
        
    return final_nodes, final_links

def contract_network_and_extract(updated_nodes, merged_links, ori_node):
    """
    更新済みノードと統合リンクから、networkx によるグラフ構築、ノード縮約、
    および最終ネットワーク抽出を一括して行う。
    ※ 車両ネットワークはターンリンクが "cross" でないため、縮約は歩行者ネットワークのみ適用される想定。
    """
    G = nx.DiGraph()
    pos = {row["id"]: (row["x"], row["y"]) for _, row in updated_nodes.iterrows()}
    for _, row in merged_links.iterrows():
        G.add_edge(row["s"], row["t"], id=row["id"], turn=row.get("turn", ""))
    G, pos = contract_network_nodes(G, pos, updated_nodes, ori_node)
    final_nodes, final_links = extract_network_from_graph(G, pos)
    final_nodes=final_nodes.merge(updated_nodes[["id","original_id","_original_link_id","in_out"]],on="id",how="left")
    final_links=final_links.merge(merged_links[["id","original_id","_original_node_id"]],on="id",how="left")
    return final_nodes, final_links

# === ネットワーク統合処理（車両・歩行者ネットワークの統合） ===
def integrate_vehicle_and_pedestrian_networks(walk_nodes, walk_links, veh_nodes, veh_links):
    """
    車両ネットワークと歩行者ネットワークを統合する関数。
    歩行者ネットワークには layer_id=1、車両ネットワークには layer_id=0 を付与して連結する。
    
    Returns:
      integrated_nodes, integrated_links : DataFrame, DataFrame
    """
    walk_nodes["layer_id"] = 1
    veh_nodes["layer_id"] = 0
    
    integrated_nodes = pd.concat([veh_nodes,walk_nodes], ignore_index=True).reset_index(drop=True)

    walknode_dict={}
    for i in integrated_nodes[integrated_nodes["layer_id"]==1].index:
        walknode_dict[int(integrated_nodes.at[i,"id"])]=i
    integrated_nodes["id"]=integrated_nodes.index
    
    
    walk_links = walk_links.copy()
    veh_links = veh_links.copy()
    walk_links["layer_id"] = 1
    veh_links["layer_id"] = 0
        
    walk_links["s"]=walk_links["s"].apply(lambda x:walknode_dict[x])
    walk_links["t"]=walk_links["t"].apply(lambda x:walknode_dict[x])
    integrated_links = pd.concat([veh_links,walk_links], ignore_index=True).reset_index(drop=True)
    
    return integrated_nodes, integrated_links

# === 表示用ノードの座標補正 ===
def adjust_display_coordinates(nodes_df, ori_nodes_df, scale_factor=10):
    """
    各ノードについて、original_id に対応する基準点を中心とし、
    現在の座標からのずれを scale_factor 倍して補正した表示用ノード座標を生成する。
    
    Parameters:
      nodes_df : DataFrame
          ノードデータ（"id", "x", "y", "original_id" を含む）。
      scale_factor : float, optional
          補正倍率（デフォルトは 10）
    
    Returns:
      display_nodes : DataFrame
          補正後のノード座標データ（"id", "x", "y"）
    """
    display_nodes = nodes_df.copy()
    for i, row in display_nodes.iterrows():
        orig_id = row.get("original_id", row["id"])
        center_row = ori_nodes_df[ori_nodes_df["id"] == orig_id]
        if not center_row.empty:
            center_x = center_row.iloc[0]["x"]
            center_y = center_row.iloc[0]["y"]
        else:
            center_x, center_y = row["x"], row["y"]
        new_x = (row["x"] - center_x) * scale_factor + center_x
        new_y = (row["y"] - center_y) * scale_factor + center_y
        display_nodes.at[i, "x"] = new_x
        display_nodes.at[i, "y"] = new_y
    return display_nodes

def finalize_network(final_nodes, final_links, ori_links, ori_nodes):
    """

    """
    final_nodes.rename(columns={"original_id": "macro_node"}, inplace=True)
    final_nodes.rename(columns={"_original_link_id": "macro_link_id"}, inplace=True)
        
    # macro_node_id と macro_link の算出 ---
    # final_nodes は "id" と "original_id" を含む
    nodes_info = final_nodes[["id", "macro_node"]].rename(columns={"id": "node_id", "macro_node": "macro_id"})
    # ソースノードの情報を結合
    links_merged = final_links.merge(nodes_info, left_on="s", right_on="node_id", how="left").rename(columns={"macro_id": "macro_node_id_s"})
    # ターゲットノードの情報を結合
    links_merged = links_merged.merge(nodes_info, left_on="t", right_on="node_id", how="left").rename(columns={"macro_id": "macro_node_id_t"})
    
    links_merged = calc_macro_link(links_merged)
    
    # macro_node_id の算出: 両端の macro_id が同一の場合はその値、異なる場合は -1
    links_merged["macro_node_id"] = links_merged.apply(
        lambda row: row["macro_node_id_s"] if row["macro_node_id_s"] == row["macro_node_id_t"] else -1, axis=1
    )
    
    # 重みの補完: 元のリンクデータからmacro_linkをキーにしてweight列を結合する
    links_merged = calc_macro_link(links_merged, s_col="macro_node_id_s", t_col="macro_node_id_t")

    links_merged = links_merged.merge(ori_links[['macro_link', 'weight']], on='macro_link', how='left')
    
    # bidirectionalpair_id の算出
    def assign_bidirectional(row):
        # macro_linkは、例："12345_67890"
        macro = row["macro_link"]
        if macro == "" or pd.isnull(macro):
            return -1
        try:
            a_str, b_str = macro.split("_")
            a = int(a_str)
            b = int(b_str)
        except Exception:
            return -1
        # 取得するマクロノードの座標は、ori_nodes_dfから取得する
        # ori_nodes_dfは、元のノードデータで、"id", "x", "y" を持つ前提とする
        A = ori_nodes[ori_nodes["id"] == a]
        B = ori_nodes[ori_nodes["id"] == b]
        if A.empty or B.empty:
            return macro  # 取得できなければそのまま返す
        Ax, Ay = A.iloc[0]["x"], A.iloc[0]["y"]
        Bx, By = B.iloc[0]["x"], B.iloc[0]["y"]
        # 現在のリンクの中点をfinal_nodesから取得する
        # ここでは、リンクのソースとターゲットの座標から中点を計算する
        nodes_coords = final_nodes.set_index("id")[["x", "y"]]
        try:
            s_coords = nodes_coords.loc[row["s"]]
            t_coords = nodes_coords.loc[row["t"]]
        except Exception:
            return macro
        mid_x = (s_coords["x"] + t_coords["x"]) / 2.0
        mid_y = (s_coords["y"] + t_coords["y"]) / 2.0
        # 直線ABの方程式を用いて、点(mid_x, mid_y)の符号付き距離を算出する
        # 直線ABの一般形: Ax + By + C = 0
        # ここでは、A_coef = By - Ay, B_coef = Ax - Bx, C = Bx*Ay - Ax*By
        A_coef = By - Ay
        B_coef = Ax - Bx
        C = Bx*Ay - Ax*By
        # 符号付き距離
        signed_distance = (A_coef * mid_x + B_coef * mid_y + C)
        # ここでは、正ならside 0、負ならside 1（どちらでも異なる番号になればよい）
        side = "0" if signed_distance >= 0 else "1"
        return macro + "_" + side
    # 歩行者レイヤのリンクのbidirectionalpair_idを再設定
    ped_mask = links_merged["layer_id"] == 1
    links_merged.loc[ped_mask, "bidirectionalpair_id"] = links_merged.loc[ped_mask, :].apply(assign_bidirectional, axis=1)

    # そのほか、車両レイヤは従来通りの処理（例：reorder_macro関数を用いる）
    vehicle_mask = links_merged["layer_id"] != 1
    links_merged.loc[vehicle_mask, "bidirectionalpair_id"] = links_merged.loc[vehicle_mask, "macro_link"].apply(
        lambda x: reorder_macro(x) if x != "" else -1
    )
    
    return final_nodes,links_merged
    
def birdirectionzie_ped_links(final_nodes, final_links):
    veh_mask = final_links["layer_id"] == 0
    ped_mask = final_links["layer_id"] == 1
    __veh_links = final_links.loc[veh_mask, :]
    __ped_links = final_links.loc[ped_mask, :]
    
    _ped_links = __ped_links.copy()
    _ped_links["s"]=__ped_links["t"]
    _ped_links["t"]=__ped_links["s"]
    _ped_links.loc[_ped_links["bidirectionalpair_id"]!=-1,"bidirectionalpair_id"]=_ped_links.loc[_ped_links["bidirectionalpair_id"]!=-1,"bidirectionalpair_id"]+".2"
    
    __ped_links.loc[__ped_links["bidirectionalpair_id"]!=-1,"bidirectionalpair_id"]=__ped_links.loc[__ped_links["bidirectionalpair_id"]!=-1,"bidirectionalpair_id"]+".1"
    
    _final_links = pd.concat([__veh_links,__ped_links,_ped_links])
    _final_links["id"] = _final_links.reset_index().index
    return final_nodes,_final_links
    

def split_links(final_nodes, final_links):
    """
    最終ネットワークのリンクデータについて、各リンクを幾何学的中点で分割し、2本のリンクに分割する。
    ただし、ターンリンク（turn列に値があるリンク）は分割しない。
    分割に伴い、中間ノードを新たに生成し、そのノードの "split" 列に 1 を設定する。
    また、新たに生成された中間ノードの _original_link_id には、元リンクの macro_link 情報を設定する。
    生成される2本のリンクは、元のリンクの情報（macro_link, turn, layer_id 等）を引き継ぎ、
    重み（weight）は元の値の半分となり、bidirectionalpair_id は元の値に ".1" と ".2" のサフィックスを付与して設定される。
    
    Returns:
      new_final_links : DataFrame
          分割後のリンクデータ（ターンリンクはそのまま）
      new_final_nodes : DataFrame
          既存のノードに加え、生成された中間ノードを含むノードデータ
    """
    new_links = []
    new_nodes_list = []
    # リンクIDを新たに連番で再割り当てする
    new_link_id = 0
    # 新規ノードIDは、既存の最大ノードID+1から開始
    max_node_id = final_nodes["id"].max() if not final_nodes.empty else 0
    new_node_id = max_node_id + 1
    # 既存のノード情報を辞書化
    nodes_dict = final_nodes.set_index("id").to_dict(orient="index")
    
    for idx, row in final_links.iterrows():
        # ターンリンクは分割せずそのまま追加
        if pd.notnull(row.get("turn", "")) and row["turn"] != "":
            new_link = row.copy()
            new_link["id"] = new_link_id
            new_link_id += 1
            new_links.append(new_link)
            continue

        s = row["s"]
        t = row["t"]
        orig_weight = row.get("weight", 1)
        macro_link = row.get("macro_link", "")
        turn = row.get("turn", None)
        layer_id = row.get("layer_id", "")
        bidir = row.get("bidirectionalpair_id", "")
        
        # 取得する元ノードの座標（final_nodesの値）
        if s not in nodes_dict or t not in nodes_dict:
            continue
        s_coord = nodes_dict[s]
        t_coord = nodes_dict[t]
        s_x, s_y = s_coord["x"], s_coord["y"]
        t_x, t_y = t_coord["x"], t_coord["y"]
        # 中点を計算
        mid_x = (s_x + t_x) / 2.0
        mid_y = (s_y + t_y) / 2.0
        
        # 新たな中間ノードを生成
        new_node = {
            "id": new_node_id,
            "x": mid_x,
            "y": mid_y,
            "macro_node": -1,  # 中間ノードには元のIDは存在しない
            "layer_id": layer_id,
            "macro_link_id": macro_link,  # 対応するmacro_link情報を設定
            "split": 1  # 分割により生成されたノードは1
        }
        new_nodes_list.append(new_node)
        mid_id = new_node_id
        new_node_id += 1
        
        # 生成するリンクの重みは元の半分
        half_weight = orig_weight / 2.0
        
        # リンク1: ソース → 中間ノード
        link1 = row.copy()
        link1["id"] = new_link_id
        new_link_id += 1
        link1["s"] = s
        link1["t"] = mid_id
        link1["weight"] = half_weight
        link1["macro_link"] = macro_link
        link1["turn"] = turn
        link1["layer_id"] = layer_id
        link1["bidirectionalpair_id"] = str(bidir) + ".1" if bidir != "" else ""
        link1["split"] = 1
        
        # リンク2: 中間ノード → ターゲット
        link2 = row.copy()
        link2["id"] = new_link_id
        new_link_id += 1
        link2["s"] = mid_id
        link2["t"] = t
        link2["weight"] = half_weight
        link2["macro_link"] = macro_link
        link2["turn"] = turn
        link2["layer_id"] = layer_id
        link2["bidirectionalpair_id"] = str(bidir) + ".2" if bidir != "" else ""
        link2["split"] = 1
        
        new_links.append(link1)
        new_links.append(link2)
    
    new_final_links = pd.DataFrame(new_links)
    new_final_nodes = pd.concat([final_nodes, pd.DataFrame(new_nodes_list)], ignore_index=True)
    
    return new_final_nodes, new_final_links



# === 最終データのエクスポート ===
def export_final_network(final_nodes, final_links, config, suffix="raw"):
    """
    最終ネットワークのノード・リンクデータをエクスポートする。
    ノードは CSV、リンクはジオメトリ（LineString）を付与した GeoJSON として出力する。
    
    Parameters:
      final_nodes : DataFrame
          ノードデータ（"id", "x", "y"）
      final_links : DataFrame
          リンクデータ（"s", "t", "id", "turn"）
      output_dir : str
          出力ディレクトリ
      suffix : str, optional
          出力ファイル名に付加するサフィックス（例："raw" または "display"）
    """
    import geopandas as gpd
    
    output_dir = config["output"]["dir"]
    input_crs = config["crs"]["input_crs"]
    export_crs = config["crs"]["export_crs"]
    
    os.makedirs(output_dir, exist_ok=True)
    nodes_csv_path = os.path.join(output_dir, f"final_nodes_{suffix}.csv")
    gdf_nodes = gpd.GeoDataFrame(final_nodes.copy(),
                             geometry=final_nodes.apply(lambda row: Point(row["x"], row["y"]), axis=1),
                             crs=input_crs)
    gdf_nodes = gdf_nodes.to_crs(export_crs)
    
    gdf_nodes.loc[gdf_nodes["layer_id"] == 1, "in_out"] = ""
    
    nodes_csv_path = os.path.join(output_dir, f"final_nodes_{suffix}.csv")
    gdf_nodes["x"]=gdf_nodes.geometry.x
    gdf_nodes["y"]=gdf_nodes.geometry.y
    gdf_nodes.drop(columns="geometry").to_csv(nodes_csv_path, index=False)
    print(f"Final nodes exported to {nodes_csv_path}")

    nodes_coords = final_nodes.set_index("id")[["x", "y"]]
    geometries = []
    for idx, row in final_links.iterrows():
        try:
            s_coords = nodes_coords.loc[row["s"]]
            t_coords = nodes_coords.loc[row["t"]]
            geom = LineString([[s_coords["x"], s_coords["y"]], [t_coords["x"], t_coords["y"]]])
        except Exception as e:
            geom = None
        geometries.append(geom)
    
    # 最終リンクデータに必要なカラムを補完
    for col, default in [('weight', 1), ('macro_node_id', -1), ('macro_link', ''), ('layer_id', ''), ('bidirectionalpair_id', -1), ('split', 0)]:
        if col not in final_links.columns:
            final_links[col] = default
    # 必要なカラムの順番に並び替え（lengthは不要）
    final_links = final_links[['id', 's', 't', 'weight', 'layer_id','macro_link', 'macro_node_id',  'bidirectionalpair_id', 'turn', 'split']]
    
    final_links["geometry"] = geometries
    gdf_links = gpd.GeoDataFrame(final_links, geometry="geometry", crs=input_crs)
    gdf_links = gdf_links.to_crs(export_crs)
    links_geojson_path = os.path.join(output_dir, f"final_links_{suffix}.geojson")
    gdf_links.to_file(links_geojson_path, driver="GeoJSON")
    print(f"Final links exported to {links_geojson_path}")

# === ネットワーク全体処理パイプライン（歩行者） ===
def process_pedestrian_network(walk_link, walk_node):
    """
    歩行者ネットワークの全体処理パイプライン
      1. compute_link_centers によりリンク中心座標を計算
      2. generate_augmented_nodes により新規ノードを生成（offset_angle=10, scale=1）
      3. generate_turn_links によりターンリンク（turn="cross"）を生成
      4. integrate_turn_links により既存リンクとターンリンクを統合
      5. contract_network_and_extract により networkx でノード縮約・最終ネットワーク抽出
    Returns:
      final_nodes, final_links : DataFrame（最終的な歩行者ネットワーク）
    """
    #print(len(walk_link))
    updated_links = compute_link_centers(walk_link, walk_node)
    #print(len(updated_links))
    updated_nodes = generate_augmented_nodes(updated_links, walk_node, offset_angle=10, scale=1.0)
    turn_links = generate_turn_links(updated_nodes, walk_node)
    #print(len(turn_links))
    normal_links = generate_normal_links(walk_link, updated_nodes)
    merged_links = integrate_turn_links(normal_links, turn_links)
    #print(len(merged_links))
    final_nodes, final_links = contract_network_and_extract(updated_nodes, merged_links, walk_node)
    #print(len(final_links))
    return final_nodes, final_links

# === ネットワーク全体処理パイプライン（車両） ===
def process_vehicle_network(veh_link, veh_node):
    """
    車両ネットワークの全体処理パイプライン
      1. compute_link_centers によりリンク中心座標を計算
      2. generate_augmented_nodes により新規ノードを生成（offset_angle=10, scale=0.5）
      3. generate_turn_links_veh によりターンリンク（"left", "right", "straight"）を生成
      4. integrate_turn_links により既存リンクとターンリンクを統合
      ※ 車両ネットワークは縮約処理は行わない前提。
    Returns:
      updated_veh_nodes, merged_veh_links : DataFrame（処理後の車両ネットワーク）
    """
    updated_links = compute_link_centers(veh_link, veh_node)
    updated_nodes = generate_augmented_nodes(updated_links, veh_node, offset_angle=10, scale=0.3)
    turn_links = generate_turn_links_veh(updated_nodes, veh_node)
    normal_links = generate_normal_links(veh_link, updated_nodes)
    merged_links = integrate_turn_links(normal_links, turn_links)
    return updated_nodes, merged_links
