# Setup repository

```
cmsrel CMSSW_13_1_0
cd CMSSW_13_1_0/src
cmsenv

git clone git@github.com:shachargot/r3k-sPlot.git
```

# Create sPlots
## Steps:
1. Make sWeight txt file from [r3k-fitter](git@github.com:shachargot/r3k-fitter.git) using `--splot` option
2. Configure `config.yml` with input jpsi data and MC files, and input sWeight txt file from (1) 
3. Run `sWeight.py` to apply sWeights to data
```
python3 sWeight.py [-c config.yml] [-o output_dir] 
```
4. Run `make_plots.py` to make sPlots 
```
python3 make_plots.py [-c config.yml] [-o output_dir] 
``` 
