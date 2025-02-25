# my_io.py
import configparser
import os
import geopandas as gpd
import pandas as pd

def load_config(config_path="config.ini"):
    """
    INI形式のコンフィグファイルを読み込み、辞書として返す。
    """
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")
    conf = {
        "input": dict(config["INPUT"]),
        "output": dict(config["OUTPUT"]),
        "crs": {
            "input_crs": config["CRS"]["input_crs"],
            "export_crs": config["CRS"]["export_crs"]
        }
    }
    return conf

def load_geojson(filepath, crs=None):
    """
    GeoJSONファイルを読み込み、必要に応じてCRS変換を行ったGeoDataFrameを返す。
    """
    gdf = gpd.read_file(filepath)#, driver="GeoJSON"
    if crs is not None:
        gdf = gdf.to_crs(crs)
    return gdf

def load_input_data(config):
    """
    コンフィグに基づいて、リンクとノードのGeoJSONデータを読み込む。
    """
    link_path = config["input"]["link"]
    node_path = config["input"]["node"]
    target_crs = config["crs"]["input_crs"]
    ori_link = load_geojson(link_path, crs=target_crs)
    ori_node = load_geojson(node_path, crs=target_crs)
    return ori_link, ori_node

def export_geojson(gdf, output_path, crs="EPSG:4326"):
    """
    GeoDataFrameを指定したCRSに変換し、GeoJSON形式で出力する。
    """
    gdf_converted = gdf.to_crs(crs)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    gdf_converted.to_file(output_path, driver="GeoJSON")
    print(f"GeoJSON exported to {output_path}")

def export_csv(df, output_path):
    """
    DataFrameをCSV形式で出力する。
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"CSV exported to {output_path}")
