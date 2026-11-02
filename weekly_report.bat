@echo off
rem Tuesday 20:00-22:00 (Windows Task "FMM weekly report"): weekly report -> Word file in D:\FMM INFOS\DOCS, opened on screen.
cd /d E:\Claude\FMM
git pull -q
python -m fmm.growth --pc && python -m fmm.savestate "Weekly report [skip ci]"
