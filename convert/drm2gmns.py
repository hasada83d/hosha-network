# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 09:30:44 2025

@author: honma-lab
"""

import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
import configparser

def get_dir_flg(regulation_code):
    """
    規制コードに基づいて、dir_flgを判定する関数。

    :param regulation_code: 規制コード (1から8の整数)
    :return: dir_flg（1, -1, 0のいずれか）
    """
    if regulation_code == 1:  # 規制無し
        return 0
    elif regulation_code == 2:  # 通行禁止（条件無）
        return None
    elif regulation_code == 3:  # 通行禁止（条件付）
        return 0
    elif regulation_code == 4:  # 一方方向（正方向、条件無）
        return 1
    elif regulation_code == 5:  # 一方方向（逆方向、条件無）
        return -1
    elif regulation_code == 6:  # 一方方向（正方向、条件付）
        return 1
    elif regulation_code == 7:  # 一方方向（逆方向、条件付）
        return -1
    elif regulation_code == 8:  # 一方方向（正逆切換え有り）
        return 0
    elif regulation_code == 0:  # 未調査
        return 0  # または、適切なエラー処理を追加
    else:
        raise ValueError("無効な規制コードが指定されました。")

def classify_facility_type(code):
    """
    規制コードに基づいて、facility_typeをexpressway, arterial, collector, localのいずれかに分類する関数。

    :param code: 道路種別コード (1から9の整数)
    :return: facility_type（expressway, arterial, collector, localのいずれか）
    """
    if code == 1:  # 高速自動車国道
        return 'expressway'
    elif code == 2:  # 都市高速道路（含指定市都市高速道路）
        return 'expressway'
    elif code == 3:  # 一般国道
        return 'arterial'
    elif code == 4:  # 主要地方道（都道府県道）
        return 'arterial'
    elif code == 5:  # 主要地方道（指定市道）
        return 'arterial'
    elif code == 6:  # 一般都道府県道
        return 'collector'
    elif code == 7:  # 指定市の一般市道
        return 'collector'
    elif code == 9:  # その他の道路
        return 'local'
    elif code == 0:  # 未調査
        return 'local'  # 未調査の場合
    else:
        raise ValueError("無効な道路種別コードが指定されました。")


def get_jurisdiction(code):
    """
    This function determines the jurisdiction based on the provided code.

    :param code: Jurisdiction code (an integer from 0 to 8)
    :return: Jurisdiction name
    """
    if code == 1:  # East Japan Expressway Company, Central Japan Expressway Company, West Japan Expressway Company
        return 'NEXCO'
    elif code == 2:  # Metropolitan Expressway Company, Hanshin Expressway Company, Honshu-Shikoku Highway Company
        return 'Metropolitan or Hanshin or Honshu-Shikoku'
    elif code == 3:  # Road Public Corporation
        return 'Public Corporation'
    elif code == 4:  # National Government
        return 'National'
    elif code == 5:  # Prefectures
        return 'Prefecture'
    elif code == 6:  # Designated Cities
        return 'Designated City'
    elif code == 7:  # Other Municipalities (including Tokyo 23 Wards)
        return 'Other Municipality'
    elif code == 8:  # Other Administrators
        return 'Others'
    elif code == 0:  # Undetermined
        return 'Undetermined'
    else:
        raise ValueError("Invalid jurisdiction code provided.")

def convert_road_width_code(code):
    """
    Converts the road width category code (0 to 4) into its corresponding description.

    :param code: Road width category code (an integer from 0 to 4)
    :return: Corresponding road width description
    """
    if code == 0:
        return 'Undetermined'
    elif code == 1:
        return '>=13.0m'
    elif code == 2:
        return '>=5.5m&<13.0m'
    elif code == 3:
        return '>=3.0m&<5.5m'
    elif code == 4:
        return '<3.0m'
    else:
        raise ValueError("Invalid road width code provided.")

def convert_node_type(code):
    """
    Converts the node type code into its corresponding description.

    :param code: Node type code (1 to 7)
    :return: Corresponding node type description
    """
    if code == 1:
        return 'Intersection'
    elif code == 2:
        return 'DeadEnd'
    elif code == 3:
        return 'Dummy'
    elif code == 4:
        return 'BlockChangeIntersection'
    elif code == 5:
        return 'AttributeChange'
    elif code == 6:
        return 'NecessaryTrafficControl'
    elif code == 7:
        return 'CensusEnd'
    else:
        raise ValueError("Invalid node type code provided.")

def merge_links_with_virtual_nodes(gmns_links, gmns_nodes):
    """
    疑似的に生成されたノード（DrmNextNodeIDおよびDrmNextMeshCodeを持つノード）を挟むリンクを統合し、 
    統合されたリンクの情報を引き継ぎ、元のノードを削除する関数。

    :param gmns_links: リンク情報のDataFrame（少なくともfrom_node_id, to_node_id, DrmNextNodeIDを含む）
    :param gmns_nodes: ノード情報のDataFrame（少なくともDrmNextNodeIDおよびDrmNextMeshCodeを含む）
    :return: 統合されたリンクとノードのDataFrame
    """
    # 1. DrmNextNodeIDとDrmNextMeshCodeを持つ仮想ノードのマッピングを作成
    virtual_nodes = gmns_nodes[gmns_nodes['nextnode_id'].notnull() & (gmns_nodes['nextnode_id']!="00000") & gmns_nodes['nextmesh'].notnull() & (gmns_nodes['nextmesh']!="000000")]
    virtual_node_map = virtual_nodes.set_index('node_id')[["nextmesh", "nextnode_id"]].apply(
        lambda x:str(x["nextmesh"]) +str(x["nextnode_id"]).zfill(5), axis=1).to_dict()

    # 2. 統合後のリンクを格納するリスト
    merged_links = []

    # 3. 統合されるリンクの情報を新しくまとめる
    for _, link in gmns_links.iterrows():
        from_node = link['from_node_id']
        to_node = link['to_node_id']

        # 4. 仮想ノードを通るリンクを統合
        if from_node in virtual_node_map:
            # 仮想ノードの次のノードを新しいリンクのfrom_node_idに設定
            new_link = link.copy()
            if not gmns_links[(gmns_links['from_node_id']==virtual_node_map[from_node])].empty:
                new_link['from_node_id'] = gmns_links.loc[(gmns_links['from_node_id']==virtual_node_map[from_node]),"to_node_id"].values[0]
                new_link["geometry"] = unary_union([new_link["geometry"], gmns_links.loc[(gmns_links['from_node_id']==virtual_node_map[from_node]),"geometry"].values[0]])
            elif not gmns_links[(gmns_links['to_node_id']==virtual_node_map[from_node])].empty:
                new_link['from_node_id'] = gmns_links.loc[(gmns_links['to_node_id']==virtual_node_map[from_node]),"from_node_id"].values[0]
                new_link["geometry"] = unary_union([new_link["geometry"], gmns_links.loc[(gmns_links['to_node_id']==virtual_node_map[from_node]),"geometry"].values[0]])
            # 統合されたリンクに関連するその他の列も引き継ぐ
            merged_links.append(new_link)
        elif to_node in virtual_node_map:
            # 仮想ノードの次のノードを新しいリンクのto_node_idに設定
            #new_link = link.copy()
            #if not gmns_links[(gmns_links['from_node_id']==virtual_node_map[to_node])].empty:
            #    new_link['to_node_id'] = gmns_links.loc[(gmns_links['from_node_id']==virtual_node_map[to_node]),"to_node_id"].values[0]
            #    new_link["geometry"] = unary_union([new_link["geometry"], gmns_links.loc[(gmns_links['from_node_id']==virtual_node_map[to_node]),"geometry"].values[0]])
            #elif not gmns_links[(gmns_links['to_node_id']==virtual_node_map[to_node])].empty:
            #    new_link['to_node_id'] = gmns_links.loc[(gmns_links['to_node_id']==virtual_node_map[to_node]),"from_node_id"].values[0]
            #    new_link["geometry"] = unary_union([new_link["geometry"], gmns_links.loc[(gmns_links['to_node_id']==virtual_node_map[to_node]),"geometry"].values[0]])
            # 統合されたリンクに関連するその他の列も引き継ぐ
            #merged_links.append(new_link)
            to_node=to_node
        else:
            # 仮想ノードを通らないリンクはそのまま残す
            merged_links.append(link)

    # 5. 新しいリンクのDataFrameを作成
    merged_links_df = gpd.GeoDataFrame(merged_links)

    # 6. 重複リンクの削除（from_node_idとto_node_idが同じリンクは削除）
    merged_links_df = merged_links_df.drop_duplicates(subset=['geometry'])

    # 7. ノードを削除する（仮想ノードを削除）
    nodes_to_delete = virtual_nodes['node_id'].tolist()
    remaining_nodes = gmns_nodes[~gmns_nodes['node_id'].isin(nodes_to_delete)]

    # 8. 統合されたリンクと残りのノードを返す
    return merged_links_df, remaining_nodes

# config.iniファイルの読み込み
config = configparser.ConfigParser()
config.read('drm2gmns.ini')

# DRMデータの読み込み (iniファイルで指定されたパスを使用)
drm_links = gpd.read_file(config['paths']['input_links'])  # 入力リンクデータのファイルパス
drm_nodes = gpd.read_file(config['paths']['input_nodes'])  # 入力ノードデータのファイルパス

# GMNSリンクデータの変換
gmns_links = gpd.GeoDataFrame({
    'link_id': drm_links[config['drm_links']['link_id']].astype("int64").astype(str),
    'from_node_id': (drm_links[config['drm_links']['mesh']].astype(str) +
                     drm_links[config['drm_links']['from_node_id']].astype(str).str.zfill(5)).astype("int64").astype(str),
    'to_node_id': (drm_links[config['drm_links']['mesh']].astype(str) +
                     drm_links[config['drm_links']['to_node_id']].astype(str).str.zfill(5)).astype("int64").astype(str),
    'directed': False,
    'geometry': drm_links[config['drm_links']['geometry']],
    'dir_flag': drm_links[config['drm_links']['direction']].apply(lambda x: get_dir_flg(x)),
    'length': drm_links[config['drm_links']['length']],
    'facility_type': drm_links[config['drm_links']['facility_type']].apply(lambda x: classify_facility_type(x)),
    'lanes': drm_links[config['drm_links']['lanes']],
    'ped_facility': drm_links[config['drm_links']['facility_type']].apply(lambda x: 'offstreet_path' if x==2 else ""),
    'jurisdiction': drm_links[config['drm_links']['jurisdiction']].apply(lambda x:get_jurisdiction(x)),
    'row_width': drm_links[config['drm_links']['row_width']].apply(lambda x:convert_road_width_code(x))
})

# GMNSノードデータの変換
gmns_nodes = gpd.GeoDataFrame({
    'node_id': drm_nodes[config['drm_nodes']['node_id']].astype("int64").astype(str),  # iniファイルで指定された列名を使用
    'x_coord': drm_nodes[config['drm_nodes']['geometry']].x,  
    'y_coord': drm_nodes[config['drm_nodes']['geometry']].y,
    'node_type': drm_nodes[config['drm_nodes']['node_type']].apply(lambda x:convert_node_type(x)),
    'geometry': drm_nodes[config['drm_nodes']['geometry']],
    'nextmesh': drm_nodes[config['drm_nodes']['nextmesh']],
    'nextnode_id': drm_nodes[config['drm_nodes']['nextnode_id']]
})


gmns_links, gmns_nodes = merge_links_with_virtual_nodes(gmns_links, gmns_nodes)

gmns_nodes = gmns_nodes.drop(['nextmesh','nextnode_id'],axis=1)

# GMNSリンクデータを書き出し (iniファイルで指定されたパスを使用)
gmns_links.to_file(config['paths']['output_links'], index=False ,driver="GeoJSON")

# GMNSノードデータを書き出し (iniファイルで指定されたパスを使用)
gmns_nodes.to_file(config['paths']['output_nodes'], index=False ,driver="GeoJSON")

print("変換完了: GMNSフォーマットのデータが出力されました。")

