import ROOT
import os
import yaml
import numpy as np
import pandas as pd
import argparse

def process_file_data(config_file, output_dir):
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    input_path = config['datasets']['data_file_jpsi']
    sWeight_file = config['sWeight_list']
    out_name = os.path.basename(input_path).replace('.root', f'_sPlot.root')
    out_path = os.path.join(output_dir, out_name)

    Bmass_branch = config['datasets']['b_mass_branch']

    if not os.path.exists(input_path):
        print(f"Skipping missing: {input_path}")
        return []

    sw_df = pd.read_csv(sWeight_file)
    bmass_arr = sw_df["Bmass"].values.astype(np.float64)
    sw_arr = sw_df["sWeight"].values.astype(np.float64)
    
    # Pass as numpy arrays - no string interpolation
    ROOT.gInterpreter.Declare("""
        #include <unordered_map>
        std::unordered_map<double, double> sw_map;
        void fill_sw_map(double* keys, double* vals, int n) {
            for (int i = 0; i < n; i++) sw_map[keys[i]] = vals[i];
        }
    """)

    tree_name = config['datasets']['tree_name']    

    # Fill the map efficiently
    ROOT.fill_sw_map(bmass_arr, sw_arr, len(sw_arr))

    df = ROOT.RDataFrame(tree_name, input_path)
    
    df = df.Filter(config['cutset'])
    df = df.Define("sWeight", f"sw_map.count({Bmass_branch}) ? sw_map[{Bmass_branch}] : 0.0")
    
    print(f"  -> Saving to {out_path}")
    
    opts = ROOT.RDF.RSnapshotOptions()
    opts.fMode = "RECREATE"
    df.Snapshot(tree_name, out_path, "", opts)

def process_file_MC(config_file, output_dir):
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    input_path = config['datasets']['jpsi_file']

    if not os.path.exists(input_path):
        print(f"Skipping missing: {input_path}")
        return []

    tree_name = config['datasets']['tree_name']

    df = ROOT.RDataFrame(tree_name, input_path)
    df = df.Filter(config['cutset'])

    out_name = os.path.basename(input_path).replace('.root', f'_sPlot.root')
    out_path = os.path.join(output_dir, out_name)
    print(f"  -> Saving to {out_path}")
    opts = ROOT.RDF.RSnapshotOptions()
    opts.fMode = "RECREATE"
    df.Snapshot(tree_name, out_path, "", opts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='config.yml')
    parser.add_argument('-o', '--output', default='')
    args = parser.parse_args()

    process_file_data(args.config, args.output)
    process_file_MC(args.config, args.output)
