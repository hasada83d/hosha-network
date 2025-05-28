# -*- coding: utf-8 -*-
"""
Created on Wed May 28 21:26:07 2025

@author: hasada83d
"""

from hosha_network import develop_hosha_network
import geopandas as gpd
import os

def test_sample_run():
    node_gdf = gpd.read_file("sample_data/koenji_macro_node.geojson").to_crs("EPSG:6677")
    link_gdf = gpd.read_file("sample_data/koenji_macro_link.geojson").to_crs("EPSG:6677")

    develop_hosha_network(
        link_gdf=link_gdf,
        node_gdf=node_gdf,
        input_crs="EPSG:6677",
        output_dir="sample_output",
        export_crs="EPSG:4326",
        contract=False,
        export_display=True
    )
test_sample_run()
