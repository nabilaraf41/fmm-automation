@echo off
rem Daily (Windows Task "FMM shard prices"): save FC Mobile Forum Star Shards prices for the cloud Budget XI.
cd /d E:\Claude\FMM
python -m fmm.shards save && python -m fmm.savestate "Shard prices from PC [skip ci]"
python -m fmm.cardstats save && python -m fmm.savestate "Card stats from PC [skip ci]"
