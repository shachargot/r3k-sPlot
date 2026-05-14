import ROOT
import yaml
import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt 
import mplhep as hep
import os

def make_sPlots(dataset, output, variables, weights=True, log=False):
    data_file = dataset["data_file_jpsi"]
    mc_file = dataset["jpsi_file"]
    tree_name = dataset["tree_name"]

    df_jpsi = ROOT.RDataFrame(tree_name, mc_file) 
    df_data = ROOT.RDataFrame(tree_name, data_file)
    mc_weight = dataset['mc_weight_branch'] if weights else None
    data_weight = dataset['data_weight_branch'] if weights else None

    for var in variables:
        name = variables[var]['name']
        ranges = variables[var]['range']
        frac = variables[var]['frac'] if 'frac' in variables[var] else False
        branch = variables[var]['branch'] if 'branch' in variables[var] else var
        bins = 50
   
        model = ROOT.RDF.TH1DModel(name, f";{var};{tree_name}", bins, ranges[0], ranges[1])
        if not frac:
            if weights:
                th1_mc = df_jpsi.Histo1D(model, branch, mc_weight).GetValue()
                th1_data = df_data.Histo1D(model, branch, data_weight).GetValue()        
            else:
                th1_mc = df_jpsi.Histo1D(model, branch).GetValue()
                th1_data = df_data.Histo1D(model, branch).GetValue()
        else: 
            var_num = branch.split("/")[0]
            var_denom = branch.split("/")[1]
            df_jpsi_ratio  = df_jpsi.Define("ratio_var",  f"{var_num} / {var_denom}")
            df_data_ratio  = df_data.Define("ratio_var",  f"{var_num} / {var_denom}")

            if weights:
                th1_mc   = df_jpsi_ratio.Histo1D(model, "ratio_var", mc_weight).GetValue()
                th1_data = df_data_ratio.Histo1D(model, "ratio_var", data_weight).GetValue()
            else:
                th1_mc   = df_jpsi_ratio.Histo1D(model, "ratio_var").GetValue()
                th1_data = df_data_ratio.Histo1D(model, "ratio_var").GetValue()

        values_mc = np.array([th1_mc.GetBinContent(i) for i in range(1, bins+1)])
        edges_mc  = np.array([th1_mc.GetBinLowEdge(i) for i in range(1, bins+2)])
        values_data = np.array([th1_data.GetBinContent(i) for i in range(1, bins+1)])
        edges_data = np.array([th1_data.GetBinLowEdge(i) for i in range(1, bins+2)])
    
        if (log and (var == 'Bcos' or var == 'bdt_score')):
            edges_mc = -1*np.log10(1-edges_mc)
            edges_data = -1*np.log10(1-edges_data) 
        if (log and var == 'LKdz'):
            edges_mc = np.log10(edges_mc)
            edges_data = np.log10(edges_data)

        yerr_mc   = np.array([th1_mc.GetBinError(i)   for i in range(1, bins+1)])
        yerr_data = np.array([th1_data.GetBinError(i) for i in range(1, bins+1)])

        norm_mc   = values_mc.sum()
        norm_data = values_data.sum()

        yerr_mc   = yerr_mc   / norm_mc
        yerr_data = yerr_data / norm_data
        values_mc   = values_mc   / norm_mc
        values_data = values_data / norm_data

        centers_mc = 0.5 * (edges_mc[:-1] + edges_mc[1:])
        centers_data = 0.5 * (edges_data[:-1] + edges_data[1:])
        xerr_mc    = 0.5 * np.diff(edges_mc)
        xerr_data    = 0.5 * np.diff(edges_data)
   
        fig, axes = plt.subplots(
            2, 1, figsize=(8, 8),
            gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
            sharex=True,
        )

        kw = dict(fmt="none", markersize=5, capsize=2.0,
                 capthick=1.2, linewidth=1.2, elinewidth=1.2)

        data_label = "Data 2023 (sWeight)" if weights else "Data 2023"
        mc_label = "MC (total weight)" if weights else "MC" 
        axes[0].errorbar(centers_data, values_data, xerr=xerr_data, yerr=yerr_data,
                      color='red', label=data_label, **kw)
        axes[0].errorbar(centers_mc, values_mc, xerr=xerr_mc, yerr=yerr_mc,
                     color='blue', label=mc_label, **kw)

        ratio = np.divide(values_data, values_mc, 
                  out=np.ones_like(values_data), 
                  where=values_mc != 0)
        ratio_err = np.divide(yerr_data, values_mc,
                              out=np.zeros_like(yerr_data),
                              where=values_mc != 0)
        axes[1].errorbar(centers_data, ratio, xerr=xerr_data, yerr=ratio_err,
                         color='black', **kw)
        axes[1].axhline(1.0, color='grey', linestyle='--', linewidth=1)
        axes[1].set_ylim(0, 2)
        
        hep.cms.label("Preliminary", ax=axes[0], loc=0, data=True, lumi=22.4, com=13.6)
        axes[0].set_ylabel("Normalized Entries")
        axes[0].legend()
        axes[1].set_ylabel("Ratio")
        axes[-1].set_xlabel(name)
        if (log and (var == 'Bcos' or var == 'bdt_score')): 
            axes[-1].set_xlabel(f"-log(1-{name})")
        if (log and var == 'LKdz'):
            axes[-1].set_xlabel(f"log({name})")
        fig.align_ylabels() 
        if (log and (var == 'Bcos' or var == 'bdt_score' or var == 'LKdz')):
            fig.savefig(f"{output}/{var.split('/')[0]}_log.png", dpi=150, bbox_inches="tight")
        else:  
            fig.savefig(f"{output}/{var.split('/')[0]}.png", dpi=150, bbox_inches="tight")
    

def main(args):
    with open(args.config, 'r') as f:
        cfg = yaml.safe_load(f)

    dataset_params = cfg['datasets_sWeight']
    var_params = cfg['variables']

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    make_sPlots(dataset_params, args.output, var_params, weights=args.weightOff, log=args.log)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, default='config.yml', help='fit configuration file (.yml)')
    parser.add_argument('-w', '--weightOff', action='store_false', help="Plot without weights")
    parser.add_argument('-log', '--log', action='store_true', help='Add log to cos, bdt_score, LKdz')
    parser.add_argument('-o', '--output', type=str, default='sPlots', help='Output directory')
    args = parser.parse_args()

    main(args)
